# src/pipeline/pipeline.py

import asyncio
from asyncio.log import logger

from src.embeddings.embed_model import EmbedModel
from src.ModelFactories.SinkConnectorFactory import SinkConnectorFactory
from src.schemas.pipeline_config_schema import PipelineConfigSchema
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

    def process_document(self, source: SourceConnector, cloud_file):
        logger.info(f"Starting document processing for: {cloud_file.id} ({cloud_file.name})")
        
        for local_file in source.download_files(cloud_file=cloud_file):
            logger.info(f"Downloaded file locally: {local_file}")
            
            for document in source.load_data(local_file=local_file, cloud_file=cloud_file):
                yield from source.chunk_data(document=document)



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