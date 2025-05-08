"""
Integration tests for testing the loader with a chunker and sink.
"""

import pytest

from tests.mocks.character_chunker import CharacterChunker
from tests.mocks.elasticsearch_sink import ElasticsearchSink
from tests.mocks.pdf_loader import LocalFile, PDFLoader


class TestVector:
    """Test vector class for testing."""
    
    def __init__(self, id, vector, metadata):
        self.id = id
        self.vector = vector
        self.metadata = metadata


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    return LocalFile(
        id="test_pdf",
        file_path="/path/to/test.pdf",
        metadata={"source": "test", "author": "Test Author"}
    )


@pytest.fixture
def pdf_loader():
    """Create a PDFLoader for testing."""
    return PDFLoader()


@pytest.fixture
def chunker():
    """Create a CharacterChunker for testing."""
    return CharacterChunker(chunk_size=50, chunk_overlap=10, batch_size=5)


@pytest.fixture
def sink():
    """Create an ElasticsearchSink for testing."""
    return ElasticsearchSink(hosts=["http://localhost:9200"], index="test_index")


def test_loader_chunker_sink(sample_pdf_file, pdf_loader, chunker, sink):
    """Test the integration of loader with chunker and sink."""
    # Step 1: Load documents from PDF
    documents = list(pdf_loader.load(sample_pdf_file))
    
    # Verify documents were loaded
    assert len(documents) > 0
    
    # Step 2: Chunk the documents
    all_chunks = []
    for chunk_batch in chunker.chunk(documents):
        all_chunks.extend(chunk_batch)
    
    # Verify chunks were created
    assert len(all_chunks) > len(documents)
    
    # Step 3: Create vectors from chunks (in a real system, this would be done by an embedding model)
    vectors = []
    for i, chunk in enumerate(all_chunks):
        # Create a simple mock vector (in a real system, this would be the embedding)
        vector = [0.1 * i, 0.2 * i, 0.3 * i]
        vectors.append(TestVector(id=chunk.id, vector=vector, metadata=chunk.metadata))
    
    # Step 4: Store vectors in the sink
    vectors_stored = sink.store(vectors)
    
    # Verify vectors were stored
    assert vectors_stored == len(vectors)
    
    # Step 5: Retrieve documents from the sink
    results = sink.get_documents(size=len(vectors))
    
    # Verify all documents were retrieved
    assert len(results) == len(vectors)
    
    # Step 6: Search for documents
    search_results = sink.search(vector=[0.1, 0.2, 0.3], number_of_results=2)
    
    # Verify search returned results
    assert len(search_results) > 0
    
    # Step 7: Get sink info
    info = sink.info()
    
    # Verify info contains vector count
    assert info.number_vectors_stored >= 0