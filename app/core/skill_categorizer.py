# app/core/skill_categorizer.py

import json
import logging
from pathlib import Path
import anthropic
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

CACHE_PATH = Path("skill_cache.json")

CATEGORIES = [
    "Programming Languages", "Frontend", "Backend", "Mobile",
    "Data & ML", "AI & NLP", "Database", "Cloud & DevOps",
    "Game Development", "Embedded & Hardware", "Security",
    "Tools & Practices", "Blockchain", "Other"
]

BASE_ONTOLOGY: dict[str, str] = {
    "python": "Programming Languages",
    "javascript": "Programming Languages",
    "typescript": "Programming Languages",
    "java": "Programming Languages",
    "c#": "Programming Languages",
    "c++": "Programming Languages",
    "go": "Programming Languages",
    "rust": "Programming Languages",
    "kotlin": "Programming Languages",
    "swift": "Programming Languages",
    "ruby": "Programming Languages",
    "php": "Programming Languages",
    "scala": "Programming Languages",
    "dart": "Programming Languages",
    "bash": "Programming Languages",
    "react": "Frontend",
    "vue": "Frontend",
    "angular": "Frontend",
    "next.js": "Frontend",
    "svelte": "Frontend",
    "html": "Frontend",
    "css": "Frontend",
    "tailwind": "Frontend",
    "bootstrap": "Frontend",
    "redux": "Frontend",
    "fastapi": "Backend",
    "django": "Backend",
    "flask": "Backend",
    "express": "Backend",
    "spring": "Backend",
    "laravel": "Backend",
    "rails": "Backend",
    "asp.net": "Backend",
    "nestjs": "Backend",
    "flutter": "Mobile",
    "react native": "Mobile",
    "android": "Mobile",
    "ios": "Mobile",
    "pandas": "Data & ML",
    "numpy": "Data & ML",
    "scikit-learn": "Data & ML",
    "sklearn": "Data & ML",
    "tensorflow": "Data & ML",
    "pytorch": "Data & ML",
    "keras": "Data & ML",
    "pyspark": "Data & ML",
    "xgboost": "Data & ML",
    "opencv": "Data & ML",
    "huggingface": "AI & NLP",
    "transformers": "AI & NLP",
    "langchain": "AI & NLP",
    "openai": "AI & NLP",
    "nltk": "AI & NLP",
    "spacy": "AI & NLP",
    "postgresql": "Database",
    "mysql": "Database",
    "sqlite": "Database",
    "mongodb": "Database",
    "redis": "Database",
    "elasticsearch": "Database",
    "firebase": "Database",
    "supabase": "Database",
    "dynamodb": "Database",
    "cassandra": "Database",
    "docker": "Cloud & DevOps",
    "kubernetes": "Cloud & DevOps",
    "aws": "Cloud & DevOps",
    "azure": "Cloud & DevOps",
    "gcp": "Cloud & DevOps",
    "terraform": "Cloud & DevOps",
    "ansible": "Cloud & DevOps",
    "jenkins": "Cloud & DevOps",
    "github actions": "Cloud & DevOps",
    "linux": "Cloud & DevOps",
    "kafka": "Cloud & DevOps",
    "unity": "Game Development",
    "unreal": "Game Development",
    "godot": "Game Development",
    "arduino": "Embedded & Hardware",
    "raspberry pi": "Embedded & Hardware",
    "jwt": "Security",
    "oauth": "Security",
    "git": "Tools & Practices",
    "rest": "Tools & Practices",
    "graphql": "Tools & Practices",
    "microservices": "Tools & Practices",
    "solidity": "Blockchain",
    "web3": "Blockchain",
}

COMMON_NOISE = {
    "haziranda", "aralik", "temmuz", "deneyimi", "bilgisi",
    "yla", "tesi", "mda", "subat", "mart", "nisan", "mayis",
    "haziran", "eylul", "ekim"
}


class SkillCategorizer:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        self.cache = self._load_cache()

    def _load_cache(self) -> dict:
        if CACHE_PATH.exists():
            return json.loads(CACHE_PATH.read_text(encoding="utf-8"))
        return {}

    def _save_cache(self):
        CACHE_PATH.write_text(
            json.dumps(self.cache, indent=2, ensure_ascii=False),
            encoding="utf-8"
        )

    def _normalize(self, skill: str) -> str:
        return skill.lower().strip()

    def _is_noise(self, key: str) -> bool:
        if len(key) < 3 and key not in {"c", "r", "go", "js", "ts"}:
            return True
        if key in COMMON_NOISE:
            return True
        return False

    def _lookup_local(self, key: str) -> str | None:
        """Ontoloji veya cache'de varsa döndür, yoksa None."""
        if key in BASE_ONTOLOGY:
            return BASE_ONTOLOGY[key]
        if key in self.cache:
            return self.cache[key]
        return None

    def _ask_claude_batch(self, skills: list[str]) -> dict[str, str]:
        """
        Bilinmeyen skill'leri TEK bir Claude çağrısıyla kategorize eder.
        Dönen format: {"skill": "Category", ...}
        """
        if not skills:
            return {}

        skills_list = "\n".join(f"- {s}" for s in skills)
        categories_str = ", ".join(CATEGORIES)

        prompt = (
            f"Aşağıdaki her girdi için, gerçek bir yazılım teknolojisi/kütüphane/araç ise "
            f"şu kategorilerden birini ata: {categories_str}\n"
            f"Teknoloji değilse 'Other' yaz.\n\n"
            f"Her satır için tam olarak şu formatta yanıt ver: skill: Kategori\n\n"
            f"Skill listesi:\n{skills_list}"
        )

        try:
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}]
            )

            result = {}
            for line in response.content[0].text.strip().splitlines():
                if ":" not in line:
                    continue
                parts = line.split(":", 1)
                skill_key = parts[0].strip().lstrip("- ").lower()
                category = parts[1].strip()
                if category not in CATEGORIES:
                    category = "Other"
                result[skill_key] = category

            logger.info(f"Claude batch: {len(skills)} skill → {len(result)} sonuç")
            return result

        except Exception as e:
            logger.error(f"Claude batch hatası: {e}", exc_info=True)
            return {}

    def categorize_bulk(self, skills: list[str]) -> dict[str, list[str]]:
        """
        Skill listesini kategorize eder.
        - Bilinen skill'ler: ontoloji/cache'den (API çağrısı yok)
        - Bilinmeyenler: tek bir Claude çağrısıyla toplu kategorize edilir
        """
        result: dict[str, list[str]] = {}
        unknown = []

        # 1. Önce local'e bak
        for skill in skills:
            if not skill or len(skill) < 2:
                continue

            key = self._normalize(skill)

            if self._is_noise(key):
                continue

            local = self._lookup_local(key)
            if local:
                if local != "Other":
                    result.setdefault(local, []).append(skill)
            else:
                unknown.append(skill)

        # 2. Bilinmeyenleri tek seferde Claude'a sor
        if unknown:
            logger.info(f"Claude'a gönderilen bilinmeyen skill sayısı: {len(unknown)}")
            batch_result = self._ask_claude_batch(unknown)

            for skill in unknown:
                key = self._normalize(skill)
                category = batch_result.get(key, "Other")
                self.cache[key] = category

                if category != "Other":
                    result.setdefault(category, []).append(skill)

            self._save_cache()

        return result