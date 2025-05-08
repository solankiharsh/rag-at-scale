"""
Mock Loader for testing purposes.
This file contains a mock implementation of the Loader class.
"""

from abc import ABC, abstractmethod
from collections.abc import Generator

from pydantic import BaseModel

from tests.mocks.local_file import LocalFile
from tests.mocks.rag_document import RagDocument


class Loader(ABC, BaseModel):
    """
    Base class for all loaders.
    
    Loaders are responsible for loading data from files into RagDocument objects.
    """
    
    @property
    @abstractmethod
    def loader_name(self) -> str:
        """Name of the loader."""
        pass
    
    @property
    @abstractmethod
    def required_properties(self) -> list[str]:
        """List of required properties for the loader."""
        pass
    
    @property
    @abstractmethod
    def optional_properties(self) -> list[str]:
        """List of optional properties for the loader."""
        pass
    
    @property
    @abstractmethod
    def available_metadata(self) -> list[str]:
        """List of available metadata fields."""
        pass
    
    @property
    @abstractmethod
    def available_content(self) -> list[str]:
        """List of available content fields."""
        pass
    
    @abstractmethod
    def load(self, file: LocalFile) -> Generator[RagDocument, None, None]:
        """Load data from a file into RagDocument objects."""
        pass
    
    @abstractmethod
    def config_validation(self) -> bool:
        """Validate the loader configuration."""
        pass
    
    def as_json(self) -> dict:
        """Convert the loader to a JSON-serializable dictionary."""
        return {
            "loader_name": self.loader_name,
            "required_properties": self.required_properties,
            "optional_properties": self.optional_properties,
            "available_metadata": self.available_metadata,
            "available_content": self.available_content
        }