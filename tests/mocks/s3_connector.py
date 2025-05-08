"""
Mock S3SourceConnector for testing purposes.
This file contains a mock implementation of the S3SourceConnector class.
"""

import os
import tempfile
from collections.abc import Generator
from datetime import datetime
from typing import Any, Dict

from pydantic import BaseModel, Field


class Selector(BaseModel):
    """Mock Selector class for testing."""
    to_embed: list[str] = Field(default_factory=list)
    to_metadata: list[str] = Field(default_factory=list)


class CloudFileSchema(BaseModel):
    """Mock CloudFileSchema class for testing."""
    id: str
    name: str
    path: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SourceConfigSchema(BaseModel):
    """Mock SourceConfigSchema class for testing."""
    name: str
    settings: Dict[str, Any] = Field(default_factory=dict)


class SourceConnector(BaseModel):
    """Mock base SourceConnector class for testing."""
    
    def __init__(self, config: SourceConfigSchema):
        super().__init__()
        self.config = config
    
    def config_validation(self) -> bool:
        """Validate the configuration."""
        return True


class S3SourceConnector:
    """
    Mock S3SourceConnector for testing.
    
    This connector simulates connecting to an S3 bucket and listing/downloading files.
    """
    
    # Mock data for testing
    _mock_files: Dict[str, Dict[str, Any]] = {}
    
    def __init__(self, config: SourceConfigSchema):
        """Initialize the S3SourceConnector with the given configuration."""
        self.config = config
        self.aws_key_id = config.settings.get("aws_access_key_id", "mock_key_id")
        self.aws_access_key = config.settings.get("aws_secret_access_key", "mock_access_key")
        self.bucket_name = config.settings.get("bucket_name", "mock-bucket")
        self.region = config.settings.get("region", "us-east-1")
        self.prefix = config.settings.get("prefix", "")
        self.selector = Selector(to_embed=[], to_metadata=[])
        
        # Initialize mock data
        self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize mock data for testing."""
        self._mock_files = {
            "file1.txt": {
                "content": "This is a mock text file for testing.",
                "metadata": {
                    "content_type": "text/plain",
                    "last_modified": datetime.now(),
                    "size": 100
                }
            },
            "file2.pdf": {
                "content": "Mock PDF content",
                "metadata": {
                    "content_type": "application/pdf",
                    "last_modified": datetime.now(),
                    "size": 500
                }
            },
            "folder1/file3.json": {
                "content": '{"key": "value", "nested": {"key": "value"}}',
                "metadata": {
                    "content_type": "application/json",
                    "last_modified": datetime.now(),
                    "size": 200
                }
            }
        }
    
    def config_validation(self) -> bool:
        """Validate the configuration."""
        # In a real implementation, this would check the AWS credentials and bucket
        # For testing, we'll just return True
        return True
    
    def get_file_metadata(self, key: str) -> CloudFileSchema:
        """Get metadata for a specific file."""
        if key not in self._mock_files:
            raise ValueError(f"File {key} not found in mock bucket {self.bucket_name}")
        
        file_data = self._mock_files[key]
        return CloudFileSchema(
            id=key,
            name=key,
            path=f"s3://{self.bucket_name}/{key}",
            metadata=file_data["metadata"]
        )
    
    def list_files_full(self) -> Generator[CloudFileSchema, None, None]:
        """List all files in the bucket with the given prefix."""
        prefix = self.prefix or ""
        
        for key, file_data in self._mock_files.items():
            if key.startswith(prefix):
                yield CloudFileSchema(
                    id=key,
                    name=key,
                    path=f"s3://{self.bucket_name}/{key}",
                    metadata=file_data["metadata"]
                )
    
    def list_files_delta(self, last_run: datetime) -> Generator[CloudFileSchema, None, None]:
        """List files modified after the given datetime."""
        for key, file_data in self._mock_files.items():
            if file_data["metadata"]["last_modified"] > last_run:
                yield CloudFileSchema(
                    id=key,
                    name=key,
                    path=f"s3://{self.bucket_name}/{key}",
                    metadata=file_data["metadata"]
                )
    
    def download_files(self, cloud_file: CloudFileSchema) -> Generator[str, None, None]:
        """Download a file to a temporary location and yield the path."""
        key = cloud_file.name
        if key not in self._mock_files:
            raise ValueError(f"File {key} not found in mock bucket {self.bucket_name}")
        
        # Create a temporary file that will persist beyond the generator
        temp_dir = tempfile.mkdtemp()
        local_file_path = os.path.join(temp_dir, key.replace("/", "_"))
        
        # Write mock content to the file
        with open(local_file_path, "w") as f:
            f.write(self._mock_files[key]["content"])
        
        # Make sure the file exists before yielding
        assert os.path.exists(local_file_path)
        
        yield local_file_path