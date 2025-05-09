import json
from abc import ABC, abstractmethod

from pydantic import BaseModel

from src.Shared.RagSearch import RagSearchResult
from src.Shared.RagSinkInfo import RagSinkInfo
from src.Shared.RagVector import RagVector
from src.SinkConnectors.filter_utils import FilterCondition


class SinkConnector(ABC, BaseModel):
    @property
    @abstractmethod
    def sink_name(self) -> str:
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
        """config_validation sink setup"""

    @abstractmethod
    def store(self, vectors_to_store: list[RagVector]) -> int:
        """Store vectors with a given service"""

    @abstractmethod
    def get_documents(self, size: int) -> list[RagSearchResult]:
        """Get vectors for a specific file id"""

    @abstractmethod
    def search(
        self, vector: list[float], number_of_results: int, filters: list[FilterCondition] = {}
    ) -> list[RagSearchResult]:
        """Search vectors for a given service"""

    @abstractmethod
    def delete_vectors_with_file_id(self, file_id: str) -> bool:
        """Deletes vectors for a specific file id"""

    @abstractmethod
    def info(self) -> RagSinkInfo:
        """Get information about what is stores in the sink"""

    def as_json(self):
        """Python does not have built-in serialization.
        We need this logic to be able to respond in our API..

        Returns:
            _type_: the json to return
        """
        json_to_return = {}
        json_to_return["sink_name"] = self.sink_name
        json_to_return["sink_information"] = json.loads(self.json())
        return json_to_return

    def config(self):
        json_to_return = {}
        json_to_return["required_properties"] = self.required_properties
        json_to_return["optional_properties"] = self.optional_properties
        return json_to_return
