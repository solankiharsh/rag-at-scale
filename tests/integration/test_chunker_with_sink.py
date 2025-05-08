"""
Integration tests for testing the chunker with a sink connector.
"""

import pytest

from tests.mocks.character_chunker import CharacterChunker
from tests.mocks.elasticsearch_sink import ElasticsearchSink
from tests.mocks.rag_document import RagDocument


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return RagDocument(
        id="test_doc",
        content="This is a test document for integration testing. It contains multiple sentences "
                "that will be split into chunks by the character chunker. The chunks will then "
                "be stored in the Elasticsearch sink.",
        metadata={"source": "integration_test", "type": "test"}
    )


@pytest.fixture
def chunker():
    """Create a character chunker for testing."""
    return CharacterChunker(chunk_size=50, chunk_overlap=10, batch_size=5)


@pytest.fixture
def sink():
    """Create an Elasticsearch sink for testing."""
    return ElasticsearchSink(hosts=["http://localhost:9200"], index="test_index")


class TestVector:
    """Test vector class for testing."""
    
    def __init__(self, id, vector, metadata):
        self.id = id
        self.vector = vector
        self.metadata = metadata


def test_chunker_with_sink(sample_document, chunker, sink):
    """Test the integration of chunker with sink."""
    # Step 1: Chunk the document
    all_chunks = []
    for chunk_batch in chunker.chunk([sample_document]):
        all_chunks.extend(chunk_batch)
    
    # Verify chunks were created
    assert len(all_chunks) > 1
    
    # Step 2: Create vectors from chunks (in a real system, this would be done by an embedding model)
    vectors = []
    for i, chunk in enumerate(all_chunks):
        # Create a simple mock vector (in a real system, this would be the embedding)
        vector = [0.1 * i, 0.2 * i, 0.3 * i]
        vectors.append(TestVector(id=chunk.id, vector=vector, metadata=chunk.metadata))
    
    # Step 3: Store vectors in the sink
    vectors_stored = sink.store(vectors)
    
    # Verify vectors were stored
    assert vectors_stored == len(vectors)
    
    # Step 4: Retrieve documents from the sink
    results = sink.get_documents(size=len(vectors))
    
    # Verify all documents were retrieved
    assert len(results) == len(vectors)
    
    # Step 5: Search for documents
    search_results = sink.search(vector=[0.1, 0.2, 0.3], number_of_results=2)
    
    # Verify search returned results
    assert len(search_results) > 0