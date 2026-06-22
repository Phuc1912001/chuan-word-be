from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    SQLALCHEMY_DATABASE_URL: str

    # --- Storage ---
    STORAGE_BACKEND: str = "local"          # local | s3
    UPLOAD_DIR: str = "uploads"
    S3_BUCKET: str | None = None
    S3_REGION: str | None = None
    S3_ENDPOINT_URL: str | None = None
    AWS_ACCESS_KEY_ID: str | None = None
    AWS_SECRET_ACCESS_KEY: str | None = None

    # --- Queue (Celery + Redis) ---
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    # True => chạy task ngay trong tiến trình gọi (dev/test, không cần Redis/worker)
    CELERY_TASK_ALWAYS_EAGER: bool = False

    PAYOS_CLIENT_ID: str| None = None
    PAYOS_API_KEY: str | None = None
    PAYOS_CHECKSUM_KEY: str| None = None
    FRONTEND_URL: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def celery_broker(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL

    @property
    def celery_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL


settings = Settings()
