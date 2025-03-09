# src/embeddings/embedding_service.py
import asyncio
from typing import Optional

import httpx
from loguru import logger


async def get_embeddings(
    embedding_routing: str,
    embeddings_model: str,
    query: str | list[str],
    user,  # Replace with your actual User type
    client: httpx.AsyncClient | None,
    embedding_dimensions: Optional[int] = None,
) -> dict:
    """
    Retrieves embeddings for the given query using the specified method and model.
    For this example, we only implement the HAM branch.
    """
    # For this example, we assume that any model other than a specific "thinktank"
    # goes through HAM embeddings.
    if embeddings_model == "jina-v2-base":
        logger.debug(
            f"Generating HAM embeddings using model: {embeddings_model} " f"for user: {user.id}"
        )
        return await generate_ham_embeddings(
            model=embeddings_model,
            input_list=[query] if isinstance(query, str) else query,
            user=user,
            httpx_client=client,
            embedding_dimensions=embedding_dimensions,
        )
    else:
        raise ValueError(f"Unsupported embedding model: {embeddings_model}")


# Dummy implementation of generate_ham_embeddings.
# Replace this with your actual implementation.
async def generate_ham_embeddings(
    model: str,
    input_list: list,
    user,
    httpx_client: httpx.AsyncClient | None = None,
    embedding_dimensions: int | None = None,
) -> dict:
    # Simulate an asynchronous call to an external API
    await asyncio.sleep(0.1)
    # Return a dummy response for demonstration purposes.
    dummy_embeddings = [
        {"combined_sentence": text, "embedding": [0.1, 0.2, 0.3]} for text in input_list
    ]
    return {
        "content_embedding": dummy_embeddings,
        "usage": {"prompt_tokens": 10, "total_tokens": 20},
    }
