from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "ForkliftCLI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./forklift_bao.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # OCR
    OCR_PROVIDER: str = "paddleocr"  # paddleocr | baidu | tencent

    # AI
    AI_PROVIDER: str = "openai"  # openai | qwen | ollama
    AI_API_KEY: str = ""
    AI_BASE_URL: str = ""
    AI_MODEL: str = "gpt-4o-mini"

    # Vector DB
    QDRANT_URL: str = "http://localhost:6333"
    WEMM_MODEL_NAME: str = "tencent/WeMM-Embedding-2B"
    WEMM_EMBED_DIM: int = 1024

    # File Storage
    UPLOAD_DIR: str = "uploads"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
