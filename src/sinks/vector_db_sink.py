# src/sinks/vector_db_sink.py
from abc import ABC, abstractmethod

from src.schemas.sink_config_schema import SinkConfigSchema
from src.schemas.vector_schema import VectorSchema


class VectorDBSink(ABC):
    def __init__(self, config: SinkConfigSchema):
        self.type = config.type
        self.settings = config.settings

    @staticmethod
    def create_sink(sink_config: SinkConfigSchema):
        sink_type = sink_config.type.lower()
        print(f"sink_type: {sink_type}")
        if sink_type == "milvus":
            from src.sinks.milvus_sink import MilvusSink
            return MilvusSink(config=sink_config)
        elif sink_type == "elasticsearch":
            from src.sinks.elasticsearch_sink import ElasticsearchSink
            return ElasticsearchSink(config=sink_config)
        else:
            raise ValueError(f"Unsupported sink type: {sink_type}")

    @abstractmethod
    def store(self, vectors_to_store: list[VectorSchema], pipeline_id: str) -> int:
        """Stores vectors in the vector database. Returns count of vectors stored."""
        pass
