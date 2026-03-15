from app.core.github_analyzer import GithubAnalyzer
import os
from dotenv import load_dotenv

load_dotenv()
analyzer = GithubAnalyzer(os.getenv("GITHUB_TOKEN"))

username = "ferihadkc"
repos = analyzer.get_repos(username)

print(f"REPO SAYISI: {len(repos)}")

all_found_skills = set()

# Sadece ilk 3 repoyu test etmek hız kazandırabilir
for repo in repos[:5]: 
    print(f"Analyzing {repo['name']}...")
    files = analyzer.get_repo_contents_recursive(repo["owner"]["login"], repo["name"])
    for file in files:
        found = analyzer.parse_file_by_type(file)
        if found:
            all_found_skills.update(found)

print("GITHUB SKILLS FOUND:")
print(list(all_found_skills))