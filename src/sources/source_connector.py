# src/sources/source_connector.py
from abc import ABC, abstractmethod
from typing import Generator

from src.schemas.cloud_file_schema import CloudFileSchema
from src.schemas.source_config_schema import SourceConfigSchema


class SourceConnector(ABC):
    def __init__(self, config: SourceConfigSchema):
        self.name = config.name
        self.settings = config.settings

    @staticmethod
    def create_source(source_config: SourceConfigSchema):
        source_type = source_config.type.lower()
        print(f"source_type: {source_type}")
        if source_type == "s3connector":
            from src.DataConnectors.S3_Connector import S3SourceConnector
            return S3SourceConnector(config=source_config)
        else:
            raise ValueError(f"Unsupported source type: {source_type}")

    def as_json(self):
        return {
            "name": self.name,
            "settings": self.settings
        }

    @abstractmethod
    def list_files_full(self) -> Generator[CloudFileSchema, None, None]:
        """Lists all files in the source."""
        pass

    @abstractmethod
    def list_files_delta(self, last_run: str) -> Generator[CloudFileSchema, None, None]:
        """Lists files modified since last run."""
        pass

    @abstractmethod
    def download_files(
        self, cloud_file: CloudFileSchema
    ) -> Generator[object, None, None]:  # object can be LocalFile representation
        """Downloads files to local storage. Yields local file paths/objects."""
        pass