from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

from app.db.base import Base


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True)  # PK đã có index, không cần index=True

    user_id = Column(Integer, index=True, nullable=True)

    filename = Column(String, nullable=False)   # tên gốc để hiển thị
    file_path = Column(String, nullable=False)  # ref storage: local path hoặc s3://...

    size_bytes = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # TTL — dọn file + bản ghi sau N ngày
