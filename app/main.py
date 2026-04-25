from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.core.cv_extractor import CVExtractor
from app.core.github_analyzer import GithubAnalyzer
from app.core.verifier import Verifier
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def index():
    return FileResponse("static/index.html")

@app.post("/api/analyze")
async def analyze(
    cv_file: UploadFile = File(...),
    github_username: str = Form(...),
    github_token: str = Form(""),
    max_repos: int = Form(10),
):
    file_bytes = await cv_file.read()
    filename   = cv_file.filename or "file"

    cv_extractor = CVExtractor()
    text      = cv_extractor.extract_text(file_bytes, filename=filename)
    cv_skills = cv_extractor.extract_skills(text)

    token    = github_token or os.getenv("GITHUB_TOKEN", "")
    analyzer = GithubAnalyzer(token)
    repos    = analyzer.get_repos(github_username)

    if not repos:
        return {"error": "GitHub repoları bulunamadı. Kullanıcı adını kontrol et."}

    recent_repos    = sorted(repos, key=lambda x: x["updated_at"], reverse=True)[:max_repos]
    github_evidence = {}

    for repo in recent_repos:
        repo_evidence = analyzer.analyze_repo(repo)
        for skill, evidences in repo_evidence.items():
            existing = set(github_evidence.get(skill, []))
            github_evidence[skill] = list(existing | set(evidences))

    verifier = Verifier()
    result   = verifier.verify(cv_skills, github_evidence)

    return {
        "cv_skills":    cv_skills,
        "github_found": len(github_evidence),
        "result":       result,
    }