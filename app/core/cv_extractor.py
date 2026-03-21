# app/core/cv_extractor.py

import re
import logging

logger = logging.getLogger(__name__)

# SkillExtractor ile aynı ontoloji — tek kaynak of truth
# İleride skills_config.yaml'a taşınabilir
SKILL_ONTOLOGY = {
    "Programming Languages": {
        "python": ["python"],
        "c#": ["c#", "csharp"],
        "javascript": ["javascript", "js", "typescript", "ts"],
        "java": ["java"],
    },
    "Frameworks & Tools": {
        "fastapi": ["fastapi"],
        "django": ["django"],
        ".net": [".net", "dotnet", "asp.net"],
        "react": ["react", "react.js"],
        "docker": ["docker"],
        "kubernetes": ["kubernetes", "k8s"],
    },
    "Cloud & DevOps": {
        "aws": ["aws", "amazon web services"],
        "azure": ["azure"],
        "gcp": ["gcp", "google cloud"],
        "ci/cd": ["ci/cd", "github actions", "jenkins"],
    },
    "Data & ML": {
        "pandas": ["pandas"],
        "scikit-learn": ["scikit-learn", "sklearn"],
        "tensorflow": ["tensorflow"],
        "pytorch": ["pytorch"],
        "numpy": ["numpy"],
        "pyspark": ["pyspark"],
    },
    "Database": {
        "sql": ["sql", "postgresql", "mysql", "sqlite", "sqlserver"],
        "mongodb": ["mongodb", "nosql"],
        "redis": ["redis"],
    },
    
    "AI & NLP": {                  
    "nlp": ["nlp", "doğal dil işleme", "natural language processing"],
    "transformers": ["transformers", "huggingface"],
    }
}


class CVExtractor:

    def extract_text(self, file_bytes: bytes, filename: str = "") -> str:
        """
        Dosya tipine göre metin çıkarır.
        - .pdf  → pdfplumber ile
        - .docx → python-docx ile
        - diğer → UTF-8 decode (test/düz metin için)
        """
        ext = filename.lower().split(".")[-1] if filename else ""

        try:
            if ext == "pdf":
                import pdfplumber, io
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    return "\n".join(
                        page.extract_text() or "" for page in pdf.pages
                    )

            elif ext == "docx":
                import docx, io
                doc = docx.Document(io.BytesIO(file_bytes))
                return "\n".join(p.text for p in doc.paragraphs)

            else:
                # Fallback: düz metin (test senaryoları için)
                return file_bytes.decode("utf-8", errors="ignore")

        except Exception as e:
            logger.error(f"Metin çıkarma hatası ({filename}): {e}", exc_info=True)
            return ""

    def extract_skills(self, text: str) -> dict:
        """
        Metinden skill çıkarır, SKILL_ONTOLOGY'e göre kategorize eder.

        Dönen format (Verifier ile uyumlu):
        {
            "Programming Languages": ["python", "javascript"],
            "Cloud & DevOps": ["aws", "docker"],
            ...
        }
        """
        if not text or not text.strip():
            logger.warning("Boş metin geldi, skill çıkarılamıyor.")
            return {}

        text_lower = text.lower()
        categorized: dict[str, list[str]] = {}

        for category, skills_dict in SKILL_ONTOLOGY.items():
            found_in_category = set()

            for skill_name, variants in skills_dict.items():
                for variant in variants:
                    # Nokta içeren ifadeler (.net, ci/cd) için özel kontrol
                    if any(c in variant for c in [".", "/"]):
                        if variant in text_lower:
                            found_in_category.add(skill_name)
                    else:
                        # Word boundary: "aws" → "drawstring"'de eşleşmesin
                        pattern = r"\b" + re.escape(variant) + r"\b"
                        if re.search(pattern, text_lower):
                            found_in_category.add(skill_name)

            if found_in_category:
                categorized[category] = list(found_in_category)

        return categorized


if __name__ == "__main__":
    extractor = CVExtractor()
    text = "Python and FastAPI developer with AWS and Docker experience. Knows drawstring too."
    skills = extractor.extract_skills(text)

    print("--- Çıkarılan Skill'ler ---")
    for category, found in skills.items():
        print(f"  {category:25}: {', '.join(found)}")

    # Beklenen: aws eşleşmeli, drawstring eşleşmemeli