from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI(
    title="test",
    description="like",
    version="1.0.0"
)
@app.get("/")
def read_root():
    return {"message":"toi day"}