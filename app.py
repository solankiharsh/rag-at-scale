# src/app.py

from fastapi import Body, FastAPI, HTTPException

from src.pipeline.pipeline import Pipeline
from src.schemas.pipeline_config_schema import PipelineConfigSchema
from tasks import data_extraction_task

# src/app.py



app = FastAPI()

# Configuration (adjust these values or load from environment)
RAG_ENDPOINT = "http://0.0.0.0:8000"

# # --- Load Pipeline Config (Example - in real app, load from DB or config file) ---
# # Example: Load from a JSON file (pipeline_config.json)
# # Ensure pipeline_config.json exists with valid PipelineConfigSchema data
# try:
#     with open("pipeline_config.json", "r") as f:
#         pipeline_config_data = json.load(f)
#         pipeline_config = PipelineConfigSchema(**pipeline_config_data) # Validate against schema
# except FileNotFoundError:
#     raise Exception("pipeline_config.json not found. Create this file with pipeline configuration.")
# except Exception as e:
#     raise Exception(f"Error loading pipeline configuration: {e}")


# @app.post("/pipelines/{pipeline_id}/run")
# async def run_pipeline(pipeline_id: str, extract_type: str = "full"):
#     """Triggers a pipeline run for a given pipeline ID."""
#     if pipeline_config.id != pipeline_id: # Basic ID check, enhance as needed
#         raise HTTPException(status_code=404, detail="Pipeline not found")

#     if extract_type not in ["full", "delta"]:
#         raise HTTPException(status_code=400, detail="Invalid extract_type. Must be 'full' or 'delta'.")

#     task = data_extraction_task.apply_async(
#         kwargs={"pipeline_config_dict": pipeline_config.dict(), "extract_type": extract_type},
#         queue="data_extraction"
#     )
#     return {"message": f"Pipeline '{pipeline_id}' run triggered for extraction type '{extract_type}'. Task ID: {task.id}"}

app = FastAPI()

# In-memory storage for pipeline configurations (replace with DB in production)
pipeline_configs: dict[str, PipelineConfigSchema] = {}

# --- API Endpoints ---

# In-memory storage for pipeline configurations (replace with DB in production)
pipeline_configs: dict[str, PipelineConfigSchema] = {}

@app.post("/pipelines/", response_model=PipelineConfigSchema, status_code=201)
async def create_pipeline(pipeline_config: PipelineConfigSchema):
    """Creates a new pipeline configuration."""
    pipeline_id = pipeline_config.id  # Assuming pipeline ID is provided in config
    if pipeline_id in pipeline_configs:
        raise HTTPException(status_code=400, detail="Pipeline ID already exists")
    pipeline_configs[pipeline_id] = pipeline_config
    return pipeline_config

@app.get("/pipelines/{pipeline_id}", response_model=PipelineConfigSchema)
async def get_pipeline(pipeline_id: str):
    """Retrieves a pipeline configuration by ID."""
    if pipeline_id not in pipeline_configs:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    return pipeline_configs[pipeline_id]

@app.post("/pipelines/{pipeline_id}/run")
async def run_pipeline(pipeline_id: str, extract_type: str = "full"):
    """Triggers a pipeline run for a given pipeline ID."""
    if pipeline_id not in pipeline_configs:
        raise HTTPException(status_code=404, detail="Pipeline not found")

    pipeline_config = pipeline_configs[pipeline_id]

    if extract_type not in ["full", "delta"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid extract_type. Must be 'full' or 'delta'."
        )

    task = data_extraction_task.apply_async(
        kwargs={"pipeline_config_dict": pipeline_config.dict(), "extract_type": extract_type},
        queue="data_extraction"
    )
    return {
        "message": (
            f"Pipeline '{pipeline_id}' run triggered for extraction type "
            f"'{extract_type}'. Task ID: {task.id}"
        )
    }

# Search endpoint
@app.post("/pipelines/{pipeline_id}/search")
async def search_embedded_chunks(
    pipeline_id: str,
    query: str = Body(..., embed=True),
    num_of_results: int = 3
):
    """
    Searches the embedded chunks stored in the vector database for the given pipeline.
    """
    if pipeline_id not in pipeline_configs:
        raise HTTPException(status_code=404, detail="Pipeline not found")
    
    # Create a Pipeline instance using the stored configuration
    pipeline_config = pipeline_configs[pipeline_id]
    pipeline = Pipeline(pipeline_config)
    
    # Use the sink's search functionality to query embedded chunks.
    try:
        search_results = pipeline.sink.search(query=query, size=num_of_results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {e}")
    
    return search_results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
    