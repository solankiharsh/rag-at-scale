"""
Unit tests for the CSVLoader class.
"""

import pytest

from tests.mocks.csv_loader import CSVLoader, LocalFile, Selector


@pytest.fixture
def csv_loader():
    """Create a CSVLoader instance for testing."""
    return CSVLoader()


@pytest.fixture
def csv_loader_with_selector():
    """Create a CSVLoader instance with a custom selector for testing."""
    return CSVLoader(
        selector=Selector(
            to_embed=["name", "city"],
            to_metadata=["age"]
        )
    )


@pytest.fixture
def sample_csv_file():
    """Create a sample CSV file for testing."""
    return LocalFile(
        id="test_csv",
        file_path="/path/to/test.csv",
        metadata={"source": "test", "format": "csv"}
    )


def test_csv_loader_initialization(csv_loader):
    """Test that CSVLoader initializes correctly with default values."""
    assert csv_loader.loader_name == "CSVLoader"
    assert csv_loader.id_key == "id"
    assert csv_loader.source_column is None
    assert csv_loader.encoding == "utf-8-sig"
    assert csv_loader.csv_args is None
    assert csv_loader.selector.to_embed == []
    assert csv_loader.selector.to_metadata == []


def test_csv_loader_custom_initialization():
    """Test that CSVLoader initializes with custom values."""
    loader = CSVLoader(
        id_key="custom_id",
        source_column="name",
        encoding="utf-8",
        csv_args={"delimiter": ","},
        selector=Selector(to_embed=["name"], to_metadata=["age"])
    )
    
    assert loader.id_key == "custom_id"
    assert loader.source_column == "name"
    assert loader.encoding == "utf-8"
    assert loader.csv_args == {"delimiter": ","}
    assert loader.selector.to_embed == ["name"]
    assert loader.selector.to_metadata == ["age"]


def test_csv_loader_properties(csv_loader):
    """Test the properties of CSVLoader."""
    assert csv_loader.required_properties == []
    assert set(csv_loader.optional_properties) == {"id_key", "source_column", "encoding", "csv_args"}
    assert csv_loader.available_metadata == ["custom"]
    assert csv_loader.available_content == ["custom"]


def test_csv_loader_config_validation(csv_loader):
    """Test the config_validation method."""
    assert csv_loader.config_validation() is True


def test_csv_loader_load(csv_loader, sample_csv_file):
    """Test loading a CSV file with default settings."""
    # Collect all documents
    documents = list(csv_loader.load(sample_csv_file))
    
    # Verify the number of documents (our mock returns 3 rows)
    assert len(documents) == 3
    
    # Verify document IDs follow the expected pattern
    assert documents[0].id == "1.id"
    assert documents[1].id == "2.id"
    assert documents[2].id == "3.id"
    
    # Verify metadata includes source and row
    for i, doc in enumerate(documents):
        assert "source" in doc.metadata
        assert doc.metadata["source"] == sample_csv_file.file_path
        assert "row" in doc.metadata
        assert doc.metadata["row"] == i
    
    # Verify content includes all fields
    assert "id: 1" in documents[0].content
    assert "name: John Doe" in documents[0].content
    assert "age: 30" in documents[0].content
    assert "city: New York" in documents[0].content


def test_csv_loader_with_source_column():
    """Test loading a CSV file with a source column specified."""
    loader = CSVLoader(source_column="name")
    file = LocalFile(id="test_csv", file_path="/path/to/test.csv")
    
    # Collect all documents
    documents = list(loader.load(file))
    
    # Verify the source is set to the value in the source column
    assert documents[0].metadata["source"] == "John Doe"
    assert documents[1].metadata["source"] == "Jane Smith"
    assert documents[2].metadata["source"] == "Bob Johnson"


def test_csv_loader_with_selector(csv_loader_with_selector, sample_csv_file):
    """Test loading a CSV file with a custom selector."""
    # Collect all documents
    documents = list(csv_loader_with_selector.load(sample_csv_file))
    
    # Verify metadata includes only the fields specified in to_metadata
    assert "age" in documents[0].metadata
    assert documents[0].metadata["age"] == "30"
    
    # Verify content includes only the fields specified in to_embed
    assert "name: John Doe" in documents[0].content
    assert "city: New York" in documents[0].content
    assert "age: 30" not in documents[0].content  # age should not be in content
    assert "id: 1" not in documents[0].content  # id should not be in content