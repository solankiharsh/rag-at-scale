from celery import Celery
from elasticsearch import NotFoundError

from config import config
from src.Pipelines.Pipeline import Pipeline
from src.Shared.CloudFile import CloudFileSchema
from src.Shared.RagDocument import RagDocument
from src.Shared.source_config_schema import SourceConfigSchema
from src.Sources.SourceConnector import SourceConnector
from utils.platform_commons.logger import logger

app = Celery("tasks", broker=config.REDIS_BROKER_URL)


# --- Task Definitions ---
@app.task
def data_extraction_task(pipeline_config_dict: dict, extract_type: str, last_extraction=None):
    pipeline = Pipeline.create_pipeline(pipeline_config_dict)
    # logger.info(f"pipeline_config_dict: {pipeline_config_dict}")
    for source, cloud_file in pipeline.run_extraction(
        extract_type=extract_type, last_extraction=last_extraction
    ):
        print(f"Sending file: {cloud_file.id} from source '{source.name}' to data_processing_task")
        data_processing_task.apply_async(
            kwargs={
                "pipeline_config_dict": pipeline_config_dict,
                "source_config_dict": source.as_json(),
                "cloud_file_dict": cloud_file.dict(),
            },
            queue="data_processing",
        )


@app.task
def data_processing_task(
    pipeline_config_dict: dict, source_config_dict: dict, cloud_file_dict: dict
):
    try:
        logger.info("Starting data processing task")
        pipeline = Pipeline.create_pipeline(pipeline_config_dict)

        source = SourceConnector.create_source(SourceConfigSchema(**source_config_dict))
        logger.debug(f"Source config: {source_config_dict}")

        # Validate and log cloud file
        cloud_file = CloudFileSchema(**cloud_file_dict)
        logger.info(f"Validated cloud file: {cloud_file}")

        batched_chunks: list[RagDocument] = []
        batch_number = 0

        for chunks in pipeline.process_document(source, cloud_file):
            batched_chunks.extend(chunks)
            logger.debug(f"Collected {len(batched_chunks)} chunks so far")

            if len(batched_chunks) > 200:
                logger.info(
                    f"Sending batch #{batch_number} for file: {cloud_file.id} to ingestion task"
                )
                data_embed_ingest_task.apply_async(
                    kwargs={
                        "pipeline_config_dict": pipeline_config_dict,
                        "chunks_dicts": [chunk.to_json() for chunk in batched_chunks],
                    },
                    queue="data_embed_ingest",
                )
                batched_chunks = []
                batch_number += 1

        if batched_chunks:
            logger.info(f"Sending final batch #{batch_number} for file: {cloud_file.id}")
            data_embed_ingest_task.apply_async(
                kwargs={
                    "pipeline_config_dict": pipeline_config_dict,
                    "chunks_dicts": [chunk.to_json() for chunk in batched_chunks],
                },
                queue="data_embed_ingest",
            )

        logger.info("Data processing task completed successfully")

    except Exception as e:
        logger.error(f"Error in data_processing_task: {e}")
        raise


@app.task
def data_embed_ingest_task(pipeline_config_dict: dict, chunks_dicts: list[dict]):
    pipeline = Pipeline.create_pipeline(pipeline_config_dict)
    chunks: list[RagDocument] = [RagDocument.as_file(chunk_dict) for chunk_dict in chunks_dicts]

    logger.info(f"Starting embedding and ingestion task for {len(chunks)} chunks")

    logger.info(f"pipeline_config_dict: {pipeline_config_dict}")

    index_name = pipeline_config_dict.get("sink", {}).get("settings").get("index")
    if not index_name:
        logger.error("Index name missing in pipeline config.")
        return

    try:
        # Embed and ingest, the sink now handles index creation
        vectors_written = pipeline.embed_and_ingest(chunks)
    except NotFoundError:
        logger.error(f"Index '{index_name}' not found during ingestion, even after sink handling.")
        return

    logger.info(f"Finished embedding and storing {vectors_written} vectors in index '{index_name}'")
