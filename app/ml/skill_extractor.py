import re

class SkillExtractor:

    def __init__(self):

        self.SKILL_ONTOLOGY = {
            "python": ["python"],
            "fastapi": ["fastapi"],
            "django": ["django"],
            "flask": ["flask"],
            "javascript": ["javascript", "js"],
            "nodejs": ["node", "nodejs", "node.js"],
            "react": ["react", "reactjs"],
            "sql": ["sql", "mysql", "postgresql"],
            "docker": ["docker"],
            "aws": ["aws", "amazon web services"],
            "c#": ["c#", "csharp"],
            ".net": ["asp.net", "asp.net core", ".net"]
        }

    def extract(self, text: str):

        text = text.lower()

        found_skills = set()

        for skill, variants in self.SKILL_ONTOLOGY.items():

            for variant in variants:

                pattern = r"\b" + re.escape(variant) + r"\b"

                if re.search(pattern, text):
                    found_skills.add(skill)

        return list(found_skills)