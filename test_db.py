from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT 1"))
    print(result.scalar())


from app.core.config import settings
from payos import PayOS

print("CLIENT ID:", settings.PAYOS_CLIENT_ID)

print("FRONTEND_URL:", settings.FRONTEND_URL)
print("CLIENT_ID:", settings.PAYOS_CLIENT_ID)

client = PayOS(
    client_id=settings.PAYOS_CLIENT_ID,
    api_key=settings.PAYOS_API_KEY,
    checksum_key=settings.PAYOS_CHECKSUM_KEY
)

print("PAYOS CLIENT INIT OK")