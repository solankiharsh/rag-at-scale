import asyncio
import inspect
import time
from statistics import mean
from typing import Optional

import httpx
from httpx import AsyncClient
from platform_commons.auth.user import User

from config import Config
from src.EmbedConnectors.commons import (
    calculate_and_publish_token_metrics,
    content_batching,
    get_embedding_dims,
    run_background_task,
)
from src.EmbedConnectors.EmbedConnector import EmbedConnector
from src.Shared.Exceptions import (
    EmbeddingSizeMismatchError,
    OpenAIRequestError,
    OpenAIResponseError,
    RateLimitError,
)

# Import your async get_embeddings function from its module
from src.Shared.RagDocument import RagDocument
from utils.platform_commons.logger import logger
from utils.platform_commons.metrics import Metrics

config = Config()

metrics = Metrics(
    enabled=config.metrics_enabled,
    dsn=config.metrics_dsn,
    blossom_id=config.blossom_id,
)


class OpenAIEmbedModel(EmbedConnector):
    api_key: str

    def __init__(self, **data):
        super().__init__(**data)
        self.api_key = config.gateway_api_key

    max_retries: Optional[int] = 20
    chunk_size: Optional[int] = 1000

    @property
    def embed_name(self) -> str:
        return "text-embedding-ada-002"

    @property
    def required_properties(self) -> list[str]:
        return ["api_key"]

    @property
    def optional_properties(self) -> list[str]:
        return ["max_retries", "chunk_size"]

    def validation(self) -> bool:
        """Validates the embedding model configuration."""
        try:
            # Example validation logic (you can adapt this to your needs)
            if not self.api_key:
                raise ValueError("API key is missing for HAM Embed model.")
            return True
        except Exception as e:
            logger.error(f"HAM embedding validation failed: {e}")
            return False

    async def embed(self, documents: list[RagDocument]) -> tuple[list, dict]:
        queries = [doc.content for doc in documents]
        user = User(id="dummy", name="Dummy User", tap_app_name="dummy")

        async with httpx.AsyncClient() as client:
            embeddings_response = await self.generate_ham_embeddings(
                model=self.embed_name,
                input_list=queries,
                user=user,
                httpx_client=client,
                # embedding_dimensions=self.settings.get("embedding_dimensions"),
                embedding_dimensions=768,
            )

        vectors = [item["embedding"] for item in embeddings_response.get("content_embedding", [])]
        usage = embeddings_response.get("usage", {})
        return vectors, usage

    async def generate_openai_embeddings(
        model,
        input_list: list,
        user: User,
        httpx_client: AsyncClient | None = None,
        batch_mode: str = config.batch_mode,
        embedding_dimensions: Optional[int] = None,
    ) -> dict:
        """
        Generates embeddings for a given list of inputs using a specified model by making
        requests to OpenAI's APIs. The embeddings are generated in batches up to a
        maximum size of 8. This batch size per request was found to perform best after
        experimentation of multiple batch sizes and the average chunk counts per document.

        Args:
            model (str): The name of the model to use for generating embeddings.
            input_list (list): The list of input strings for which embeddings will be generated.
            user (User): The user to track and bill accurately for cost showback purposes.
            httpx_client (Async Httpx Client): Singleton httpx client from lifespan
            batch_mode (str): The mode of batching to use for generating embeddings. Options are
            'static' or 'dynamic'.
            embedding_dimensions (int | None): Custom dimensions for the model, if supported.

        Returns:
            dict: A dictionary containing the list of content embeddings and usage information
                including 'prompt_tokens' and 'total_tokens'.

        Raises:
            EmbeddingSizeMismatchError (Exception): If there's a mismatch between the number of
            requested embeddings and the number received in response.
            OpenAIResponseError (Exception): If there is a non-200 status code response from
            OpenAI's API.
            OpenAIRequestError (Exception): If there is a network / request related exception
            during the call to OpenAI.

        """
        input_size = len(input_list)

        if batch_mode == "static":
            batched_content_list = (
                list(content_batching(input_list, config.openai_embeddings_batch_size))
                if input_size > config.openai_embeddings_batch_size
                else [input_list]
            )

        headers = {"Authorization": f"Bearer {config.openai_api_key}"}
        parsed_output, prompt_tokens, total_tokens = [], 0, 0

        if batch_mode == "dynamic":
            dynamic_batch_size = config.openai_embeddings_batch_size
            recent_latencies = []

        if httpx_client is None:
            httpx_transport = httpx.AsyncHTTPTransport(retries=config.retry_count)
            httpx_client = httpx.AsyncClient(http2=True, transport=httpx_transport)

        async def batch_parallelism(batch):
            nonlocal prompt_tokens, total_tokens

            if not batch:
                return []

            openai_payload = {
                "input": batch,
                "model": model,
                "encoding_format": "float",
                **(
                    {
                        "dimensions": get_embedding_dims(
                            model_name=model, embedding_dimensions=embedding_dimensions
                        )
                    }
                    if model != "text-embedding-ada-002"
                    else {}
                ),
            }

            start_time = time.time()

            embeddings_response = await httpx_client.post(
                url=config.openai_embeddings_endpoint,
                json=openai_payload,
                headers=headers,
                timeout=config.openai_embeddings_timeout,
            )

            embeddings_time_ms = (time.time() - start_time) * 1000  # NOQA

            if embeddings_response.status_code != 200:
                if embeddings_response.status_code == 429:
                    await metrics.emit_exception_metric(Exception("openai_rate_limit_error"))
                    raise RateLimitError(router="openai", model=model)
                else:
                    await metrics.emit_exception_metric(
                        Exception("generate_openai_embeddings_response_error")
                    )
                    raise OpenAIResponseError(embeddings_response.status_code)

            json_res = embeddings_response.json()
            if inspect.isawaitable(json_res):
                embeddings_response_json = await json_res
            else:
                embeddings_response_json = json_res

            response_data = embeddings_response_json["data"]

            response_data_size, input_content_size = len(response_data), len(batch)
            if response_data_size != input_content_size:
                raise EmbeddingSizeMismatchError(input_content_size, response_data_size)

            result = [
                {
                    "combined_sentence": batch[idx],
                    "embedding": item["embedding"],
                }
                for idx, item in enumerate(response_data)
            ]

            usage = embeddings_response_json.get("usage", {})
            prompt_tokens += usage.get("prompt_tokens", 0)
            batch_prompt_tokens = usage.get("prompt_tokens", 0)
            total_tokens += usage.get("total_tokens", 0)

            batch_latency_ms = (time.time() - start_time) * 1000

            if batch_mode == "dynamic":
                recent_latencies.append(batch_latency_ms)
                if len(recent_latencies) > config.dynamic_batch_window:
                    recent_latencies.pop(0)

            run_background_task(
                calculate_and_publish_token_metrics(
                    input_list=batch,
                    user=user,
                    model=model,
                    embeddings_time_ms=batch_latency_ms,
                    prompt_tokens=batch_prompt_tokens,
                    token_calculation=False,
                )
            )

            logger.info(
                f"OpenAI call took: {batch_latency_ms}",
                tap_application=user.tap_app_name,
                user_id=user.id,
            )

            return result

        def adjust_batch_size():
            nonlocal dynamic_batch_size
            avg_latency = mean(recent_latencies) if recent_latencies else 0
            if (
                avg_latency < config.latency_threshold_ms
                and dynamic_batch_size < config.max_batch_size
            ):
                dynamic_batch_size = min(dynamic_batch_size + 1, config.max_batch_size)
            elif (
                avg_latency > config.latency_threshold_ms
                and dynamic_batch_size > config.min_batch_size
            ):
                dynamic_batch_size = max(dynamic_batch_size - 1, config.min_batch_size)

        try:
            if batch_mode == "dynamic":
                while input_list:
                    batch = input_list[:dynamic_batch_size]
                    input_list = input_list[dynamic_batch_size:]
                    batch_results = await batch_parallelism(batch)
                    parsed_output.extend(batch_results)
                    adjust_batch_size()

            if batch_mode == "static":
                # TODO: Another ingest improvement will be to switch to ascompleted for earlier
                # batch jobs to move to next step rather than all batches waiting
                # till the slowest one.
                if input_size != 1:
                    batch_results = await asyncio.gather(
                        *(batch_parallelism(batch) for batch in batched_content_list)
                    )
                    parsed_output = [item for sublist in batch_results for item in sublist]

                else:
                    parsed_output = await batch_parallelism(input_list)

            return {
                "content_embedding": parsed_output,
                "usage": {"prompt_tokens": prompt_tokens, "total_tokens": total_tokens},
            }

        except EmbeddingSizeMismatchError as e:
            await metrics.emit_exception_metric(e)
            raise e from e
        except RateLimitError as e:
            raise e from e
        except OpenAIResponseError as e:
            await metrics.emit_exception_metric(e)
            raise e from e
        except Exception as e:
            await metrics.emit_exception_metric(
                Exception("generate_openai_embeddings_request_error")
            )
            raise OpenAIRequestError(e)
