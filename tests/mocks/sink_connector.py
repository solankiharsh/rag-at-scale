"""
Mock SinkConnector for testing purposes.
This file contains a mock implementation of the SinkConnector class.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class FilterCondition(BaseModel):
    """Filter condition for querying vector stores."""
    field: str
    operator: str
    value: Any


class RagSearchResult(BaseModel):
    """Result from a RAG search operation."""
    id: str
    metadata: dict
    score: float
    vector: Optional[List[float]] = None


class RagSinkInfo(BaseModel):
    """Information about a RAG sink."""
    number_vectors_stored: int


class SinkConnector(ABC, BaseModel):
    """Base class for all sink connectors."""
    
    sink_name: str = Field(..., description="Name of the sink connector")
    required_properties: list[str] = Field(..., description="List of required properties")
    optional_properties: list[str] = Field(..., description="List of optional properties")
    
    @abstractmethod
    def validation(self) -> bool:
        """Validate the sink connector configuration."""
        pass
    
    @abstractmethod
    def store(self, vectors_to_store: list[Any]) -> int:
        """Store vectors in the sink."""
        pass
    
    @abstractmethod
    def search(
        self, vector: list[float], number_of_results: int, filters: list[FilterCondition] = []
    ) -> list[RagSearchResult]:
        """Search for similar vectors in the sink."""
        pass
    
    @abstractmethod
    def info(self) -> RagSinkInfo:
        """Get information about the sink."""
        pass