# src/embeddings/embed_model.py
from abc import ABC, abstractmethod

from src.schemas.embed_config_schema import EmbedConfigSchema
from src.Shared.RagDocument import RagDocument


class EmbedModel(ABC):
    def __init__(self, config: EmbedConfigSchema):
        self.model_name = config.model_name
        self.settings = config.settings

    @staticmethod
    def create_embed_model(embed_config: EmbedConfigSchema) -> "EmbedModel":
        model_name = embed_config.model_name.lower()
        if model_name == "jina-v2-base":
            from src.embeddings.ham_embed_model import HamEmbedModel
            return HamEmbedModel(config=embed_config)
        else:
            raise ValueError(f"Unsupported embedding model: {model_name}")

    @abstractmethod
    async def embed(self, documents: list[RagDocument]) -> tuple[list[list[float]], dict]:
        """
        Embeds documents and returns a tuple:
        - A list of embedding vectors (one per document)
        - A dictionary with usage or additional metadata.
        """
        pass
