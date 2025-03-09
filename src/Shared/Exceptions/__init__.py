from platform_commons.models.error_response import ErrorResponse


class HAMResponseError(Exception):
    """
    This exception is raised when there are non-200 response status codes returned from HAM
    """

    def __init__(self, status_code: int):
        self.reason = f"Response to HAM returned the following status_code: {status_code}"
        super().__init__(self.reason)


def ham_response_error_to_error_response(
    error: HAMResponseError,
) -> ErrorResponse:
    """
    Translates a HAMResponseError into an ErrorResponse for logging
    and building web responses in a consistent way.

    Args:
        error (HAMResponseError): the error to translate

    Returns:
        ErrorResponse: an error response for use in logging and building web response
    """

    return ErrorResponse(
        message=error.reason,
        error_type="Internal Server Error",
        code="ham_response_error",
    )


class InvalidModelDimensions(Exception):
    """Exception raised when the dimensions are invalid for a model."""

    def __init__(self, model: str, dimensions: int, expected_dimensions: int):
        super().__init__(
            f"`.embedders.{model}.dimensions`: Model `{model}` does not support "
            f"overriding its native dimensions of {expected_dimensions}. Found {dimensions}"
        )
        self.model = model
        self.dimensions = dimensions
        self.expected_dimensions = expected_dimensions


class UnsupportedDimensionError(Exception):
    """Exception raised when the dimensions are not in the allowed list."""

    def __init__(self, model: str, dimensions: int, allowed_dimensions: list[int]):
        super().__init__(
            f"`.embedders.{model}.dimensions`: Model `{model}` only supports dimensions "
            f"from the allowed list {allowed_dimensions}. Found {dimensions}."
        )
        self.model = model
        self.dimensions = dimensions
        self.allowed_dimensions = allowed_dimensions


def unsupported_dimension_error_to_error_response(
    error: UnsupportedDimensionError,
) -> ErrorResponse:
    """
    Translates an UnsupportedDimensionError exception into an ErrorResponse.

    Args:
        error (UnsupportedDimensionError): the error to translate

    Returns:
        ErrorResponse: an error response for use in logging and building web responses
    """
    return ErrorResponse(
        message=(
            f"Model `{error.model}` only supports dimensions from the allowed list "
            f"{error.allowed_dimensions}. Found: {error.dimensions}."
        ),
        error_type="Invalid Configuration",
        code="unsupported_dimension_error",
    )


def invalid_model_dimensions_to_error_response(
    error: InvalidModelDimensions,
) -> ErrorResponse:
    """
    Translates an InvalidModelDimensions exception into an ErrorResponse for logging
    and building web responses in a consistent way.

    Args:
        error (InvalidModelDimensions): the error to translate

    Returns:
        ErrorResponse: an error response for use in logging and building web response
    """
    return ErrorResponse(
        message=(
            f"Model `{error.model}` does not support overriding its native dimensions. "
            f"Expected: {error.expected_dimensions}, Found: {error.dimensions}."
        ),
        error_type="Invalid Configuration",
        code="invalid_model_dimensions",
    )


class InvalidModelError(Exception):
    """
    This exception is raised for unsupported embedding models on ingestion
    """

    def __init__(self, model_name: str):
        self.reason = f"Unsupported Embedding Model {str(model_name)}"
        super().__init__(self.reason)


def invalid_model_error_to_error_response(
    error: InvalidModelError,
) -> ErrorResponse:
    """
    Translates an InvalidModelError exception into an ErrorResponse for logging
    and building web responses in a consistent way.

    Args:
        error (InvalidModelError): The error to translate.

    Returns:
        ErrorResponse: An error response for use in logging and building web response.
    """
    return ErrorResponse(
        message=error.reason,
        error_type="Invalid Configuration",
        code="invalid_model_error",
    )


class EmbeddingSizeMismatchError(Exception):
    """
    This exception is raised when there are generic errors in generating embeddings
    """

    def __init__(self, input_size: int, embed_size: int):
        self.reason = (
            f"The input len: {input_size} and generated embeddings len: {embed_size} do not match."
        )
        super().__init__(self.reason)


def embedding_size_mismatch_error_to_error_response(
    error: EmbeddingSizeMismatchError,
) -> ErrorResponse:
    """
    Translates a EmbeddingSizeMismatchError into an ErrorResponse for logging
    and building web responses in a consistent way.

    Args:
        error (EmbeddingSizeMismatchError): the error to translate

    Returns:
        ErrorResponse: an error response for use in logging and building web response
    """

    return ErrorResponse(
        message=error.reason,
        error_type="Internal Server Error",
        code="embedding_size_mismatch_error",
    )


class HAMRateLimitError(Exception):
    """
    This exception is raised when HAM returns a 429 status code
    """

    def __init__(self):
        self.reason = (
            "We have reached the provider rate limit with HAM/On-prem models. Please "
            "try again after some time."
        )
        super().__init__(self.reason)


def ham_rate_limit_error_to_error_response(
    error: HAMRateLimitError,
) -> ErrorResponse:
    """
    Translates a HAMRateLimitError into an ErrorResponse for logging
    and building web responses in a consistent way.

    Args:
        error (HAMRateLimitError): the error to translate

    Returns:
        ErrorResponse: an error response for use in logging and building web response
    """

    return ErrorResponse(
        message=error.reason,
        error_type="Internal Server Error",
        code="ham_rate_limit_error",
    )


class HAMRequestError(Exception):
    """
    This exception is raised when there are request errors to HAM
    """

    def __init__(self, e: Exception):
        self.reason = f"There was an error with making a request to HAM. Error{str(e)}"
        super().__init__(self.reason)


def ham_request_error_to_error_response(
    error: HAMRequestError,
) -> ErrorResponse:
    """
    Translates a HAMRequestError into an ErrorResponse for logging
    and building web responses in a consistent way.

    Args:
        error (HAMRequestError): the error to translate

    Returns:
        ErrorResponse: an error response for use in logging and building web response
    """

    return ErrorResponse(
        message=error.reason,
        error_type="Internal Server Error",
        code="ham_request_error",
    )


class AzureBlobConnectionException(Exception):
    """Raised if establishing a connection to Azure Blob fails"""

    pass


class CloudFileEmptyException(Exception):
    """Raised when the cloud file dictionary is empty"""

    pass


class LocalFileEmptyException(Exception):
    """Raised when the local file dictionary is empty"""

    pass


class InvalidDataConnectorException(Exception):
    """Raised when an invalid data connector is detected"""

    pass


class InvalidEmbedConnectorException(Exception):
    """Raised when an invalid embed connector is detected"""

    pass


class InvalidSinkConnectorException(Exception):
    """Raised when an invalid sink connector is detected"""

    pass


class RagDocumentEmptyException(Exception):
    """Raised when the Rag document dictionary is empty"""

    pass


class RagSearchResultEmptyException(Exception):
    """Raised when the Rag search result dictionary is empty"""

    pass


class RagSinkInfoEmptyException(Exception):
    """Raised when the Rag search result dictionary is empty"""

    pass


class OpenAIConnectionException(Exception):
    """Raised if establishing a connection to OpenAI fails"""

    pass


class HuggingFaceConnectonException(Exception):
    """Raised if establishing a connection to HuggingFace fails"""

    pass


class PineconeConnectionException(Exception):
    """Raised if establishing a connection to Pinecone fails"""

    pass


class PineconeInsertionException(Exception):
    """Raised if inserting into Pinecone fails"""

    pass


class PineconeIndexInfoException(Exception):
    """Raised if getting index info from Pinecone fails"""

    pass


class PineconeQueryException(Exception):
    """Raised if querying Pinecone fails"""

    pass


class QdrantInsertionException(Exception):
    """Raised if inserting into Qdrant fails"""

    pass


class QdrantIndexInfoException(Exception):
    """Raised if getting index info from Qdrant fails"""

    pass


class QdrantQueryException(Exception):
    """Raised if querying Qdrant fails"""

    pass


class MarqoInsertionException(Exception):
    """Raised if inserting into Marqo fails"""

    pass


class MarqoIndexInfoException(Exception):
    """Raised if getting index info from Marqo fails"""

    pass


class MarqoQueryException(Exception):
    """Raised if querying Marqo fails"""

    pass


class LanceDBInsertionException(Exception):
    """Raised if inserting into LanceDB fails"""

    pass


class LanceDBIndexInfoException(Exception):
    """Raised if getting index info from LanceDB fails"""

    pass


class LanceDBQueryException(Exception):
    """Raised if querying LanceDB fails"""

    pass


class LanceDBIndexCreationException(Exception):
    """Raised when index creation fails in lanceDB"""

    pass


class PostgresConnectionException(Exception):
    """Raised if establishing a connection to a Postgres db fails"""

    pass


class S3ConnectionException(Exception):
    """Raised if establishing a connection to AWS S3 fails"""

    pass


class SharepointConnectionException(Exception):
    """Raised if establishing a connection to Sharepoint fails"""

    pass


class SinglestoreConnectionException(Exception):
    """Raised if establishing a connection to Singlestore fails"""

    pass


class SinglestoreInsertionException(Exception):
    """Raised if inserting into Singlestore fails"""

    pass


class SinglestoreIndexInfoException(Exception):
    """Raised if getting index info from Singlestore fails"""

    pass


class SinglestoreQueryException(Exception):
    """Raised if querying Singlestore fails"""

    pass


class SourceConnectorEmptyException(Exception):
    """Raised when the SourceConnector dictionary is empty"""

    pass


class SupabaseConnectionException(Exception):
    """Raised if establishing a connection to Supabase fails"""

    pass


class SupabaseInsertionException(Exception):
    """Raised if inserting into Supabase fails"""

    pass


class SupabaseIndexInfoException(Exception):
    """Raised if getting index info from Supabase fails"""

    pass


class SupabaseQueryException(Exception):
    """Raised if querying Supabase fails"""

    pass


class ElasticsearchConnectionException(Exception):
    pass


class ElasticsearchIndexInfoException(Exception):
    pass


class ElasticsearchInsertionException(Exception):
    pass


class ElasticsearchQueryException(Exception):
    pass


class WeaviateConnectionException(Exception):
    """Raised if establishing a connection to Weaviate fails"""

    pass


class WeaviateInsertionException(Exception):
    """Raised if inserting into Weaviate fails"""

    pass


class WeaviateIndexInfoException(Exception):
    """Raised if getting index info from Weaviate fails"""

    pass


class WeaviateQueryException(Exception):
    """Raised if querying Weaviate fails"""

    pass


class WebsiteConnectionException(Exception):
    """Raised if establishing a connection to a website fails"""

    pass


class RagFileException(Exception):
    """Rasied if file couldn't be opened"""

    pass


class CustomChunkerException(Exception):
    """Raised if provided code doesn't work with established format"""

    pass
