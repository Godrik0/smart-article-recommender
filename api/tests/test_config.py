from app.config import Settings


class TestSettings:
    def test_model_fields_allowed(self):
        s = Settings(
            database_url="postgresql+asyncpg://u:p@localhost/db",
            database_sync_url="postgresql+psycopg://u:p@localhost/db",
            redis_url="redis://localhost:6379/0",
            celery_broker_url="redis://localhost:6379/0",
            celery_result_backend="redis://localhost:6379/0",
        )
        assert s.model_id == "sentence-transformers/all-MiniLM-L6-v2"
        assert s.model_concurrency == 2

    def test_model_max_prompt_length(self):
        s = Settings(
            database_url="postgresql+asyncpg://u:p@localhost/db",
            database_sync_url="postgresql+psycopg://u:p@localhost/db",
            redis_url="redis://localhost:6379/0",
            celery_broker_url="redis://localhost:6379/0",
            celery_result_backend="redis://localhost:6379/0",
        )
        assert s.model_max_prompt_length == 1200
