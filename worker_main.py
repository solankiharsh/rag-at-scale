# worker_main.py
from hatchet_instance import hatchet
from tasks import PipelineWorkflow


def start():
    worker = hatchet.worker('pipeline-worker')
    worker.register_workflow(PipelineWorkflow())
    worker.start()
