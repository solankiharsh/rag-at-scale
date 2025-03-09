from src.Chunkers.CharacterChunker import CharacterChunker
from src.Chunkers.Chunker import Chunker
from src.Chunkers.ChunkerEnum import ChunkerEnum
from src.Chunkers.CustomChunker import CustomChunker
from src.Chunkers.RecursiveChunker import RecursiveChunker


class ChunkerFactory:
    """Class that leverages the Factory pattern to get the appropriate chunker"""

    @staticmethod
    def get_chunker(chunker_name: str, chunker_information: dict) -> Chunker:
        if chunker_information is None:
            return RecursiveChunker()
        chunker_name_enum: ChunkerEnum = ChunkerEnum.as_chunker_enum(chunker_name)
        if chunker_name_enum == ChunkerEnum.characterchunker:
            return CharacterChunker(**chunker_information)
        elif chunker_name_enum == ChunkerEnum.customchunker:
            return CustomChunker(**chunker_information)
        elif chunker_name_enum == ChunkerEnum.recursivechunker:
            return RecursiveChunker(**chunker_information)
        else:
            return RecursiveChunker(**chunker_information)
