from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime

from app.db.base import Base


class AnalysisResult(Base):
    __tablename__ = "analysis_results"

    id = Column(Integer, primary_key=True, index=True)

    file_id = Column(Integer, ForeignKey("uploaded_files.id"), index=True, nullable=False)

    rule_code = Column(String, nullable=False)  # FONT, MARGIN_LEFT, QUOC_HIEU...

    error_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)