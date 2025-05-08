"""
Unit tests for the OpenAIEmbedModel class.
"""

import pytest

from tests.mocks.openai_embed_model import OpenAIEmbedModel
from tests.mocks.rag_document import RagDocument


@pytest.fixture
def openai_embed_model():
    """Create an OpenAIEmbedModel instance for testing."""
    return OpenAIEmbedModel(api_key="test_api_key")


@pytest.fixture
def sample_documents():
    """Create sample documents for testing."""
    return [
        RagDocument(id="doc1", content="This is the first test document.", metadata={"source": "test1"}),
        RagDocument(id="doc2", content="This is the second test document.", metadata={"source": "test2"}),
        RagDocument(id="doc3", content="This is the third test document.", metadata={"source": "test3"})
    ]


def test_openai_embed_model_initialization(openai_embed_model):
    """Test that OpenAIEmbedModel initializes correctly."""
    assert openai_embed_model.embed_name == "text-embedding-ada-002"
    assert openai_embed_model.api_key == "test_api_key"
    assert openai_embed_model.max_retries == 20
    assert openai_embed_model.chunk_size == 1000


def test_openai_embed_model_custom_initialization():
    """Test that OpenAIEmbedModel initializes with custom values."""
    model = OpenAIEmbedModel(
        api_key="custom_api_key",
        max_retries=10,
        chunk_size=500
    )
    
    assert model.api_key == "custom_api_key"
    assert model.max_retries == 10
    assert model.chunk_size == 500


def test_openai_embed_model_properties(openai_embed_model):
    """Test the properties of OpenAIEmbedModel."""
    assert openai_embed_model.required_properties == ["api_key"]
    assert set(openai_embed_model.optional_properties) == {"max_retries", "chunk_size"}


def test_openai_embed_model_validation(openai_embed_model):
    """Test the validation method."""
    assert openai_embed_model.validation() is True
    
    # Test with empty API key
    invalid_model = OpenAIEmbedModel(api_key="")
    assert invalid_model.validation() is False


@pytest.mark.asyncio
async def test_openai_embed_model_embed(openai_embed_model, sample_documents):
    """Test the embed method."""
    # Call the embed method
    vectors, usage = await openai_embed_model.embed(sample_documents)
    
    # Verify the number of vectors matches the number of documents
    assert len(vectors) == len(sample_documents)
    
    # Verify each vector is a list of floats
    for vector in vectors:
        assert isinstance(vector, list)
        assert all(isinstance(val, float) for val in vector)
    
    # Verify usage information
    assert "prompt_tokens" in usage
    assert "total_tokens" in usage
    assert usage["prompt_tokens"] == len(sample_documents) * 100
    assert usage["total_tokens"] == len(sample_documents) * 100


def test_openai_embed_model_embed_query(openai_embed_model):
    """Test the embed_query method."""
    # Call the embed_query method
    vector = openai_embed_model.embed_query("Test query")
    
    # Verify the vector is a list of floats
    assert isinstance(vector, list)
    assert all(isinstance(val, float) for val in vector)
    assert len(vector) == 10  # Our mock returns a 10-dimensional vector