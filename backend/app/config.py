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
    USE_MEMORY_STORE: bool = False

    # File Storage & 3D Assets
    STORAGE_PROVIDER: str = "local"  # local | minio | s3
    UPLOAD_DIR: str = "uploads"
    STORAGE_BUCKET: str = "forklift-models"
    STORAGE_ENDPOINT: str = "http://localhost:9000"
    STORAGE_ACCESS_KEY: str = ""
    STORAGE_SECRET_KEY: str = ""
    STORAGE_REGION: str = "us-east-1"
    STORAGE_SECURE: bool = False
    STORAGE_PUBLIC_BASE_URL: str = ""  # CDN or bucket public URL, e.g. http://localhost:8000/static/uploads

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()
