from fastapi import FastAPI
from app.api.v1.router import api_router
# app/main.py veya app/core/github_analyzer.py başında
from dotenv import load_dotenv
import os

load_dotenv()  # .env dosyasını oku

app = FastAPI()

app.get("/")
def hello():
    return {"message": "hello"}

app.include_router(api_router, prefix="/api/v1")