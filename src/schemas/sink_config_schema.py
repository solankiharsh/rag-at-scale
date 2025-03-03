# src/schemas/sink_config_schema.py

from pydantic import BaseModel, Field


class SinkConfigSchema(BaseModel):
    type: str = Field(..., description="Type of sink (e.g., 'pinecone')")
    settings: dict = Field(..., description="Sink specific settings")