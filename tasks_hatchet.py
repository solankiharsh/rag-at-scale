import datetime
import os
import time

from fastapi.encoders import jsonable_encoder
from hatchet_sdk import Context
from tqdm import tqdm

from hatchet_instance import hatchet
from src.Pipelines.IngestPipeline import Pipeline
from src.Shared.CloudFile import CloudFileSchema
from src.Shared.RagDocument import RagDocument
from src.Shared.source_config_schema import SourceConfigSchema
from src.Sources.SourceConnector import SourceConnector


def serialize_data(data):
    if isinstance(data, dict):
        return {k: serialize_data(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [serialize_data(item) for item in data]
    elif isinstance(data, datetime.datetime):
        return data.isoformat()
    else:
        return data


@hatchet.workflow(on_events=["pipeline:run"])
class PipelineWorkflow:
    @hatchet.step()
    def data_extraction(self, context: Context):
        context.log("Starting data_extraction step...")
        input_data = context.workflow_input()
        pipeline_config_dict = input_data["pipeline_config_dict"]
        extract_type = input_data.get("extract_type", "full")
        last_extraction = input_data.get("last_extraction", None)
        context.log(f"pipeline_config_dict: {pipeline_config_dict}")
        context.log(f"extract_type: {extract_type}")
        context.log(f"last_extraction: {last_extraction}")
        context.log("Running data extraction...")

        pipeline = Pipeline.create_pipeline(pipeline_config_dict)
        extraction_results = []
        for source, cloud_file in pipeline.run_extraction(
            extract_type=extract_type, last_extraction=last_extraction
        ):
            context.log(f"source: {source.as_json()}")
            context.log(f"cloud_file: {cloud_file.dict()}")
            extraction_results.append({
                "source_config_dict": source.as_json(),
                "cloud_file_dict": cloud_file.dict()
            })
        result = {
            "extraction_results": extraction_results,
            "pipeline_config_dict": pipeline_config_dict
        }
        context.log(f"result: {result}")
        # Convert the result into a JSON-serializable object
        return jsonable_encoder(result)

    @hatchet.step(parents=["data_extraction"], timeout="300m")
    def data_processing(self, context: Context):
        input_data = context.workflow_input()
        pipeline_config_dict = input_data["pipeline_config_dict"]
        processing_results = []
        pipeline = Pipeline.create_pipeline(pipeline_config_dict)

        extraction_results = context.step_output("data_extraction")["extraction_results"]
        total_files = len(extraction_results)
        context.log(f"Starting data_processing for {total_files} files.")

        # Create a progress bar using tqdm.
        progress_bar = tqdm(total=total_files, desc="Processing files", leave=True)

        for idx, result in enumerate(extraction_results):
            source_config_dict = result["source_config_dict"]
            cloud_file_dict = result["cloud_file_dict"]

            source = SourceConnector.create_source(SourceConfigSchema(**source_config_dict))
            cloud_file = CloudFileSchema(**cloud_file_dict)

            batched_chunks = []
            doc_processing_start = time.perf_counter()
            for chunks in pipeline.process_document(source, cloud_file):
                batched_chunks.extend(chunks)
            chunking_time = time.perf_counter() - doc_processing_start

            processing_results.append({
                "cloud_file_id": cloud_file.id,
                "batched_chunks": [chunk.to_json() for chunk in batched_chunks],
                "chunking_time": chunking_time
            })
            
            progress_bar.update(1)
            context.log(
                f"Processed file {idx + 1}/{total_files}: "
                f"cloud_file_id {cloud_file.id} in {chunking_time:.2f} seconds."
            )

        progress_bar.close()
        context.log("Completed processing all files.")

        return {
            "processing_results": processing_results,
            "pipeline_config_dict": pipeline_config_dict
        }

    @hatchet.step(parents=["data_processing"], timeout="300m")
    async def data_embed_ingest(self, context: Context):
        context.log("Starting data_embed_ingest step...")
        input_data = context.workflow_input()
        pipeline_config_dict = input_data["pipeline_config_dict"]
        context.log(f"Pipeline config: {pipeline_config_dict}")
        processing_results = context.step_output("data_processing")["processing_results"]
        pipeline = Pipeline.create_pipeline(pipeline_config_dict)

        index_name = pipeline_config_dict.get("sink", {}).get("settings", {}).get("index")
        if not index_name:
            error_msg = "Index name missing in pipeline config."
            context.log(error_msg)
            return jsonable_encoder({"error": error_msg})

        embed_results = []
        start_time = time.perf_counter()
        for idx, result in enumerate(processing_results):
            context.log(f"Processing embed for result {idx+1}: {result}")
            batched_chunks_json = result["batched_chunks"]
            # Convert each chunk using RagDocument.as_file() (ensure it returns a dict)
            chunks = [RagDocument.as_file(chunk_dict) for chunk_dict in batched_chunks_json]
            try:
                embed_start = time.perf_counter()
                # Await the asynchronous embed function
                vectors_written = await pipeline.embed_and_ingest(chunks)
                embed_time = time.perf_counter() - embed_start
                context.log(
                    f"Embed success for cloud_file_id {result['cloud_file_id']} "
                    f"with vectors_written {vectors_written} in {embed_time:.2f} seconds"
                )
                # Ensure vectors_written is a native int
                embed_results.append({
                    "cloud_file_id": result["cloud_file_id"],
                    "vectors_written": int(vectors_written),
                    "embed_time": embed_time
                })
            except Exception as e:
                error_detail = str(e)
                context.log(
                    f"Embed failed for cloud_file_id {result['cloud_file_id']}: {error_detail}"
                )
                embed_results.append({
                    "cloud_file_id": result["cloud_file_id"],
                    "error": error_detail
                })
        total_time = time.perf_counter() - start_time
        final_result = {"embedding_results": embed_results, "total_time": total_time}
        context.log(f"data_embed_ingest final result: {final_result}")
        return jsonable_encoder(final_result)

    
def start_worker(worker_id: int) -> None:
    # Create and configure a Hatchet worker instance
    worker = hatchet.worker("rag-worker")
    worker.register_workflow(PipelineWorkflow())
    print(f"Starting RAG ingestion worker {worker_id}...")
    worker.start()

def main() -> None:
    # Use multiprocessing to spawn one worker per CPU core.
    from multiprocessing import Process, freeze_support
    freeze_support()  # For Windows compatibility if needed

    # Get number of cores (10 on your Mac)
    num_cores = int(os.popen("sysctl -n hw.ncpu").read())
    print(f"Detected {num_cores} cores. Starting {num_cores} worker processes.")

    processes = []
    for i in range(num_cores):
        p = Process(target=start_worker, args=(i,))
        p.start()
        processes.append(p)
    # Wait for all workers to finish (they usually run indefinitely)
    for p in processes:
        p.join()

if __name__ == "__main__":
    main()
