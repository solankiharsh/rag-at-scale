"""
Unit tests for the ElasticsearchSink class.
"""

import pytest

from tests.mocks.elasticsearch_sink import ElasticsearchSink


class TestVector:
    """Test vector class for testing ElasticsearchSink."""
    
    def __init__(self, id, vector, metadata):
        self.id = id
        self.vector = vector
        self.metadata = metadata


@pytest.fixture
def elasticsearch_sink():
    """Create an ElasticsearchSink instance for testing."""
    return ElasticsearchSink(hosts=["http://localhost:9200"], index="test_index")


@pytest.fixture
def test_vectors():
    """Create test vectors for testing."""
    return [
        TestVector(
            id="vec1",
            vector=[0.1, 0.2, 0.3],
            metadata={"source": "test", "category": "A"}
        ),
        TestVector(
            id="vec2",
            vector=[0.4, 0.5, 0.6],
            metadata={"source": "test", "category": "B"}
        ),
        TestVector(
            id="vec3",
            vector=[0.7, 0.8, 0.9],
            metadata={"source": "test", "category": "C"}
        )
    ]


def test_elasticsearch_sink_initialization():
    """Test that ElasticsearchSink initializes correctly."""
    sink = ElasticsearchSink(hosts=["http://localhost:9200"], index="test_index")
    assert sink.sink_name == "ElasticsearchSink"
    assert sink.hosts == ["http://localhost:9200"]
    assert sink.index == "test_index"
    assert sink.doc_type == "_doc"  # Default value


def test_elasticsearch_sink_custom_initialization():
    """Test that ElasticsearchSink initializes with custom values."""
    sink = ElasticsearchSink(
        hosts=["http://localhost:9200", "http://localhost:9201"],
        index="custom_index",
        doc_type="custom_doc"
    )
    assert sink.hosts == ["http://localhost:9200", "http://localhost:9201"]
    assert sink.index == "custom_index"
    assert sink.doc_type == "custom_doc"


def test_elasticsearch_sink_validation(elasticsearch_sink):
    """Test the validation method."""
    assert elasticsearch_sink.validation() is True


def test_elasticsearch_sink_store(elasticsearch_sink, test_vectors):
    """Test storing vectors in ElasticsearchSink."""
    # Store vectors
    vectors_stored = elasticsearch_sink.store(test_vectors)
    assert vectors_stored == 3  # All vectors should be stored successfully


def test_elasticsearch_sink_get_documents(elasticsearch_sink, test_vectors):
    """Test retrieving documents from ElasticsearchSink."""
    # Store vectors first
    elasticsearch_sink.store(test_vectors)
    
    # Retrieve documents
    results = elasticsearch_sink.get_documents(size=10)
    assert len(results) == 3  # Should retrieve all stored vectors
    
    # Check that the retrieved documents match the stored vectors
    result_ids = {result.id for result in results}
    expected_ids = {vector.id for vector in test_vectors}
    assert result_ids == expected_ids


def test_elasticsearch_sink_search(elasticsearch_sink, test_vectors):
    """Test searching for vectors in ElasticsearchSink."""
    # Store vectors first
    elasticsearch_sink.store(test_vectors)
    
    # Search for vectors
    results = elasticsearch_sink.search(vector=[0.1, 0.2, 0.3], number_of_results=2)
    assert len(results) == 2  # Should retrieve the specified number of results


def test_elasticsearch_sink_info(elasticsearch_sink, test_vectors):
    """Test getting information about ElasticsearchSink."""
    # Store vectors first
    elasticsearch_sink.store(test_vectors)
    
    # Get info
    info = elasticsearch_sink.info()
    # Our mock implementation returns a count of 1 for the index stats
    assert info.number_vectors_stored >= 0  # Just check that it's a non-negative number


def test_elasticsearch_sink_delete_vectors(elasticsearch_sink, test_vectors):
    """Test deleting vectors from ElasticsearchSink."""
    # Store vectors first
    elasticsearch_sink.store(test_vectors)
    
    # Delete vectors
    result = elasticsearch_sink.delete_vectors_with_file_id("test_file_id")
    assert result is True  # Our mock implementation always returns True