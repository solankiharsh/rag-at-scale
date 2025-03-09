# src/pipeline/pipeline.py

import asyncio
import os
from asyncio.log import logger

from src.embeddings.embed_model import EmbedModel
from src.Loaders.LoaderFactory import LoaderFactory
from src.ModelFactories.SinkConnectorFactory import SinkConnectorFactory
from src.schemas.cloud_file_schema import CloudFileSchema
from src.schemas.pipeline_config_schema import PipelineConfigSchema
from src.Shared.LocalFile import LocalFile
from src.Shared.RagDocument import RagDocument
from src.Shared.RagVector import RagVector
from src.Sources.source_connector import SourceConnector


class Pipeline:
    def __init__(self, pipeline_config: PipelineConfigSchema):
        self.id = pipeline_config.id
        self.name = pipeline_config.name
        logger.info(f"pipeline_config.sources: {pipeline_config.sources}")
        self.sources = [
            SourceConnector.create_source(source_config)
            for source_config in pipeline_config.sources
        ]
        self.embed = EmbedModel.create_embed_model(pipeline_config.embed_model)
        
        self.sink = SinkConnectorFactory.get_sink(
            pipeline_config.sink.type, pipeline_config.sink.settings
        )
        self.config = pipeline_config

    @staticmethod
    def create_pipeline(pipeline_config_dict: dict):
        config = PipelineConfigSchema(**pipeline_config_dict)
        logger.info(f"config: {config}")
        return Pipeline(pipeline_config=config)

    def as_json(self):
        return self.config.dict()

    def run_extraction(self, extract_type, last_extraction = None):
        for source in self.sources:
            if extract_type == "full": # Assuming string for now, can use Enum
                for file in source.list_files_full():
                    yield source, file # Yield source and file for processing
            elif extract_type == "delta":
                for file in source.list_files_delta(last_run = last_extraction):
                    yield source, file

    def process_document(self, source: SourceConnector, cloud_file: CloudFileSchema):
        logger.info(f"Starting document processing for: {cloud_file.id} ({cloud_file.name})")
        
        for local_file in source.download_files(cloud_file=cloud_file):
            logger.info(f"Downloaded file locally: {local_file}")

            # Handle file object creation
            try:
                # Handle both dict and non-dict file representations
                if isinstance(local_file, dict):
                    file_obj = LocalFile.as_file(local_file)
                    logger.info(f"Converted local file to LocalFile object: {file_obj}")

                elif isinstance(local_file, str):
                    logger.warning(
                        f"Received file as a string. Wrapping in a dictionary: {local_file}"
                    )
                    metadata = cloud_file.metadata if cloud_file.metadata else {}
                    file_obj = LocalFile.as_file({
                        "file_path": local_file,
                        "metadata": metadata,
                        "type": os.path.splitext(local_file)[1],
                        "id": cloud_file.id
                    })

                else:
                    logger.error(
                        f"Invalid local_file type: {type(local_file)} with value: {local_file}"
                    )
                    raise TypeError("local_file must be a dictionary or file path string")
                
                # Extract file extension
                file_path = local_file if isinstance(local_file, str) else file_obj.file_path
                file_extension = os.path.splitext(file_path)[1]
                file_extension = file_extension.lstrip('.').lower() or "unknown"
                logger.info(f"Detected file extension: {file_extension}")
                
                loader = LoaderFactory.get_loader(file_extension, cloud_file.metadata or {})
                logger.info(f"Using loader: {loader.loader_name}")

                # Load and process documents
                for document in loader.load(file=file_obj):
                    logger.info(f"Loaded document with ID: {document.id}")
                    yield from source.chunk_data(document=document)

            except Exception as e:
                logger.error(f"Error while processing document: {e}", exc_info=True)
                raise



    def embed_and_ingest(self, chunks: list[RagDocument]):
        logger.info(f"Starting embedding for {len(chunks)} documents.")
        
        # Ensure embed object exists
        if not hasattr(self, 'embed') or not callable(getattr(self.embed, 'embed', None)):
            raise AttributeError(
                "'Pipeline' object has no attribute 'embed' or 'embed' is not callable."
            )

        # Run the asynchronous embed function and wait for the result
        vector_embeddings, embeddings_info = asyncio.run(self.embed.embed(documents=chunks))
        logger.info(f"Embeddings generated. Embeddings info: {vector_embeddings}")
        
        # Prepare vectors to store
        vectors_to_store = [
            RagVector(
                id=chunk.id,
                vector=embedding,
                metadata=chunk.metadata
            )
            for chunk, embedding in zip(chunks, vector_embeddings)
        ]
        logger.info("Prepared %d vectors for storage.", len(vectors_to_store))
        
        # Store the vectors in the sink
        vectors_written = self.sink.store(vectors_to_store=vectors_to_store)
        logger.info("Stored %d vectors in the vector database.", vectors_written)
        
        return vectors_written