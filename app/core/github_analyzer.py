# app/core/github_analyzer.py
import requests
import xml.etree.ElementTree as ET
import re
import json
import yaml
import os
import anthropic as anthropic_sdk
from dotenv import load_dotenv
load_dotenv()

PACKAGE_NORMALIZE: dict[str, str] = {
    # .NET / ASP.NET
    "swashbuckle.aspnetcore":                    "swagger",
    "microsoft.entityframeworkcore":             "entity framework",
    "microsoft.entityframeworkcore.sqlserver":   "entity framework",
    "microsoft.entityframeworkcore.tools":       "entity framework",
    "microsoft.entityframeworkcore.design":      "entity framework",
    "microsoft.entityframeworkcore.sqlite":      "entity framework",
    "microsoft.entityframeworkcore.inmemory":    "entity framework",
    "microsoft.aspnetcore.openapi":              "asp.net",
    "microsoft.aspnetcore.authentication":       "asp.net",
    "microsoft.aspnetcore.authentication.jwtbearer": "jwt",
    "microsoft.aspnetcore.mvc":                  "asp.net",
    "microsoft.extensions.apidescription.client": ".net",
    "microsoft.extensions.dependencyinjection":  "dependency injection",
    "microsoft.extensions.logging":              ".net",
    "newtonsoft.json":                           "json.net",
    "nswag.apidescription.client":               "openapi",
    "nswag.msbuild":                             "openapi",
    "automapper":                                "automapper",
    "fluentvalidation":                          "fluentvalidation",
    "dapper":                                    "dapper",
    "serilog":                                   "serilog",
    "mediatr":                                   "mediatr",
    "xunit":                                     "xunit",
    "nunit":                                     "nunit",
    "moq":                                       "moq",
    "bogus":                                     "bogus",
    "signalr":                                   "signalr",
    "microsoft.aspnetcore.signalr":              "signalr",
    "hangfire":                                  "hangfire",
    "polly":                                     "polly",
    "stackexchange.redis":                       "redis",
    "mongodb.driver":                            "mongodb",
    "npgsql":                                    "postgresql",
    "mysql.data":                                "mysql",
    "mysqlconnector":                            "mysql",
    # JS / TS
    "react-dom":                                 "react",
    "react-router-dom":                          "react",
    "react-router":                              "react",
    "next":                                      "next.js",
    "tailwindcss":                               "tailwind",
    "eslint-config-next":                        "eslint",
    "eslint-config-prettier":                    "eslint",
    "@eslint/eslintrc":                          "eslint",
    "daisyui":                                   "tailwind",
    "@mui/material":                             "material ui",
    "@chakra-ui/react":                          "chakra ui",
    "axios":                                     "axios",
    "zustand":                                   "zustand",
    "@tanstack/react-query":                     "react query",
    "socket.io":                                 "socket.io",
    "socket.io-client":                          "socket.io",
    "graphql":                                   "graphql",
    "@apollo/client":                            "graphql",
    "apollo-server":                             "graphql",
    "prisma":                                    "prisma",
    "@prisma/client":                            "prisma",
    "typeorm":                                   "typeorm",
    "mongoose":                                  "mongodb",
    "pg":                                        "postgresql",
    "mysql2":                                    "mysql",
    "redis":                                     "redis",
    "ioredis":                                   "redis",
    "jest":                                      "jest",
    "vitest":                                    "vitest",
    "vite":                                      "vite",
    "webpack":                                   "webpack",
    "passport":                                  "passport.js",
    "jsonwebtoken":                              "jwt",
    "zod":                                       "zod",
    # Python
    "scikit-learn":                              "scikit-learn",
    "sklearn":                                   "scikit-learn",
    "pydantic":                                  "pydantic",
    "sqlalchemy":                                "sqlalchemy",
    "alembic":                                   "alembic",
    "celery":                                    "celery",
    "pytest":                                    "pytest",
    "uvicorn":                                   "fastapi",
    "httpx":                                     "httpx",
    "aiohttp":                                   "aiohttp",
    "boto3":                                     "aws",
    "pymongo":                                   "mongodb",
    "psycopg2":                                  "postgresql",
    "psycopg2-binary":                           "postgresql",
    "redis-py":                                  "redis",
    "motor":                                     "mongodb",
    "beanie":                                    "mongodb",
    # Java / Kotlin (Maven artifact IDs)
    "spring-boot-starter-web":                   "spring boot",
    "spring-boot-starter-data-jpa":              "spring boot",
    "spring-boot-starter-security":              "spring boot",
    "spring-boot-starter-test":                  "spring boot",
    "spring-boot-starter-data-mongodb":          "mongodb",
    "spring-boot-starter-data-redis":            "redis",
    "spring-kafka":                              "kafka",
    "lombok":                                    "lombok",
    "mapstruct":                                 "mapstruct",
    "postgresql":                                "postgresql",
    "mysql-connector-java":                      "mysql",
    "h2":                                        "h2",
    # Go modules
    "gin-gonic/gin":                             "gin",
    "go-chi/chi":                                "chi",
    "gorilla/mux":                               "gorilla mux",
    "gorm.io/gorm":                              "gorm",
    "gorm.io/driver/postgres":                   "postgresql",
    "gorm.io/driver/mysql":                      "mysql",
    "go-redis/redis":                            "redis",
    "mongodb/mongo-go-driver":                   "mongodb",
    "golang-jwt/jwt":                            "jwt",
    "uber-go/zap":                               "zap",
    "stretchr/testify":                          "testify",
    # Ruby (Gemfile)
    "rails":                                     "ruby on rails",
    "sinatra":                                   "sinatra",
    "devise":                                    "devise",
    "pg":                                        "postgresql",
    "mongoid":                                   "mongodb",
    "sidekiq":                                   "sidekiq",
    "rspec-rails":                               "rspec",
    # AI / ML kütüphaneleri - Python
    "torch":                                     "pytorch",
    "torchaudio":                                "pytorch",
    "torchvision":                               "pytorch",
    "tensorflow":                                "tensorflow",
    "tensorflow-cpu":                            "tensorflow",
    "keras":                                     "keras",
    "transformers":                              "huggingface",
    "datasets":                                  "huggingface",
    "huggingface-hub":                           "huggingface",
    "diffusers":                                 "huggingface",
    "accelerate":                                "huggingface",
    "peft":                                      "huggingface",
    "trl":                                       "huggingface",
    "sentence-transformers":                     "huggingface",
    "langchain":                                 "langchain",
    "langchain-core":                            "langchain",
    "langchain-community":                       "langchain",
    "langchain-openai":                          "langchain",
    "langchain-anthropic":                       "langchain",
    "langgraph":                                 "langchain",
    "llama-index":                               "llama index",
    "llama_index":                               "llama index",
    "llama-cpp-python":                          "llama.cpp",
    "openai":                                    "openai",
    "anthropic":                                 "anthropic",
    "google-generativeai":                       "gemini",
    "google-cloud-aiplatform":                   "vertex ai",
    "cohere":                                    "cohere",
    "mistralai":                                 "mistral",
    "groq":                                      "groq",
    "together":                                  "together ai",
    "replicate":                                 "replicate",
    "tiktoken":                                  "openai",
    "chromadb":                                  "chromadb",
    "pinecone-client":                           "pinecone",
    "pinecone":                                  "pinecone",
    "weaviate-client":                           "weaviate",
    "qdrant-client":                             "qdrant",
    "faiss-cpu":                                 "faiss",
    "faiss-gpu":                                 "faiss",
    "xgboost":                                   "xgboost",
    "lightgbm":                                  "lightgbm",
    "catboost":                                  "catboost",
    "optuna":                                    "optuna",
    "spacy":                                     "spacy",
    "nltk":                                      "nltk",
    "gensim":                                    "gensim",
    "opencv-python":                             "opencv",
    "opencv-python-headless":                    "opencv",
    # AI / ML - JS
    "@anthropic-ai/sdk":                         "anthropic",
    "@google/generative-ai":                     "gemini",
    "@langchain/core":                           "langchain",
    "@langchain/openai":                         "langchain",
    "@langchain/anthropic":                      "langchain",
    "langchain":                                 "langchain",
    "llamaindex":                                "llama index",
    "ollama":                                    "ollama",
    "onnxruntime-web":                           "onnx",
    "@tensorflow/tfjs":                          "tensorflow",
    # AI / ML - .NET
    "microsoft.ml":                              "ml.net",
    "microsoft.semantickernel":                  "semantic kernel",
    "microsoft.semantickernel.core":             "semantic kernel",
    "azure.ai.openai":                           "openai",
    "betalgo.openai":                            "openai",
    "microsoft.aspnetcore.authentication.jwtbearer": "jwt",

    # Rust (Cargo.toml)
    "actix-web":                                 "actix",
    "axum":                                      "axum",
    "tokio":                                     "tokio",
    "serde":                                     "serde",
    "sqlx":                                      "sqlx",
    "diesel":                                    "diesel",
    "reqwest":                                   "reqwest",
}

SKIP_PREFIXES = (
    "@types/", "babel-", "postcss", "@testing-library",
    "webpack-", "loader-", "css-", "style-", "file-",
)

# Repo language → skill mapping
LANGUAGE_MAP = {
    "python":     "python",
    "javascript": "javascript",
    "typescript": "typescript",
    "java":       "java",
    "kotlin":     "kotlin",
    "c#":         "c#",
    "go":         "go",
    "rust":       "rust",
    "ruby":       "ruby",
    "swift":      "swift",
    "dart":       "dart",
    "php":        "php",
    "scala":      "scala",
    "c++":        "c++",
    "c":          "c",
    "r":          "r",
    "shell":      "bash",
}

# docker-compose image → skill
DOCKER_IMAGE_MAP = {
    "postgres":    "postgresql",
    "mysql":       "mysql",
    "mongo":       "mongodb",
    "redis":       "redis",
    "rabbitmq":    "rabbitmq",
    "kafka":       "kafka",
    "zookeeper":   "kafka",
    "nginx":       "nginx",
    "elasticsearch": "elasticsearch",
    "kibana":      "elasticsearch",
    "grafana":     "grafana",
    "prometheus":  "prometheus",
    "minio":       "minio",
    "keycloak":    "keycloak",
}

MANIFEST_FILES = {
    "requirements.txt", "package.json", "dockerfile",
    "docker-compose.yml", "docker-compose.yaml",
    ".env.example", "pom.xml", "build.gradle",
    "build.gradle.kts", "go.mod", "cargo.toml",
    "gemfile", "pubspec.yaml", "pyproject.toml",
    "packages.config",
}

INFRA_EXTENSIONS = {".tf", ".csproj", ".sh"}
CI_EXTENSIONS   = {".yaml", ".yml"}


class GithubAnalyzer:

    def __init__(self, token: str = None):
        self.token = token
        self.base_url = "https://api.github.com"
        self.headers = {"Authorization": f"Bearer {self.token}"} if token else {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_repos(self, username: str) -> list:
        url = f"{self.base_url}/users/{username}/repos?per_page=100"
        r = requests.get(url, headers=self.headers)
        return r.json() if r.status_code == 200 else []

    def analyze_repo(self, repo: dict) -> dict[str, list[str]]:
        """
        Tek bir repo için skill evidence toplar.
        Dönen format: {"skill": ["direct", "infra", ...], ...}
        """
        evidence: dict[str, list[str]] = {}

        owner = repo["owner"]["login"]
        name  = repo["name"]

        # 1. Repo metadata (API çağrısı yok, zaten elimizde)
        self._extract_from_metadata(repo, evidence)

        # 2. Dosya listesini al (1 API çağrısı)
        files = self._get_relevant_files(owner, name)

        # 3. Her dosyayı parse et
        for f in files:
            self._parse_file(f, evidence)

        return evidence

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------

    def _extract_from_metadata(self, repo: dict, evidence: dict):
        # Ana dil
        lang = (repo.get("language") or "").lower()
        if lang in LANGUAGE_MAP:
            self._add(evidence, LANGUAGE_MAP[lang], "metadata")

        # Topics (github repo etiketleri)
        for topic in repo.get("topics") or []:
            self._add(evidence, topic.lower(), "metadata")

    # ------------------------------------------------------------------
    # File discovery
    # ------------------------------------------------------------------

    def _get_relevant_files(self, owner: str, repo: str, path="", depth=0, max_depth=2) -> list:
        if depth > max_depth:
            return []

        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        r = requests.get(url, headers=self.headers)
        if r.status_code != 200:
            return []

        items = []
        for item in r.json():
            name_lower = item["name"].lower()
            ext = "." + name_lower.rsplit(".", 1)[-1] if "." in name_lower else ""

            if item["type"] == "file":
                is_manifest  = name_lower in MANIFEST_FILES
                is_infra     = ext in INFRA_EXTENSIONS
                is_ci        = ext in CI_EXTENSIONS and ".github/workflows" in item["path"].lower()
                is_readme    = name_lower in ("readme.md", "readme.rst", "readme.txt")

                if is_manifest or is_infra or is_ci or is_readme:
                    items.append(item)

            elif item["type"] == "dir":
                if name_lower not in {"node_modules", "venv", ".git", "__pycache__", "obj", "bin", "dist", "build"}:
                    items.extend(
                        self._get_relevant_files(owner, repo, item["path"], depth + 1, max_depth)
                    )
        return items

    # ------------------------------------------------------------------
    # File parsers (dispatcher)
    # ------------------------------------------------------------------

    def _parse_file(self, file_item: dict, evidence: dict):
        filename = file_item["name"].lower()
        file_path = file_item["path"].lower()

        content = self._fetch_text(file_item.get("download_url"))
        if content is None:
            return

        # Manifest dispatch
        if filename == "requirements.txt":
            self._parse_requirements(content, evidence)
        elif filename == "package.json":
            self._parse_package_json(content, evidence)
        elif filename.endswith(".csproj") or filename == "packages.config":
            self._parse_csproj(content, evidence)
        elif filename == "pom.xml":
            self._parse_pom(content, evidence)
        elif filename in ("build.gradle", "build.gradle.kts"):
            self._parse_gradle(content, evidence)
        elif filename == "go.mod":
            self._parse_go_mod(content, evidence)
        elif filename == "cargo.toml":
            self._parse_cargo(content, evidence)
        elif filename == "gemfile":
            self._parse_gemfile(content, evidence)
        elif filename == "pubspec.yaml":
            self._parse_pubspec(content, evidence)
        elif filename == "pyproject.toml":
            self._parse_pyproject(content, evidence)
        elif filename in ("docker-compose.yml", "docker-compose.yaml"):
            self._parse_docker_compose(content, evidence)
        elif "dockerfile" in filename:
            self._add(evidence, "docker", "infra")
        elif filename.endswith(".tf"):
            self._parse_terraform(content, evidence)
        elif ".github/workflows" in file_path and filename.endswith((".yml", ".yaml")):
            self._parse_github_actions(content, evidence)
        elif "env" in filename:
            self._parse_env(content, evidence)
        elif filename.endswith((".md", ".rst", ".txt")) and "readme" in filename:
            self._parse_readme(content, evidence)

    # ------------------------------------------------------------------
    # Individual parsers
    # ------------------------------------------------------------------

    def _parse_requirements(self, content: str, evidence: dict):
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith(("#", "-e", "-r")):
                continue
            pkg = re.split(r"[=><!;\[]", line)[0].strip().lower()
            self._add_pkg(evidence, pkg, "direct")

    def _parse_package_json(self, content: str, evidence: dict):
        try:
            data = json.loads(content)
            deps = {**data.get("dependencies", {}), **data.get("devDependencies", {})}
            for pkg in deps:
                self._add_pkg(evidence, pkg.lower(), "direct")
        except Exception:
            pass

    def _parse_csproj(self, content: str, evidence: dict):
        try:
            root = ET.fromstring(content)
            for pkg in root.findall(".//*[@Include]"):
                name = pkg.attrib.get("Include", "").lower()
                if name:
                    self._add_pkg(evidence, name, "direct")
        except Exception:
            pass
        self._add(evidence, "c#", "direct")
        self._add(evidence, ".net", "direct")

    def _parse_pom(self, content: str, evidence: dict):
        try:
            # namespace'i sil
            content_clean = re.sub(r'\sxmlns="[^"]+"', '', content)
            root = ET.fromstring(content_clean)
            for dep in root.findall(".//dependency"):
                artifact = dep.findtext("artifactId", "").lower().strip()
                if artifact:
                    self._add_pkg(evidence, artifact, "direct")
        except Exception:
            pass
        self._add(evidence, "java", "metadata")

    def _parse_gradle(self, content: str, evidence: dict):
        # implementation 'group:artifact:version' veya ("group:artifact:version")
        for match in re.finditer(r'''["'][\w.\-]+:([\w.\-]+):[\w.\-]+(["'])''', content):
            artifact = match.group(1).lower()
            self._add_pkg(evidence, artifact, "direct")
        self._add(evidence, "java", "metadata")

    def _parse_go_mod(self, content: str, evidence: dict):
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("require") or line.startswith("//") or not line:
                continue
            parts = line.split()
            if parts:
                module = parts[0].lower()
                # sadece son iki segment önemli: github.com/gin-gonic/gin → gin-gonic/gin
                segments = module.split("/")
                key = "/".join(segments[-2:]) if len(segments) >= 2 else segments[-1]
                self._add_pkg(evidence, key, "direct")
        self._add(evidence, "go", "metadata")

    def _parse_cargo(self, content: str, evidence: dict):
        for line in content.splitlines():
            m = re.match(r'^([\w-]+)\s*=', line.strip())
            if m:
                pkg = m.group(1).lower()
                if pkg not in ("name", "version", "edition", "authors", "description"):
                    self._add_pkg(evidence, pkg, "direct")
        self._add(evidence, "rust", "metadata")

    def _parse_gemfile(self, content: str, evidence: dict):
        for line in content.splitlines():
            m = re.match(r'''^\s*gem\s+['"]([^'"]+)['"]''', line)
            if m:
                self._add_pkg(evidence, m.group(1).lower(), "direct")
        self._add(evidence, "ruby", "metadata")

    def _parse_pubspec(self, content: str, evidence: dict):
        try:
            data = yaml.safe_load(content)
            deps = {**(data.get("dependencies") or {}), **(data.get("dev_dependencies") or {})}
            for pkg in deps:
                if pkg != "flutter" and pkg != "sdk":
                    self._add_pkg(evidence, pkg.lower(), "direct")
        except Exception:
            pass
        self._add(evidence, "flutter", "metadata")
        self._add(evidence, "dart", "metadata")

    def _parse_pyproject(self, content: str, evidence: dict):
        # [tool.poetry.dependencies] veya [project] dependencies
        for line in content.splitlines():
            m = re.match(r'^([\w\-]+)\s*[=><!\[]', line.strip())
            if m:
                pkg = m.group(1).lower()
                if pkg not in ("python", "name", "version", "description"):
                    self._add_pkg(evidence, pkg, "direct")
        self._add(evidence, "python", "metadata")

    def _parse_docker_compose(self, content: str, evidence: dict):
        self._add(evidence, "docker", "infra")
        # image: redis:alpine → redis
        for match in re.finditer(r'image:\s*([^\s:]+)', content.lower()):
            image = match.group(1).split("/")[-1]  # registry prefix'ini at
            for key, skill in DOCKER_IMAGE_MAP.items():
                if image.startswith(key):
                    self._add(evidence, skill, "infra")
                    break

    def _parse_terraform(self, content: str, evidence: dict):
        self._add(evidence, "terraform", "infra")
        for p in re.findall(r'provider\s+"([^"]+)"', content.lower()):
            self._add(evidence, p, "infra")

    def _parse_github_actions(self, content: str, evidence: dict):
        mapping = {
            "aws-actions":          "aws",
            "google-github-actions": "gcp",
            "azure/":               "azure",
            "docker/":              "docker",
            "actions/setup-node":   "node.js",
            "actions/setup-python": "python",
            "actions/setup-java":   "java",
            "gradle/gradle-build":  "java",
        }
        cl = content.lower()
        for key, val in mapping.items():
            if key in cl:
                self._add(evidence, val, "infra")

    def _parse_env(self, content: str, evidence: dict):
        env_map = {
            "AWS_":     "aws",
            "S3_":      "aws",
            "KAFKA":    "kafka",
            "MONGODB":  "mongodb",
            "REDIS":    "redis",
            "POSTGRES": "postgresql",
            "MYSQL":    "mysql",
            "ELASTIC":  "elasticsearch",
            "AZURE_":   "azure",
            "GCP_":     "gcp",
        }
        for key, val in env_map.items():
            if key in content:
                self._add(evidence, val, "config")


    def _parse_readme(self, content: str, evidence: dict):
        if not content or len(content.strip()) < 50:
            return
        snippet = content[:3000]
        try:
            client = anthropic_sdk.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": (
                         "Bu README'den sadece şunları listele:\n"
                         "- Programlama dilleri\n"
                         "- Framework isimleri (kısa: 'ASP.NET' değil 'asp.net', "
                          "'Entity Framework' değil 'entity framework')\n"
                        "- Veritabanı isimleri\n"
                        "- Cloud/DevOps araçları\n\n"
                        "HER SATIRA TEK kelime/kısa isim yaz. "
                        "Birleşik string YAZMA ('asp.net web api' değil → 'asp.net').\n"
                        "Genel kavramları YAZMA (CRUD, REST, API, microservice).\n\n"
                        f"README:\n{snippet}"
                    )
                }]
            )
            for line in response.content[0].text.strip().splitlines():
                skill = line.strip().lstrip("-•* ").lower()
                # Çok uzun stringler birleşik yazılmış demektir, atla
                if skill and 2 <= len(skill) <= 30:
                    self._add(evidence, skill, "mention")
        except Exception as e:
            print(f"README analiz hatası: {e}")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _fetch_text(self, url: str | None) -> str | None:
        if not url:
            return None
        try:
            r = requests.get(url, headers=self.headers, timeout=10)
            return r.text if r.status_code == 200 else None
        except Exception:
            return None

    def _normalize_package(self, pkg: str) -> str | None:
        pkg_lower = pkg.lower().strip()
        if any(pkg_lower.startswith(p) for p in SKIP_PREFIXES):
            return None
        return PACKAGE_NORMALIZE.get(pkg_lower, pkg_lower)

    def _add(self, evidence: dict, skill: str, evidence_type: str):
        skill = skill.lower().strip()
        if not skill or len(skill) < 2:
            return
        if skill not in evidence:
            evidence[skill] = []
        if evidence_type not in evidence[skill]:
            evidence[skill].append(evidence_type)

    def _add_pkg(self, evidence: dict, pkg: str, evidence_type: str):
        normalized = self._normalize_package(pkg)
        if normalized:
            self._add(evidence, normalized, evidence_type)


    # ------------------------------------------------------------------
    # Legacy compat (test_pipeline.py'daki eski çağrılar için)
    # ------------------------------------------------------------------

    def get_repo_contents_recursive(self, owner, repo, path="", depth=0, max_depth=2):
        return self._get_relevant_files(owner, repo, path, depth, max_depth)

    def parse_file_by_type(self, file_item):
        evidence = {}
        self._parse_file(file_item, evidence)
        return evidence
    




    