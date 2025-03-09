# src/sources/s3_source.py
import os
from typing import Generator, List

import boto3

from src.schemas.cloud_file_schema import CloudFileSchema
from src.schemas.document_schema import DocumentSchema
from src.schemas.source_config_schema import SourceConfigSchema
from src.Sources.source_connector import SourceConnector


class S3SourceConnector(SourceConnector):
    def __init__(self, config: SourceConfigSchema):
        super().__init__(config)
        # Read bucket and AWS credentials from payload settings
        self.bucket_name = self.settings.get("bucket_name")
        self.prefix = self.settings.get("prefix", "")
        self.aws_access_key_id = self.settings.get("aws_access_key_id")
        self.aws_secret_access_key = self.settings.get("aws_secret_access_key")
        self.endpoint_url = self.settings.get("region", "us-east-1")
        
        if not self.bucket_name:
            raise ValueError("Bucket name is required in settings.")
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise ValueError("AWS credentials are required in settings.")

        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key,
            endpoint_url=self.endpoint_url,
            verify=False
        )

    def list_files_full(self) -> Generator[CloudFileSchema, None, None]:
        paginator = self.s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=self.bucket_name, Prefix=self.prefix)
        for page in pages:
            for obj in page.get('Contents', []):
                yield CloudFileSchema(
                    id=obj['ETag'],  # Example unique ID, can be improved
                    name=obj['Key'],
                    path=f"s3://{self.bucket_name}/{obj['Key']}",
                    metadata={"last_modified": str(obj['LastModified'])}
                )

    def list_files_delta(self, last_run: str) -> Generator[CloudFileSchema, None, None]:
        # Implement delta logic - placeholder uses full listing
        yield from self.list_files_full()

    def download_files(self, cloudFile: CloudFileSchema) -> Generator[object, None, None]:
        # Create a simple local file path by replacing slashes
        local_file_path = f"/tmp/{cloudFile.name.replace('/', '_')}"
        os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
        self.s3_client.download_file(self.bucket_name, cloudFile.name, local_file_path)
        yield local_file_path

    def load_data(
        self, file: object, cloud_file: CloudFileSchema
    ) -> Generator[DocumentSchema, None, None]:
        # Read the file and create a DocumentSchema using the provided cloud_file info
        try:
            with open(file) as f:  # Assuming text files for simplicity
                content = f.read()
                yield DocumentSchema(id=cloud_file.id, content=content, metadata=cloud_file.metadata)
        except Exception as e:
            print(f"Error loading file {file}: {e}")

    def chunk_data(self, document: DocumentSchema) -> Generator[List[DocumentSchema], None, None]:
        # Simple chunking by sentence; you may replace with more advanced techniques
        sentences = document.content.split('.')
        chunk_size = 3  # Group sentences into chunks of 3
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunk_content = '.'.join(sentences[i:i + chunk_size])
            if chunk_content.strip():  # Avoid empty chunks
                chunk_id = f"{document.id}-chunk-{i}"  # Unique ID for chunk
                chunks.append(
                    DocumentSchema(
                        id=chunk_id,
                        content=chunk_content,
                        metadata=document.metadata
                    )
                )
        yield chunks
