from sqlalchemy import Column, Integer, String, DateTime, Float
from app.db.base import Base
from datetime import datetime


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, index=True, nullable=True)

    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)

    status = Column(String, default="PENDING")  # PENDING / PROCESSING / DONE / FAILED

    score = Column(Float, default=0)

    total_errors = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)