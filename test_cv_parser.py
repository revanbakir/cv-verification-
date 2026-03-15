from app.services.cv_parser import CVParser
from app.ml.skill_extractor import SkillExtractor

parser = CVParser()

text = parser.parse("revan_cv_turkce.pdf")

extractor = SkillExtractor()

skills = extractor.extract(text)

print(skills)

