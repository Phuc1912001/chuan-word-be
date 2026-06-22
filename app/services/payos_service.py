from app.core.config import settings
from payos import PayOS

print(settings.PAYOS_CLIENT_ID)

client = PayOS(
    client_id=settings.PAYOS_CLIENT_ID,
    api_key=settings.PAYOS_API_KEY,
    checksum_key=settings.PAYOS_CHECKSUM_KEY
)