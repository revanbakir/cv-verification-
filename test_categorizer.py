# test_categorizer.py
from app.core.skill_categorizer import SkillCategorizer

categorizer = SkillCategorizer()

test_skills = ["xgboost", "supabase", "tauri", "bun", "astro", "htmx", "deno"]

for skill in test_skills:
    category = categorizer.categorize(skill)
    print(f"{skill:20} → {category}")

    
