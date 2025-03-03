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

config = Config()