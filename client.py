# client.py
from abc import ABC
from enum import Enum

import requests

from src.schemas.embed_config_schema import EmbedConfigSchema
from src.schemas.pipeline_config_schema import PipelineConfigSchema
from src.schemas.sink_config_schema import SinkConfigSchema
from src.schemas.source_config_schema import SourceConfigSchema


class TriggerSyncTypeEnum(str, Enum): # Using Enum from Python stdlib
    full = "full"
    delta = "delta"

class RagClient(ABC):
    def __init__(self, api_key: str, endpoint: str = 'http://localhost:8000') -> None: # Default to localhost for example
        self.api_key = api_key
        self.endpoint = endpoint

    def create_pipeline(self, pipeline_config: PipelineConfigSchema):
        url = f"{self.endpoint}/pipelines/"

        headers = {
            "Content-Type": "application/json"
        }

        try:
            response = requests.post(url, headers=headers, json=pipeline_config.dict())
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json() # Returns the created pipeline config, including ID
        except requests.exceptions.RequestException as e:
            print(f"Pipeline creation failed. Exception - {e}")
            if response is not None:
                print(f"Response Status Code: {response.status_code}")
                print(f"Response Content: {response.text}")
            return None


    def get_pipeline(self, pipeline_id: str):
        url = f"{self.endpoint}/pipelines/{pipeline_id}"

        headers = {
            "accept": "application/json"
        }
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Pipeline fetching failed. Exception - {e}")
            if response is not None:
                print(f"Response Status Code: {response.status_code}")
                print(f"Response Content: {response.text}")
            return None


    def trigger_pipeline(self, pipeline_id: str, sync_type: TriggerSyncTypeEnum):
        url = f"{self.endpoint}/pipelines/{pipeline_id}/run?extract_type={sync_type.value}" # Construct query parameter in URL

        headers = {
            "Content-Type": "application/json"
        }
        try:
            response = requests.post(url, headers=headers) # No JSON payload needed for trigger in this version
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Pipeline trigger failed. Exception - {e}")
            if response is not None:
                print(f"Response Status Code: {response.status_code}")
                print(f"Response Content: {response.text}")
            return None


# --- Example Usage in client.py ---
if __name__ == '__main__':
    client = RagClient(api_key="YOUR_API_KEY_HERE") # Replace with your API Key (if you were using auth)

    # 1. Define Pipeline Configuration using Pydantic Models
    pipeline_config = PipelineConfigSchema(
        id="pipeline-from-client-1",  # Define ID here, API will check for uniqueness
        name="Client Created Pipeline",
        sources=[
            SourceConfigSchema(
                name="s3-source-client",
                type="s3",
                settings={
                    "bucket_name": "your-s3-bucket-name", # Replace with your bucket
                    "prefix": "client-documents/"
                }
            )
        ],
        embed_model=EmbedConfigSchema(
            model_name="sentence-transformers",
            settings={}
        ),
        sink=SinkConfigSchema(
            type="pinecone",
            settings={
                "api_key": "YOUR_PINECONE_API_KEY", # Replace with your Pinecone API Key
                "environment": "us-west1-gcp", # Replace with your Pinecone Environment
                "index_name": "rag-pipeline-index" # Replace with your Pinecone Index Name
            }
        )
    )

    # 2. Create Pipeline via API
    created_pipeline_response = client.create_pipeline(pipeline_config)
    if created_pipeline_response:
        pipeline_id = created_pipeline_response['id'] # Assuming API returns the created pipeline config
        print(f"Pipeline created successfully with ID: {pipeline_id}")

        # 3. Get Pipeline details
        retrieved_pipeline = client.get_pipeline(pipeline_id)
        if retrieved_pipeline:
            print(f"Retrieved Pipeline: {retrieved_pipeline}")

        # 4. Trigger Pipeline Run (Full Sync)
        trigger_response = client.trigger_pipeline(pipeline_id, TriggerSyncTypeEnum.full)
        if trigger_response:
            print(f"Pipeline run triggered: {trigger_response}")
    else:
        print("Pipeline creation failed.")