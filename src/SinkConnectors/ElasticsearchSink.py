
from typing import Any, Dict, List

from elasticsearch import Elasticsearch
from pydantic import Extra, Field, validator

from src.Shared.Exceptions import (
    ElasticsearchConnectionException,
    ElasticsearchIndexInfoException,
    ElasticsearchInsertionException,
    ElasticsearchQueryException,
)
from src.Shared.RagSearch import RagSearchResult
from src.Shared.RagSinkInfo import RagSinkInfo
from src.SinkConnectors.filter_utils import FilterCondition
from src.SinkConnectors.SinkConnector import SinkConnector

# Import your types for RagSearchResult and RagSinkInfo, FilterCondition, etc.

class ElasticsearchSink(SinkConnector):
    """
    Elasticsearch Sink

    A sink connector specifically designed for Elasticsearch, facilitating the output of
    processed data into an Elasticsearch index.
    """
    sink_name: str = Field("ElasticsearchSink", description="Name of the sink connector")
    required_properties: List[str] = Field(default_factory=lambda: ["hosts", "index"], description="List of required properties")
    optional_properties: List[str] = Field(default_factory=lambda: ["doc_type"], description="List of optional properties")
    
    hosts: List[str] = Field(..., description="List of Elasticsearch hosts.")
    index: str = Field(..., description="Elasticsearch index to store data.")
    doc_type: str = Field("_doc", description="Elasticsearch document type. Defaults to '_doc'.")
    config: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = Extra.allow
        arbitrary_types_allowed = True

    @validator("sink_name", pre=True, always=True)
    def validate_sink_name(cls, value):
        if not value:
            raise ValueError("Sink name is None. Please ensure your configuration includes a valid sink name.")
        return value
    
    def as_json(self) -> Dict[str, Any]:
        return self.dict(by_alias=True, exclude_unset=False)

    def validation(self) -> bool:
        try:
            es = Elasticsearch(self.hosts)
            if not es.ping():
                raise ElasticsearchConnectionException(f"Could not connect to Elasticsearch at {self.hosts}.")
        except Exception as e:
            raise ElasticsearchConnectionException(f"Elasticsearch connection couldn't be initialized. Exception: {e}")
        return True

    def store(self, vectors_to_store: List[Any]) -> int:
        try:
            es = Elasticsearch(self.hosts)
            vectors_stored = 0
            for vector in vectors_to_store:
                doc = {
                    "vector": vector.vector,
                    "metadata": vector.metadata
                }
                response = es.index(index=self.index, id=vector.id, document=doc)
                if response.get("result") in ["created", "updated"]:
                    vectors_stored += 1
            es.indices.refresh(index=self.index)
        except Exception as e:
            raise ElasticsearchInsertionException(f"Failed to store vectors in Elasticsearch. Exception: {e}")
        return vectors_stored

    def search(
        self,
        vector: List[float],
        number_of_results: int,
        filters: List[FilterCondition] = []
    ) -> List[Any]:
        try:
            es = Elasticsearch(self.hosts)
            must_clauses = []
            for condition in filters:
                if condition.operator.value == "=":
                    must_clauses.append({"term": {condition.field: condition.value}})
                elif condition.operator.value in [">", ">=", "<", "<="]:
                    range_operator = {" >": "gt", ">=": "gte", "<": "lt", "<=": "lte"}[condition.operator.value]
                    must_clauses.append({
                        "range": {condition.field: {range_operator: str(condition.value)}}
                    })
                else:
                    must_clauses.append({"match": {condition.field: condition.value}})
            query_body = {
                "size": number_of_results,
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                }
            }
            response = es.search(index=self.index, body=query_body)
            results = []
            for hit in response["hits"]["hits"]:
                results.append(
                    RagSearchResult(
                        id=hit["_id"],
                        metadata=hit["_source"].get("metadata", {}),
                        score=hit["_score"]
                    )
                )
        except Exception as e:
            raise ElasticsearchQueryException(f"Failed to query Elasticsearch. Exception: {e}")
        return results

    def delete_vectors_with_file_id(self, file_id: str) -> bool:
        try:
            es = Elasticsearch(self.hosts)
            query = {
                "query": {
                    "term": {"metadata._file_entry_id": file_id}
                }
            }
            response = es.delete_by_query(index=self.index, body=query)
            return response.get("deleted", 0) > 0
        except Exception as e:
            raise ElasticsearchConnectionException(f"Failed to delete vectors by file id. Exception: {e}")

    def info(self) -> RagSinkInfo:
        try:
            es = Elasticsearch(self.hosts)
            stats = es.indices.stats(index=self.index)
            doc_count = stats["_all"]["primaries"]["docs"]["count"]
            return RagSinkInfo(number_vectors_stored=doc_count)
        except Exception as e:
            raise ElasticsearchIndexInfoException(f"Failed to retrieve index info from Elasticsearch. Exception: {e}")

    

