# app/api/endpoints/analyze.py
#
# /analyze: phân tích sync, KHÔNG persist (trả kết quả).
# /fix, /preview: tạo file kết quả → lưu lên storage (S3/local) → trả URL
#   (presigned nếu S3; link /files nếu local). Dọn temp sau khi xử lý.

import os
import tempfile
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session
from app.models.statistics import Statistic
from collections import Counter, defaultdict
from pathlib import Path

from app.db.session import get_db
from app.models.file import UploadedFile
from app.rules.presets import get_preset
from app.schemas.analysis import AnalysisErrorOut, AnalyzeResponse, FileUrlResponse, AnalysisGroupOut
from app.services.analyzer import analyze_file
from app.services.fixer import fix_file
from app.services.storage import get_storage
router = APIRouter(prefix="/analyze", tags=["Analyze"])

DOCX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"


def _get_uploaded(db: Session, file_id: int) -> UploadedFile:
    uploaded = db.query(UploadedFile).filter(UploadedFile.id == file_id).first()
    if uploaded is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy file")
    return uploaded


def _localize(storage, uploaded: UploadedFile) -> str:
    try:
        local = storage.localize(uploaded.file_path)
    except Exception:
        raise HTTPException(status_code=410, detail="File không còn tồn tại trên hệ thống")
    if not os.path.exists(local):
        raise HTTPException(status_code=410, detail="File không còn tồn tại trên hệ thống")
    return local


def _safe_remove(path: str | None) -> None:
    try:
        if path and os.path.exists(path):
            os.remove(path)
    except OSError:
        pass


def _local_url(request: Request, key: str) -> str:
    return f"{str(request.base_url).rstrip('/')}/files/{key}"


@router.post("/{file_id}", response_model=AnalyzeResponse)
def analyze_endpoint(
    file_id: int,
    preset: str | None = None,
    db: Session = Depends(get_db),
):
    uploaded = _get_uploaded(db, file_id)

    storage = get_storage()
    local = _localize(storage, uploaded)

    spec = get_preset(preset)

    try:
        report = analyze_file(local, spec)

    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Không phân tích được file: {e}",
        )

    finally:
        storage.cleanup_local(uploaded.file_path, local)

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

    # summary
    summary = dict(Counter(error.type for error in errors))

    # groups
    grouped = defaultdict(list)

    for error in errors:
        grouped[error.type].append(error)

    groups = [
        AnalysisGroupOut(
            type=error_type,
            count=len(items),
            errors=items,
        )
        for error_type, items in grouped.items()
    ]

    return AnalyzeResponse(
        file_id=file_id,
        score=report.score,
        total_errors=report.total_errors,
        summary=summary,
        groups=groups,
    )


@router.post("/{file_id}/fix", response_model=FileUrlResponse)
def fix_endpoint(
    file_id: int,
    request: Request,
    preset: str | None = None,
    db: Session = Depends(get_db),
):
    uploaded = _get_uploaded(db, file_id)
    storage = get_storage()
    local = _localize(storage, uploaded)
    spec = get_preset(preset)

    fd, tmp_out = tempfile.mkstemp(suffix=".docx")
    os.close(fd)
    key = f"{uuid.uuid4().hex}.docx"
    try:
        fix_file(local, spec, tmp_out)
        ref = storage.save_file(key, tmp_out, content_type=DOCX_MEDIA_TYPE)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Không chuẩn hóa được file: {e}",
        )
    finally:
        storage.cleanup_local(uploaded.file_path, local)
        _safe_remove(tmp_out)
    stat = db.query(Statistic).filter(Statistic.id == 1).first()
    if not stat:
        stat = Statistic(id=1, total_downloads=0)
        db.add(stat)

    stat.total_downloads += 1
    db.commit()

    original_name = uploaded.filename or "document.docx"

    if not original_name.lower().endswith(".docx"):
        original_name = f"{Path(original_name).stem}.docx"

    download_name = f"chuan-hoa_{original_name}"

    url = (
        storage.presigned_url(
            ref,
            download_name=download_name,
        )
        or _local_url(request, key)
    )

    return FileUrlResponse(
        url=url,
        filename=download_name,
    )


@router.post("/{file_id}/preview")
def preview_endpoint(
    file_id: int,
    preset: str | None = None,
    db: Session = Depends(get_db),
):
    """Trả file .docx ĐÃ CHUẨN HÓA (bytes) để FE render bằng docx-preview.
    Không còn convert PDF/LibreOffice. FE fetch endpoint này (cùng origin → CORS sẵn)."""
    uploaded = _get_uploaded(db, file_id)
    storage = get_storage()
    local = _localize(storage, uploaded)
    spec = get_preset(preset)

    fd, tmp_out = tempfile.mkstemp(suffix=".docx")
    os.close(fd)
    try:
        fix_file(local, spec, tmp_out)
        with open(tmp_out, "rb") as f:
            data = f.read()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Không tạo được bản xem trước: {e}")
    finally:
        storage.cleanup_local(uploaded.file_path, local)
        _safe_remove(tmp_out)

    return Response(content=data, media_type=DOCX_MEDIA_TYPE)


@router.get("/stats")
def get_stats(db: Session = Depends(get_db)):
    stat = db.query(Statistic).filter(Statistic.id == 1).first()

    return {
        "total_downloads": stat.total_downloads if stat else 0
    }
