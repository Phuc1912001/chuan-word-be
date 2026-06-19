# app/api/endpoints/upload.py

import os
import uuid

from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.file import UploadedFile
from app.schemas.file import UploadResponse, FileResponse
from app.services.storage import get_storage

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    data = await file.read()

    # tên lưu duy nhất (uuid) để tránh ghi đè; tên gốc giữ trong cột filename
    ext = os.path.splitext(file.filename or "")[1] or ".docx"
    stored_name = f"{uuid.uuid4().hex}{ext}"
    file_path = get_storage().save(stored_name, data)

    new_file = UploadedFile(
        filename=file.filename,
        file_path=file_path,
        size_bytes=len(data),
        mime_type=file.content_type,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return UploadResponse(
        message="Upload thành công",
        file=FileResponse.model_validate(new_file),
    )
