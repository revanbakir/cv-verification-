# app/services/analysis_service.py

from app.core.cv_extractor import CVExtractor
from app.core.github_analyzer import GithubAnalyzer
from app.core.timeline_analyzer import TimelineAnalyzer
from app.core.verifier import Verifier


class AnalysisService:

    def __init__(self, github_token: str):
        self.cv_extractor = CVExtractor()
        self.github_analyzer = GithubAnalyzer(github_token)
        self.timeline_analyzer = TimelineAnalyzer()
        self.verifier = Verifier()


    # app/services/analysis_service.py

def analyze(self, cv_text: str, github_username: str, cv_start_year: int):
    cv_skills = self.cv_extractor.extract_skills(cv_text)
    repos = self.github_analyzer.get_repos(github_username)
    
    # 1. Dilleri direkt API'den al (Python, C#, JS vb.)
    all_github_skills = set(self.github_analyzer.extract_languages(repos))

    for repo in repos:
        owner = repo["owner"]["login"]
        repo_name = repo["name"]
        
        # 2. Kritik dosyaları bul (Geliştirdiğimiz derinlik kontrollü hali)
        files = self.github_analyzer.get_repo_contents_recursive(owner, repo_name)
        
        for file in files:
            # 3. Dosyalardan kütüphaneleri çıkar
            found = self.github_analyzer.parse_file_by_type(file)
            if found:
                all_github_skills.update(found)

    github_skills_list = list(all_github_skills)
    # ... skorlama ...

    
    



    