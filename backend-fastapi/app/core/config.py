from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SynVerse API"
    debug: bool = True

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    # PostgreSQL + pgvector
    database_url: str = "postgresql+asyncpg://zen:123456@localhost:5432/synverse"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Neo4j
    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "synverse123"

    # MinIO
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "synverse"

    # Embedding
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    # Ollama (辅助模型)
    ollama_base_url: str = "http://localhost:11434"

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
