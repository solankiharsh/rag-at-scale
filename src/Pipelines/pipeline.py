# src/pipeline/pipeline.py

import asyncio
import os
from asyncio.log import logger
from collections.abc import Generator

from src.Chunkers.Chunker import Chunker
from src.EmbedConnectors.EmbedConnector import EmbedConnector
from src.ModelFactories.ChunkerFactory import ChunkerFactory
from src.ModelFactories.DataConnectorFactory import DataConnectorFactory
from src.ModelFactories.EmbedConnectorFactory import EmbedConnectorFactory
from src.ModelFactories.LoaderFactory import LoaderFactory
from src.ModelFactories.SinkConnectorFactory import SinkConnectorFactory
from src.Shared.CloudFile import CloudFileSchema
from src.Shared.Exceptions import InvalidDataConnectorException, InvalidEmbedConnectorException
from src.Shared.LocalFile import LocalFile
from src.Shared.pipeline_config_schema import PipelineConfigSchema
from src.Shared.RagDocument import RagDocument
from src.Shared.RagVector import RagVector
from src.SinkConnectors.SinkConnector import SinkConnector
from src.Sources.SourceConnector import SourceConnector


class Pipeline:
    """
    A data ingestion and processing pipeline that handles extraction, document processing,
    chunking, embedding, and ingestion into a vector store.
    """

    def __init__(self, pipeline_config: PipelineConfigSchema):
        """
        Initializes the pipeline with the given configuration.
        """
        self.id = pipeline_config.id
        self.name = pipeline_config.name
        self.config = pipeline_config

        logger.info(f"Initializing pipeline: {self.name} with ID: {self.id}")

        self.sources = self._initialize_sources(pipeline_config.sources)
        self.embed_model = self._initialize_embed_model(pipeline_config.embed_model)
        self.sink = self._initialize_sink(pipeline_config.sink)

    def _initialize_sources(self, source_configs: list) -> list:
        """Initializes source connectors from configuration."""
        # return [SourceConnector.create_source(config) for config in source_configs]
        sources = []
        for config in source_configs:
            try:
                logger.info(f"config.type: {config.type}")
                logger.info(f"config.settings: {config.settings}")
                source_connector = DataConnectorFactory.get_data_connector(
                    data_connector_name=config.type, connector_information=config.settings
                )
                sources.append(source_connector)
                logger.info(f"Initialized source connector: {config.type}")
            except InvalidDataConnectorException as e:
                logger.error(f"Failed to initialize source connector: {e}")
                raise

        return sources

    def _initialize_embed_model(self, embed_model_config) -> EmbedConnector:
        """
        Initializes the embedding model using the EmbedConnectorFactory.
        """
        try:
            return EmbedConnectorFactory.get_embed(
                embed_name=embed_model_config.model_name,
                embed_information=embed_model_config.settings,
            )
        except InvalidEmbedConnectorException as e:
            logger.error(f"Failed to initialize embed model: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing embed model: {e}")
            raise

    def _initialize_sink(self, sink_config) -> SinkConnector:
        """Initializes the sink connector."""
        return SinkConnectorFactory.get_sink(sink_config.type, sink_config.settings)

    def _get_file_extension(self, file_path: str) -> str:
        """Extracts and returns the file extension from the given file path."""
        return os.path.splitext(file_path)[1].lstrip(".").lower() or "unknown"

    def _create_local_file(self, local_file, cloud_file) -> LocalFile:
        """Creates a LocalFile object from a local file or file path."""
        if isinstance(local_file, dict):
            return LocalFile.as_file(local_file)

        if isinstance(local_file, str):
            logger.warning(f"Wrapping file path in dictionary: {local_file}")
            return LocalFile.as_file(
                {
                    "file_path": local_file,
                    "metadata": cloud_file.metadata or {},
                    "type": self._get_file_extension(local_file),
                    "id": cloud_file.id,
                }
            )

        logger.error(f"Invalid local_file type: {type(local_file)} with value: {local_file}")
        raise TypeError("local_file must be a dictionary or file path string")

    def _get_chunker(self, metadata: dict) -> Chunker:
        """Retrieves the appropriate chunker based on metadata."""
        chunker_name = metadata.get("chunker_name", "markdownchunker")
        chunker_config = metadata.get("chunker_information", {})
        logger.info(f"Initializing chunker: {chunker_name} with config: {chunker_config}")
        return ChunkerFactory.get_chunker(chunker_name, chunker_config)

    @staticmethod
    def create_pipeline(pipeline_config_dict: dict) -> "Pipeline":
        """Creates a pipeline instance from a configuration dictionary."""
        config = PipelineConfigSchema(**pipeline_config_dict)
        logger.info(f"Pipeline configuration loaded: {config}")
        return Pipeline(pipeline_config=config)

    def as_json(self) -> dict:
        """Returns the pipeline configuration as a dictionary."""
        return self.config.dict()

    def run_extraction(self, extract_type: str, last_extraction=None) -> Generator:
        """
        Runs the extraction process for each source, yielding extracted files.
        """
        for source in self.sources:
            file_iterator = (
                source.list_files_full()
                if extract_type == "full"
                else source.list_files_delta(last_run=last_extraction)
            )
            for file in file_iterator:
                yield source, file

    def process_document(self, source: SourceConnector, cloud_file: CloudFileSchema) -> Generator:
        """
        Processes a document: downloads, loads, chunks, and yields the chunks.
        """
        logger.info(f"Processing document: {cloud_file.id} ({cloud_file.name})")

        for local_file in source.download_files(cloud_file=cloud_file):
            logger.info(f"Downloaded file locally: {local_file}")

            try:
                file_obj = self._create_local_file(local_file, cloud_file)
                file_extension = self._get_file_extension(file_obj.file_path)
                loader = LoaderFactory.get_loader(file_extension, cloud_file.metadata or {})

                logger.info(f"Using loader: {loader.loader_name}")

                for document in loader.load(file=file_obj):
                    chunker = self._get_chunker(cloud_file.metadata or {})

                    for chunk_batch in chunker.chunk([document]):
                        logger.info(
                            f"Generated {len(chunk_batch)} chunks for document {document.id}"
                        )
                        yield chunk_batch

            except Exception as e:
                logger.error(f"Error processing document {cloud_file.id}: {e}", exc_info=True)
                raise

    async def embed_and_ingest(self, chunks: list[RagDocument]) -> int:
        """
        Embeds document chunks and ingests them into the sink.
        """
        logger.info(f"Starting embedding for {len(chunks)} chunks.")

        if not hasattr(self, "embed_model") or not callable(
            getattr(self.embed_model, "embed", None)
        ):
            raise AttributeError("'Pipeline' object has no valid 'embed_model' instance.")

        if asyncio.get_event_loop().is_running():
            # If already in an event loop, use `await`
            vector_embeddings, _ = await self.embed_model.embed(documents=chunks)
        else:
            # If no event loop is running, use `asyncio.run()`
            vector_embeddings, _ = asyncio.run(self.embed_model.embed(documents=chunks))
        
        logger.info("Embeddings generated successfully.")

        vectors_to_store = [
            RagVector(id=chunk.id, vector=embedding, metadata=chunk.metadata)
            for chunk, embedding in zip(chunks, vector_embeddings)
        ]

        logger.info(f"Prepared {len(vectors_to_store)} vectors for storage.")
        vectors_written = self.sink.store(vectors_to_store)
        logger.info(f"Stored {vectors_written} vectors in the vector database.")

        return vectors_written
