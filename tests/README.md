# Testing for RAG-at-Scale

This directory contains tests for the RAG-at-Scale project. The tests are organized into unit tests and integration tests.

## Test Structure

- `tests/unit/`: Contains unit tests for individual components
- `tests/integration/`: Contains integration tests for testing multiple components together
- `tests/mocks/`: Contains mock implementations of classes for testing purposes

## Running Tests

To run all tests:

```bash
python -m pytest
```

To run unit tests only:

```bash
python -m pytest tests/unit/
```

To run integration tests only:

```bash
python -m pytest tests/integration/
```

To run a specific test file:

```bash
python -m pytest tests/unit/test_character_chunker.py
```

To run a specific test:

```bash
python -m pytest tests/unit/test_character_chunker.py::test_character_chunker_initialization
```

## Integration Tests

The integration tests demonstrate how different components work together:

- `test_chunker_with_sink.py`: Tests the integration of a chunker with a sink connector
- `test_loader_chunker_sink.py`: Tests the integration of a loader, chunker, and sink connector
- `test_loader_with_embed.py`: Tests the integration of a loader with an embedding model

These tests ensure that the components can work together seamlessly in a pipeline.

## Mock Implementations

Due to dependencies on external modules like `platform_commons`, we've created mock implementations of several classes in the `tests/mocks/` directory. These mocks allow us to test the functionality of our components without requiring the actual dependencies.

The following components have mock implementations:

- `RagDocument`: A document in the RAG system
- `CharacterChunker`: A chunker that splits documents based on character count
- `ElasticsearchSink`: A sink connector for Elasticsearch
- `SinkConnector`: Base class for all sink connectors

## Test Coverage

The tests cover the following components:

- `CharacterChunker`: Tests for initialization, chunking functionality, and configuration
- `RecursiveChunker`: Tests for initialization, recursive chunking functionality, and configuration
- `RagDocument`: Tests for initialization, conversion to/from JSON, and handling empty documents
- `ElasticsearchSink`: Tests for initialization, storing vectors, retrieving documents, and searching
- `PDFLoader`: Tests for initialization, loading PDF files, and handling metadata
- `CSVLoader`: Tests for initialization, loading CSV files, and handling metadata
- `S3SourceConnector`: Tests for initialization, listing files, filtering by prefix, and downloading files
- `OpenAIEmbedModel`: Tests for initialization, embedding documents, and handling API responses

## Adding New Tests

When adding new tests:

1. Create a new test file in the appropriate directory (`unit/` or `integration/`)
2. If necessary, create mock implementations in the `mocks/` directory
3. Follow the existing test patterns for consistency
4. Ensure all tests pass before committing changes

## Test Fixtures

Common test fixtures are defined in `conftest.py`. These fixtures can be used across multiple test files.

## Continuous Integration

Tests are run automatically as part of the CI/CD pipeline. Make sure all tests pass locally before pushing changes.