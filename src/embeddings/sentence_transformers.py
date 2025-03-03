# src/embeddings/sentence_transformers.py

from src.embeddings.embed_model import EmbedModel
from src.schemas.document_schema import DocumentSchema
from src.schemas.embed_config_schema import EmbedConfigSchema

from sentence_transformers import SentenceTransformer


class SentenceTransformersEmbedModel(EmbedModel):
    def __init__(self, config: EmbedConfigSchema):
        super().__init__(config)
        self.model = SentenceTransformer(self.model_name)

    def embed(self, documents: list[DocumentSchema]) -> tuple[list[list[float]], dict]:
        texts = [doc.content for doc in documents]
        embeddings = self.model.encode(texts).tolist() # Convert numpy array to list
        return embeddings, {"model_name": self.model_name}