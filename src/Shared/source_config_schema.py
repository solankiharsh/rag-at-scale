# src/schemas/source_config_schema.py

from pydantic import BaseModel, Field


class SourceConfigSchema(BaseModel):
    name: str = Field(..., description="Name of the source")
    type: str = Field("s3connector", description="The type of source (default: 's3')")
    settings: dict = Field({}, description="Settings for the source")
