class SkillExtractor:

    def __init__(self):

        # Yetenekleri kategorize ederek tanımlıyoruz

        self.ontology = {
            "Programming Languages": [
                "python", "c#", "javascript", "java", "sql", "html", "css", "typescript", "c++"
            ],
            "Web Frameworks": [
                "fastapi", "django", "flask", "asp.net", "spring boot", "react", "vue", "angular", "node.js"
            ],
            "Data & Big Data": [
                "pandas", "numpy", "matplotlib", "seaborn", "pyspark", "hadoop", "spark", "scikit-learn"
            ],
            "Machine Learning & AI": [
                "tensorflow", "pytorch", "keras", "nlp", "nltk", "spacy", "xgboost", "neural networks", "opencv"
            ],
            "Database": [
                "mongodb", "pymongo", "postgresql", "mysql", "sqlite", "redis", "elasticsearch", "oracle"
            ],
            "Business Intelligence": [
                "sap analytics cloud", "sac", "power bi", "tableau", "excel"
            ],
            "Software Architecture & Design": [
                "uml", "visual paradigm", "design patterns", "microservices", "rest api"
            ],
            "Testing & QA": [
                "junit", "selenium", "pytest", "unit testing", "integration testing"
            ],
            "DevOps & Tools": [
                "docker", "kubernetes", "git", "github", "aws", "amazon bedrock", "uvicorn", "pydantic", "requests", "dotenv"
            ]
        }

    def extract(self, raw_skills):

        found_skills = {}

        # Küçük harfe çevirerek karşılaştırıyoruz (Case-insensitivity)
        raw_skills_lower = [s.lower() for s in raw_skills]

        for category, keywords in self.ontology.items():
            # Ham veri içinde bu kategoriden eşleşenleri bul
            matches = [k for k in keywords if k in raw_skills_lower]

            if matches:
                # Ekranda daha güzel görünmesi için isimleri düzeltelim (capitalize)
                found_skills[category] = [m.capitalize() for m in matches]

        return found_skills