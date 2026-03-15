# app/core/verifier.py

class Verifier:

    def verify(self, cv_skills: list, github_skills: list):
        if not cv_skills:
            return 0

        match_count = len(set(cv_skills) & set(github_skills))
        score = match_count / len(cv_skills)

        return round(score * 100, 2)