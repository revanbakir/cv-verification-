import logging
import anthropic
import os
import json
import io  
import docx
import pdfplumber
from app.core.skill_categorizer import SkillCategorizer
import spacy
from spacy.matcher import PhraseMatcher

logger = logging.getLogger(__name__)

class CVExtractor:
    def __init__(self):
        self.categorizer = SkillCategorizer()
        self.client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        self.nlp = spacy.load("en_core_web_sm")
        self.matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")

        skill_list = [
            "python", "java", "c#", "javascript", "typescript", "go", "rust",
            "fastapi", "django", "flask", "react", "vue", "angular", "asp.net",
            "postgresql", "mysql", "mongodb", "redis", "sqlite", "sql server",
            "docker", "kubernetes", "aws", "gcp", "azure", "terraform",
            "pandas", "numpy", "scikit-learn", "pytorch", "tensorflow",
            "xgboost", "huggingface", "transformers", "spacy", "nltk",
            "git", "linux", "nginx", "celery", "kafka", "rabbitmq"
        ]
        patterns = [self.nlp.make_doc(skill) for skill in skill_list]
        self.matcher.add("SKILL", patterns)

    def _extraxt_with_spacy(self, text: str) -> list[str]:
        doc = self.nlp(text[:10000])
        matches = self.matcher(doc)
        found = {doc[start:end].text.lower() for _, start, end in matches}
        return list(found)
    
    def _needs_fallback(self, skills: list[str], text: str) -> bool:
        word_count = len(text.split())
        if len(skills) < 5:
            return True
        return False
    
    def extract_skills(self, text: str) -> dict[str, list[str]]:
        if not text or not text.strip():
            return {}
        
        # 1. spacy katmanı
        spacy_skills = self._extraxt_with_spacy(text)
        logger.info(f"spaCy buldu: {len(spacy_skills)} skill")

        # 2. yeterli değilse claude fallback
        if self._needs_fallback(spacy_skills, text):
            logger.info("Claude fallback devreye giriyor...")
            claude_skills = self._get_technical_terms_via_claude(text)
            merged = list(set(spacy_skills) | set(claude_skills))
            logger.info(f"Merge sonrası: {len(merged)} skill")
        else:
            merged = spacy_skills

        # 3. kategorize
        return self.categorizer.categorize_bulk(merged)
    

    def _get_technical_terms_via_claude(self, text: str) -> list[str]:
        truncated_text = text[:8000] 

        prompt = (
           "Sen bir teknik işe alım uzmanısın. Aşağıdaki CV'den AÇIKÇA GEÇEN teknik terimleri çıkar:\n"
           "Metinde geçmeyen hiçbir şeyi ekleme, tahmin yapma.\n\n"
           "1. Programlama dilleri (Python, C#, Java...)\n"
           "2. Framework'ler (ASP.NET, FastAPI, React...)\n"
           "3. Veritabanları (SQL Server, PostgreSQL, MongoDB...)\n"
           "4. Cloud/DevOps araçları (AWS, Docker, Kubernetes...)\n"
           "5. Tanınmış kütüphaneler (Entity Framework, Pandas...)\n\n"
           "ALMA: DbContext, DTO, CRUD, async/await, dependency injection, "
           "RESTful API, Web API gibi pattern/kavram/mimari terimlerini.\n"
           "ALMA: pattern/kavram/mimari terimleri, Soft skill, şehir, tarih, eğitim bilgisi.\n"
           "Metinde hiç teknik terim yoksa sadece 'YOK' yaz.\n"
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
            
            content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    content +=block.text
                    
            terms = [t.strip().lower() for t in content.split(",") if len(t.strip()) > 1]
            if terms == ["yok"]:
                return []
            text_lower = text.lower()
            verified = [t for t in terms if t in text_lower]
            return list(set(verified))

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

    # test 1. spacy yeterli olmalı
    test_spacy = "Python and FastAPI developer with AWS and Docker experience. Uses PostgreSQL and MongoDB. Familiar with Redis and Kubernetes."
    print("=== TEST1: spacy yeterliyse cloude cağrılmamalı ===")
    skills = extractor.extract_skills(test_spacy)
    for category, found in skills.items():
        if found:
            print(f"   {category:25}: {', '.join(found)}")

    print()

    #TEST 2: türkçe ifadeler +az skill -> claude fallback tetiklenmeli
    test_fallback = "Makine öğrenmesi alanında deneyimliyim. Derin öğrenme projeleri yaptım. Veri analizi konusunda çalıştım. vue.jsile frontend geliştirme tecrübem var" 
    print ("=== TEST 2: türkçe cv claude fallback tetiklenmeli ===")
    skills2 = extractor.extract_skills(test_fallback)
    for category, found in skills2.items():
        if found:
            print(f"   {category:25}: {', '.join(found)}")

    print()


    #TEST 3: boş içerik
    print("=== TEST 3: boş input -> boş dict dönmeli")
    skills3 = extractor.extract_skills("")
    print(f"   Sonuç: {skills3}")



