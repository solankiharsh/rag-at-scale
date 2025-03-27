import time

from celery import Celery
from elasticsearch import NotFoundError

from config import config
from src.Pipelines.IngestPipeline import Pipeline
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
    for source, cloud_file in pipeline.run_extraction(
        extract_type=extract_type, last_extraction=last_extraction
    ):
        logger.info(
            f"Sending file: {cloud_file.id} from source '{source.name}' to data_processing_task"
        )
        data_processing_task.apply_async(
            kwargs={
                "pipeline_config_dict": pipeline_config_dict,
                "source_config_dict": source.as_json(),
                "cloud_file_dict": cloud_file.dict(),
            },
            queue="data_processing",
        )

@app.task
def data_processing_task(pipeline_config_dict: dict, source_config_dict: dict, cloud_file_dict: dict):
    try:
        logger.info("Starting data processing task")
        start_time = time.perf_counter()
        
        pipeline = Pipeline.create_pipeline(pipeline_config_dict)
        source = SourceConnector.create_source(SourceConfigSchema(**source_config_dict))
        logger.debug(f"Source config: {source_config_dict}")
        
        cloud_file = CloudFileSchema(**cloud_file_dict)
        logger.info(f"Validated cloud file: {cloud_file}")
        
        doc_processing_start = time.perf_counter()
        batched_chunks: list[RagDocument] = []
        batch_number = 0

        # Process document and measure chunking time
        for chunks in pipeline.process_document(source, cloud_file):
            batched_chunks.extend(chunks)
            logger.debug(f"Collected {len(batched_chunks)} chunks so far")
        chunking_time = time.perf_counter() - doc_processing_start
        logger.info(
            f"Document {cloud_file.id} processed and chunked in {chunking_time:.2f} seconds"
        )

        # If there are too many chunks, send them in batches
        if batched_chunks:
            logger.info(
                f"Sending final batch with {len(batched_chunks)} chunks for file: {cloud_file.id}"
            )
            data_embed_ingest_task.apply_async(
                kwargs={
                    "pipeline_config_dict": pipeline_config_dict,
                    "chunks_dicts": [chunk.to_json() for chunk in batched_chunks],
                },
                queue="data_embed_ingest",
            )
        
        total_time = time.perf_counter() - start_time
        logger.info(
            f"Data processing task for file {cloud_file.id} completed in {total_time:.2f} seconds"
        )
    
    except Exception as e:
        logger.error(f"Error in data_processing_task: {e}")
        raise

@app.task
def data_embed_ingest_task(pipeline_config_dict: dict, chunks_dicts: list[dict]):
    pipeline = Pipeline.create_pipeline(pipeline_config_dict)
    chunks: list[RagDocument] = [RagDocument.as_file(chunk_dict) for chunk_dict in chunks_dicts]

    index_name = pipeline_config_dict.get("sink", {}).get("settings").get("index")
    if not index_name:
        logger.error("Index name missing in pipeline config.")
        return

    logger.info(f"Starting embedding and ingestion task for {len(chunks)} chunks")
    start_time = time.perf_counter()
    
    try:
        # Run the asynchronous embed_and_ingest method
        embed_start = time.perf_counter()
        vectors_written = pipeline.embed_and_ingest(chunks)
        embed_time = time.perf_counter() - embed_start
        logger.info(f"Embedding completed in {embed_time:.2f} seconds")
    except NotFoundError:
        logger.error(f"Index '{index_name}' not found during ingestion, even after sink handling.")
        return
    except Exception as e:
        logger.error(f"Error during embed and ingest: {e}", exc_info=True)
        return

    total_time = time.perf_counter() - start_time
    logger.info(
        f"Finished embedding and storing {vectors_written} vectors in index "
        f"'{index_name}' in {total_time:.2f} seconds"
    )

