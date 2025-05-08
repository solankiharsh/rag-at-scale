"""
Mock PDFLoader for testing purposes.
This file contains a mock implementation of the PDFLoader class.
"""

from collections.abc import Generator

from tests.mocks.rag_document import RagDocument


class LocalFile:
    """Mock LocalFile class for testing."""
    
    def __init__(self, id: str, file_path: str, metadata: dict = None):
        self.id = id
        self.file_path = file_path
        self.metadata = metadata or {}


class PDFLoader:
    """
    Mock PyPDF Loader for testing.

    Loads PDF files leveraging PyPDF.
    """

    @property
    def loader_name(self) -> str:
        return "PDFLoader"

    @property
    def required_properties(self) -> list[str]:
        return []

    @property
    def optional_properties(self) -> list[str]:
        return []

    @property
    def available_metadata(self) -> list[str]:
        return []

    @property
    def available_content(self) -> list[str]:
        return []

    def load(self, file: LocalFile) -> Generator[RagDocument, None, None]:
        """Mock load method that yields sample documents."""
        # In a real implementation, this would use PyPDFLoader
        # For testing, we'll just yield some sample documents
        
        # Simulate a PDF with 3 pages
        for i in range(3):
            content = f"This is page {i+1} of the PDF document. Sample content for testing."
            yield RagDocument(id=f"{file.id}_page_{i+1}", content=content, metadata=file.metadata)

    def config_validation(self) -> bool:
        return True