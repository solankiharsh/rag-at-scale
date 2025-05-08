"""
Unit tests for the RecursiveChunker class.
"""

from tests.mocks.rag_document import RagDocument
from tests.mocks.recursive_chunker import RecursiveChunker


def test_recursive_chunker_initialization():
    """Test that the RecursiveChunker initializes with default values."""
    chunker = RecursiveChunker()
    assert chunker.chunk_size == 500
    assert chunker.chunk_overlap == 0
    assert chunker.batch_size == 1000
    assert chunker.separators == ["\n\n", "\n", " ", ""]


def test_recursive_chunker_custom_initialization():
    """Test that the RecursiveChunker initializes with custom values."""
    chunker = RecursiveChunker(
        chunk_size=100,
        chunk_overlap=20,
        batch_size=50,
        separators=["\n", ",", " "]
    )
    assert chunker.chunk_size == 100
    assert chunker.chunk_overlap == 20
    assert chunker.batch_size == 50
    assert chunker.separators == ["\n", ",", " "]


def test_chunker_name():
    """Test that the chunker_name property returns the correct value."""
    chunker = RecursiveChunker()
    assert chunker.chunker_name == "RecursiveChunker"


def test_required_properties():
    """Test that the required_properties property returns the correct value."""
    chunker = RecursiveChunker()
    assert chunker.required_properties == []


def test_optional_properties():
    """Test that the optional_properties property returns the correct value."""
    chunker = RecursiveChunker()
    assert set(chunker.optional_properties) == {"chunk_size", "chunk_overlap", "batch_size", "separators"}


def test_config_validation():
    """Test that the config_validation method returns True."""
    chunker = RecursiveChunker()
    assert chunker.config_validation() is True


def test_chunk_single_document():
    """Test chunking a single document with paragraph separators."""
    chunker = RecursiveChunker(chunk_size=50, chunk_overlap=0, batch_size=5)
    doc = RagDocument(
        id="test_doc",
        content="This is paragraph one.\n\nThis is paragraph two.\n\nThis is paragraph three.",
        metadata={"source": "test"}
    )
    
    # Collect all chunks
    all_chunks = []
    for chunk_batch in chunker.chunk([doc]):
        all_chunks.extend(chunk_batch)
    
    # Verify the chunks
    assert len(all_chunks) == 3  # Should be split into 3 chunks (one per paragraph)
    assert all_chunks[0].id.startswith("test_doc_")
    assert all_chunks[0].metadata == {"source": "test"}
    
    # Check content of chunks
    assert "paragraph one" in all_chunks[0].content
    assert "paragraph two" in all_chunks[1].content
    assert "paragraph three" in all_chunks[2].content


def test_chunk_with_nested_separators():
    """Test chunking with nested separators."""
    chunker = RecursiveChunker(chunk_size=20, chunk_overlap=0, batch_size=5)
    doc = RagDocument(
        id="test_doc",
        content="Line 1, part A. Line 1, part B.\nLine 2, part A. Line 2, part B.",
        metadata={"source": "test"}
    )
    
    # Collect all chunks
    all_chunks = []
    for chunk_batch in chunker.chunk([doc]):
        all_chunks.extend(chunk_batch)
    
    # Verify the chunks
    assert len(all_chunks) > 2  # Should be split into multiple chunks
    assert all_chunks[0].id.startswith("test_doc_")
    
    # Check that each chunk is smaller than the chunk_size
    for chunk in all_chunks:
        assert len(chunk.content) <= 20


def test_chunk_multiple_documents():
    """Test chunking multiple documents."""
    chunker = RecursiveChunker(chunk_size=50, chunk_overlap=0, batch_size=5)
    docs = [
        RagDocument(
            id="doc1",
            content="This is document one.\n\nIt has two paragraphs.",
            metadata={"source": "test1"}
        ),
        RagDocument(
            id="doc2",
            content="This is document two.\n\nIt also has two paragraphs.",
            metadata={"source": "test2"}
        )
    ]
    
    # Collect all chunks
    all_chunks = []
    for chunk_batch in chunker.chunk(docs):
        all_chunks.extend(chunk_batch)
    
    # Verify the chunks
    assert len(all_chunks) == 4  # Should be 2 chunks per document
    
    # Check that chunks from different documents have different IDs
    doc1_chunks = [chunk for chunk in all_chunks if chunk.id.startswith("doc1")]
    doc2_chunks = [chunk for chunk in all_chunks if chunk.id.startswith("doc2")]
    assert len(doc1_chunks) == 2
    assert len(doc2_chunks) == 2
    
    # Check that metadata is preserved
    for chunk in doc1_chunks:
        assert chunk.metadata == {"source": "test1"}
    for chunk in doc2_chunks:
        assert chunk.metadata == {"source": "test2"}


def test_batch_size_respected():
    """Test that the batch_size is respected."""
    chunker = RecursiveChunker(chunk_size=10, chunk_overlap=0, batch_size=2)
    doc = RagDocument(
        id="test_doc",
        content="This is a test document with multiple sentences. "
                "It should be split into many chunks. "
                "Each chunk should be small. "
                "The batch size is set to 2.",
        metadata={"source": "test"}
    )
    
    # Collect batches
    batches = list(chunker.chunk([doc]))
    
    # Verify that each batch has at most batch_size chunks
    for batch in batches:
        assert len(batch) <= 2