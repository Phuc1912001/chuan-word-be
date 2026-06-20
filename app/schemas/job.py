# app/schemas/job.py

from pydantic import BaseModel

from app.schemas.analysis import AnalysisErrorOut


class JobCreate(BaseModel):
    file_id: int
    template_key: str | None = None


class JobCreateResponse(BaseModel):
    job_id: int
    status: str


class JobStatusResponse(BaseModel):
    id: int
    file_id: int
    status: str
    score: float | None = None
    total_errors: int | None = None
    error_message: str | None = None
    errors: list[AnalysisErrorOut] = []
