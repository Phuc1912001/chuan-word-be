from pydantic import BaseModel
from datetime import datetime


class PaymentBase(BaseModel):
    order_code: int
    amount: int
    status: str = "PENDING"


class PaymentCreate(PaymentBase):
    pass


class PaymentResponse(PaymentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True