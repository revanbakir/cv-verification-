import os
from dotenv import load_dotenv
from app.core.github_analyzer import GithubAnalyzer
from app.ml.skill_extractor import SkillExtractor

def run_test():
    load_dotenv()
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        print("UYARI: GITHUB_TOKEN bulunamadı, rate limit'e takılabilirsiniz!")

    analyzer = GithubAnalyzer(token)
    extractor = SkillExtractor()
    username = "umithavare" # Kendi kullanıcı adın

    print(f"--- {username} İçin Analiz Başlıyor ---")
    
    # 1. Repoları Getir
    repos = analyzer.get_repos(username)
    print(f"Toplam Repo Sayısı: {len(repos)}")

    raw_git_skills = set()

    # 2. Dil Bilgisi (API'den hızlıca)
    languages = analyzer.extract_languages(repos)
    raw_git_skills.update(languages)

    # 3. Derinlemesine Dosya Analizi (Sadece son güncellenen 3 repo)
    # Hız ve Rate Limit için en güncel projelere odaklanıyoruz
    sorted_repos = sorted(repos, key=lambda x: x['updated_at'], reverse=True)[:3]

    for repo in sorted_repos:
        print(f"İnceleniyor: {repo['name']}...")
        files = analyzer.get_repo_contents_recursive(repo["owner"]["login"], repo["name"], max_depth=2)
        
        for file in files:
            found = analyzer.parse_file_by_type(file)
            if found:
                raw_git_skills.update(found)

    # 4. Ontoloji ile Temizle
    final_skills = extractor.extract(list(raw_git_skills))

    print("\n--- ANALİZ SONUCU ---")
    for category, skills in final_skills.items():
        print(f"{category}: {', '.join(skills)}")
        

if __name__ == "__main__":
    run_test()