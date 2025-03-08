# src/config.py
import os

from dotenv import load_dotenv

load_dotenv()

class Config:
    REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-mpnet-base-v2") # Example
    VECTOR_DB_API_KEY = os.getenv("VECTOR_DB_API_KEY")
    VECTOR_DB_ENVIRONMENT = os.getenv("VECTOR_DB_ENVIRONMENT")
    VECTOR_DB_INDEX_NAME = os.getenv("VECTOR_DB_INDEX_NAME", "rag-pipeline-index")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY") # Added default value
    openai_embeddings_endpoint: str = os.getenv("OPENAI_EMBEDDINGS_ENDPOINT", "https://api.openai.com/v1/embeddings") # Added default value
    openai_embeddings_timeout: int = int(os.getenv("OPENAI_EMBEDDINGS_TIMEOUT", "30")) # Added default and type conversion
    openai_embeddings_batch_size: int = int(os.getenv("OPENAI_EMBEDDINGS_BATCH_SIZE", "10")) # Added default and type conversion
    # retry_count: int = int(os.getenv("RETRY_COUNT", "3")) # Added default and type conversion
    # batch_mode: str = os.getenv("BATCH_MODE", "static") # Added default value
    # dynamic_batch_window: int = int(os.getenv("DYNAMIC_BATCH_WINDOW", "5")) # Added default and type conversion
    # ham_embeddings_batch_size: int = int(os.getenv("HAM_EMBEDDINGS_BATCH_SIZE", "10")) # Added default and type conversion
    # ham_embeddings_endpoint: str = os.getenv("HAM_EMBEDDINGS_ENDPOINT", "YOUR_HAM_EMBEDDINGS_ENDPOINT") # Added default value
    # ham_embeddings_timeout: int = int(os.getenv("HAM_EMBEDDINGS_TIMEOUT", "30")) # Added default and type conversion
    # gateway_api_key: str = os.getenv("GATEWAY_API_KEY", "YOUR_GATEWAY_API_KEY") # Added default value
    batch_mode: str = "static"
    ham_embeddings_batch_size: int = 100
    ham_embeddings_endpoint: str = "https://your-ham-endpoint"
    gateway_api_key: str = "your_gateway_api_key"
    retry_count: int = 3
    ham_embeddings_timeout: int = 30
    dynamic_batch_window: int = 5
    latency_threshold_ms: float = 1000.0
    max_batch_size: int = 500
    min_batch_size: int = 50
    thinktank: str = os.getenv("THINKTANK_URL", "YOUR_THINKTANK_URL") # Added default value
    default_embedding_model: str = os.getenv("DEFAULT_EMBEDDING_MODEL", "text-embedding-ada-002") # Added default value
    # max_batch_size: int = int(os.getenv("MAX_BATCH_SIZE", "50")) # Added default and type conversion
    # min_batch_size: int = int(os.getenv("MIN_BATCH_SIZE", "1")) # Added default and type conversion
    # latency_threshold_ms: int = int(os.getenv("LATENCY_THRESHOLD_MS", "100")) # Added default and type conversion
    oauth_url: str = os.getenv("OAUTH_URL", "YOUR_OAUTH_URL") # OAuth URL
    oauth_client_credentials: str = os.getenv("OAUTH_CLIENT_CREDENTIALS", "YOUR_OAUTH_CLIENT_CREDENTIALS") # OAuth client credentials (Basic Auth format)
    oauth_nuid_username: str = os.getenv("OAUTH_NUID_USERNAME", "YOUR_OAUTH_NUID_USERNAME") # OAuth NUID username
    oauth_nuid_password: str = os.getenv("OAUTH_NUID_PASSWORD", "YOUR_OAUTH_NUID_PASSWORD") # OAuth NUID password
    metrics_enabled: bool = os.getenv("METRICS_ENABLED", "True").lower() == 'true' # Default to True, convert string to boolean
    metrics_dsn: str = os.getenv("METRICS_DSN", "influxdb://localhost:8086/metrics") # Metrics DSN
    blossom_id: str = os.getenv("BLOSSOM_ID", "YOUR_BLOSSOM_ID") # Blossom ID
    markdown_headers_to_split_on: list = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]

config = Config()