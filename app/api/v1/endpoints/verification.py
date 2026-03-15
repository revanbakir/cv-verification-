from fastapi import APIRouter
import os
from app.schemas.verification import VerificationRequest
from app.services.analysis_service import AnalysisService


router = APIRouter()

@router.post("/")
def verify(request: VerificationRequest):

    service = AnalysisService(os.getenv("GITHUB_TOKEN"))

    result = service.analyze(
        request.cv_text,
        request.github_username,
        request.cv_start_year
    )
    return result