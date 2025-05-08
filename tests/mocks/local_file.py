"""
Mock LocalFile for testing purposes.
This file contains a mock implementation of the LocalFile class.
"""

from pydantic import BaseModel, Field


class LocalFile(BaseModel):
    """
    Represents a local file in the system.
    
    Attributes:
        id (str): Unique identifier for the file
        file_path (str): Path to the file on the local filesystem
        metadata (dict): Additional metadata about the file
    """
    
    id: str = Field(..., description="Unique identifier for the file")
    file_path: str = Field(..., description="Path to the file on the local filesystem")
    metadata: dict = Field(default_factory=dict, description="Additional metadata about the file")