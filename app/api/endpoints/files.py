# app/api/endpoints/files.py
# Serve file kết quả ở chế độ local (STORAGE_BACKEND=local).
# Chế độ S3 dùng presigned URL trực tiếp, không qua endpoint này.

import os

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.core.config import settings

router = APIRouter(prefix="/files", tags=["Files"])


@router.get("/{name}")
def serve_file(name: str):
    # chặn path traversal: chỉ cho tên file phẳng
    if "/" in name or "\\" in name or ".." in name:
        raise HTTPException(status_code=400, detail="Tên file không hợp lệ")
    path = os.path.join(settings.UPLOAD_DIR, name)
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Không tìm thấy file")
    return FileResponse(path)
