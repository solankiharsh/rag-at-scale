"""
Mock CSVLoader for testing purposes.
This file contains a mock implementation of the CSVLoader class.
"""

from collections.abc import Generator

from tests.mocks.rag_document import RagDocument


class LocalFile:
    """Mock LocalFile class for testing."""
    
    def __init__(self, id: str, file_path: str, metadata: dict = None):
        self.id = id
        self.file_path = file_path
        self.metadata = metadata or {}


class Selector:
    """Mock Selector class for testing."""
    
    def __init__(self, to_embed=None, to_metadata=None):
        self.to_embed = to_embed or []
        self.to_metadata = to_metadata or []


class CSVLoader:
    """
    Mock CSV Loader for testing.
    """

    def __init__(self, **kwargs):
        self.id_key = kwargs.get("id_key", "id")
        self.source_column = kwargs.get("source_column", None)
        self.encoding = kwargs.get("encoding", "utf-8-sig")
        self.csv_args = kwargs.get("csv_args", None)
        self.selector = kwargs.get("selector", Selector(to_embed=[], to_metadata=[]))

    @property
    def loader_name(self) -> str:
        return "CSVLoader"

    @property
    def required_properties(self) -> list[str]:
        return []

    @property
    def optional_properties(self) -> list[str]:
        return ["id_key", "source_column", "encoding", "csv_args"]

    @property
    def available_metadata(self) -> list[str]:
        return ["custom"]

    @property
    def available_content(self) -> list[str]:
        return ["custom"]

    def config_validation(self) -> bool:
        return True

    def load(self, file: LocalFile) -> Generator[RagDocument, None, None]:
        """Mock load method that yields sample documents."""
        # For testing, we'll simulate a CSV with 3 rows
        
        # Mock CSV data
        mock_csv_data = [
            {"id": "1", "name": "John Doe", "age": "30", "city": "New York"},
            {"id": "2", "name": "Jane Smith", "age": "25", "city": "Los Angeles"},
            {"id": "3", "name": "Bob Johnson", "age": "40", "city": "Chicago"}
        ]
        
        for i, row in enumerate(mock_csv_data):
            document_id = f"{row.get(self.id_key, '')}.{self.id_key}"
            metadata = self.extract_metadata(row)
            content = self.extract_content(row)
            source = row[self.source_column] if self.source_column and self.source_column in row else file.file_path
            metadata["source"] = source
            metadata["row"] = i
            doc = RagDocument(content=content, metadata=metadata, id=document_id)
            yield doc

    def extract_metadata(self, row: dict) -> dict:
        return {key: row[key] for key in self.selector.to_metadata if key in row}

    def extract_content(self, row: dict) -> str:
        if self.selector.to_embed:
            row = {k: row[k] for k in self.selector.to_embed if k in row}
        return "\n".join(f"{k.strip()}: {v.strip()}" for k, v in row.items())