# rag-at-scale

<h1 align="center">Rag AI</h1>

<div align="center">
  
  [Homepage](https://tap.prod.platform.target.com/) | [Documentation](https://pages.git.target.com/GenAI-Platform/documentation/ai_studio/overview/) |
  
</div>

Core library with Rag AI components to connect, load, chunk and sink vector embeddings. **[Rag AI](https://tap.prod.platform.target.com/) is a data platform that helps developers leverage their data to contextualize Large Language Models through Retrieval Augmented Generation (RAG)** This includes
extracting data from existing data sources like document storage and NoSQL, processing the contents into vector embeddings and ingesting the vector embeddings into vector databases for similarity search.

It provides you a comprehensive solution for RAG that can scale with your application and reduce the time spent integrating services like data connectors, embedding models and vector databases.

## Features

- 🏭 **High throughput distrubted architecture** to handle billions of data points. Allows high degrees of parallelization to optimize embedding generation and ingestion.
- 🧱 **Built-in data connectors** to common data sources, embedding services and vector stores.
- 🔄 **Real-time synchronization** of data sources to ensure your data is always up-to-date.
- 🤝 **Cohesive data management** to support hybrid retrieval with metdata. Rag AI automatically augments and tracks metadata to provide rich retrieval experience.

## Getting Started

### Local Development

Install the [`ragai`](https://pypi.org/project/ragai/) package:

```bash
pip install ragai
```

To create your first data pipelines visit our [quickstart]().

## Roadmap

Connectors
- [ ]  Milvus - Sink
- [ ]  Chroma - Sink

Search
- [ ]  Retrieval feedback
- [ ]  Filter support
- [ ]  Unified Rag AI filters
- [ ]  Self-Query Retrieval (w/ Metadata attributes generation)

Extensibility
- [ ]  Langchain / Llama Index Document to Rag Document converter
- [ ]  Custom chunking and loading