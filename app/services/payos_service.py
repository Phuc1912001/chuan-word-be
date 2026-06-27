"""Khởi tạo PayOS client.

Không để thiếu cấu hình PayOS làm sập TOÀN BỘ API khi chạy dev: nếu thiếu
PAYOS_CLIENT_ID/API_KEY/CHECKSUM_KEY thì `client = None`, các endpoint thanh
toán sẽ báo lỗi mềm thay vì crash lúc import. Điền 3 biến PAYOS_* vào .env để bật.
"""

from app.core.config import settings
from payos import PayOS

if settings.PAYOS_CLIENT_ID and settings.PAYOS_API_KEY and settings.PAYOS_CHECKSUM_KEY:
    client = PayOS(
        client_id=settings.PAYOS_CLIENT_ID,
        api_key=settings.PAYOS_API_KEY,
        checksum_key=settings.PAYOS_CHECKSUM_KEY,
    )
else:
    client = None
    print("⚠️  PayOS chưa cấu hình (thiếu PAYOS_* trong .env) — endpoint thanh toán tạm tắt.")
