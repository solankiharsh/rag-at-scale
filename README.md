<h1 align="center">Rag-at-Scale</h1>

<div align="center">
  
  [Homepage](https://tap.prod.platform.target.com/) | [Documentation](https://pages.git.target.com/GenAI-Platform/documentation/ai_studio/overview/)
  
</div>

Core library with Rag AI components to connect, load, chunk and sink vector embeddings. **[Rag-at-Scale](https://tap.prod.platform.target.com/) is a data platform that helps developers leverage their data to contextualize Large Language Models through Retrieval Augmented Generation (RAG).** This includes
extracting data from existing data sources like document storage and NoSQL, processing the contents into vector embeddings and ingesting the vector embeddings into vector databases for similarity search.

It provides you a comprehensive solution for RAG that can scale with your application and reduce the time spent integrating services like data connectors, embedding models and vector databases.

## Features

- 🏭 **High throughput distributed architecture** to handle lots of data. Allows high degrees of parallelization to optimize embedding generation and ingestion.
- 🧱 **Data connectors** to common data sources, embedding services and vector stores.

## Getting Started

### Local Development

Install the [`rag-at-scale`](https://pypi.org/project/ragai/) package:

```bash
pip install rag_at_scale
```

This repo contains a sample of a distributed architecture solution using Celery and Redis Queues. By design, rag-at-scale framework provides constructs to parallelize workloads in order to process larger data sets.

### Development Setup

To leverage this repo, you will need to install dependencies:

```bash
pip install -r requirements.txt
```

In addition:
- Install the [Redis CLI](https://redis.io/docs/install/install-redis/install-redis-on-linux/) to run it locally.
- You will need an OpenAI API Key for the OpenAI embedding model. To get an API Key visit **[OpenAI](https://platform.openai.com/signup)**. Make sure you have configured billing for the account.
- You will need a local Elasticsearch DB for the Elasticsearch vector database.

## Configure Connectors

In the [`app.py`](./app.py) file, you have the API endpoints for pipeline processing.

## Run It Locally

To get everything ready to run this solution, we first need to get our Redis queues running. To do this, we will use the Redis CLI:

```bash
sudo service redis-server start
```

Once we have the Redis queues running, we can now start our Celery-based workers. We will have each running on its own command line.

**data_extraction worker**

```bash
celery -A tasks worker --concurrency 1 -Q data_extraction
```

**data_processing worker**

```bash
celery -A tasks worker --concurrency 1 -Q data_processing
```

**data_embed_ingest worker**

```bash
celery -A tasks worker --concurrency 1 -Q data_embed_ingest
```

Once everything is running, we can now trigger our pipeline. This will distribute the tasks into the different queues as it processes the data.

```bash
make start
```

### Example API Calls

#### Create a Pipeline

```python
import requests

url = "http://127.0.0.1:8000/pipelines"

payload = {
    "id": "pipeline-003",
    "name": "Example Pipeline",
    "sources": [
        {
            "name": "s3",
            "data_connector": {
                "connector_name": "s3connector",
                "bucket_name": "faq-test",
                "aws_access_key_id": "aws_access_key_id",
                "aws_secret_access_key": "aws_secret_access_key",
                "region": "https://stage.ttce.toss.target.com"
            },
            "settings": {
                "bucket_name": "conduit-sink",
                "aws_access_key_id": "aws_access_key_id",
                "aws_secret_access_key": "aws_secret_access_key",
                "region": "https://stage.ttce.toss.target.com"
            }
        }
    ],
    "embed_model": {
        "model_name": "jina-v2-base",
        "settings": {
            "api_key": "2f7fe9468715a0a625480f611ae3a5479e73e4c4",
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
headers = {"Content-Type": "application/json"}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)
```

#### Run a Pipeline

```python
import requests

url = "http://127.0.0.1:8000/pipelines/pipeline-002/run"

querystring = {"extract_type":"full"}

payload = ""
response = requests.request("POST", url, data=payload, params=querystring)

print(response.text)
```

#### Search Using a Pipeline

```python
import requests

url = "http://127.0.0.1:8000/pipelines/pipeline-002/search"

querystring = {"query":"all bikes must be inspected by a bike builder before setting on the sales floor","top_k":"3"}

payload = ""
response = requests.request("POST", url, data=payload, params=querystring)

print(response.text)
```

#### Get Documents from a Pipeline

```python
import requests

url = "http://localhost:8000/pipelines/pipeline-002/documents"

payload = {
    "query": "search text",
    "num_of_results": 3
}
headers = {"Content-Type": "application/json"}

response = requests.request("GET", url, json=payload, headers=headers)

print(response.text)
```

## Contributing

Contributions to Rag-at-Scale are welcome! Feel free to submit issues or pull requests to help improve the framework.

## License

This project is licensed under the terms specified in the repository.
