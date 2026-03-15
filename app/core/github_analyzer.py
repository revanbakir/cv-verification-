# app/core/github_analyzer.py
import requests
import os

class GithubAnalyzer:

    def __init__(self, token: str = None):
        self.token = token
        self.base_url = "https://api.github.com"

    def get_repos(self, username: str):
        headers = {}
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}
        
        url = f"{self.base_url}/users/{username}/repos"
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        print("GitHub API error:", response.status_code)
        return []

    def extract_languages(self, repos: list):
        languages = set()

        for repo in repos:
            if repo.get("language"):
                languages.add(repo["language"].lower())

        return list(languages)
    
    
    def get_repo_contents_recursive(self, owner, repo, path=""):

        headers = {}
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}

        url = f"{self.base_url}/repos/{owner}/{repo}/contents{path}"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            return []
        
        contents = response.json()
        all_files = []


        for item in contents:
            if item["type"] == "file":
                all_files.append(item)
            elif item["type"] == "dir":
                # klasör varsa recursive aç
                all_files.extend(self.get_repo_contents_recursive(owner, repo, item["path"]))
        return all_files
    
    
    # github apiden repo içindeki dosyaları çeken fonksiyon
    def get_repo_contents(self, owner, repo):

        headers = {}
        if self.token:
            headers = {"Authorization": f"Bearer {self.token}"}

        url = f"{self.base_url}/repos/{owner}/{repo}/contents"

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        
        return []
    

    # dosya tipine göre skill çıkarımı
    # app/core/github_analyzer.py

def parse_file_by_type(self, file):
    filename = file["name"].lower()
    skills = []
    
    # Header hazırlığı (Rate limit için kritik)
    headers = {}
    if self.token:
        headers = {"Authorization": f"Bearer {self.token}"}

    try:
        if filename == "requirements.txt":
            content = requests.get(file["download_url"], headers=headers).text
            for line in content.splitlines():
                if line.strip() and not line.startswith("#"):
                    pkg = line.split("==")[0].split(">")[0].split("<")[0].strip().lower()
                    skills.append(pkg)

        elif filename == "package.json":
            content = requests.get(file["download_url"], headers=headers).json()
            # ... dependencies ve devDependencies mantığın aynı kalsın ...

        elif filename.endswith(".csproj"):
            content = requests.get(file["download_url"], headers=headers).text
            import xml.etree.ElementTree as ET
            root = ET.fromstring(content)
            for pkg in root.findall(".//PackageReference"):
                skills.append(pkg.attrib.get("Include", "").lower())
            # C# projesi olduğunu kesinleştir
            skills.append("c#")
            skills.append(".net")
            
    except Exception as e:
        print(f"Hata oluştu ({filename}):", e)

    return skills

