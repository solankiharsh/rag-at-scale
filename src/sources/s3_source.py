# src/sources/s3_source.py
import os
import tempfile
from datetime import datetime
from typing import Generator, Optional

import boto3
from pydantic import Field

from src.schemas.cloud_file_schema import CloudFileSchema
from src.schemas.source_config_schema import SourceConfigSchema
from src.Shared.Exceptions import S3ConnectionException
from src.Shared.RagDocument import RagDocument
from src.Shared.Selector import Selector
from src.Sources.source_connector import SourceConnector
from utils.platform_commons.logger import logger


class S3SourceConnector(SourceConnector):
    aws_key_id: str = Field(..., description="AWS Key ID for S3 access.")
    aws_access_key: str = Field(..., description="AWS Access Key for S3 access.")
    bucket_name: str = Field(..., description="S3 bucket name.")
    prefix: Optional[str] = Field("", description="Optional prefix for S3 files.")
    selector: Optional[Selector] = Field(
        Selector(to_embed=[], to_metadata=[]),
        description="Selector for metadata"
    )

    def __init__(self, config: SourceConfigSchema):
        super().__init__(config)
        logger.info(f"Initializing S3SourceConnector for bucket: {config.name}")
        self.aws_key_id = config.settings.get('aws_access_key_id')
        self.aws_access_key = config.settings.get('aws_secret_access_key')
        self.bucket_name = config.settings.get('bucket_name')
        self.region = config.settings.get('region')
        self.prefix = config.settings.get('prefix')

        self.client = boto3.client(
            service_name="s3",
            endpoint_url=self.region,
            aws_access_key_id=self.aws_key_id,
            aws_secret_access_key=self.aws_access_key,
            verify=False
        )
        
        # Initialize the S3 resource
        self.s3_resource = boto3.resource(
            service_name="s3",
            endpoint_url=self.region,
            aws_access_key_id=self.aws_key_id,
            aws_secret_access_key=self.aws_access_key,
            verify=False
        )
        
        self.config_validation()

    def config_validation(self) -> bool:
        # if not all(x in self.available_metadata for x in self.selector.to_metadata):
        #     raise ValueError("Invalid metadata values provided")
        try:
            client = boto3.client(
                service_name="s3",
                endpoint_url=self.region,
                aws_access_key_id=self.aws_key_id,
                aws_secret_access_key=self.aws_access_key,
                verify=False
            )
            client.head_bucket(Bucket=self.bucket_name)
        except Exception as e:
            raise S3ConnectionException(
                f"Connection to S3 failed, check key and key ID. See Exception: {e}"
            )
        return True

    def list_files_full(self) -> Generator[CloudFileSchema, None, None]:
        prefix = self.prefix or ""  # Use empty string if prefix is None
        logger.info(f"Listing files in bucket {self.bucket_name} with prefix '{prefix}'")
        
        bucket = self.s3_resource.Bucket(self.bucket_name)
        logger.info(f"bucket: {bucket}")
        for obj in bucket.objects.filter(Prefix=prefix):
            logger.info(f"obj: {obj}")
            metadata = {"last_modified": obj.last_modified}
            logger.info(f"metadata: {metadata}")
            if hasattr(self.selector, "to_metadata") and "metadata" in self.selector.to_metadata:
                additional_metadata = self.client.head_object(
                    Bucket=self.bucket_name, Key=obj.key
                )["Metadata"]
                metadata.update(additional_metadata)

            logger.info(f"Found file: {obj.key}")
            yield CloudFileSchema(
                id=obj.key,
                name=obj.key,
                path=f"s3://{self.bucket_name}/{obj.key}",
                metadata=metadata
            )


    def list_files_delta(self, last_run: datetime) -> Generator[CloudFileSchema, None, None]:
        for obj in self.bucket.objects.filter(Prefix=self.prefix):
            if obj.last_modified > last_run:
                metadata = {"last_modified": obj.last_modified}
                if "metadata" in self.selector.to_metadata:
                    additional_metadata = self.client.head_object(
                        Bucket=self.bucket_name, Key=obj.key
                    )["Metadata"]
                    metadata.update(additional_metadata)
                yield CloudFileSchema(
                    id=obj.key,
                    name=obj.key,
                    path=f"s3://{self.bucket_name}/{obj.key}",
                    metadata=metadata
                )

    def download_files(self, cloud_file: CloudFileSchema) -> Generator[object, None, None]:
        with tempfile.TemporaryDirectory() as temp_dir:
            local_file_path = os.path.join(temp_dir, cloud_file.name.replace("/", "_"))
            try:
                logger.info(f"Downloading file {cloud_file.name} to {local_file_path}")
                self.client.download_file(self.bucket_name, cloud_file.name, local_file_path)
                yield local_file_path
            except Exception as e:
                logger.error(f"Error downloading file {cloud_file.name}: {e}")
                raise

    def load_data(
        self, local_file: object, cloud_file: CloudFileSchema
    ) -> Generator[RagDocument, None, None]:
        logger.info(f"Loading data from local file: {local_file} with cloud metadata: {cloud_file}")
        try:
            with open(local_file) as f:
                content = f.read()
                yield RagDocument(id=cloud_file.id, content=content, metadata=cloud_file.metadata)
        except Exception as e:
            print(f"Error loading file {local_file}: {e}")

    def chunk_data(self, document: RagDocument) -> Generator[list[RagDocument], None, None]:
        sentences = document.content.split(".")
        chunk_size = 3
        chunks = []
        for i in range(0, len(sentences), chunk_size):
            chunk_content = ".".join(sentences[i:i + chunk_size])
            if chunk_content.strip():
                chunk_id = f"{document.id}-chunk-{i}"
                chunks.append(
                    RagDocument(
                        id=chunk_id,
                        content=chunk_content,
                        metadata=document.metadata
                    )
                )
        yield chunks
