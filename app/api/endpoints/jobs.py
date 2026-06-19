# app/api/endpoints/jobs.py
#
# Luồng async (GĐ0): tạo job → đẩy vào Celery → trả 202 + job_id; client poll GET /jobs/{id}.
# Kết quả lưu gọn trong cột JSONB của job (không tách bảng lỗi).

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.file import UploadedFile
from app.models.job import AnalysisJob
from app.schemas.analysis import AnalysisErrorOut
from app.schemas.job import JobCreate, JobCreateResponse, JobStatusResponse
from app.worker.tasks import run_analysis

router = APIRouter(prefix="/jobs", tags=["Jobs"])


@router.post("", status_code=status.HTTP_202_ACCEPTED, response_model=JobCreateResponse)
def create_job(payload: JobCreate, db: Session = Depends(get_db)):
    uploaded = db.query(UploadedFile).filter(UploadedFile.id == payload.file_id).first()
    if uploaded is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy file")

    job = AnalysisJob(
        file_id=payload.file_id,
        template_key=payload.template_key,
        kind="analyze",
        status="PENDING",
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    run_analysis.delay(job.id)

    return JobCreateResponse(job_id=job.id, status=job.status)


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.query(AnalysisJob).filter(AnalysisJob.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Không tìm thấy job")

    errors: list[AnalysisErrorOut] = []
    if job.status == "DONE":
        for e in (job.details or []):
            errors.append(AnalysisErrorOut(
                id=e.get("id", ""),
                type=e.get("type", ""),
                message=e.get("message", ""),
                suggestion=e.get("suggestion", "") or "",
                page=e.get("page"),
                paragraph_index=e.get("paragraph_index"),
            ))

    return JobStatusResponse(
        id=job.id,
        file_id=job.file_id,
        status=job.status,
        score=job.score,
        total_errors=job.total_errors,
        error_message=job.error_message,
        errors=errors,
    )
