from collections.abc import Generator

from langchain.document_loaders import PyPDFLoader

from src.Loaders.Loader import Loader
from src.Shared.LocalFile import LocalFile
from src.Shared.RagDocument import RagDocument


class PDFLoader(Loader):
    """
    PyPDF Loader

    Loads PDF files leveraging PyPDF.

    Attributes:
    -----------

    None

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

    # Probably worth re-writing directly on top of pypdf to get access
    # to more metadata including images, tables, etc.
    def load(self, file: LocalFile) -> Generator[RagDocument, None, None]:
        """Load data into Document objects."""
        loader = PyPDFLoader(file_path=file.file_path)
        documents = loader.load()
        # join the file and document metadata objects
        for doc in documents:
            yield RagDocument(id=file.id, content=doc.page_content, metadata=file.metadata)

    def config_validation(self) -> bool:
        return True
