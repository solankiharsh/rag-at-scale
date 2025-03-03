# src/sources/source_connector.py
from abc import ABC, abstractmethod
from typing import Generator, List

from src.schemas.cloud_file_schema import CloudFileSchema
from src.schemas.document_schema import DocumentSchema
from src.schemas.source_config_schema import SourceConfigSchema


class SourceConnector(ABC):
    def __init__(self, config: SourceConfigSchema):
        self.name = config.name
        self.settings = config.settings

    @staticmethod
    def create_source(source_config: SourceConfigSchema):
        source_type = source_config.type.lower()
        print(f"source_type: {source_type}")
        if source_type == "s3":
            from src.sources.s3_source import S3SourceConnector
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
    def download_files(self, cloudFile: CloudFileSchema) -> Generator[object, None, None]: # object can be LocalFile representation
        """Downloads files to local storage. Yields local file paths/objects."""
        pass

    @abstractmethod
    def load_data(self, file: object) -> Generator[DocumentSchema, None, None]: # file is the local file object
        """Loads data from a local file and yields NeumDocumentSchema objects."""
        pass

    @abstractmethod
    def chunk_data(self, document: DocumentSchema) -> Generator[List[DocumentSchema], None, None]:
        """Chunks a document into smaller NeumDocumentSchema objects."""
        pass