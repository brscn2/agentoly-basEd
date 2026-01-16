from fastapi import APIRouter
from app.api.v1.endpoints import tutoring

api_router = APIRouter()
api_router.include_router(tutoring.tutoring_router, prefix="/tutor", tags=["tutoring"])
api_router.include_router(tutoring.evaluation_router, prefix="/evaluate", tags=["evaluation"])
