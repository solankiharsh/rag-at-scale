"""
Unit tests for the PDFLoader class.
"""

import pytest

from tests.mocks.pdf_loader import LocalFile, PDFLoader


@pytest.fixture
def pdf_loader():
    """Create a PDFLoader instance for testing."""
    return PDFLoader()


@pytest.fixture
def sample_pdf_file():
    """Create a sample PDF file for testing."""
    return LocalFile(
        id="test_pdf",
        file_path="/path/to/test.pdf",
        metadata={"source": "test", "author": "Test Author"}
    )


def test_pdf_loader_initialization(pdf_loader):
    """Test that PDFLoader initializes correctly."""
    assert pdf_loader.loader_name == "PDFLoader"
    assert pdf_loader.required_properties == []
    assert pdf_loader.optional_properties == []
    assert pdf_loader.available_metadata == []
    assert pdf_loader.available_content == []


def test_pdf_loader_config_validation(pdf_loader):
    """Test the config_validation method."""
    assert pdf_loader.config_validation() is True


def test_pdf_loader_load(pdf_loader, sample_pdf_file):
    """Test loading a PDF file."""
    # Collect all documents
    documents = list(pdf_loader.load(sample_pdf_file))
    
    # Verify the number of documents (our mock returns 3 pages)
    assert len(documents) == 3
    
    # Verify document IDs follow the expected pattern
    assert documents[0].id == "test_pdf_page_1"
    assert documents[1].id == "test_pdf_page_2"
    assert documents[2].id == "test_pdf_page_3"
    
    # Verify metadata is preserved
    for doc in documents:
        assert doc.metadata == sample_pdf_file.metadata
        assert "source" in doc.metadata
        assert doc.metadata["source"] == "test"
        assert "author" in doc.metadata
        assert doc.metadata["author"] == "Test Author"
    
    # Verify content
    for i, doc in enumerate(documents):
        assert f"This is page {i+1}" in doc.content
        assert "Sample content for testing" in doc.content