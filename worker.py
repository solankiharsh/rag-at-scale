import asyncio

import tiktoken
from dotenv import load_dotenv
from hatchet_sdk import Context

from hatchet_instance import hatchet

# from hatchet_sdk import Hatchet

# # # Load environment variables (if any)
load_dotenv()

# # Initialize Hatchet in debug mode
# hatchet = Hatchet(debug=True)

# @hatchet.workflow(name="rag-ingest-pipeline", on_events=["ingest:start"])
# class RagIngestPipeline:
#     @hatchet.step()
#     async def parse(self, context):
#         # Simulate parsing logic with hardcoded document info and extractions.
#         document_info = {"id": "doc-001", "status": "PARSING", "total_tokens": 100}
#         extractions = ["chunk1", "chunk2"]
#         print("Parse step complete:", document_info)
#         return {"document_info": document_info, "extractions": extractions}

#     @hatchet.step(parents=["parse"])
#     async def embed(self, context):
#         # Retrieve the output from the 'parse' step.
#         parse_output = context.step_output("parse")
#         document_info = parse_output.get("document_info", {})
#         # Simulate generation of embeddings.
#         embeddings = ["embedding1", "embedding2"]
#         print("Embed step complete for document:", document_info.get("id"))
#         return {"document_info": document_info, "embeddings": embeddings}

#     @hatchet.step(parents=["embed"])
#     async def store(self, context):
#         # Retrieve the output from the 'embed' step.
#         embed_output = context.step_output("embed")
#         document_info = embed_output.get("document_info", {})
#         print("Store step complete for document:", document_info.get("id"))
#         # Simulate storing by updating the document status.
#         document_info["status"] = "STORED"
#         return {"document_info": document_info}

#     @hatchet.step(parents=["store"])
#     async def finalize(self, context):
#         # Retrieve the output from the 'store' step.
#         store_output = context.step_output("store")
#         document_info = store_output.get("document_info", {})
#         # Finalize ingestion by marking it as successful.
#         document_info["status"] = "SUCCESS"
#         print("Finalize step complete for document:", document_info.get("id"))
#         return {"document_info": document_info}

# # Create a worker and register the workflow
# worker = hatchet.worker('rag-worker')
# worker.register_workflow(RagIngestPipeline())

# if __name__ == '__main__':
#     # For Windows compatibility: call freeze_support() before starting worker.
#     from multiprocessing import freeze_support
#     freeze_support()
#     print("Starting RAG ingestion worker...")
#     worker.start()



# Define IngestionStatus constants
class IngestionStatus:
    PARSING = "PARSING"
    AUGMENTING = "AUGMENTING"
    EMBEDDING = "EMBEDDING"
    STORING = "STORING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    ENRICHING = "ENRICHING"

# Dummy token counter function using tiktoken
def count_tokens_for_text(text: str, model: str = "gpt-4o") -> int:
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text, disallowed_special=()))


@hatchet.workflow(name="rag-ingest-pipeline-2", on_events=["ingest:start"])
class RagIngestPipeline:
    @hatchet.step()
    async def parse(self, context: Context) -> dict:
        print("Starting parse step")
        # Use a fallback if 'request' is not provided.
        input_data = context.workflow_input().get("request", {
            "document_id": "doc-001",
            "user": {"id": "user-001"},
            "file_data": {"filename": "dummy.txt"},
            "metadata": {},
            "version": "v1",
            "size_in_bytes": 1234,
            "ingestion_config": {}
        })
        # Simulate parsing: create document info and extractions.
        document_info = {
            "id": input_data.get("document_id"),
            "owner_id": input_data.get("user", {}).get("id"),
            "title": input_data.get("file_data", {}).get("filename"),
            "summary": "Dummy summary",
            "ingestion_status": IngestionStatus.PARSING,
            "total_tokens": 0
        }
        # Simulate asynchronous parsing by waiting and creating dummy extractions.
        await asyncio.sleep(0.1)
        extractions = [
            {"data": f"Dummy text chunk {i}"} for i in range(2)
        ]
        # Sum tokens from all extractions.
        total_tokens = sum(count_tokens_for_text(chunk["data"]) for chunk in extractions)
        document_info["total_tokens"] = total_tokens
        print("Parse step complete:", document_info)
        return {"document_info": document_info, "extractions": extractions}

    @hatchet.step(parents=["parse"])
    async def embed(self, context: Context) -> dict:
        parse_output = context.step_output("parse")
        document_info = parse_output.get("document_info", {})
        extractions = parse_output.get("extractions", [])
        await asyncio.sleep(0.1)
        embeddings = [f"embedding-{i}" for i in range(len(extractions))]
        print("Embed step complete for document:", document_info.get("id"))
        return {"document_info": document_info, "embeddings": embeddings}

    @hatchet.step(parents=["embed"])
    async def store(self, context: Context) -> dict:
        embed_output = context.step_output("embed")
        document_info = embed_output.get("document_info", {})
        # Simulate storing by updating status.
        document_info["ingestion_status"] = IngestionStatus.STORING
        await asyncio.sleep(0.1)
        print("Store step complete for document:", document_info.get("id"))
        return {"document_info": document_info}

    @hatchet.step(parents=["store"])
    async def finalize(self, context: Context) -> dict:
        store_output = context.step_output("store")
        document_info = store_output.get("document_info", {})
        # Finalize ingestion by marking it as SUCCESS.
        document_info["ingestion_status"] = IngestionStatus.SUCCESS
        await asyncio.sleep(0.1)
        print("Finalize step complete for document:", document_info.get("id"))
        return {"document_info": document_info}

# --- Worker Setup ---
worker = hatchet.worker("rag-worker")
worker.register_workflow(RagIngestPipeline())

if __name__ == "__main__":
    from multiprocessing import freeze_support
    freeze_support()  # For Windows multiprocessing support.
    print("Starting RAG ingestion worker...")
    worker.start()
