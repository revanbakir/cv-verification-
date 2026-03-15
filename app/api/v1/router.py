from fastapi import APIRouter
from app.api.v1.endpoints import cv, github, ecv, verification

api_router = APIRouter()

api_router.include_router(cv.router, prefix="/cv", tags=["CV"])
api_router.include_router(github.router, prefix="/github", tags=["GitHub"])
api_router.include_router(ecv.router, prefix="/ecv", tags=["e-CV"])
api_router.include_router(verification.router, prefix="/verify", tags=["Verification"])