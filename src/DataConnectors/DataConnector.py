import json
from abc import ABC, abstractmethod
from collections.abc import Generator
from datetime import datetime

from pydantic import BaseModel

from src.Shared.CloudFile import CloudFileSchema
from src.Shared.LocalFile import LocalFile


class DataConnector(BaseModel, ABC):
    @property
    @abstractmethod
    def connector_name(self) -> str:
        pass

    @property
    @abstractmethod
    def required_properties(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def optional_properties(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def available_metadata(self) -> list[str]:
        pass

    @property
    @abstractmethod
    def schedule_avaialable(self) -> bool:
        pass

    @property
    @abstractmethod
    def auto_sync_available(self) -> bool:
        pass

    @property
    @abstractmethod
    def compatible_loaders(self) -> list[str]:
        pass

    @abstractmethod
    def connect_and_list_full(self) -> Generator[CloudFileSchema, None, None]:
        """Connect to source and download file into local storage"""

    @abstractmethod
    def connect_and_list_delta(self, last_run: datetime) -> Generator[LocalFile, None, None]:
        """Check for changes in the source Code to be pushed to a worker and run on a schedule"""

    @abstractmethod
    def connect_and_download(self, cloudFile: CloudFileSchema) -> Generator[LocalFile, None, None]:
        """Connect to source and download file into local storage"""

    @abstractmethod
    def config_validation(self) -> bool:
        """config_validation if the connector is correctly configured"""

    # To do auto_sync logic.

    def as_json(self):
        """Python does not have built in serialization.
        We need this logic to be able to respond in our API..

        Returns:
            _type_: the json to return
        """
        json_to_return = {}
        json_to_return["connector_name"] = self.connector_name
        json_to_return["connector_information"] = json.loads(self.json())
        return json_to_return

    def config(self):
        json_to_return = {}
        json_to_return["required_properties"] = self.required_properties
        json_to_return["optional_properties"] = self.optional_properties
        json_to_return["available_metadata"] = self.available_metadata
        json_to_return["compatible_loaders"] = self.compatible_loaders
        json_to_return["schedule_avaialable"] = self.schedule_avaialable
        json_to_return["auto_sync_available"] = self.auto_sync_available
        return json_to_return
