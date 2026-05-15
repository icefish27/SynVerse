from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "SynVerse API"
    debug: bool = True

    # DeepSeek
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"

    # PostgreSQL
    database_url: str = "postgresql+asyncpg://zen:123456@localhost:5432/synverse"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Embedding
    embedding_model: str = "BAAI/bge-small-zh-v1.5"

    # Ollama
    ollama_base_url: str = "http://localhost:11434"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
