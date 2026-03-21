# app/services/analysis_service.py

import logging
from app.core.cv_extractor import CVExtractor
from app.core.github_analyzer import GithubAnalyzer
from app.core.timeline_analyzer import TimelineAnalyzer
from app.core.verifier import Verifier

logger = logging.getLogger(__name__)


class AnalysisService:

    def __init__(self, github_token: str):
        self.cv_extractor = CVExtractor()
        self.github_analyzer = GithubAnalyzer(github_token)
        self.timeline_analyzer = TimelineAnalyzer()
        self.verifier = Verifier()

    def analyze(self, cv_text: str, github_username: str, cv_start_year: int) -> dict:
        # CV'den skill çıkar
        cv_skills = self.cv_extractor.extract_skills(cv_text)

        # GitHub repolarını getir
        repos = self.github_analyzer.get_repos(github_username)
        if not repos:
            logger.warning(f"'{github_username}' için repo bulunamadı veya rate limit aşıldı.")
            return {"cv_skills": cv_skills, "github_skills": [], "verified": []}

        # 1. Dilleri direkt API'den al (Python, C#, JS vb.)
        all_github_skills: set[str] = set(self.github_analyzer.extract_languages(repos))

        for repo in repos:
            owner = repo["owner"]["login"]
            repo_name = repo["name"]

            # 2. Kritik dosyaları bul (derinlik kontrollü)
            try:
                files = self.github_analyzer.get_repo_contents_recursive(owner, repo_name)
            except Exception as e:
                logger.error(f"Repo taranamadı ({repo_name}): {e}", exc_info=True)
                continue

            for file in files:
                # 3. Dosyalardan kütüphaneleri çıkar
                found = self.github_analyzer.parse_file_by_type(file)
                if found:
                    all_github_skills.update(found)

        github_skills_list = list(all_github_skills)

        # 4. Doğrulama ve skorlama
        verified = self.verifier.verify(cv_skills, github_skills_list)

        return {
            "cv_skills": cv_skills,
            "github_skills": github_skills_list,
            "verified": verified,
        }