# app/api/upload.py

import os
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.file import UploadedFile

router = APIRouter(prefix="/upload", tags=["Upload"])

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/")
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    file_path = os.path.join(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    new_file = UploadedFile(
        filename=file.filename,
        file_path=file_path
    )

    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return {
        "message": "Upload thành công",
        "file": new_file
    }