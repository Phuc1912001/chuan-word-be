"""Lớp lưu trữ file trừu tượng: local (dev) hoặc S3 (prod).

- save(key, data)         : lưu bytes, trả ref (đường dẫn local hoặc s3://...).
- save_file(key, path)    : lưu 1 file local đã có lên storage, trả ref.
- localize(ref)           : trả đường dẫn local để xử lý (S3 tải về temp).
- cleanup_local(ref, path): xoá file temp tải về từ S3 (local: no-op).
- presigned_url(ref, ...) : link tải có hạn cho S3; local trả None (serve qua /files).
"""

from __future__ import annotations

import os
import shutil
import tempfile
from typing import Protocol

from app.core.config import settings


class Storage(Protocol):
    def save(self, key: str, data: bytes, content_type: str | None = None) -> str: ...
    def save_file(self, key: str, local_path: str, content_type: str | None = None) -> str: ...
    def localize(self, ref: str) -> str: ...
    def cleanup_local(self, ref: str, local_path: str) -> None: ...
    def presigned_url(self, ref: str, expires: int = 3600, download_name: str | None = None) -> str | None: ...


class LocalStorage:
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        os.makedirs(base_dir, exist_ok=True)

    def _path(self, key: str) -> str:
        p = os.path.join(self.base_dir, key)
        os.makedirs(os.path.dirname(p) or self.base_dir, exist_ok=True)
        return p

    def save(self, key: str, data: bytes, content_type: str | None = None) -> str:
        p = self._path(key)
        with open(p, "wb") as f:
            f.write(data)
        return p

    def save_file(self, key: str, local_path: str, content_type: str | None = None) -> str:
        p = self._path(key)
        if os.path.abspath(local_path) != os.path.abspath(p):
            shutil.copyfile(local_path, p)
        return p

    def localize(self, ref: str) -> str:
        return ref

    def cleanup_local(self, ref: str, local_path: str) -> None:
        # ref chính là file thật trên đĩa → không xoá
        return None

    def presigned_url(self, ref: str, expires: int = 3600, download_name: str | None = None) -> str | None:
        return None  # local: tải qua endpoint /files/{name}


class S3Storage:
    def __init__(self):
        import boto3  # lazy: chỉ cần khi dùng S3
        from botocore.config import Config

        self.bucket = settings.S3_BUCKET
        # Dùng endpoint theo region để presigned URL không bị 307 redirect
        # (bucket ngoài us-east-1 sẽ lỗi chữ ký nếu ký theo endpoint global).
        endpoint = settings.S3_ENDPOINT_URL
        if not endpoint and settings.S3_REGION:
            endpoint = f"https://s3.{settings.S3_REGION}.amazonaws.com"

        self.client = boto3.client(
            "s3",
            region_name=settings.S3_REGION,
            endpoint_url=endpoint,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
        )

    def save(self, key: str, data: bytes, content_type: str | None = None) -> str:
        kwargs = {"Bucket": self.bucket, "Key": key, "Body": data}
        if content_type:
            kwargs["ContentType"] = content_type
        self.client.put_object(**kwargs)
        return f"s3://{self.bucket}/{key}"

    def save_file(self, key: str, local_path: str, content_type: str | None = None) -> str:
        extra = {"ContentType": content_type} if content_type else None
        self.client.upload_file(local_path, self.bucket, key, ExtraArgs=extra)
        return f"s3://{self.bucket}/{key}"

    def localize(self, ref: str) -> str:
        if not ref.startswith("s3://"):
            return ref
        bucket, key = ref[len("s3://"):].split("/", 1)
        fd, tmp = tempfile.mkstemp(suffix=os.path.splitext(key)[1])
        os.close(fd)
        self.client.download_file(bucket, key, tmp)
        return tmp

    def cleanup_local(self, ref: str, local_path: str) -> None:
        # local_path là temp tải từ S3 → xoá; (ref local thì không vào nhánh này)
        if ref.startswith("s3://") and local_path and os.path.exists(local_path):
            try:
                os.remove(local_path)
            except OSError:
                pass

    def presigned_url(self, ref: str, expires: int = 3600, download_name: str | None = None) -> str | None:
        bucket, key = ref[len("s3://"):].split("/", 1)
        params = {"Bucket": bucket, "Key": key}
        if download_name:
            params["ResponseContentDisposition"] = f'attachment; filename="{download_name}"'
        return self.client.generate_presigned_url("get_object", Params=params, ExpiresIn=expires)


def get_storage() -> Storage:
    if settings.STORAGE_BACKEND == "s3":
        return S3Storage()
    return LocalStorage(settings.UPLOAD_DIR)
