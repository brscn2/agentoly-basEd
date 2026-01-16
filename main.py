from fastapi import FastAPI
from app.api.v1 import api_router
from app.config import settings
import os

app = FastAPI(
    title="Multi-Agent Tutoring System",
    description="AI tutoring system that infers student understanding levels and provides personalized teaching",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {
        "message": "Welcome to Multi-Agent Tutoring System",
        "description": "AI tutors that infer student understanding through interaction and teach adaptively"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


# Ensure logs directory exists
os.makedirs(settings.log_dir, exist_ok=True)
