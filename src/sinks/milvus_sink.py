# src/sinks/elasticsearch_sink.py
from elasticsearch import Elasticsearch, helpers
from src.schemas.sink_config_schema import SinkConfigSchema
from src.schemas.vector_schema import VectorSchema
from src.sinks.vector_db_sink import VectorDBSink


class MilvusSink(VectorDBSink):
    def __init__(self, config: SinkConfigSchema):
        super().__init__(config)
        # Get index name and hosts from configuration settings
        self.index_name = self.settings.get("index_name", "vectors")
        self.client = Elasticsearch(
            hosts=self.settings.get("hosts", ["http://localhost:9200"])
        )
        self._ensure_index()

    def _ensure_index(self):
        # Check if the index exists; if not, create it.
        if not self.client.indices.exists(index=self.index_name):
            self.client.indices.create(index=self.index_name)
            print(f"Created index: {self.index_name}")

    def store(self, vectors_to_store: list[VectorSchema], pipeline_id: str) -> int:
        # Prepare bulk actions for indexing
        actions = []
        for vector in vectors_to_store:
            # Convert the vector schema to a dictionary and attach pipeline_id
            doc = vector.dict()
            doc["pipeline_id"] = pipeline_id
            action = {
                "_index": self.index_name,
                # Optionally use a unique identifier from the vector if available
                "_id": doc.get("id", None),
                "_source": doc,
            }
            actions.append(action)
        success, _ = helpers.bulk(self.client, actions)
        return success
