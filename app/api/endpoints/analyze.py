# app/api/endpoints/analyze.py
#
# Endpoint SYNC tiện cho dev/FE hiện tại. Phân tích KHÔNG còn persist xuống bảng
# (lỗi là ephemeral, tính lại được) — chỉ trả kết quả. Lịch sử/lưu trữ dùng luồng /jobs (JSONB).

import os
import uuid

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models.file import UploadedFile
from app.rules.presets import get_preset
from app.schemas.analysis import AnalysisErrorOut, AnalyzeResponse
from app.services.analyzer import analyze_file
from app.services.fixer import fix_file
from app.services.preview import docx_to_pdf
from app.services.storage import get_storage

router = APIRouter(prefix="/analyze", tags=["Analyze"])

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _get_local_path(db: Session, file_id: int) -> tuple[str, UploadedFile]:
    uploaded = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if uploaded is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy file")
    try:
        local = get_storage().localize(uploaded.file_path)
    except Exception:
        raise HTTPException(status_code=410, detail="File không còn tồn tại trên hệ thống")
    if not os.path.exists(local):
        raise HTTPException(status_code=410, detail="File không còn tồn tại trên hệ thống")
    return local, uploaded


@router.post("/{file_id}", response_model=AnalyzeResponse)
def analyze_endpoint(file_id: int, preset: str | None = None, db: Session = Depends(get_db)):
    local, _ = _get_local_path(db, file_id)
    spec = get_preset(preset)
    try:
        report = analyze_file(local, spec)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Không phân tích được file: {e}")

    errors = [
        AnalysisErrorOut(
            id=f"{issue.rule_code}-{idx}",
            type=issue.rule_code,
            message=issue.message,
            suggestion=issue.suggestion,
            page=issue.page_number,
            paragraph_index=issue.paragraph_index,
        )
        for idx, issue in enumerate(report.issues)
    ]
    return AnalyzeResponse(
        file_id=file_id,
        score=report.score,
        total_errors=report.total_errors,
        errors=errors,
    )


@router.post("/{file_id}/fix")
def fix_endpoint(file_id: int, preset: str | None = None, db: Session = Depends(get_db)):
    local, uploaded = _get_local_path(db, file_id)
    spec = get_preset(preset)
    out_path = os.path.join(settings.UPLOAD_DIR, f"{uuid.uuid4().hex}.docx")
    try:
        fix_file(local, spec, out_path)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Không chuẩn hóa được file: {e}")

    download_name = f"chuan-hoa_{uploaded.filename or 'document.docx'}"
    return FileResponse(out_path, filename=download_name, media_type=DOCX_MEDIA_TYPE)


@router.post("/{file_id}/preview")
def preview_endpoint(file_id: int, preset: str | None = None, db: Session = Depends(get_db)):
    local, _ = _get_local_path(db, file_id)
    spec = get_preset(preset)
    out_dir = settings.UPLOAD_DIR
    fixed_path = os.path.join(out_dir, f"{uuid.uuid4().hex}.docx")
    try:
        fix_file(local, spec, fixed_path)
        pdf_path = docx_to_pdf(fixed_path, out_dir)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Không tạo được bản xem trước: {e}")

    return FileResponse(pdf_path, media_type="application/pdf")
