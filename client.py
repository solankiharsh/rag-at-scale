# client.py
from abc import ABC
from enum import Enum

import requests

from src.schemas.pipeline_config_schema import PipelineConfigSchema


class TriggerSyncTypeEnum(str, Enum):  # Using Enum from Python stdlib
    full = "full"
    delta = "delta"


class RagClient(ABC):
    def __init__(
        self, api_key: str, endpoint: str = "http://localhost:8000"
    ) -> None:  # Default to localhost for example
        self.api_key = api_key
        self.endpoint = endpoint

    def create_pipeline(self, pipeline_config: PipelineConfigSchema):
        url = f"{self.endpoint}/pipelines/"

        headers = {"Content-Type": "application/json"}

        try:
            response = requests.post(url, headers=headers, json=pipeline_config.dict())
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            return response.json()  # Returns the created pipeline config, including ID
        except requests.exceptions.RequestException as e:
            print(f"Pipeline creation failed. Exception - {e}")
            if response is not None:
                print(f"Response Status Code: {response.status_code}")
                print(f"Response Content: {response.text}")
            return None

    def get_pipeline(self, pipeline_id: str):
        url = f"{self.endpoint}/pipelines/{pipeline_id}"

        headers = {"accept": "application/json"}
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
        url = f"{self.endpoint}/pipelines/{pipeline_id}/run?extract_type={sync_type.value}"

        headers = {"Content-Type": "application/json"}
        try:
            response = requests.post(
                url, headers=headers
            )  # No JSON payload needed for trigger in this version
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Pipeline trigger failed. Exception - {e}")
            if response is not None:
                print(f"Response Status Code: {response.status_code}")
                print(f"Response Content: {response.text}")
            return None
