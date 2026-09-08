import hashlib
from pathlib import Path
from app.config import get_settings

settings = get_settings()


class StorageClient:
    """统一存储客户端：支持 local 磁盘目录与 MinIO/S3 对象存储。"""

    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER.lower()
        self.upload_dir = settings.UPLOAD_DIR
        self.bucket = settings.STORAGE_BUCKET
        self.public_base_url = settings.STORAGE_PUBLIC_BASE_URL
        self._root = Path(settings.UPLOAD_DIR).resolve()

        if self.provider == "local":
            (self._root / "models").mkdir(parents=True, exist_ok=True)

    def _local_path(self, s3_key: str) -> Path:
        # s3_key 只允许小写字母数字、点、下划线、连字符、斜杠，且不含 ".."/"./"。
        if ".." in s3_key or s3_key.startswith("/") or s3_key.startswith("."):
            raise ValueError("invalid storage key")
        for seg in s3_key.split("/"):
            if seg in ("", ".", ".."):
                raise ValueError("invalid storage key")
            if not all(c.isalnum() or c in "._-" for c in seg):
                raise ValueError("invalid storage key")
        file_path = (self._root / s3_key).resolve()
        if file_path != self._root and self._root not in file_path.parents:
            raise ValueError("path traversal detected")
        return file_path

    def put_object(self, key: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """存储对象并返回访问 URL。"""
        s3_key = key.lstrip("/")

        if self.provider in ("minio", "s3"):
            try:
                import boto3

                s3 = boto3.client(
                    "s3",
                    endpoint_url=settings.STORAGE_ENDPOINT if self.provider == "minio" else None,
                    aws_access_key_id=settings.STORAGE_ACCESS_KEY,
                    aws_secret_access_key=settings.STORAGE_SECRET_KEY,
                    region_name=settings.STORAGE_REGION,
                )
                s3.put_object(Bucket=self.bucket, Key=s3_key, Body=data, ContentType=content_type)
                if self.public_base_url:
                    return f"{self.public_base_url.rstrip('/')}/{s3_key}"
                return f"{settings.STORAGE_ENDPOINT.rstrip('/')}/{self.bucket}/{s3_key}"
            except Exception:
                pass

        file_path = self._local_path(s3_key)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(data)

        if self.public_base_url:
            return f"{self.public_base_url.rstrip('/')}/{s3_key}"
        return f"/uploads/{s3_key}"

    def compute_hash(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()


storage_client = StorageClient()


def get_storage_client() -> StorageClient:
    return storage_client
