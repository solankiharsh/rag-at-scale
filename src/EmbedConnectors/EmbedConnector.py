import json
from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel

from src.Shared.RagDocument import RagDocument


class EmbedConnector(ABC, BaseModel):

    @property
    @abstractmethod
    def embed_name(self) -> str:
        pass
    
    @property
    @abstractmethod
    def required_properties(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def optional_properties(self) -> list[str]:
        pass

    @abstractmethod
    def validation(self) -> bool:
        """Validates the embedding model configuration."""
        return True  # Add proper validation logic if needed

    @abstractmethod
    async def embed(self, documents: list[RagDocument]) -> tuple[list[Any], dict[Any, Any]]:
        """Generates embeddings asynchronously."""
        pass

    
    # @abstractmethod
    # def embed_query(self, query:str) -> list[float]:
    #     """Generate embeddings with a given service"""
    
    def embed_query(self, query: str) -> list[float]:
        raise NotImplementedError("embed_query is not supported in HamEmbedModel")



    def as_json(self):
        """Python does not have built in serialization.
        We need this logic to be able to respond in our API..

        Returns:
            _type_: the json to return
        """
        json_to_return = {}
        json_to_return['embed_name'] = self.embed_name
        json_to_return['embed_information'] = json.loads(self.json())
        return json_to_return
    
    def config(self):
        json_to_return = {}
        json_to_return['required_properties'] = self.required_properties
        json_to_return['optional_properties'] = self.optional_properties
        return json_to_return