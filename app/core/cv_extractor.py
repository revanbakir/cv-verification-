import logging
import anthropic
import os
import json
import io  
import docx
import pdfplumber
from app.core.skill_categorizer import SkillCategorizer

logger = logging.getLogger(__name__)

class CVExtractor:
    def __init__(self):
        self.categorizer = SkillCategorizer()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    def extract_skills(self, text: str) -> dict[str, list[str]]:
        if not text or not text.strip():
            return {}

        # 1. ADIM: Claude ile temizleme
        technical_terms = self._get_technical_terms_via_claude(text)
        
        # 2. ADIM: Kategorize etme
        return self.categorizer.categorize_bulk(technical_terms)

    def _get_technical_terms_via_claude(self, text: str) -> list[str]:
        truncated_text = text[:8000] 

        prompt = (
           "Sen bir teknik işe alım uzmanısın. Aşağıdaki CV'den SADECE şunları çıkar:\n"
           "1. Programlama dilleri (Python, C#, Java...)\n"
           "2. Framework'ler (ASP.NET, FastAPI, React...)\n"
           "3. Veritabanları (SQL Server, PostgreSQL, MongoDB...)\n"
           "4. Cloud/DevOps araçları (AWS, Docker, Kubernetes...)\n"
           "5. Tanınmış kütüphaneler (Entity Framework, Pandas...)\n\n"
           "ALMA: DbContext, DTO, CRUD, async/await, dependency injection, "
           "RESTful API, Web API gibi pattern/kavram/mimari terimlerini.\n"
           "ALMA: Soft skill, şehir, tarih, eğitim bilgisi.\n"
           "Sadece virgülle ayrılmış liste döndür, açıklama yapma.\n\n"
           f"CV:\n{truncated_text}"
        )

        try:
            # Model ismini güncelledim: claude-3-haiku-20240307 (en stabil hızlı model)
            response = self.client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            content = response.content[0].text
            terms = [t.strip().lower() for t in content.split(",") if len(t.strip()) > 1]
            return list(set(terms))

        except Exception as e:
            logger.error(f"Claude extraction hatası: {e}")
            return []

    def extract_text(self, file_bytes: bytes, filename: str = "") -> str:
        ext = filename.lower().split(".")[-1] if filename else ""

        try:
            if ext == "pdf":
                # io.BytesIO doğru kullanımı
                with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                    return "\n".join(page.extract_text() or "" for page in pdf.pages)

            elif ext == "docx":
                # io.BytesIO doğru kullanımı
                doc = docx.Document(io.BytesIO(file_bytes))
                return "\n".join(p.text for p in doc.paragraphs)

            else:
                return file_bytes.decode("utf-8", errors="ignore")

        except Exception as e:
            logger.error(f"Metin cikartma hatasi ({filename}): {e}")
            return ""

if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    extractor = CVExtractor()
    test_text = "Python and FastAPI developer with AWS and Docker experience. Uses PostgreSQL and MongoDB."
    skills = extractor.extract_skills(test_text)

    print("--- Cikarilan Skill'ler ---")
    for category, found in skills.items():
        print(f"  {category:25}: {', '.join(found)}")