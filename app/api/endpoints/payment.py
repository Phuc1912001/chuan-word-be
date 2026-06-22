from fastapi import APIRouter, Request, Depends
import time

from sqlalchemy.orm import Session

from app.services.payos_service import client
from payos.types import CreatePaymentLinkRequest
from payos import WebhookError
from app.core.config import settings

from app.db.session import get_db
from app.models.payment import Payment

router = APIRouter()


# =========================
# CREATE PAYMENT
# =========================
@router.post("/create")
async def create_payment(db: Session = Depends(get_db)):
    try:
        order_code = int(time.time() * 1000)

        payment_data = CreatePaymentLinkRequest(
            order_code=order_code,
            amount=50000,
            description="Nang cap goi ChuanWord",
            cancel_url=f"{settings.FRONTEND_URL}/quy-trinh/thanh-toan",
            return_url=f"{settings.FRONTEND_URL}/quy-trinh/thanh-toan",
        )

        response = client.payment_requests.create(payment_data=payment_data)

        # lấy checkout url (PayOS SDK có thể trả nhiều format khác nhau)
        checkout_url = (
            getattr(response, "checkout_url", None)
            or getattr(response, "checkoutUrl", None)
            or getattr(getattr(response, "data", None), "checkoutUrl", None)
        )

        # =========================
        # SAVE DB (PENDING)
        # =========================
        payment = Payment(
            order_code=order_code,
            amount=50000,
            status="PENDING",
            checkout_url=checkout_url
        )

        db.add(payment)
        db.commit()
        db.refresh(payment)

        return {
            "checkoutUrl": checkout_url,
            "orderCode": order_code
        }

    except Exception as e:
        print("🔥 PAYOS CREATE ERROR:", repr(e))
        return {"error": str(e)}


# =========================
# WEBHOOK
# =========================
@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db)):
    try:
        print("🔥 WEBHOOK HIT")

        data = await request.json()
        print("DATA:", data)

        payload = data.get("data", {})

        order_code = payload.get("orderCode")
        code = payload.get("code")

        print("ORDER:", order_code)

        payment = db.query(Payment).filter(
            Payment.order_code == order_code
        ).first()

        if not payment:
            return {"message": "payment not found"}

        payment.status = "SUCCESS" if code == "00" else "FAILED"
        db.commit()

        print("✅ UPDATED:", payment.status)

        return {"message": "ok"}

    except Exception as e:
        print("ERROR:", repr(e))
        return {"error": str(e)}
    
@router.get("/status/{order_code}")
def get_payment_status(order_code: int, db: Session = Depends(get_db)):
    payment = db.query(Payment).filter(
        Payment.order_code == order_code
    ).first()

    if not payment:
        return {
            "success": False,
            "message": "Payment not found"
        }

    return {
        "success": True,
        "orderCode": payment.order_code,
        "amount": payment.amount,
        "status": payment.status,
        "checkoutUrl": payment.checkout_url
    }