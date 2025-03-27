import uuid

from locust import HttpUser, between, task


class PipelineUser(HttpUser):
    wait_time = between(1, 3)

    @task
    def create_and_run_pipeline(self):
        pipeline_id = f"test-pipeline-{uuid.uuid4()}"

        pipeline_payload = {
            "id": pipeline_id,
            "name": "Test Pipeline",
            "sources": [
                {
                "name": "s3",
                "data_connector": {
                            "connector_name": "s3connector",
                            "bucket_name": "newindex",
                            "aws_access_key_id": "dummy",
                            "aws_secret_access_key": "dummy",
                            "region": "https://stage.ttce.toss.target.com"
                        },
                "settings": {
                    "bucket_name": "newindex",
                    "aws_access_key_id": "dummy",
                    "aws_secret_access_key": "dummy",
                    "region": "https://stage.ttce.toss.target.com"
                }
                }
            ],
            "embed_model": {
                "model_name": "jina-v2-base",
                "settings": {
                            "api_key": "dummy",
                            "max_retries": 5,
                            "chunk_size": 1000
                    }
            },
            "sink": {
                "type": "elasticsearch",
                "settings": {
                "hosts": ["http://localhost:9200"],
                "index": "my_index",
                "doc_type": "_doc"
                }
            }
            }


        # Attempt to create the pipeline
        with self.client.post(
            "/pipelines/", json=pipeline_payload, catch_response=True
        ) as response:
            if response.status_code == 201:
                # Successfully created, extract the pipeline id
                pipeline_data = response.json()
                pipeline_id = pipeline_data.get("id")
                response.success()
            else:
                # If pipeline already exists or another error occurred, handle it
                response.failure(
                    f"Failed to create pipeline, status: {response.status_code}"
                )
                # Optionally, you could try to GET the existing pipeline
                pipeline_id = pipeline_payload["id"]

        # Now use the pipeline_id for subsequent calls, e.g., to run the pipeline
        if pipeline_id:
            self.client.post(f"/pipelines/{pipeline_id}/run", json={"extract_type": "full"})
        else:
            print("Pipeline ID is None, cannot run pipeline")
