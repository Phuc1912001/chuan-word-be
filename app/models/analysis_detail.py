from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from app.db.base import Base


class AnalysisDetail(Base):
    __tablename__ = "analysis_details"

    id = Column(Integer, primary_key=True, index=True)

    file_id = Column(Integer, ForeignKey("uploaded_files.id"), index=True)

    rule_code = Column(String, nullable=False)

    page_number = Column(Integer, nullable=True)

    paragraph_index = Column(Integer, nullable=True)

    message = Column(String, nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)