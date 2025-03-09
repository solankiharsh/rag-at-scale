import json
from abc import ABC, abstractmethod
from collections.abc import Generator

from pydantic import BaseModel

from src.Shared.RagDocument import RagDocument


class Chunker(ABC, BaseModel):
    @property
    @abstractmethod
    def chunker_name(self) -> str:
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
    def chunk(self, documents: list[RagDocument]) -> Generator[list[RagDocument], None, None]:
        """Chunk documents into more documents"""

    @abstractmethod
    def config_validation(self) -> bool:
        """config_validation if the chunker is correctly configured"""

    def as_json(self):
        """Python does not have built in serialization.
        We need this logic to be able to respond in our API..

        Returns:
            _type_: the json to return
        """
        json_to_return = {}
        json_to_return["chunker_name"] = self.chunker_name
        json_to_return["chunker_information"] = json.loads(self.json())
        return json_to_return

    def config(self):
        json_to_return = {}
        json_to_return["required_properties"] = self.required_properties
        json_to_return["optional_properties"] = self.optional_properties
        return json_to_return
