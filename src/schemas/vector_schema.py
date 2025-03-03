# src/schemas/vector_schema.py
from typing import Optional

from pydantic import BaseModel


class VectorSchema(BaseModel):
    id: str
    vector: list[float]
    metadata: Optional[dict] = None
