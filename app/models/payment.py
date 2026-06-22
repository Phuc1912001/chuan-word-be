from sqlalchemy import Column, Integer, String, BigInteger, DateTime
from sqlalchemy.sql import func
from app.db.base import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)

    order_code = Column(BigInteger, unique=True, nullable=False, index=True)

    amount = Column(Integer, nullable=False)

    status = Column(String, default="PENDING")  # PENDING / SUCCESS / FAILED

    checkout_url = Column(String, nullable=True)  # 🔥 thêm cái này

    created_at = Column(DateTime(timezone=True), server_default=func.now())