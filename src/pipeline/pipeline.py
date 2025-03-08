# src/pipeline/pipeline.py

import asyncio
from asyncio.log import logger

from src.embeddings.embed_model import EmbedModel
from src.schemas.document_schema import DocumentSchema
from src.schemas.pipeline_config_schema import PipelineConfigSchema
from src.schemas.vector_schema import VectorSchema
from src.sinks.vector_db_sink import VectorDBSink
from src.Sources.source_connector import SourceConnector


class Pipeline:
    def __init__(self, pipeline_config: PipelineConfigSchema):
        self.id = pipeline_config.id
        self.name = pipeline_config.name
        self.sources = [
            SourceConnector.create_source(source_config)
            for source_config in pipeline_config.sources
        ]
        self.embed = EmbedModel.create_embed_model(pipeline_config.embed_model)
        self.sink = VectorDBSink.create_sink(pipeline_config.sink)
        self.config = pipeline_config

    @staticmethod
    def create_pipeline(pipeline_config_dict: dict):
        config = PipelineConfigSchema(**pipeline_config_dict)
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
        for local_file in source.download_files(cloudFile=cloud_file):
            for document in source.load_data(file=local_file, cloud_file=cloud_file):
                yield from source.chunk_data(document=document)

    def embed_and_ingest(self, chunks: list[DocumentSchema]):
        logger.info("Starting embedding for %d documents.", len(chunks))
        # Run the asynchronous embed function and wait for the result
        vector_embeddings, embeddings_info = asyncio.run(self.embed.embed(documents=chunks))
        logger.info("Embeddings generated. Embeddings info: %s", embeddings_info)
        
        # Prepare vectors to store
        vectors_to_store = [
            VectorSchema(
                id=chunks[i].id,
                vector=vector_embeddings[i],
                metadata=chunks[i].metadata
            )
            for i in range(len(vector_embeddings))
        ]
        logger.info("Prepared %d vectors for storage.", len(vectors_to_store))
        
        # Store the vectors in the sink
        vectors_written = self.sink.store(
            vectors_to_store=vectors_to_store,
            pipeline_id=self.id
        )
        logger.info("Stored %d vectors in the vector database.", vectors_written)
        return vectors_written