# src/schemas/pipeline_config_schema.py

from pydantic import BaseModel, Field

from src.Shared.embed_config_schema import EmbedConfigSchema
from src.Shared.sink_config_schema import SinkConfigSchema
from src.Shared.source_config_schema import SourceConfigSchema


class PipelineConfigSchema(BaseModel):
    id: str = Field(..., description="Unique identifier for the pipeline")
    name: str = Field(..., description="Name of the pipeline")
    sources: list[SourceConfigSchema] = Field(..., description="List of source configurations")
    embed_model: EmbedConfigSchema = Field(..., description="Configuration for the embedding model")
    sink: SinkConfigSchema = Field(..., description="Configuration for the sink (Vector DB)")
