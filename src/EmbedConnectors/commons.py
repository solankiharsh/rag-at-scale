import asyncio
import json
import uuid
from typing import Any, Optional, TypedDict

import tiktoken
from confluent_kafka import KafkaException
from httpx import AsyncClient, HTTPError, HTTPStatusError
from platform_commons.auth.user import User

from config import Config
from src.Shared.Exceptions import (
    InvalidModelDimensions,
    InvalidModelError,
    UnsupportedDimensionError,
)
from utils.kafka.helpers import get_kafka_producer, uh_delivery_report
from utils.platform_commons.logger import logger
from utils.platform_commons.metrics import metrics

settings = Config()


def update_embedding_configs(
    old_config: dict[str, Any], new_config: dict[str, Any]
) -> dict[str, Any]:
    """
    Update embedding configurations by comparing old and new settings.

    Args:
        old_config (Dict[str, Any]): Existing configuration.
        new_config (Dict[str, Any]): New configuration.

    Returns:
        Dict[str, Any]: Updated configuration.
    """
    return {**old_config, **{k: v for k, v in new_config.items() if old_config.get(k) != v}}


class ModelConfig(TypedDict):
    default: int
    supports_override: bool
    allowed_dimensions: list[int]


def get_embedding_dims(
    model_name: Optional[str], embedding_dimensions: Optional[int] = None
) -> int:
    """
    Get embedding dimensions for a given model. Supports configurable dimensions
    for models that allow overrides; defaults otherwise.

    Args:
        model_name (str | None): The model name. Defaults to a configured setting.
        embedding_dimensions (int | None): Custom dimensions for the model, if supported.

    Returns:
        int: The dimension for the given model.

    Raises:
        InvalidModelError: If the model is unsupported.
    """
    # Define supported models with specific types
    # Define supported models with strongly-typed configurations
    supported_models: dict[str, ModelConfig] = {
        "text-embedding-3-small": {
            "default": 1024,
            "supports_override": True,
            "allowed_dimensions": settings.text_embedding_3_small_dimensions,
        },
        "jina-v2-base": {
            "default": 768,
            "supports_override": False,
            "allowed_dimensions": settings.jina_v2_base_dimensions,
        },
        "text-embedding-ada-002": {
            "default": 1536,
            "supports_override": False,
            "allowed_dimensions": settings.text_embedding_ada_002_dimensions,
        },
        "text-embedding-3-large": {
            "default": 1024,
            "supports_override": True,
            "allowed_dimensions": settings.text_embedding_3_large_dimensions,
        },
    }

    if model_name is None or model_name not in supported_models:
        raise InvalidModelError(model_name or "default_model")

    model_config = supported_models[model_name]
    default_dimensions = model_config["default"]
    supports_override = model_config["supports_override"]
    allowed_dimensions = model_config["allowed_dimensions"]

    # Special case: text-embedding-ada-002 always returns None
    # if model_name == "text-embedding-ada-002":
    #     return None

    # Validate custom dimensions if provided
    if embedding_dimensions is not None:
        if not isinstance(embedding_dimensions, int):
            raise TypeError("embedding_dimensions must be an integer.")
        # If override is not supported, dimensions must match the default
        if not supports_override and embedding_dimensions != default_dimensions:
            raise InvalidModelDimensions(
                model=model_name,
                dimensions=embedding_dimensions,
                expected_dimensions=default_dimensions,
            )
        if embedding_dimensions not in allowed_dimensions:
            raise UnsupportedDimensionError(
                model=model_name,
                dimensions=embedding_dimensions,
                allowed_dimensions=allowed_dimensions,
            )
        return embedding_dimensions

    # Return the default dimensions
    return default_dimensions


def content_batching(content_list: list, batch_size: int):
    """
    Generator that yields batches of content from a list based on a specified batch size.

    Args:
        content_list (list): The list of input content text to be batched.
        batch_size (int): The size of each batch.

    Yields:
        list: A batch of content items.

    Raises:
        ZeroDivisionError (Exception): If batch_size is zero. placeholder for user configurable
        batchsize - pending discussion with SCA
        ValueError (Exception): If batch_size is negative
    """
    if batch_size == 0:
        raise ZeroDivisionError("batch_size cannot be zero")
    if batch_size < 0:
        raise ValueError("batch_size cannot be negative")
    if not isinstance(content_list, list):
        raise TypeError("content_list must be a list")
    for i in range(0, len(content_list), batch_size):
        yield content_list[i : i + batch_size]


async def validate_user_for_tap_quota(tap_application: str, user_token: str):
    """
    Fetches usage for TAP application from Assimilator to verify registration of Quota

    Args:
        tap_application (str): The name of the TAP application for which to fetch quota status.
        user_token (str): Bearer token for authorization.

    Returns:
        dict: Response JSON containing quota information.

    Raises:
        httpx.HTTPError: If the API request fails or returns a non-200 status code.
        ValueError: If the quota is unavailable in the response.
        json.JSONDecodeError: If the response JSON is invalid.
    """

    url = settings.quota_endpoint
    auth_header = {"Authorization": user_token}
    quota_key = f"dpm_quota:{tap_application}:total"

    async with AsyncClient() as httpx_client:
        try:
            response = await httpx_client.get(url, headers=auth_header, params={"key": quota_key})
            if response is None:
                raise ValueError(
                    f"No response from quota service for tap application:" f" {tap_application}"
                )
            response.raise_for_status()
            response_data = response.json()
        except HTTPStatusError as e:
            logger.error(
                f"Quota http status error for tap application: {tap_application}: {str(e)}",
                exception=e,
                tap_application=tap_application,
            )
            raise
        except HTTPError as e:
            logger.error(
                f"Quota http call failure for tap application: {tap_application}: {str(e)}",
                exception=e,
                tap_application=tap_application,
            )
            raise
        except json.JSONDecodeError as e:
            logger.error(
                f"Quota response decode failure for tap application: {tap_application} "
                f"with content: {response.text} : {str(e)}",
                exception=e,
                tap_application=tap_application,
            )
            raise
        except Exception as e:
            logger.error(
                f"Quota response error for tap application: {tap_application} : {str(e)}",
                exception=e,
                tap_application=tap_application,
            )
            raise

    logger.debug(f"Quota response for tap application: {tap_application} with {response_data}")
    if not (
        isinstance(response_data, dict)
        and "hard_cap" in response_data
        and "usage_available" in response_data
        and response_data["usage_available"] > 0
    ):
        raise ValueError(f"Quota unavailable or invalid for TAP application: {tap_application}.")

    return response_data


def get_model_cost(model: str):
    """
    Returns the cost of a model in tokens per token.
    Args:
        model: The model for which to get the cost.

    Returns:
        float: The cost of the model in tokens per token.
    """
    model_token_cost = {
        "text-embedding-3-small": 0.00000002,
        "jina-v2-base": 0.0000001,
        "text-embedding-ada-002": 0.0000001,
        "text-embedding-3-large": 0.00000013,
    }

    return model_token_cost[model]


def run_background_task(coro):
    """
    Schedules a coroutine to run as a background task.
    """
    asyncio.create_task(coro)


async def publish_usage_history(user: User, model: str, tokens_used: int):
    """
    Publishes usage history to Assimilator kafka topic for the given user, model, and tokens.

    Args:
        user (User): The user for whom to publish usage history.
        model (str): The model for which to publish usage history.
        tokens_used (int): The tokens used in the request.

    Raises:
        BufferError: If the producer's local buffer is full.
        KafkaException: If an unexpected Kafka error occurs.
    """
    if settings.usage_history_enabled:
        total_cost = get_model_cost(model) * tokens_used

        # TODO: schema changes tap app,
        #  entityid alongside usage history table switch - new topic when that happens
        payload = {
            "user_id": user.id,
            "model_name": model,
            "input_tokens": 0,
            "completion_tokens": tokens_used,
            "application": user.tap_app_name,
            "requests": 1,
            "cost": total_cost,
            "transaction_id": str(
                uuid.uuid4()
            ),  # Future - replaced with request span id for platform
            "source_platform_application": "ragservice",
        }

        try:
            logger.info(f"Sending usage history log to Kafka: {payload}")
            producer = get_kafka_producer()
            producer.produce(
                topic=settings.kafka_usage_history_topic,
                value=json.dumps(payload).encode("utf-8"),
                on_delivery=uh_delivery_report,
            )
            producer.poll(0)

        except BufferError as e:
            logger.error(
                f"Failed to send usage history log, due to local buffer being full: {e}",
                user_id=payload["user_id"],
                tap_application=user.tap_app_name,
                exception=e,
            )
            await metrics.emit_exception_metric(
                e, payload["user_id"], user_id=user.id, tap_application=user.tap_app_name
            )
            return False

        except KafkaException as e:
            logger.error(
                f"An unexpected Kafka error occurred: {e}",
                user_id=payload["user_id"],
                tap_application=payload["user_id"],
                exception=e,
            )
            await metrics.emit_exception_metric(
                e, payload["user_id"], user_id=user.id, tap_application=user.tap_app_name
            )
            return False

    return True


async def calculate_and_publish_token_metrics(
    input_list: list,
    user: User,
    model: str,
    embeddings_time_ms: float,
    prompt_tokens: int,
    token_calculation: bool,
):
    """
    Calculates token counts for each item in the input list and publishes metrics.
    This method is executed asynchronously and does not block the response of the API.

    Args:
        input_list (list): The list of input strings for which token usage will be calculated.
        user (User): The user associated with the request, for metric tagging.
        model (str): The model namser.tap_app_nae, used for metrics.
        embeddings_time_ms (float): The time taken to generate embeddings, used for metrics.
        prompt_tokens (int): The number of tokens used for the prompt.
        token_calculation (bool): Whether to calculate the tokens used or not.
    """
    logger.info(
        f"Calculating and publishing token metrics for model: {model}",
        user_id=user.id,
        tap_application=user.tap_app_name,
    )

    def calculate_tokens(text: str) -> int:
        tokenizer = tiktoken.get_encoding("cl100k_base")
        tokens = tokenizer.encode(text)
        return len(tokens)

    if token_calculation:
        token_counts = [calculate_tokens(text) for text in input_list]
        total_tokens = sum(token_counts)
    else:
        total_tokens = prompt_tokens

    await publish_usage_history(user=user, model=model, tokens_used=total_tokens)

    if settings.metrics_enabled:
        await metrics.write(
            name="embeddings_token_usage",
            tags={
                "model": model,
                "user_id": user.id,
            },
            fields={
                "total_token_count": total_tokens,
                "input_item_count": len(input_list),
                "response_time_ms": embeddings_time_ms,
            },
        )
