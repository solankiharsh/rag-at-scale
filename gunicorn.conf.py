import multiprocessing
from math import floor

from platform_commons.platform_360_logging.helpers import add_platform_360_logging_middleware
from uvicorn_worker import UvicornWorker  # type: ignore

from app import app
from config import Config
from utils.platform_commons import metrics
from utils.platform_commons.logger import logger

config = Config()


class CustomUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "http": config.uvicorn_worker_http,
        "loop": config.uvicorn_worker_loop,
        "lifespan": config.uvicorn_worker_lifespan,
        "timeout_keep_alive": config.uvicorn_worker_timeout_keep_alive,
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config_kwargs = self.CONFIG_KWARGS


# Binding address and port
bind = f"{config.server_host}:{config.server_port}"

# Worker class for handling requests (using Uvicorn)
worker_class = CustomUvicornWorker

# Worker timeout (in seconds)
timeout = config.uvicorn_worker_timeout

preload_app = config.uvicorn_worker_preload_app
graceful_timeout = config.uvicorn_worker_graceful_timeout
loglevel = config.uvicorn_worker_log_level
max_requests = config.uvicorn_worker_max_requests
max_requests_jitter = config.uvicorn_worker_max_requests_jitter

# Enable worker processes if 'workers_enabled' is True in settings
if config.uvicorn_workers_enabled:
    num_workers = floor(config.uvicorn_workers_multiplier * multiprocessing.cpu_count())
    logger.info(f"Starting Gunicorn server with {num_workers} Uvicorn workers")
    workers = num_workers
else:
    workers = 1
    logger.info(f"Gunicorn disabled, starting {workers} Uvicorn worker")


# Gunicorn hook for initializing custom implementations after workers are worked
def post_fork(server, worker):
    try:
        rag_service_app = app
        logger.info(f"Worker {worker.pid} started")

        logger.debug(f"adding platform 360 logging middleware to worker: {worker.pid}")
        add_platform_360_logging_middleware(rag_service_app, logger, metrics)
    except Exception as e:
        logger.error(f"Error in gunicorn post_fork: {e}")
        raise e
