# src/sources/source_connector.py
from collections.abc import Generator
from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, validator

from src.Chunkers.Chunker import Chunker
from src.Chunkers.RecursiveChunker import RecursiveChunker
from src.DataConnectors.DataConnector import DataConnector
from src.Loaders.AutoLoader import AutoLoader
from src.Loaders.Loader import Loader
from src.ModelFactories import ChunkerFactory, DataConnectorFactory, LoaderFactory
from src.Shared.CloudFile import CloudFile
from src.Shared.LocalFile import LocalFile
from src.Shared.RagDocument import RagDocument
from utils.platform_commons.logger import logger


class SourceConnector(BaseModel):

    data_connector: DataConnector = Field(..., description="Connector to data source")

    chunker: Chunker = Field(
        default=RecursiveChunker(),
        description="Chunker to be used to break down content"
    )

    loader: Loader = Field(
        default=AutoLoader(),
        description="Loader to load data from file / data type"
    )

    custom_metadata: Optional[dict] = Field(
        default_factory=dict,
        description="Custom metadata to be added to the vector"
    )

    def list_files_full(self) -> Generator[CloudFile, None, None]:
        yield from self.data_connector.connect_and_list_full()

    def list_files_delta(self, last_run:datetime) -> Generator[CloudFile, None, None]:
        yield from self.data_connector.connect_and_list_delta(last_run=last_run)

    def download_files(self, cloudFile:CloudFile) -> Generator[LocalFile, None, None]:
        yield from self.data_connector.connect_and_download(cloudFile=cloudFile)

    def load_data(self, file:LocalFile) -> Generator[RagDocument, None, None]:
        yield from self.loader.load(file=file)

    def chunk_data(self, document:RagDocument) -> Generator[list[RagDocument], None, None]:
        for chunk_set in self.chunker.chunk(documents=[document]):
            chunk_set_with_custom_metadata = [
                RagDocument(
                    id=chunk.id,
                    content=chunk.content,
                    metadata={
                        **chunk.metadata,
                        **self.custom_metadata,
                        **{"text": chunk.content}
                    }
                ) for chunk in chunk_set
            ]
            yield chunk_set_with_custom_metadata

    def validation(self) -> bool:
        core_validation = (
            self.data_connector.config_validation() and
            self.loader.config_validation() and
            self.chunker.config_validation()
        )
        loader_validation = self.loader.loader_name in self.data_connector.compatible_loaders
        return core_validation and loader_validation

    @validator("data_connector", pre=True, always=True)
    def deserialize_data_connector(cls, value):
        logger.info("*"*100)
        logger.info(f"deserialize_data_connector received: {value}")
        logger.info("*"*100)
        logger.info(f"deserialize_data_connector received: {value}")
        if not isinstance(value, dict) or not value:
            raise ValueError("Data connector configuration must be a non-empty dictionary")
        if "connector_name" not in value:
            raise ValueError("data_connector is missing 'connector_name'")
        return DataConnectorFactory.get_data_connector(value["connector_name"], value)


    @validator("chunker", pre=True, always=True)
    def deserialize_chunker(cls, value):
        if isinstance(value, dict):
            return ChunkerFactory.get_chunker(
                value.get("chunker_name"), value.get("chunker_information")
            )
        return value

    @validator("loader", pre=True, always=True)
    def deserialize_loader(cls, value):
        if isinstance(value, dict):
            return LoaderFactory.get_loader(
                value.get("loader_name"), value.get("loader_information")
            )
        return value

    def as_json(self) -> Dict[str, Any]:
        return self.dict(by_alias=True, exclude_unset=False)
