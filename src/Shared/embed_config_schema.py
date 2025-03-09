# src/schemas/embed_config_schema.py

from pydantic import BaseModel, Field


class EmbedConfigSchema(BaseModel):
    model_name: str = Field(..., description="Name of the embedding model")
    settings: dict = Field(default_factory=dict, description="Embedding model specific settings")
