# src/app.py


import nltk
from fastapi import FastAPI, HTTPException

from src.ModelFactories.EmbedConnectorFactory import EmbedConnectorFactory
from src.ModelFactories.SinkConnectorFactory import SinkConnectorFactory
from src.Shared.pipeline_config_schema import PipelineConfigSchema
from src.Shared.RagDocument import RagDocument
from tasks import data_extraction_task
from utils.platform_commons.logger import logger

# /Users/Z0084K9/nltk_data/corpora/stopwords

nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")

app = FastAPI()

# --- API Endpoints ---

# In-memory storage for pipeline configurations (replace with DB in production)
pipeline_configs: dict[str, PipelineConfigSchema] = {}


@app.post("/pipelines/", response_model=PipelineConfigSchema, status_code=201)
async def create_pipeline(pipeline_config: PipelineConfigSchema):
    pipeline_id = pipeline_config.id
    logger.info(f"Received request to create pipeline with ID: {pipeline_id}")

    if pipeline_id in pipeline_configs:
        logger.warning(f"Pipeline ID '{pipeline_id}' already exists.")
        raise HTTPException(status_code=400, detail="Pipeline ID already exists")

    logger.info(f"pipeline_config: {pipeline_config}")

    # Extract Elasticsearch settings
    index_name = pipeline_config.sink.settings.get("index")
    host = pipeline_config.sink.settings.get("hosts")

    if host and isinstance(host, list):
        host = host[0]

    logger.info(f"Extracted index_name: {index_name}, host: {host}")

    if not host or not index_name:
        logger.error("Elasticsearch host or index name is missing")
        raise HTTPException(status_code=400, detail="Elasticsearch host or index name is missing")

    # Initialize and store the pipeline
    try:
        logger.info(f"Initializing pipeline with ID: {pipeline_id}")
        pipeline_configs[pipeline_id] = pipeline_config
        logger.info(f"Pipeline initialized for ID: {pipeline_id}")

        pipeline_configs[pipeline_id] = pipeline_config
        logger.info(f"Pipeline configuration saved for ID: {pipeline_id}")

        return pipeline_config

    except Exception as e:
        logger.error(f"Failed to initialize pipeline '{pipeline_id}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize pipeline: {str(e)}")


@app.get("/pipelines/{pipeline_id}", response_model=PipelineConfigSchema)
async def get_pipeline(pipeline_id: str):
    if pipeline_id not in pipeline_configs:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline_configs[pipeline_id]


@app.post("/pipelines/{pipeline_id}/run")
async def run_pipeline(pipeline_id: str, extract_type: str = "full"):
    logger.info(f"Triggering pipeline '{pipeline_id}' with extract type '{extract_type}'")

    if pipeline_id not in pipeline_configs:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline_config = pipeline_configs[pipeline_id]

    # Extract Elasticsearch settings from sink.settings
    index_name = pipeline_config.sink.settings.get("index")
    host = pipeline_config.sink.settings.get("hosts")
    if host and isinstance(host, list):
        host = host[0]

    logger.info(f"Extracted Elasticsearch settings - index: {index_name}, host: {host}")

    if not host or not index_name:
        logger.error("Elasticsearch host or index name is missing")
        raise HTTPException(status_code=400, detail="Elasticsearch host or index name is missing")

    if extract_type not in ["full", "delta"]:
        raise HTTPException(
            status_code=400, detail="Invalid extract_type. Must be 'full' or 'delta'."
        )

    task = data_extraction_task.apply_async(
        kwargs={"pipeline_config_dict": pipeline_config.dict(), "extract_type": extract_type},
        queue="data_extraction",
    )
    return {
        "message": (
            f"Pipeline '{pipeline_id}' run triggered for extraction type "
            f"'{extract_type}'. Task ID: {task.id}"
        )
    }


# Search endpoint
@app.post("/pipelines/{pipeline_id}/search")
async def search_pipeline(pipeline_id: str, query: str, top_k: int = 5):
    """Searches documents in the sink using the embedded query."""
    if pipeline_id not in pipeline_configs:
        logger.error(f"❌ Pipeline '{pipeline_id}' not found")
        raise HTTPException(status_code=404, detail="Pipeline not found")

    # Use the same creation method to ensure es_monitor is set
    pipeline_config = pipeline_configs[pipeline_id]

    try:
        logger.info(f"🔍 Starting search in pipeline: {pipeline_id}")
        logger.info(f"📘 Query: {query}, Top K: {top_k}")

        # Wrap query in a RagDocument with required fields
        query_document = RagDocument(id="query-id", content=query, metadata={})

        # Instantiate the embed connector using the factory
        embed_connector = EmbedConnectorFactory.get_embed(
            embed_name=pipeline_config.embed_model.model_name,
            embed_information=pipeline_config.embed_model.settings,
        )
        logger.info("Embed connector instantiated successfully.")

        embeddings, _ = await embed_connector.embed([query_document])

        if not embeddings or not isinstance(embeddings, list):
            raise ValueError("Failed to generate embeddings for query")
        embedded_query = embeddings[0]
        logger.info(f"📊 Embedded query vector: {embedded_query}")

        sink_connector = SinkConnectorFactory.get_sink(
            pipeline_config.sink.type, pipeline_config.sink.settings
        )

        # Perform the search using the sink's search method
        results = sink_connector.search(embedded_query, top_k)
        logger.info(f"✅ Search successful, results count: {len(results)}")

        return {"results": [result.dict() for result in results]}

    except Exception as e:
        logger.error(f"❌ Search failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.get("/pipelines/{pipeline_id}/documents")
async def get_documents(pipeline_id: str, size: int = 10):
    if pipeline_id not in pipeline_configs:
        logger.error(f"Pipeline '{pipeline_id}' not found.")
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline_config = pipeline_configs[pipeline_id]

    try:
        # Create the sink connector from the config
        sink_connector = SinkConnectorFactory.get_sink(
            pipeline_config.sink.type, pipeline_config.sink.settings
        )
        # Ensure index exists (if required) before querying documents
        # pipeline_config.

        results = sink_connector.get_documents(size=size)
        logger.info(f"Retrieved {len(results)} documents from Elasticsearch.")
        return {"documents": [result.dict() for result in results]}
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to retrieve documents: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
