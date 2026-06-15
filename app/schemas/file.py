# app/schemas/file.py

from pydantic import BaseModel
from datetime import datetime

class FileResponse(BaseModel):
    id: int
    filename: str
    file_path: str
    created_at: datetime

    class Config:
        from_attributes = True