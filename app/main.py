from fastapi import FastAPI
from app.api.endpoints.upload import router as upload_router

app = FastAPI(
    title="test",
    description="like",
    version="1.0.0"
)

app.include_router(upload_router)

@app.get("/")
def read_root():
    return {"message": "toi day"}