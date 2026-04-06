# test_pipeline.py
import os
from dotenv import load_dotenv
from app.core.cv_extractor import CVExtractor
from app.core.github_analyzer import GithubAnalyzer
from app.core.verifier import Verifier

load_dotenv()

CV_PATH = "revan_cv_turkce.pdf"
GITHUB_USERNAME = "revanbakir"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def run_pipeline():
    print("="*55)
    print("          CV - Github Doğrulama Pipeline Testi")
    print("="*55)

    # 1 - CV
    print("\n[1/4] CV Okunuyor...")
    cv_extractor = CVExtractor()

    with open(CV_PATH, "rb") as f:
        file_bytes = f.read()

    text = cv_extractor.extract_text(file_bytes, filename=CV_PATH)
    cv_skills = cv_extractor.extract_skills(text)

    if not cv_skills:
        print("CV den skill çıkarılamadı.")
        return

    print("CV den çıkarılan skiller:")
    for category, skills in cv_skills.items():
        print(f"{category:25}: {', '.join(skills)}")

    # 2 - GitHub
    print(f"\n[2/4] Github analizi ({GITHUB_USERNAME})")

    analyzer = GithubAnalyzer(GITHUB_TOKEN)
    repos = analyzer.get_repos(GITHUB_USERNAME)

    if not repos:
        print("Repo bulunamadı.")
        return

    github_evidence = {}  # 🔥 EN ÖNEMLİ SATIR

    sorted_repos = sorted(repos, key=lambda x: x["updated_at"], reverse=True)[:10]

    for repo in sorted_repos:
        print(f"   -> {repo['name']}")

        files = analyzer.get_repo_contents_recursive(
            repo["owner"]["login"],
            repo["name"],
            max_depth=2
        )

        for file in files:
            found = analyzer.parse_file_by_type(file)

            if found:
                for skill, evidences in found.items():

                    if skill not in github_evidence:
                        github_evidence[skill] = []

                    github_evidence[skill] = list(set(github_evidence[skill] + evidences))

    print("\nGithub Evidence:")
    for skill, ev in github_evidence.items():
        print(f"{skill:20} -> {ev}")

    # 3 - Doğrulama
    print("\n[3/4] Doğrulama")

    verifier = Verifier()
    result = verifier.verify(cv_skills, github_evidence)

    # 4 - Sonuç
    print("\n[4/4] Sonuçlar")
    print("="*55)

    print(f"Score: %{result['overall_verification_score']}")
    print(f"Toplam Skill: {result['summary']['total_skills_claimed']}")
    print(f"Verified: {result['summary']['verified_count']}")
    print(f"Bonus: {', '.join(result['summary']['bonus_skills']) or 'Yok'}")

    print("\nDetay:")
    for category, items in result["detailed_report"].items():
        print(f"\n{category}")
        for s in items:
            print(f"  - {s['skill']} -> {s['status']} ({s['confidence']})")

if __name__ == "__main__":
    run_pipeline()