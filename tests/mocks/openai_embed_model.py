"""
Mock OpenAIEmbedModel for testing purposes.
This file contains a mock implementation of the OpenAIEmbedModel class.
"""

from typing import Optional

from tests.mocks.rag_document import RagDocument


class OpenAIEmbedModel:
    """
    Mock OpenAI Embedding Model for testing.
    """

    api_key: str = "mock_api_key"
    max_retries: Optional[int] = 20
    chunk_size: Optional[int] = 1000

    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def embed_name(self) -> str:
        return "text-embedding-ada-002"

    @property
    def required_properties(self) -> list[str]:
        return ["api_key"]

    @property
    def optional_properties(self) -> list[str]:
        return ["max_retries", "chunk_size"]

    def validation(self) -> bool:
        """Validates the embedding model configuration."""
        return bool(self.api_key)

    async def embed(self, documents: list[RagDocument]) -> tuple[list, dict]:
        """Mock embed method that returns sample embeddings."""
        # For testing, we'll generate mock embeddings
        vectors = []
        for i, doc in enumerate(documents):
            # Generate a simple mock embedding vector
            vector = [0.1 * (i + j) for j in range(10)]  # 10-dimensional vector for simplicity
            vectors.append(vector)
        
        # Mock usage information
        usage = {
            "prompt_tokens": len(documents) * 100,  # Simulate token usage
            "total_tokens": len(documents) * 100
        }
        
        return vectors, usage

    def embed_query(self, query: str) -> list[float]:
        """Mock embed_query method."""
        # Generate a simple mock embedding vector for the query
        return [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]