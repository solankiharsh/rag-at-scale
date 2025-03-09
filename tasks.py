# src/tasks.py

from celery import Celery

from config import config
from src.Pipelines.pipeline import Pipeline
from src.schemas.cloud_file_schema import CloudFileSchema
from src.schemas.document_schema import DocumentSchema
from src.schemas.source_config_schema import SourceConfigSchema
from src.Shared.RagDocument import RagDocument
from src.Sources.source_connector import SourceConnector
from utils.platform_commons.logger import logger

app = Celery('tasks', broker=config.REDIS_BROKER_URL)

# --- Task Definitions ---

@app.task
def data_extraction_task(pipeline_config_dict: dict, extract_type: str, last_extraction=None):
    pipeline = Pipeline.create_pipeline(pipeline_config_dict)
    for source, cloud_file in pipeline.run_extraction(
        extract_type=extract_type, last_extraction=last_extraction
    ):
        print(f"Sending file: {cloud_file.id} from source '{source.name}' to data_processing_task")
        data_processing_task.apply_async(
            kwargs={
                "pipeline_config_dict": pipeline_config_dict,
                "source_config_dict": source.as_json(),
                "cloud_file_dict": cloud_file.dict()
            },
            queue="data_processing"
        )

@app.task
def data_processing_task(
    pipeline_config_dict: dict,
    source_config_dict: dict,
    cloud_file_dict: dict
):
    pipeline = Pipeline.create_pipeline(pipeline_config_dict)
    print(f"source_config_dict:> {source_config_dict}")
    source = SourceConnector.create_source(SourceConfigSchema(**source_config_dict))
    cloud_file = CloudFileSchema(**cloud_file_dict)

    batched_chunks: list[DocumentSchema] = []
    batch_number = 0
    for chunks in pipeline.process_document(source, cloud_file): # Now process_document yields chunks
        batched_chunks.extend(chunks)
        if len(batched_chunks) > 200:
            print(
                f"Sending batch #{batch_number} for file: {cloud_file.id} "
                "to data_embed_ingest_task"
            )
            data_embed_ingest_task.apply_async(
                kwargs={
                    "pipeline_config_dict": pipeline_config_dict,
                    "chunks_dicts": [chunk.to_json() for chunk in batched_chunks]
                },
                queue="data_embed_ingest"
            )
            batched_chunks = []
            batch_number += 1

    if len(batched_chunks) > 0:
        print(
            f"Sending final batch #{batch_number} for file: {cloud_file.id} "
            "to data_embed_ingest_task"
        )
        data_embed_ingest_task.apply_async(
            kwargs={
                "pipeline_config_dict": pipeline_config_dict,
                "chunks_dicts": [chunk.to_json() for chunk in batched_chunks]
            },
            queue="data_embed_ingest"
        )

@app.task
def data_embed_ingest_task(pipeline_config_dict: dict, chunks_dicts: list[dict]):
    pipeline = Pipeline.create_pipeline(pipeline_config_dict)
    chunks: list[RagDocument] = [
        RagDocument.as_file(chunk_dict) for chunk_dict in chunks_dicts
    ]
    
    logger.info(f"chunks: {chunks}")

    vectors_written = pipeline.embed_and_ingest(chunks) # Now pipeline handles embed and ingest
    print(f"Finished embedding and storing {vectors_written} vectors")

# --- Example Task Trigger (for testing, can be moved to API) ---
if __name__ == '__main__':
    # Example Pipeline Configuration (Load from DB or config file in real app)
    pipeline_config_data = {
        "id": "pipeline-1",
        "name": "Document Pipeline",
        "sources": [
            {
                "name": "s3-source-1",
                "type": "s3",
                "settings": {
                    "bucket_name": "your-s3-bucket-name", # Replace with your bucket
                    "prefix": "documents/"
                }
            }
        ],
        "embed_model": {
            "model_name": "sentence-transformers",
            "settings": {"model_name": config.EMBEDDING_MODEL_NAME} # Use config for model name
        },
        "sink": {
            "type": "pinecone",
            "settings": {
                "api_key": config.VECTOR_DB_API_KEY, # Use config for API key
                "environment": config.VECTOR_DB_ENVIRONMENT, # Use config for environment
                "index_name": config.VECTOR_DB_INDEX_NAME # Use config for index name
            }
        }
    }

    print("Triggering Data Extraction Task (Full Sync)")
    data_extraction_task.apply_async(
        kwargs={"pipeline_config_dict": pipeline_config_data, "extract_type": "full"},
        queue="data_extraction"
    )