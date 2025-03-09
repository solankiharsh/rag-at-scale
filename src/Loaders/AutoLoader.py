from collections.abc import Generator

from langchain.document_loaders import UnstructuredFileLoader

from src.Loaders.CSVLoader import CSVLoader
from src.Loaders.HTMLLoader import HTMLLoader
from src.Loaders.JSONLoader import JSONLoader
from src.Loaders.Loader import Loader
from src.Loaders.MarkdownLoader import MarkdownLoader
from src.Loaders.PDFLoader import PDFLoader
from src.Shared.LocalFile import LocalFile
from src.Shared.RagDocument import RagDocument


class AutoLoader(Loader):
    """
    Auto Loader

    Automatically picks a loading strategy based on the type of file being provided.

    Attributes:
    -----------

    None

    """

    @property
    def loader_name(self) -> str:
        return "AutoLoader"

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
        """Load data into Document objects."""
        if "csv" in file.type:
            loader = CSVLoader()
        elif "string" in file.type:
            yield RagDocument(content=file.in_mem_data, metadata=file.metadata, id=file.id)
            return
        elif "application/octet-stream" in file.type:
            loader = MarkdownLoader()
        elif "html" in file.type:
            loader = HTMLLoader()
        elif "pdf" in file.type:
            loader = PDFLoader()
        elif "json" in file.type:
            loader = JSONLoader()
        else:
            loader = UnstructuredFileLoader(file_path=file.file_path)
            documents = loader.load()
            for doc in documents:
                yield RagDocument(id=file.id, content=doc.page_content, metadata=file.metadata)
            return

        yield from loader.load(file=file)

    def config_validation(self) -> bool:
        return True
