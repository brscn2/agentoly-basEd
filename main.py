from fastapi import FastAPI
from app.api.v1 import api_router

app = FastAPI(
    title="FastAPI Application",
    description="A basic FastAPI application",
    version="1.0.0"
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "Welcome to FastAPI Application"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
