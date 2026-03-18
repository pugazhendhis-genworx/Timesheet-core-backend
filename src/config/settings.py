from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    POSTGRES_DB_URL: str
    SYNC_POSTGRES_DB_URL: str
    app_secret: str
    REDIS_URL: str
    QUEUE_NAME: str
    SERVICE_TYPE: str
    WATCH_INTERVAL_SECONDS: int = 30
    GROQ_API_KEY: str
    GEMINI_API_KEY: str
    LANGFUSE_SECRET_KEY: str
    LANGFUSE_PUBLIC_KEY: str
    LANGFUSE_BASE_URL: str
    TOKEN_FILE: str
    CREDENTIALS_FILE: str
    FRONTEND_URL: str
    AUTHBACKEND_URL: str

    class Config:
        env_file = ".env"


settings = Settings()
