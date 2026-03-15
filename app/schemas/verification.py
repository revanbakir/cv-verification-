from pydantic import BaseModel

class VerificationRequest(BaseModel):  
    cv_text: str
    github_username: str
    cv_start_year: int