"""
Mock CharacterChunker for testing purposes.
This file contains a mock implementation of the CharacterChunker class.
"""

from collections.abc import Generator
from typing import Optional

from pydantic import Field

from tests.mocks.chunker import Chunker
from tests.mocks.rag_document import RagDocument


class CharacterChunker(Chunker):
    """
    Character Chunker

    Chunk text data based on the number of characters. This chunker is designed to break down text
    into manageable pieces based on character count, making it suitable for processing large texts
    or for use in systems that require fixed-size input.

    Attributes:
    -----------

    chunk_size : Optional[int]
        The size of each chunk in terms of the number of characters. Default is 500 characters.

    chunk_overlap : Optional[int]
        The number of characters that will overlap between consecutive chunks.
        Default is 0, meaning no overlap.

    batch_size : Optional[int]
        The size of the batch for processing chunks. Specifies how many chunks are processed
        together. Default is 1000.

    separator : Optional[str]
        The separator to be used between chunks. Default is a double newline ("\n\n").
    """

    chunk_size: Optional[int] = Field(default=500, description="Optional chunk size.")

    chunk_overlap: Optional[int] = Field(default=0, description="Optional chunk overlap.")

    batch_size: Optional[int] = Field(
        default=1000, description="Optional batch size for processing."
    )

    separator: Optional[str] = Field(default="\n\n", description="Optional separator for chunking.")

    @property
    def chunker_name(self) -> str:
        return "CharacterChunker"

    @property
    def required_properties(self) -> list[str]:
        return []

    @property
    def optional_properties(self) -> list[str]:
        return ["chunk_size", "chunk_overlap", "batch_size", "separator"]

    def chunk(self, documents: list[RagDocument]) -> Generator[list[RagDocument], None, None]:
        batch_size = self.batch_size

        # Simple text splitting implementation for testing
        documents_to_embed: list[RagDocument] = []
        for doc in documents:
            # Split by separator
            chunks = []
            remaining_text = doc.content
            while remaining_text:
                # Take chunk_size characters
                if len(remaining_text) <= self.chunk_size:
                    chunks.append(remaining_text)
                    break
                
                # Find a good split point
                split_point = self.chunk_size
                if self.separator in remaining_text[:split_point]:
                    # Split at the last separator before chunk_size
                    last_sep = remaining_text[:split_point].rindex(self.separator)
                    split_point = last_sep + len(self.separator)
                
                chunks.append(remaining_text[:split_point])
                
                # Move to next chunk with overlap
                start_point = max(0, split_point - self.chunk_overlap)
                remaining_text = remaining_text[start_point:]
            
            # Create RagDocument for each chunk
            for i, chunk in enumerate(chunks):
                documents_to_embed.append(
                    RagDocument(id=doc.id + "_" + str(i), content=chunk, metadata=doc.metadata)
                )
                if len(documents_to_embed) == batch_size:
                    yield documents_to_embed
                    documents_to_embed = []

        # Pass last remaining
        if len(documents_to_embed) > 0:
            yield documents_to_embed

    def config_validation(self) -> bool:
        return True