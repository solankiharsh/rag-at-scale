import pytest

from tests.mocks.rag_document import RagDocument


@pytest.fixture
def sample_rag_document():
    """Fixture to create a sample RagDocument for testing."""
    return RagDocument(
        id="test-doc-001",
        content="This is a test document for RAG testing.",
        metadata={"source": "test", "author": "pytest"}
    )


@pytest.fixture
def sample_rag_documents():
    """Fixture to create a list of sample RagDocuments for testing."""
    return [
        RagDocument(
            id="doc-001",
            content="This is the first test document.",
            metadata={"source": "test", "index": 1}
        ),
        RagDocument(
            id="doc-002",
            content="This is the second test document.",
            metadata={"source": "test", "index": 2}
        ),
        RagDocument(
            id="doc-003",
            content="This is the third test document.",
            metadata={"source": "test", "index": 3}
        )
    ]