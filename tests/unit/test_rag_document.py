import pytest

from tests.mocks.exceptions import RagDocumentEmptyException
from tests.mocks.rag_document import RagDocument


def test_rag_document_initialization():
    """Test that RagDocument initializes correctly with the provided values."""
    doc = RagDocument(id="test_id", content="test content", metadata={"source": "test"})
    
    assert doc.id == "test_id"
    assert doc.content == "test content"
    assert doc.metadata == {"source": "test"}


def test_rag_document_as_file():
    """Test the as_file class method for creating a RagDocument from a dictionary."""
    doc_dict = {
        "id": "test_id",
        "content": "test content",
        "metadata": {"source": "test"}
    }
    
    doc = RagDocument.as_file(doc_dict)
    
    assert doc.id == "test_id"
    assert doc.content == "test content"
    assert doc.metadata == {"source": "test"}


def test_rag_document_as_file_empty_dict():
    """Test that as_file raises an exception when given None."""
    with pytest.raises(RagDocumentEmptyException):
        RagDocument.as_file(None)


def test_rag_document_to_json():
    """Test the to_json method returns the correct dictionary representation."""
    doc = RagDocument(id="test_id", content="test content", metadata={"source": "test"})
    
    json_data = doc.to_json()
    
    assert json_data == {
        "id": "test_id",
        "content": "test content",
        "metadata": {"source": "test"}
    }


def test_rag_document_with_empty_metadata():
    """Test that RagDocument works with empty metadata."""
    doc = RagDocument(id="test_id", content="test content", metadata={})
    
    assert doc.id == "test_id"
    assert doc.content == "test content"
    assert doc.metadata == {}
    
    json_data = doc.to_json()
    assert json_data["metadata"] == {}