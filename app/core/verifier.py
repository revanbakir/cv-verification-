# app/core/verifier.py

import logging

logger = logging.getLogger(__name__)


class Verifier:

    def verify(self, cv_skills: dict, github_skills: list[str]) -> dict:
        """
        cv_skills   : CVExtractor'dan gelen kategorili dict
                      {"Programming Languages": ["python", "js"], ...}
        github_skills: GithubAnalyzer'dan gelen düz liste
                      ["python", "requests", "django", ...]
        """
        if not cv_skills:
            logger.warning("CV skill listesi boş, doğrulama yapılamıyor.")
            return {"score": 0, "matched": [], "unmatched": [], "bonus": []}

        # CV'deki tüm skill'leri düz listeye çevir (kategori fark etmeksizin)
        all_cv_skills = {
            skill
            for skills in cv_skills.values()
            for skill in skills
        }

        github_set = set(github_skills)

        matched   = list(all_cv_skills & github_set)        # CV'de var, GitHub'da da var
        unmatched = list(all_cv_skills - github_set)        # CV'de var, GitHub'da yok
        bonus     = list(github_set - all_cv_skills)        # CV'de yok ama GitHub'da var

        partial_score = len(matched) + (len(unmatched) * 0.3)
        score = round(partial_score / len(all_cv_skills) * 100, 2) if all_cv_skills else 0

        return {
            "score":     score,      # CV'deki skill'lerin yüzde kaçı GitHub'da kanıtlandı
            "matched":   matched,    # Doğrulanan skill'ler
            "unmatched": unmatched,  # CV'de iddia edilip GitHub'da görülmeyen skill'ler
            "bonus":     bonus,      # CV'de yazmayan ama GitHub'dan çıkan ekstra skill'ler
        }