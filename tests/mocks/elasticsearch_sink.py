"""
Mock ElasticsearchSink for testing purposes.
This file contains a mock implementation of the ElasticsearchSink class.
"""

from typing import Any

from pydantic import Extra, Field

from tests.mocks.sink_connector import FilterCondition, RagSearchResult, RagSinkInfo, SinkConnector


class MockElasticsearch:
    """Mock Elasticsearch client for testing."""
    
    def __init__(self, hosts):
        self.hosts = hosts
        self.indices = MockIndices()
        self.documents = {}  # Store documents in memory
        
    def ping(self):
        """Mock ping method."""
        return True
        
    def index(self, index, id, document):
        """Mock index method."""
        if index not in self.documents:
            self.documents[index] = {}
        self.documents[index][id] = document
        return {"result": "created"}
        
    def search(self, index, body):
        """Mock search method."""
        if index not in self.documents:
            return {"hits": {"hits": []}}
            
        hits = []
        for doc_id, doc in self.documents[index].items():
            hits.append({
                "_id": doc_id,
                "_source": doc,
                "_score": 1.0
            })
            
        # Apply size limit if specified
        size = body.get("size", len(hits))
        hits = hits[:size]
            
        return {"hits": {"hits": hits}}
        
    def delete_by_query(self, index, body):
        """Mock delete_by_query method."""
        if index not in self.documents:
            return {"deleted": 0}
            
        # In a real implementation, we would apply the query
        # For simplicity, we'll just return a success response
        return {"deleted": 1}


class MockIndices:
    """Mock Indices class for Elasticsearch."""
    
    def __init__(self):
        self.indices = {}
        
    def exists(self, index):
        """Check if index exists."""
        return index in self.indices
        
    def create(self, index):
        """Create an index."""
        self.indices[index] = {"docs": {"count": 0}}
        
    def refresh(self, index):
        """Refresh an index."""
        pass
        
    def stats(self, index):
        """Get index stats."""
        if index not in self.indices:
            self.indices[index] = {"docs": {"count": 0}}
            
        return {
            "_all": {
                "primaries": {
                    "docs": {
                        "count": len(self.indices[index].get("docs", {}))
                    }
                }
            }
        }


class ElasticsearchSink(SinkConnector):
    """
    Elasticsearch Sink

    A sink connector specifically designed for Elasticsearch, facilitating the output of
    processed data into an Elasticsearch index.
    """

    sink_name: str = Field("ElasticsearchSink", description="Name of the sink connector")
    required_properties: list[str] = Field(
        default_factory=lambda: ["hosts", "index"], description="List of required properties"
    )
    optional_properties: list[str] = Field(
        default_factory=lambda: ["doc_type"], description="List of optional properties"
    )

    hosts: list[str] = Field(..., description="List of Elasticsearch hosts.")
    index: str = Field(..., description="Elasticsearch index to store data.")
    doc_type: str = Field("_doc", description="Elasticsearch document type. Defaults to '_doc'.")
    config: dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = Extra.allow
        arbitrary_types_allowed = True

    def __init__(self, **data):
        super().__init__(**data)
        self.es_client = MockElasticsearch(self.hosts)

    def ensure_index_exists(self):
        """Ensure the Elasticsearch index exists, create if missing."""
        if not self.es_client.indices.exists(index=self.index):
            self.es_client.indices.create(index=self.index)

    def as_json(self) -> dict[str, Any]:
        return self.dict(by_alias=True, exclude_unset=False)

    def validation(self) -> bool:
        """Validate the sink connector configuration."""
        return self.es_client.ping()

    def store(self, vectors_to_store: list[Any]) -> int:
        """Store vectors in the sink."""
        self.ensure_index_exists()
        vectors_stored = 0
        for vector in vectors_to_store:
            doc = {"vector": vector.vector, "metadata": vector.metadata}
            response = self.es_client.index(index=self.index, id=vector.id, document=doc)
            if response.get("result") in ["created", "updated"]:
                vectors_stored += 1
        self.es_client.indices.refresh(index=self.index)
        return vectors_stored

    def get_documents(self, size: int = 10) -> list[RagSearchResult]:
        """
        Retrieve documents stored in the Elasticsearch index using a match_all query.

        Args:
            size (int): Number of documents to retrieve.

        Returns:
            List[RagSearchResult]: A list of search results.
        """
        query_body = {"size": size, "query": {"match_all": {}}}
        response = self.es_client.search(index=self.index, body=query_body)
        results = []
        for hit in response["hits"]["hits"]:
            result = RagSearchResult(
                id=hit["_id"],
                metadata=hit["_source"].get("metadata", {}),
                score=hit["_score"],
                vector=hit["_source"].get("vector"),
            )
            results.append(result)
        return results

    def search(
        self, vector: list[float], number_of_results: int, filters: list[FilterCondition] = []
    ) -> list[RagSearchResult]:
        """Search for similar vectors in the sink."""
        query_body = {"size": number_of_results, "query": {"match_all": {}}}
        response = self.es_client.search(index=self.index, body=query_body)
        results = []
        for hit in response["hits"]["hits"]:
            result = RagSearchResult(
                id=hit["_id"],
                metadata=hit["_source"].get("metadata", {}),
                score=hit["_score"],
                vector=hit["_source"].get("vector"),
            )
            results.append(result)
        return results

    def delete_vectors_with_file_id(self, file_id: str) -> bool:
        """Delete vectors with a specific file ID."""
        query = {"query": {"term": {"metadata._file_entry_id": file_id}}}
        response = self.es_client.delete_by_query(index=self.index, body=query)
        return response.get("deleted", 0) > 0

    def info(self) -> RagSinkInfo:
        """Get information about the sink."""
        stats = self.es_client.indices.stats(index=self.index)
        doc_count = stats["_all"]["primaries"]["docs"]["count"]
        return RagSinkInfo(number_vectors_stored=doc_count)