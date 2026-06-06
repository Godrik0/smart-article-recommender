from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "smart-article-recommender"
    app_env: str = "dev"
    api_prefix: str = "/api/v1"

    database_url: str
    database_sync_url: str
    redis_url: str

    celery_broker_url: str
    celery_result_backend: str

    model_id: str = "sentence-transformers/all-MiniLM-L6-v2"
    model_cache_dir: str = "/models/hf_cache"
    model_device: str = "cpu"
    model_top_k_default: int = 5
    model_max_prompt_length: int = 1200
    model_concurrency: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        protected_namespaces=("settings_",),
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
