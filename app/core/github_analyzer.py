import requests
import base64
import xml.etree.ElementTree as ET

class GithubAnalyzer:
    def __init__(self, token: str = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {"Authorization": f"Bearer {self.token}"} if token else {}
        # Analiz etmek istediğimiz kritik dosyalar
        self.critical_files = ["requirements.txt", "package.json"]

    def get_repos(self, username: str):
        url = f"{self.base_url}/users/{username}/repos"
        response = requests.get(url, headers=self.headers)
        return response.json() if response.status_code == 200 else []

    def extract_languages(self, repos: list):
        languages = {repo.get("language").lower() for repo in repos if repo.get("language")}
        return list(languages)

    def get_repo_contents_recursive(self, owner, repo, path="", depth=0, max_depth=3):
        """Rate limit dostu derinlik kontrollü tarama"""
        if depth > max_depth:
            return []

        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        response = requests.get(url, headers=self.headers)
        
        if response.status_code != 200:
            return []
        
        contents = response.json()
        all_files = []

        for item in contents:
            if item["type"] == "file":
                # Sadece ilgili uzantıları veya dosyaları listeye ekle (Hız kazandırır)
                if item["name"].lower() in self.critical_files or item["name"].endswith(".csproj"):
                    all_files.append(item)
            elif item["type"] == "dir":
                # Klasör taraması (Derinlik kontrolü ile)
                all_files.extend(self.get_repo_contents_recursive(owner, repo, item["path"], depth + 1, max_depth))
        
        return all_files

    def parse_file_by_type(self, file):
        """Dosya içeriğini okur ve yetenekleri ayıklar"""
        filename = file["name"].lower()
        skills = []
        
        # Dosya içeriğini çek (download_url kullanımı rate limit'i daha az etkiler)
        try:
            res = requests.get(file["download_url"], headers=self.headers)
            if res.status_code != 200: return []
            content = res.text

            if filename == "requirements.txt":
                for line in content.splitlines():
                    if line.strip() and not line.startswith(("#", "-e")):
                        pkg = line.split("==")[0].split(">")[0].split("<")[0].strip().lower()
                        skills.append(pkg)

            elif filename == "package.json":
                import json
                data = json.loads(content)
                deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
                skills.extend([d.lower() for d in deps.keys()])

            elif filename.endswith(".csproj"):
                root = ET.fromstring(content)
                for pkg in root.findall(".//PackageReference"):
                    skills.append(pkg.attrib.get("Include", "").lower())
                skills.extend(["c#", ".net"])

        except Exception as e:
            print(f"Hata ({filename}): {e}")

        return skills