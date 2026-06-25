from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.endpoints.analyze import router as analyze_router
from app.api.endpoints.files import router as files_router
from app.api.endpoints.jobs import router as jobs_router
from app.api.endpoints.upload import router as upload_router
from app.api.endpoints.payment import router as payment_router

app = FastAPI(
    title="ChuanWord API",
    description="Phân tích & chuẩn hóa file Word theo quy chuẩn định dạng",
    version="1.0.0",
)

# CORS cho frontend dev (Next.js tại localhost:3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "https://chuanword.vercel.app",
        "https://www.chuanword.vn"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(analyze_router)
app.include_router(jobs_router)
app.include_router(files_router)
app.include_router(payment_router, prefix="/payment")


@app.get("/")
def read_root():
    return {"message": "ChuanWord API"}
