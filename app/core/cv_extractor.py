import re

class CVExtractor:

    def extract_text(self, file_bytes: bytes) -> str:
        # Şimdilik sadece dummy bir metin
        return file_bytes.decode("utf-8")

    def extract_skills(self, text: str) -> list:
        skill_keywords = ["python", "fastapi", "sql", "docker", "aws"]

        found_skills = []
        text_lower = text.lower()

        for skill in skill_keywords:
            if skill in text_lower:
                found_skills.append(skill)

        return found_skills
    

if __name__ == "__main__":
    extractor = CVExtractor()
    text = "Python and FastAPI developer with AWS experience"
    skills = extractor.extract_skills(text)
    print(skills)
