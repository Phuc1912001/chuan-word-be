from sqlalchemy import Column, Integer

from app.db.base import Base

class Statistic(Base):
    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True)
    total_downloads = Column(Integer, default=0, nullable=False)