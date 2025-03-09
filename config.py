# src/config.py
import os

from dotenv import load_dotenv

load_dotenv()


class Config:
    REDIS_BROKER_URL = os.getenv("REDIS_BROKER_URL", "redis://localhost:6379/0")
    EMBEDDING_MODEL_NAME = os.getenv("EMBEDDING_MODEL_NAME", "all-mpnet-base-v2")  # Example
    VECTOR_DB_API_KEY = os.getenv("VECTOR_DB_API_KEY")
    VECTOR_DB_ENVIRONMENT = os.getenv("VECTOR_DB_ENVIRONMENT")
    VECTOR_DB_INDEX_NAME = os.getenv("VECTOR_DB_INDEX_NAME", "rag-pipeline-index")
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "YOUR_OPENAI_API_KEY")  # Added default value
    openai_embeddings_endpoint: str = os.getenv(
        "OPENAI_EMBEDDINGS_ENDPOINT", "https://api.openai.com/v1/embeddings"
    )  # Added default value
    openai_embeddings_timeout: int = int(
        os.getenv("OPENAI_EMBEDDINGS_TIMEOUT", "30")
    )  # Added default and type conversion
    openai_embeddings_batch_size: int = int(
        os.getenv("OPENAI_EMBEDDINGS_BATCH_SIZE", "10")
    )  # Added default and type conversion
    batch_mode: str = "static"
    ham_embeddings_batch_size: int = 100
    ham_embeddings_endpoint: str = (
        "https://stgapi-internal.target.com/hosted_ai_models/v1/text/embed?model=jina-v2-base"
    )
    gateway_api_key: str = "2f7fe9468715a0a625480f611ae3a5479e73e4c4"
    retry_count: int = 3
    ham_embeddings_timeout: int = 30
    dynamic_batch_window: int = 5
    latency_threshold_ms: float = 1000.0
    max_batch_size: int = 500
    min_batch_size: int = 50
    thinktank: str = os.getenv("THINKTANK_URL", "YOUR_THINKTANK_URL")  # Added default value
    default_embedding_model: str = os.getenv(
        "DEFAULT_EMBEDDING_MODEL", "text-embedding-ada-002"
    )  # Added default value
    oauth_url: str = os.getenv("OAUTH_URL", "YOUR_OAUTH_URL")  # OAuth URL
    oauth_client_credentials: str = os.getenv(
        "OAUTH_CLIENT_CREDENTIALS", "YOUR_OAUTH_CLIENT_CREDENTIALS"
    )  # OAuth client credentials (Basic Auth format)
    oauth_nuid_username: str = os.getenv(
        "OAUTH_NUID_USERNAME", "YOUR_OAUTH_NUID_USERNAME"
    )  # OAuth NUID username
    oauth_nuid_password: str = os.getenv(
        "OAUTH_NUID_PASSWORD", "YOUR_OAUTH_NUID_PASSWORD"
    )  # OAuth NUID password
    metrics_enabled: bool = (
        os.getenv("METRICS_ENABLED", "True").lower() == "true"
    )  # Default to True, convert string to boolean
    metrics_dsn: str = os.getenv("METRICS_DSN", "influxdb://localhost:8086/metrics")  # Metrics DSN
    blossom_id: str = os.getenv("BLOSSOM_ID", "YOUR_BLOSSOM_ID")  # Blossom ID
    markdown_headers_to_split_on: list = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    local_tenant_id: str = os.getenv("LOCAL_TENANT_ID", "10000000-0000-0000-0000-000000000000")
    secret_key: str = os.getenv("SECRET_KEY", "12345678901234567890123456789012")
    server_host: str = os.getenv("SERVER_HOST", "0.0.0.0")
    blossom_id: str = os.getenv("BLOSSOM_ID", "CI15837495")
    server_port: int = int(os.getenv("SERVER_PORT", "8000"))
    fqdn: str = os.getenv("FQDN", "http://localhost:8000")
    priority_ingest: bool = os.getenv("PRIORITY_INGEST", "False").lower() == "true"
    db_entitlement_protection: bool = (
        os.getenv("DB_ENTITLEMENT_PROTECTION", "False").lower() == "true"
    )
    rag_common_db: str = os.getenv("RAG_COMMON_DB", "ragcommondb")
    logging_level: str = os.getenv("LOGGING_LEVEL", "INFO")
    environment: str = os.getenv("ENVIRONMENT", "local")
    cluster_type: str = os.getenv("CLUSTER_TYPE", "default")
    reload: bool = os.getenv("RELOAD", "False").lower() == "true"
    toss_host: str = os.getenv("TOSS_HOST", "https://ttc.toss.target.com")
    toss_access_key: str = os.getenv("TOSS_ACCESS_KEY", "TEST_ACCESS")
    toss_secret_key: str = os.getenv("TOSS_SECRET_KEY", "TEST_SECRET")
    toss_async_timeout: int = int(os.getenv("TOSS_ASYNC_TIMEOUT", "60"))
    admin_group: str = os.getenv(
        "ADMIN_GROUP",
        "cn=app-oauth2-cha-admin-non-prod,ou=application,ou=groupings,dc=corp,dc=target,dc=com",
    )
    protected_indexes: str = os.getenv(
        "PROTECTED_INDEXES",
        '[["protected_index","cn=has-access,ou=application,ou=groupings,dc=corp,dc=target,dc=com"]]',
    )
    default_chunking_strategy: str = os.getenv("DEFAULT_CHUNKING_STRATEGY", "semantic")
    supported_chunking_strategies: str = os.getenv(
        "SUPPORTED_CHUNKING_STRATEGIES", "semantic,markdown,recursive"
    )
    supported_embedding_models: str = os.getenv(
        "SUPPORTED_EMBEDDING_MODELS",
        "jina-v2-base,text-embedding-ada-002,text-embedding-3-large,text-embedding-3-small",
    )
    upload_formats_supported: str = os.getenv(
        "UPLOAD_FORMATS_SUPPORTED", "txt,pdf,docx,pdf2,pptx,adoc,md"
    )
    upload_formats_skipped: str = os.getenv("UPLOAD_FORMATS_SKIPPED", "metadata")
    vision_token_limit: int = int(os.getenv("VISION_TOKEN_LIMIT", "2048"))
    max_rectangle_over_image_intersection: float = float(
        os.getenv("MAX_RECTANGLE_OVER_IMAGE_INTERSECTION", "0.8")
    )
    max_rectangle_over_table_intersection: float = float(
        os.getenv("MAX_RECTANGLE_OVER_TABLE_INTERSECTION", "0.4")
    )
    max_table_over_rectangle_intersection: float = float(
        os.getenv("MAX_TABLE_OVER_RECTANGLE_INTERSECTION", "0.5")
    )
    max_table_over_image_intersection: float = float(
        os.getenv("MAX_TABLE_OVER_IMAGE_INTERSECTION", "0.5")
    )
    max_text_over_rectangle_intersection: float = float(
        os.getenv("MAX_TEXT_OVER_RECTANGLE_INTERSECTION", "0.8")
    )
    max_text_over_image_intersection: float = float(
        os.getenv("MAX_TEXT_OVER_IMAGE_INTERSECTION", "0.8")
    )
    max_text_over_table_intersection: float = float(
        os.getenv("MAX_TEXT_OVER_TABLE_INTERSECTION", "0.2")
    )
    max_image_over_rectangle_intersection: float = float(
        os.getenv("MAX_IMAGE_OVER_RECTANGLE_INTERSECTION", "0.8")
    )
    max_image_over_table_intersection: float = float(
        os.getenv("MAX_IMAGE_OVER_TABLE_INTERSECTION", "0.5")
    )
    metrics_scheduler_interval: int = int(os.getenv("METRICS_SCHEDULER_INTERVAL", "1440"))
    nltk_data: str = os.getenv("NLTK_DATA", "rag-service/utils/query_expansion/nltk_data")
    test_es_instance_1: str = os.getenv("TEST_ES_INSTANCE_1", "http://elasticsearch:9200")
    test_es_instance_2: str = os.getenv("TEST_ES_INSTANCE_2", "http://elasticsearch_store_tm:9201")
    test_es_instance_3: str = os.getenv("TEST_ES_INSTANCE_3", "http://elasticsearch_tes:9202")
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_db_name: str = os.getenv("POSTGRES_DB_NAME", "ragaas")
    postgres_user: str = os.getenv("POSTGRES_USER", "postgres")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    postgres_db_schema: str = os.getenv("POSTGRES_DB_SCHEMA", "ragaas")
    postgres_pool_size: int = int(os.getenv("POSTGRES_POOL_SIZE", "5"))
    postgres_pool_recycle: int = int(os.getenv("POSTGRES_POOL_RECYCLE", "3600"))
    postgres_max_overflow: int = int(os.getenv("POSTGRES_MAX_OVERFLOW", "0"))

    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    max_file_size: float = float(os.getenv("MAX_FILE_SIZE", "10"))
    max_parsed_character_length: int = int(os.getenv("MAX_PARSED_CHARACTER_LENGTH", "1000000"))

    workflow_retry: int = int(os.getenv("WORKFLOW_RETRY", "3"))
    workflow_jwt_algorithm: str = os.getenv("WORKFLOW_JWT_ALGORITHM", "HS256")
    workflow_scheduler_interval: int = int(os.getenv("WORKFLOW_SCHEDULER_INTERVAL", "60"))
    workflow_semaphore_concurrency: int = int(os.getenv("WORKFLOW_SEMAPHORE_CONCURRENCY", "5"))
    workflow_record_lock_limit: int = int(os.getenv("WORKFLOW_RECORD_LOCK_LIMIT", "5"))

    milvus_ingest_batch_size: int = int(os.getenv("MILVUS_INGEST_BATCH_SIZE", "100"))
    profiler_enabled: bool = os.getenv("PROFILER_ENABLED", "False").lower() == "true"

    # Redis configuration
    redis_cache_host: str = os.getenv("REDIS_CACHE_HOST", "localhost")
    redis_cache_port: int = int(os.getenv("REDIS_CACHE_PORT", "26379"))
    redis_cache_db: int = int(os.getenv("REDIS_CACHE_DB", "0"))
    redis_cache_username: str = os.getenv("REDIS_CACHE_USERNAME", "default_username")
    redis_cache_password: str = os.getenv("REDIS_CACHE_PASSWORD", "default_password")
    redis_cache_workflow_retries: bool = (
        os.getenv("REDIS_CACHE_WORKFLOW_RETRIES", "False").lower() == "true"
    )
    redis_socket_timeout: int = int(os.getenv("REDIS_SOCKET_TIMEOUT", "1"))
    redis_retries: int = int(os.getenv("REDIS_RETRIES", "3"))
    redis_cache_max_ttl: int = int(os.getenv("REDIS_CACHE_MAX_TTL", "172800"))

    # Redis eviction and memory configuration
    redis_eviction_policy: str = os.getenv("REDIS_EVICTION_POLICY", "volatile-lru")
    redis_memory_limit: int = int(
        os.getenv("REDIS_MEMORY_LIMIT", str(512 * 1024 * 1024))
    )  # Need to stringify for getenv then convert to int
    use_eviction_policy: bool = os.getenv("USE_EVICTION_POLICY", "False").lower() == "true"
    use_memory_limit: bool = os.getenv("USE_MEMORY_LIMIT", "False").lower() == "true"

    # Gunicorn-Uvicorn workers config
    uvicorn_workers_enabled: bool = os.getenv("UVICORN_WORKERS_ENABLED", "False").lower() == "true"
    uvicorn_workers_multiplier: float = float(os.getenv("UVICORN_WORKERS_MULTIPLIER", "1"))
    uvicorn_worker_timeout: int = int(os.getenv("UVICORN_WORKER_TIMEOUT", "30"))
    # Core uvicorn workers configs
    uvicorn_worker_loop: str = os.getenv("UVICORN_WORKER_LOOP", "asyncio")
    uvicorn_worker_lifespan: str = os.getenv("UVICORN_WORKER_LIFESPAN", "on")
    uvicorn_worker_http: str = os.getenv("UVICORN_WORKER_HTTP", "httptools")
    uvicorn_worker_timeout_keep_alive: int = int(
        os.getenv("UVICORN_WORKER_TIMEOUT_KEEP_ALIVE", "5")
    )
    # gunicorn additional configs
    uvicorn_worker_preload_app: bool = (
        os.getenv("UVICORN_WORKER_PRELOAD_APP", "True").lower() == "true"
    )  # Note default changed to True to match original Settings
    uvicorn_worker_graceful_timeout: int = int(os.getenv("UVICORN_WORKER_GRACEFUL_TIMEOUT", "60"))
    uvicorn_worker_log_level: str = os.getenv("UVICORN_WORKER_LOG_LEVEL", "info")
    uvicorn_worker_max_requests: int = int(os.getenv("UVICORN_WORKER_MAX_REQUESTS", "0"))
    uvicorn_worker_max_requests_jitter: int = int(
        os.getenv("UVICORN_WORKER_MAX_REQUESTS_JITTER", "0")
    )

    # Embeddings configurations
    # Embedding models with configurable dimensions from .env
    text_embedding_3_small_dimensions: list[int] = [
        int(x)
        for x in os.getenv("TEXT_EMBEDDING_3_SMALL_DIMENSIONS", "256,512,1024,1536").split(",")
    ]
    text_embedding_3_large_dimensions: list[int] = [
        int(x) for x in os.getenv("TEXT_EMBEDDING_3_LARGE_DIMENSIONS", "256,1024,3072").split(",")
    ]
    text_embedding_ada_002_dimensions: list[int] = [
        int(x) for x in os.getenv("TEXT_EMBEDDING_ADA_002_DIMENSIONS", "1536").split(",")
    ]
    jina_v2_base_dimensions: list[int] = [768]

    # Redis queue configuration # currently using the same values as redis configuration
    # but creating separate variables for future flexibility
    redis_queue_host: str = os.getenv("REDIS_QUEUE_HOST", "localhost")
    redis_queue_port: int = int(os.getenv("REDIS_QUEUE_PORT", "6379"))
    redis_queue_username: str = os.getenv("REDIS_QUEUE_USERNAME", "default")
    redis_queue_password: str = os.getenv("REDIS_QUEUE_PASSWORD", "dummy_password")

    # Reranker configuration
    rerankers_endpoint: str = os.getenv("RERANKERS_ENDPOINT", "http://rerankers:1234")
    rerankers_timeout: int = int(os.getenv("RERANKERS_TIMEOUT", "60"))
    rerankers_retrieval_size: int = int(os.getenv("RERANKERS_RETRIEVAL_SIZE", "96"))
    rerankers_batch_size: int = int(os.getenv("RERANKERS_BATCH_SIZE", "32"))

    # SCA

    # Toss file limit
    toss_max_file_limit: int = int(os.getenv("TOSS_MAX_FILE_LIMIT", "25"))

    quota_endpoint: str = os.getenv(
        "QUOTA_ENDPOINT", "https://ttassimilator.dev.target.com/v1/quota_service"
    )
    quota_check: bool = os.getenv("QUOTA_CHECK", "False").lower() == "true"

    # Usage History
    kafka_ca_location: str = os.getenv(
        "KAFKA_CA_LOCATION", "/usr/local/share/ca-certificates/tgt-ca-bundle.crt"
    )
    kafka_certificate_location: str = os.getenv(
        "KAFKA_CERTIFICATE_LOCATION", "/tap/certificates/cert.pem"
    )
    kafka_key_location: str = os.getenv("KAFKA_KEY_LOCATION", "/tap/certificates/key.pem")
    kafka_usage_history_brokers: str = os.getenv("KAFKA_USAGE_HISTORY_BROKERS", "localhost:9092")
    kafka_usage_history_topic: str = os.getenv(
        "KAFKA_USAGE_HISTORY_TOPIC", "genai-platform-dev-usage-history"
    )
    usage_history_enabled: bool = os.getenv("USAGE_HISTORY_ENABLED", "False").lower() == "true"


config = Config()
