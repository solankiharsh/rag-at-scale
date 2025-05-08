"""
Unit tests for the S3SourceConnector class.
"""

from datetime import datetime, timedelta

import pytest

from tests.mocks.s3_connector import CloudFileSchema, S3SourceConnector, SourceConfigSchema


@pytest.fixture
def s3_config():
    """Create a sample S3 configuration for testing."""
    return SourceConfigSchema(
        name="test-s3-source",
        settings={
            "aws_access_key_id": "test_key_id",
            "aws_secret_access_key": "test_access_key",
            "bucket_name": "test-bucket",
            "region": "us-east-1",
            "prefix": ""
        }
    )


@pytest.fixture
def s3_connector(s3_config):
    """Create an S3SourceConnector instance for testing."""
    return S3SourceConnector(s3_config)


def test_s3_connector_initialization(s3_connector, s3_config):
    """Test that S3SourceConnector initializes correctly."""
    assert s3_connector.aws_key_id == "test_key_id"
    assert s3_connector.aws_access_key == "test_access_key"
    assert s3_connector.bucket_name == "test-bucket"
    assert s3_connector.region == "us-east-1"
    assert s3_connector.prefix == ""


def test_s3_connector_config_validation(s3_connector):
    """Test the config_validation method."""
    assert s3_connector.config_validation() is True


def test_s3_connector_list_files_full(s3_connector):
    """Test listing all files in the bucket."""
    # Get all files
    files = list(s3_connector.list_files_full())
    
    # Verify we got the expected number of files
    assert len(files) == 3
    
    # Verify all files are CloudFileSchema objects
    assert all(isinstance(file, CloudFileSchema) for file in files)
    
    # Verify file paths
    file_names = [file.name for file in files]
    assert "file1.txt" in file_names
    assert "file2.pdf" in file_names
    assert "folder1/file3.json" in file_names
    
    # Verify file metadata
    for file in files:
        assert "content_type" in file.metadata
        assert "last_modified" in file.metadata
        assert "size" in file.metadata


def test_s3_connector_list_files_with_prefix(s3_config):
    """Test listing files with a prefix."""
    # Create a connector with a prefix
    s3_config.settings["prefix"] = "folder1/"
    s3_connector = S3SourceConnector(s3_config)
    
    # Get files with the prefix
    files = list(s3_connector.list_files_full())
    
    # Verify we got only files with the prefix
    assert len(files) == 1
    assert files[0].name == "folder1/file3.json"


def test_s3_connector_list_files_delta(s3_connector):
    """Test listing files modified after a certain time."""
    # Set a time in the past
    past_time = datetime.now() - timedelta(days=1)
    
    # Get files modified after the past time
    files = list(s3_connector.list_files_delta(past_time))
    
    # Verify we got all files (since they were all "modified" after the past time)
    assert len(files) == 3
    
    # Set a time in the future
    future_time = datetime.now() + timedelta(days=1)
    
    # Get files modified after the future time
    files = list(s3_connector.list_files_delta(future_time))
    
    # Verify we got no files
    assert len(files) == 0


def test_s3_connector_get_file_metadata(s3_connector):
    """Test getting metadata for a specific file."""
    # Get metadata for a file
    file_metadata = s3_connector.get_file_metadata("file1.txt")
    
    # Verify the metadata
    assert file_metadata.id == "file1.txt"
    assert file_metadata.name == "file1.txt"
    assert file_metadata.path == "s3://test-bucket/file1.txt"
    assert "content_type" in file_metadata.metadata
    assert file_metadata.metadata["content_type"] == "text/plain"
    
    # Test with a non-existent file
    with pytest.raises(ValueError):
        s3_connector.get_file_metadata("non_existent_file.txt")


def test_s3_connector_download_files(s3_connector):
    """Test downloading a file."""
    # Get a file to download
    files = list(s3_connector.list_files_full())
    file_to_download = files[0]
    
    # Download the file
    downloaded_paths = list(s3_connector.download_files(file_to_download))
    
    # Verify we got a path
    assert len(downloaded_paths) == 1
    downloaded_path = downloaded_paths[0]
    
    # Verify the file exists and has content
    import os
    assert os.path.exists(downloaded_path)
    
    with open(downloaded_path, "r") as f:
        content = f.read()
    
    # Verify the content matches what we expect
    if file_to_download.name == "file1.txt":
        assert content == "This is a mock text file for testing."
    elif file_to_download.name == "file2.pdf":
        assert content == "Mock PDF content"
    elif file_to_download.name == "folder1/file3.json":
        assert content == '{"key": "value", "nested": {"key": "value"}}'