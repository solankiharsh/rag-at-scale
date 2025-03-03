# src/schemas/document_schema.py
from typing import Optional

from pydantic import BaseModel


class DocumentSchema(BaseModel):
    id: str
    content: str
    metadata: Optional[dict] = None

    def to_json(self):
        return self.dict()

    @staticmethod
    def as_file(data: dict):
        return DocumentSchema(**data)
