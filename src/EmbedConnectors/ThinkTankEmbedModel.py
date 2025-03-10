import time
from typing import Optional

import httpx
from platform_commons.auth.user import User
from platform_commons.errors.unauthorized_error import UnauthorizedError

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
    RateLimitError,
    ThinktankRequestError,
    ThinktankResponseError,
)
from src.Shared.RagDocument import RagDocument
from utils.platform_commons.logger import logger
from utils.platform_commons.metrics import Metrics

config = Config()

metrics = Metrics(
    enabled=config.metrics_enabled,
    dsn=config.metrics_dsn,
    blossom_id=config.blossom_id,
)


class ThinkTankEmbedModel(EmbedConnector):
    api_key: str

    def __init__(self, **data):
        super().__init__(**data)
        self.api_key = config.gateway_api_key

    max_retries: Optional[int] = 20
    chunk_size: Optional[int] = 1000

    @property
    def embed_name(self) -> str:
        return "thinktank-v1-base"

    @property
    def required_properties(self) -> list[str]:
        return ["api_key"]

    @property
    def optional_properties(self) -> list[str]:
        return ["max_retries", "chunk_size"]

    def validation(self) -> bool:
        """Validates the embedding model configuration."""
        try:
            if not self.api_key:
                raise ValueError("API key is missing for ThinkTank Embed model.")
            return True
        except Exception as e:
            logger.error(f"ThinkTank embedding validation failed: {e}")
            return False

    async def embed(self, documents: list[RagDocument]) -> tuple[list, dict]:
        queries = [doc.content for doc in documents]
        user = User(id="dummy", name="Dummy User", tap_app_name="dummy")

        async with httpx.AsyncClient() as client:
            embeddings_response = await self.generate_thinktank_embeddings(
                model=self.embed_name,
                input_list=queries,
                user=user,
                httpx_client=client,
                embedding_dimensions=768,
            )

        vectors = [item["embedding"] for item in embeddings_response.get("content_embedding", [])]
        usage = embeddings_response.get("usage", {})
        return vectors, usage

    async def generate_thinktank_embeddings(
        self,
        model: str,
        input_list: list,
        user: User,
        httpx_client: Optional[httpx.AsyncClient] = None,
        embedding_dimensions: Optional[int] = None,
    ) -> dict:
        """
        Generates embeddings for a given list of inputs using a specified model by making
        requests to the thinktank service. The embeddings are generated in batches up to a
        maximum size of 16 due to SCA constraints.

        Args:
            model (str): The name of the model to use for generating embeddings.
            input_list (list): The list of input strings for which embeddings will be generated.
            user (User): The user for authentication with Target services.
            httpx_client (Async Httpx Client): Singleton httpx client from lifespan
        Returns:
            dict: A dictionary containing the list of content embeddings and usage information
                including 'prompt_tokens' and 'total_tokens'.

        Raises:
            EmbeddingSizeMismatchError (Exception): If there's a mismatch between the number of
            requested embeddings and the number received in response.
            ThinktankResponseError (Exception): If there is a non-200 status code response from the
            thinktank API.
            ThinktankRequestError (Exception): If there is a network / request related exception
            during the call to thinktank API.

        """

        # SCA max batch size 16
        if len(input_list) > 16:
            batched_content_list = list(content_batching(input_list, 16))
        else:
            batched_content_list = [input_list]

        thinktank_url = config.thinktank
        embeddings_url = thinktank_url + "/v1/embeddings"
        auth_header = {"Authorization": user.token}

        parsed_output = []
        if httpx_client is None:
            httpx_client = httpx.AsyncClient()
        try:
            prompt_tokens, total_tokens, batch_size = 0, 0, len(batched_content_list)
            for batch in batched_content_list:
                if not batch:
                    continue

                # for each sub batch create a thinktank call
                if model != "text-embedding-ada-002":
                    thinktank_embeddings_body = {
                        "input": batch,
                        "model": model,
                        "dimensions": get_embedding_dims(
                            model_name=model, embedding_dimensions=embedding_dimensions
                        ),
                    }
                else:
                    thinktank_embeddings_body = {"input": batch, "model": model}

                start_time = time.time()
                # TODO Search uses lifespan httpx, Ingest needs to use same after it refactors
                embeddings_response = await httpx_client.post(
                    url=embeddings_url,
                    json=thinktank_embeddings_body,
                    headers=auth_header,
                    timeout=35,
                )

                if embeddings_response.status_code == 401:
                    await metrics.emit_exception_metric(
                        Exception("generate_thinktank_embeddings_auth_error")
                    )
                    raise UnauthorizedError("ThinkTank API returned a 401 unauthorized error.")
                if embeddings_response.status_code == 429:
                    await metrics.emit_exception_metric(
                        Exception("generate_thinktank_embeddings_rate_limit_error")
                    )
                    raise RateLimitError(router="thinktank", model=model)
                elif embeddings_response.status_code != 200:
                    await metrics.emit_exception_metric(
                        Exception("generate_thinktank_embeddings_response_error")
                    )
                    raise ThinktankResponseError(embeddings_response.status_code)

                embeddings_response_json = embeddings_response.json()
                response_data = embeddings_response_json["data"]
                response_data_size, input_content_size = len(response_data), len(batch)
                if response_data_size != input_content_size:
                    raise EmbeddingSizeMismatchError(input_content_size, response_data_size)
                for idx, item in enumerate(response_data):
                    content_embedding = {
                        "combined_sentence": batch[idx],
                        "embedding": item["embedding"],
                    }
                    parsed_output.append(content_embedding)
                if batch_size > 1:
                    prompt_tokens += embeddings_response_json["usage"]["prompt_tokens"]
                    total_tokens += embeddings_response_json["usage"]["total_tokens"]
                else:
                    prompt_tokens = embeddings_response_json["usage"]["prompt_tokens"]
                    total_tokens = embeddings_response_json["usage"]["total_tokens"]

                end_time = time.time()

                embeddings_time_ms = (end_time - start_time) * 1000

                run_background_task(
                    calculate_and_publish_token_metrics(
                        input_list=batch,
                        user=user,
                        model=model,
                        embeddings_time_ms=embeddings_time_ms,
                        prompt_tokens=prompt_tokens,
                        token_calculation=False,
                    )
                )

            generated_embeddings = {
                "content_embedding": parsed_output,
                "usage": {"prompt_tokens": prompt_tokens, "total_tokens": total_tokens},
            }

            return generated_embeddings

        except RateLimitError as e:
            raise e from e
        except UnauthorizedError as e:
            await metrics.emit_exception_metric(e)
            raise e from e
        except EmbeddingSizeMismatchError as e:
            await metrics.emit_exception_metric(e)
            raise e from e
        except ThinktankResponseError as e:
            await metrics.emit_exception_metric(e)
            raise e from e
        except Exception as e:
            await metrics.emit_exception_metric(
                Exception("generate_thinktank_embeddings_request_error")
            )
            raise ThinktankRequestError(e)

    async def validate_thinktank_access(self, model: str | None, user: User):
        """
        Helper function to validate thinktank access.
        Args:
            model (str): The thinktank model to validate.
            user (User): The user for authentication with Target services.
        """
        thinktank_url = config.thinktank
        auth_url = f"{thinktank_url}/v1/auth"
        if model is not None:
            auth_url = thinktank_url + f"/v1/models/{model or config.default_embedding_model}"
        auth_header = {"Authorization": user.token}
        try:
            async with httpx.AsyncClient() as client:
                auth_response = await client.get(url=auth_url, headers=auth_header)
                if auth_response.status_code == 401:
                    await metrics.emit_exception_metric(
                        Exception("validate_thinktank_access_auth_error")
                    )
                    raise UnauthorizedError("ThinkTank API returned a 401 unauthorized error.")
                elif auth_response.status_code != 200:
                    await metrics.emit_exception_metric(
                        Exception("validate_thinktank_access_auth_error")
                    )
                    raise ThinktankResponseError(auth_response.status_code)

        except UnauthorizedError:
            raise
        except ThinktankResponseError:
            raise
        except Exception as e:
            await metrics.emit_exception_metric(Exception("validate_thinktank_access_auth_error"))
            raise ThinktankRequestError(e)
