from src.Loaders.AutoLoader import AutoLoader
from src.Loaders.CSVLoader import CSVLoader
from src.Loaders.HTMLLoader import HTMLLoader
from src.Loaders.JSONLoader import JSONLoader
from src.Loaders.Loader import Loader
from src.Loaders.LoaderEnum import LoaderEnum
from src.Loaders.MarkdownLoader import MarkdownLoader
from src.Loaders.PDFLoader import PDFLoader


class LoaderFactory:
    """Class that leverages the Factory pattern to get the appropriate loader"""

    @staticmethod
    def get_loader(loader_name: str, loader_information: dict) -> Loader:
        if loader_information is None:
            return AutoLoader()
        loader_name_enum: LoaderEnum = LoaderEnum.as_loader_enum(loader_name)
        if loader_name_enum == LoaderEnum.autoloader:
            return AutoLoader(**loader_information)
        elif loader_name_enum == LoaderEnum.htmlloader:
            return HTMLLoader(**loader_information)
        elif loader_name_enum == LoaderEnum.markdownloader:
            return MarkdownLoader(**loader_information)
        elif loader_name_enum == LoaderEnum.jsonloader:
            return JSONLoader(**loader_information)
        elif loader_name_enum == LoaderEnum.csvloader:
            return CSVLoader(**loader_information)
        elif loader_name_enum == LoaderEnum.pdfloader:
            return PDFLoader(**loader_information)
        else:
            return AutoLoader(**loader_information)
