from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime

from app.db.base import Base


class AnalysisJob(Base):
    """Một lần phân tích/chuẩn hóa + kết quả (gói gọn trong JSONB, không tách bảng lỗi)."""

    __tablename__ = "analysis_jobs"

    id = Column(Integer, primary_key=True)

    file_id = Column(Integer, ForeignKey("uploaded_files.id"), index=True, nullable=False)

    user_id = Column(Integer, index=True, nullable=True)

    template_key = Column(String, nullable=True)

    kind = Column(String, nullable=False, default="analyze")        # analyze | fix

    status = Column(String, nullable=False, default="PENDING", index=True)  # PENDING/PROCESSING/DONE/FAILED

    score = Column(Float, nullable=True)
    total_errors = Column(Integer, nullable=True)

    # đếm theo rule, vd {"FONT": 3, "MARGIN": 4} — cho dashboard
    summary = Column(JSONB, nullable=True)
    # danh sách lỗi cho bước 3: [{id,type,message,suggestion,paragraph_index,page}]
    details = Column(JSONB, nullable=True)

    result_file_path = Column(String, nullable=True)   # file .docx đã chuẩn hóa
    error_message = Column(String, nullable=True)

    started_at = Column(DateTime, nullable=True)
    finished_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
