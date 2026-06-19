"""Lớp lưu trữ file trừu tượng: local (dev) hoặc S3 (prod).

`save(key, data)` lưu và trả về tham chiếu (đường dẫn local hoặc s3://...).
`localize(ref)` trả về đường dẫn local để xử lý (S3 sẽ tải về temp).
"""

from __future__ import annotations

import os
import tempfile
from typing import Protocol

from app.core.config import settings


class Storage(Protocol):
    def save(self, key: str, data: bytes) -> str: ...
    def localize(self, ref: str) -> str: ...


class LocalStorage:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def save(self, key: str, data: bytes) -> str:
        path = os.path.join(self.base_dir, key)
        os.makedirs(os.path.dirname(path) or self.base_dir, exist_ok=True)
        with open(path, "wb") as f:
            f.write(data)
        return path

    def localize(self, ref: str) -> str:
        return ref


class S3Storage:
    def __init__(self):
        import boto3  # import lazy: chỉ cần khi dùng S3

        self.bucket = settings.S3_BUCKET
        self.client = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        )

    def save(self, key: str, data: bytes) -> str:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data)
        return f"s3://{self.bucket}/{key}"

    def localize(self, ref: str) -> str:
        if not ref.startswith("s3://"):
            return ref
        bucket, key = ref[len("s3://"):].split("/", 1)
        fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(key)[1])
        os.close(fd)
        self.client.download_file(bucket, key, tmp)
        return tmp


def get_storage() -> Storage:
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage(settings.UPLOAD_DIR)
