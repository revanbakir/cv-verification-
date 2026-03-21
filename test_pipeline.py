import os
from dotenv import load_dotenv
from app.core.cv_extractor import CVExtractor
from app.core.github_analyzer import GithubAnalyzer
from app.ml.skill_extractor import SkillExtractor
from app.core.verifier import Verifier

load_dotenv()

CV_PATH = "revan_cv_turkce.pdf"
GITHUB_USERNAME = "revanbakir"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def run_pipeline():
    print("="*55)
    print("          CV - Github Doğrulama Pipeline Testi")
    print("="*55)

    # 1 - CV den skill çıkar
    print("\n[1/4] CV Okunuyor...")
    cv_extractor = CVExtractor()
    with open(CV_PATH, "rb") as f:
        file_bytes = f.read()

    text = cv_extractor.extract_text(file_bytes, filename=CV_PATH)
    cv_skills = cv_extractor.extract_skills(text)

    if not cv_skills:
        print("CV den skill çıkarılamadı. Durduruluyor.")
        return

    print("CV den çıkarılan skiller:")
    for category, skills in cv_skills.items():
        print(f"     {category:25}: {', '.join(skills)}")

    # 2. Github tan skill çıkar
    print(f"\n[2/4] Github analizi başlıyor ({GITHUB_USERNAME})...")
    if not GITHUB_TOKEN:
        print("Github token bulunamadı. Rate limite takılabilirsiniz.")

    analyzer = GithubAnalyzer(GITHUB_TOKEN)
    extractor = SkillExtractor()

    repos = analyzer.get_repos(GITHUB_USERNAME)
    if not repos:
        print("Repo bulunamadı veya kullanıcı adı hatalı. Durduruluyor.")
        return
    print(f"{len(repos)} repo bulundu.")

    raw_github_skills = set(analyzer.extract_languages(repos))

    # En son güncellenen 3 repoyu derinlemesine tara
    sorted_repos = sorted(repos, key=lambda x: x["updated_at"], reverse=True)[:10]
    for repo in sorted_repos:
        print(f"   Inceleniyor: {repo['name']}...")
        files = analyzer.get_repo_contents_recursive(
            repo["owner"]["login"], repo["name"], max_depth=2
        )
        for file in files:
            found = analyzer.parse_file_by_type(file)
            if found:
                raw_github_skills.update(found)

    # Ontoloji ile kategorize et
    categorized_github = extractor.extract(list(raw_github_skills))
    flat_github_skills = [
        skill
        for skills in categorized_github.values()
        for skill in skills
    ]

    print("Github'dan çikarilan skill'ler:")
    for category, skills in categorized_github.items():
        print(f"     {category:25}: {', '.join(skills)}")

    # 3. Dogrulama
    print("\n[3/4] Dogrulama yapiliyor...")
    verifier = Verifier()
    result = verifier.verify(cv_skills, flat_github_skills)

    # 4. Sonuc
    print("\n[4/4] Sonuclar:")
    print("="*55)
    print(f"  Dogrulama Skoru : %{result['score']}")
    print(f"  Eslesen         : {', '.join(result['matched'])  or 'Yok'}")
    print(f"  Eslesmyen       : {', '.join(result['unmatched']) or 'Yok'}")
    print(f"  Bonus (CV disi) : {', '.join(result['bonus'])    or 'Yok'}")
    print("="*55)

if __name__ == "__main__":
    run_pipeline()