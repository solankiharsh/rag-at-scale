from tests.mocks.character_chunker import CharacterChunker
from tests.mocks.rag_document import RagDocument


def test_character_chunker_initialization():
    """Test that the CharacterChunker initializes with default values."""
    chunker = CharacterChunker()
    assert chunker.chunk_size == 500
    assert chunker.chunk_overlap == 0
    assert chunker.batch_size == 1000
    assert chunker.separator == "\n\n"


def test_character_chunker_custom_initialization():
    """Test that the CharacterChunker initializes with custom values."""
    chunker = CharacterChunker(
        chunk_size=200,
        chunk_overlap=50,
        batch_size=500,
        separator="\n"
    )
    assert chunker.chunk_size == 200
    assert chunker.chunk_overlap == 50
    assert chunker.batch_size == 500
    assert chunker.separator == "\n"


def test_chunker_name():
    """Test that the chunker_name property returns the correct value."""
    chunker = CharacterChunker()
    assert chunker.chunker_name == "CharacterChunker"


def test_required_properties():
    """Test that the required_properties property returns an empty list."""
    chunker = CharacterChunker()
    assert chunker.required_properties == []


def test_optional_properties():
    """Test that the optional_properties property returns the correct list."""
    chunker = CharacterChunker()
    assert set(chunker.optional_properties) == {"chunk_size", "chunk_overlap", "batch_size", "separator"}


def test_config_validation():
    """Test that config_validation returns True."""
    chunker = CharacterChunker()
    assert chunker.config_validation() is True


def test_chunk_single_document():
    """Test chunking a single document."""
    chunker = CharacterChunker(chunk_size=10, chunk_overlap=0, batch_size=5)
    doc = RagDocument(id="test_doc", content="This is a test document for chunking.", metadata={"source": "test"})
    
    # Collect all chunks
    all_chunks = []
    for chunk_batch in chunker.chunk([doc]):
        all_chunks.extend(chunk_batch)
    
    # Verify the chunks
    assert len(all_chunks) > 1  # Should be split into multiple chunks
    assert all_chunks[0].id.startswith("test_doc_")
    assert all_chunks[0].metadata == {"source": "test"}
    
    # Verify that all chunks together contain the original content
    # Note: Due to the way chunking works, we can't guarantee exact reconstruction
    # but we can check that all chunks are from the original document
    original_content = doc.content.lower()
    for chunk in all_chunks:
        assert chunk.content.lower() in original_content or original_content in chunk.content.lower()


def test_chunk_multiple_documents():
    """Test chunking multiple documents."""
    chunker = CharacterChunker(chunk_size=10, chunk_overlap=0, batch_size=10)
    docs = [
        RagDocument(id="doc1", content="This is document one.", metadata={"source": "test1"}),
        RagDocument(id="doc2", content="This is document two.", metadata={"source": "test2"})
    ]
    
    # Collect all chunks
    all_chunks = []
    for chunk_batch in chunker.chunk(docs):
        all_chunks.extend(chunk_batch)
    
    # Verify we have chunks from both documents
    doc1_chunks = [chunk for chunk in all_chunks if chunk.id.startswith("doc1")]
    doc2_chunks = [chunk for chunk in all_chunks if chunk.id.startswith("doc2")]
    
    assert len(doc1_chunks) > 0
    assert len(doc2_chunks) > 0
    
    # Verify metadata is preserved
    assert doc1_chunks[0].metadata == {"source": "test1"}
    assert doc2_chunks[0].metadata == {"source": "test2"}


def test_batch_size_respected():
    """Test that the batch_size is respected when yielding chunks."""
    chunker = CharacterChunker(chunk_size=5, chunk_overlap=0, batch_size=3)
    # Create a document that will generate more chunks than the batch size
    doc = RagDocument(id="test_doc", content="This is a test document that should generate multiple batches of chunks.", metadata={})
    
    # Collect batches
    batches = list(chunker.chunk([doc]))
    
    # Verify that most batches have the specified batch size
    # (The last batch might have fewer chunks)
    for i in range(len(batches) - 1):  # Skip the last batch
        assert len(batches[i]) == 3  # Should match batch_size
    
    # The last batch might have fewer chunks
    assert len(batches[-1]) <= 3