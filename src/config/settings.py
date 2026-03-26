from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB_URL: str
    SYNC_POSTGRES_DB_URL: str
    APP_SECRET: str
    REDIS_URL: str
    QUEUE_NAME: str
    SERVICE_TYPE: str
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_BASE_URL: str
    TOKEN_FILE: str
    CREDENTIALS_FILE: str
    FRONTEND_URL: str
    GCS_PROJECT_ID: str
    GCS_BUCKET_NAME: str
    GCS_BUCKET_PREFIX: str = "timeguard"
    GCS_TARGET_SERVICE_ACCOUNT: str
    GCS_SIGNED_URL_EXPIRY_HOURS: int = 4
    AUTHBACKEND_URL: str

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
