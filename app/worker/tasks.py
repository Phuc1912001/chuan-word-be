"""Celery tasks: phân tích file nền, lưu kết quả gọn vào JSONB của job."""

from datetime import datetime

from app.db.session import SessionLocal
from app.models.file import UploadedFile
from app.models.job import AnalysisJob
from app.rules.presets import get_preset
from app.services.analyzer import analyze_file
from app.services.storage import get_storage
from app.worker.celery_app import celery_app


def _issue_to_dict(idx, issue) -> dict:
    return {
        "id": f"{issue.rule_code}-{idx}",
        "type": issue.rule_code,
        "message": issue.message,
        "suggestion": issue.suggestion,
        "paragraph_index": issue.paragraph_index,
        "page": issue.page_number,
    }


@celery_app.task(name="analysis.run")
def run_analysis(job_id: int):
    db = SessionLocal()
    try:
        job = db.get(AnalysisJob, job_id)
        if job is None:
            return {"error": "job not found", "job_id": job_id}

        job.status = "PROCESSING"
        job.started_at = datetime.utcnow()
        db.commit()

        uploaded = db.get(UploadedFile, job.file_id)
        if uploaded is None:
            job.status = "FAILED"
            job.error_message = "uploaded file missing"
            job.finished_at = datetime.utcnow()
            db.commit()
            return {"error": "file missing", "job_id": job_id}

        local_path = get_storage().localize(uploaded.file_path)
        report = analyze_file(local_path, get_preset(job.template_key))

        job.summary = report.by_rule
        job.details = [_issue_to_dict(i, iss) for i, iss in enumerate(report.issues)]
        job.score = report.score
        job.total_errors = report.total_errors
        job.status = "DONE"
        job.finished_at = datetime.utcnow()
        db.commit()

        return {
            "job_id": job_id,
            "status": "DONE",
            "score": report.score,
            "total_errors": report.total_errors,
        }
    except Exception as e:
        db.rollback()
        job = db.get(AnalysisJob, job_id)
        if job is not None:
            job.status = "FAILED"
            job.error_message = str(e)[:500]
            job.finished_at = datetime.utcnow()
            db.commit()
        raise
    finally:
        db.close()
