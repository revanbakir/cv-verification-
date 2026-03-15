# app/core/timeline_analyzer.py

from datetime import datetime

class TimelineAnalyzer:

    def analyze(self, cv_year: int, github_repos: list):
        if not github_repos:
            return False

        first_repo_year = min(
            datetime.strptime(repo["created_at"], "%Y-%m-%dT%H:%M:%SZ").year
            for repo in github_repos
        )

        return first_repo_year >= cv_year
    