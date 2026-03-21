# app/ml/skill_extractor.py
import re

class SkillExtractor:
    def __init__(self):
        # Yetenekleri mantıksal gruplara ayırdık
        self.SKILL_ONTOLOGY = {
            "Programming Languages": {
                "python": ["python", "py"],
                "c#": ["c#", "csharp"],
                "javascript": ["javascript", "js", "typescript", "ts"],
                "java": ["java"]
            },
            "Frameworks & Tools": {
                "fastapi": ["fastapi"],
                "django": ["django"],
                ".net": [".net", "dotnet", "asp.net", "entityframework"],
                "react": ["react", "react.js"],
            },
            "Data & ML": {
                "pandas": ["pandas", "pd"],
                "scikit-learn": ["sklearn", "scikit-learn"],
                "tensorflow": ["tensorflow", "tf"],
                "pytorch": ["pytorch"]
            },
            "Database": {
                "sql": ["sql", "postgresql", "mysql", "sqlserver", "sqlite"],
                "mongodb": ["mongodb", "nosql"]
            }
        }

    def extract(self, text_list: list):
        categorized_results = {}
        combined_text = " ".join(text_list).lower()

        for category, skills_dict in self.SKILL_ONTOLOGY.items():
            found_in_category = set()
            
            for skill_name, variants in skills_dict.items():
                for variant in variants:
                    # Nokta gibi özel karakterleri korumak için escape kullanıyoruz
                    pattern = re.escape(variant.lower())
                    if re.search(pattern, combined_text):
                        found_in_category.add(skill_name)
            
            # Eğer bu kategoride bir şey bulunduysa sözlüğe ekle
            if found_in_category:
                categorized_results[category] = list(found_in_category)
                
        return categorized_results