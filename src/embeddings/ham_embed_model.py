# src/embeddings/ham_embed_model.py

import httpx
from src.embeddings.embed_model import EmbedModel
# Import your async get_embeddings function from its module
from src.embeddings.embedding_service import get_embeddings
from src.schemas.document_schema import DocumentSchema


# Dummy User class; replace with your actual User model
class User:
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name

class HamEmbedModel(EmbedModel):
    
    
    async def embed(self, documents: list[DocumentSchema]) -> tuple[list[list[float]], dict]:
        # Extract the text from documents. Assume DocumentSchema has a 'text' attribute.
        queries = [doc.content for doc in documents]
        
        # For this example, create a dummy user.
        user = User(id="dummy", name="Dummy User")
        
        # Optionally, you might create or pass an httpx.AsyncClient instance.
        async with httpx.AsyncClient() as client:
            # Call get_embeddings using the HAM branch.
            # Here, we assume that if the embedding routing is not "thinktank",
            # and the model is "jina-v2-base", then HAM embeddings are generated.
            embeddings_response = await get_embeddings(
                embedding_routing="default",  # or however you want to route HAM calls
                embeddings_model=self.model_name,
                query=queries,
                user=user,
                client=client,
                embedding_dimensions=self.settings.get("embedding_dimensions")
            )
        
        # Process the response. We assume the response contains a key "content_embedding"
        # which is a list of objects each with an "embedding" field.
        vectors = [item["embedding"] for item in embeddings_response.get("content_embedding", [])]
        usage = embeddings_response.get("usage", {})
        return vectors, usage
