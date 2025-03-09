# src/schemas/cloud_file_schema.py
from typing import Optional

from pydantic import BaseModel


class CloudFileSchema(BaseModel):
    id: str
    name: str
    path: str
    metadata: Optional[dict] = None
    type: Optional[str] = None