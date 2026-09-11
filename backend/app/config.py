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

    # JWT（与 account-service 共享，用于本地验签）
    SECRET_KEY: str = "8a2971c6d285a150f8b3c36b66d7914cd8d2423b578084184266517b882b6dda"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # account-service（账户权威服务）
    ACCOUNT_SERVICE_URL: str = "http://127.0.0.1:8001/api/v1"

    # 超级管理员初始化（scripts/init_admin.py 使用；生产环境务必通过 .env 覆盖）
    ADMIN_PHONE: str = "13800000000"
    ADMIN_PASSWORD: str = ""
    ADMIN_NICKNAME: str = "超级管理员"

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
