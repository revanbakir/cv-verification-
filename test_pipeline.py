import os
from dotenv import load_dotenv
from app.core.cv_extractor import CVExtractor
from app.core.github_analyzer import GithubAnalyzer
from app.core.verifier import Verifier

load_dotenv()

CV_PATH        = "CV.pdf"
GITHUB_USERNAME = "ferihadkc"
GITHUB_TOKEN   = os.getenv("GITHUB_TOKEN")
MAX_REPOS      = 10   # en güncel kaç repo taransın


def run_pipeline():
    print("=" * 55)
    print("     CV - Github Doğrulama Pipeline Testi")
    print("=" * 55)

    # ----------------------------------------------------------------
    # 1. CV'den skill çıkar
    # ----------------------------------------------------------------
    print("\n[1/4] CV Okunuyor...")

    cv_extractor = CVExtractor()
    with open(CV_PATH, "rb") as f:
        file_bytes = f.read()

    text      = cv_extractor.extract_text(file_bytes, filename=CV_PATH)
    cv_skills = cv_extractor.extract_skills(text)

    if not cv_skills:
        print("  HATA: CV'den skill çıkarılamadı.")
        return

    print("  Çıkarılan skill'ler:")
    for category, skills in cv_skills.items():
        print(f"    {category:<25}: {', '.join(skills)}")

    # ----------------------------------------------------------------
    # 2. GitHub repo'larını tara, evidence topla
    # ----------------------------------------------------------------
    print(f"\n[2/4] Github analizi ({GITHUB_USERNAME})")

    if not GITHUB_TOKEN:
        raise ValueError("GITHUB_TOKEN bulunamadı. .env dosyanı kontrol et.")


    analyzer = GithubAnalyzer(GITHUB_TOKEN)
    repos    = analyzer.get_repos(GITHUB_USERNAME)

    if not repos:
        print("  HATA: Repo bulunamadı. Token veya kullanıcı adını kontrol et.")
        return

    # En son güncellenen MAX_REPOS repo'yu al
    recent_repos   = sorted(repos, key=lambda x: x["updated_at"], reverse=True)[:MAX_REPOS]
    github_evidence: dict[str, list[str]] = {}

    for repo in recent_repos:
        print(f"  -> {repo['name']}")

        # analyze_repo tek çağrıda tüm dosyaları tarar ve evidence döner
        repo_evidence = analyzer.analyze_repo(repo)

        # Repo evidence'ını genel evidence dict'e birleştir
        for skill, evidences in repo_evidence.items():
            existing               = set(github_evidence.get(skill, []))
            github_evidence[skill] = list(existing | set(evidences))

    print(f"\n  Toplam bulunan teknoloji: {len(github_evidence)}")
    print("  Github Evidence:")
    for skill, ev in github_evidence.items():
        print(f"    {skill:<30} -> {ev}")

    # ----------------------------------------------------------------
    # 3. CV skill'lerini GitHub kanıtıyla doğrula
    # ----------------------------------------------------------------
    print("\n[3/4] Doğrulama yapılıyor...")

    verifier = Verifier()
    result   = verifier.verify(cv_skills, github_evidence)

    # ----------------------------------------------------------------
    # 4. Sonuçları yazdır
    # ----------------------------------------------------------------
    print("\n[4/4] Sonuçlar")
    print("=" * 55)

    summary = result["summary"]
    print(f"  Genel Score         : %{result['overall_verification_score']}")
    print(f"  Toplam Skill        : {summary['total_skills_claimed']}")
    print(f"  Verified            : {summary['verified_count']}")
    print(f"  Partially Verified  : {summary.get('partially_verified_count', 0)}")
    print(f"  Unverified          : {summary['total_skills_claimed'] - summary['verified_count'] - summary.get('partially_verified_count', 0)}")

    bonus = summary["bonus_skills"]
    print(f"\n  Bonus Skill'ler ({len(bonus)} adet):")
    if bonus:
        for b in bonus:
            print(f"    + {b}")
    else:
        print("    Yok")

    print("\n  Detaylı Rapor:")
    for category, items in result["detailed_report"].items():
        print(f"\n  [{category}]")
        for s in items:
            icon = "✓" if s["status"] == "verified" else ("~" if s["status"] == "partially_verified" else "✗")
            print(f"    {icon} {s['skill']:<25} {s['status']:<22} (confidence: {s['confidence']})")


if __name__ == "__main__":
    run_pipeline()