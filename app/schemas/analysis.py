# app/schemas/analysis.py

from pydantic import BaseModel


class AnalysisErrorOut(BaseModel):
    """Khớp shape IAnalysisError ở frontend: {id, type, message, suggestion, page}.
    paragraph_index là vị trí đoạn (FE có thể bỏ qua)."""

    id: str
    type: str          # = rule_code
    message: str
    suggestion: str = ""
    page: int | None = None
    paragraph_index: int | None = None

class AnalysisGroupOut(BaseModel):
    type: str
    count: int
    errors: list[AnalysisErrorOut]


class AnalyzeResponse(BaseModel):
    file_id: int
    score: float
    total_errors: int
    summary: dict[str, int] = {}
    groups: list[AnalysisGroupOut] = []



class FileUrlResponse(BaseModel):
    """Trả URL tải/xem file kết quả (presigned S3 hoặc link /files local)."""

    url: str
    filename: str | None = None
