import json
import os
import logging
import anthropic

logger = logging.getLogger(__name__)

# CV'den gelen ama doğrulanamaz pattern/kavram terimleri — score hesabına dahil edilmez
SKIP_CV_TERMS = {
    "crud", "dto", "rest", "restful", "mvc", "oop", "solid",
    "design patterns", "microservices", "dependency injection",
    "async/await", "web api", "dbcontext", "repository pattern",
    "clean architecture", "tdd", "bdd", "agile", "scrum", "kanban",
    "ci/cd", "api", "sdk", "orm", "ioc", "di", "ddd",
}

# Canonical skill → bilinen alias/varyantları
SKILL_ALIASES: dict[str, list[str]] = {
    # .NET / C#
    "sql server":           ["ms sql server", "mssql", "sqlserver", "sql server management studio", "ssms"],
    "entity framework":     ["entity framework core", "efcore", "ef core", "ef"],
    "asp.net":              ["asp.net core", "asp.net web api", "aspnetcore", "asp.net mvc"],
    ".net":                 [".net core", ".net framework", ".net 6", ".net 7", ".net 8", "dotnet"],
    "c#":                   ["csharp", "c sharp"],
    "linq":                 ["language integrated query"],
    "signalr":              ["microsoft.aspnetcore.signalr"],
    # JS / TS
    "javascript":           ["js", "es6", "es2015", "ecmascript", "vanilla js"],
    "typescript":           ["ts"],
    "react":                ["react.js", "reactjs"],
    "node.js":              ["node", "nodejs"],
    "next.js":              ["nextjs", "next"],
    "express":              ["express.js", "expressjs"],
    "vue":                  ["vue.js", "vuejs"],
    "angular":              ["angularjs", "angular.js"],
    "socket.io":            ["socketio"],
    # Databases
    "postgresql":           ["postgres", "psql", "pg"],
    "mongodb":              ["mongo"],
    "mysql":                ["mariadb"],
    "redis":                ["ioredis", "redis-py", "stackexchange.redis"],
    "elasticsearch":        ["elastic", "opensearch"],
    "sqlite":               ["sqlite3"],
    # Cloud / DevOps
    "kubernetes":           ["k8s"],
    "github actions":       ["actions/checkout", "github-actions", "github workflow"],
    "aws":                  ["amazon web services", "s3", "ec2", "lambda", "boto3"],
    "gcp":                  ["google cloud", "google cloud platform"],
    "azure":                ["microsoft azure"],
    "docker":               ["dockerfile", "docker-compose", "container"],
    "terraform":            ["tf", "hashicorp"],
    # Python
    "scikit-learn":         ["sklearn"],
    "fastapi":              ["uvicorn"],
    "pytorch":              ["torch"],
    # Java
    "spring boot":          ["spring", "spring framework", "spring mvc"],
    # Misc
    "graphql":              ["apollo", "apollo-server", "apollo client"],
    "jwt":                  ["jsonwebtoken", "json web token"],
    "kafka":                ["apache kafka"],
    "rabbitmq":             ["amqp"],
    "nginx":                ["nginx.conf"],
    "swagger":              ["openapi", "swashbuckle"],
}

# Alias → canonical ters lookup (her alias için canonical'ı bul)
def _build_reverse_aliases() -> dict[str, str]:
    reverse: dict[str, str] = {}
    for canonical, aliases in SKILL_ALIASES.items():
        reverse[canonical] = canonical          # canonical kendisi de aranabilsin
        for alias in aliases:
            reverse[alias] = canonical
    return reverse

REVERSE_ALIASES = _build_reverse_aliases()


class Verifier:
    def __init__(self):
        self.weights = {
            "direct":  1.0,   # requirements.txt, package.json, .csproj
            "infra":   0.8,   # .tf, workflow, dockerfile
            "config":  0.6,   # .env, settings
            "mention": 0.4,   # README.md
        }
        self.master_map = self._load_master_map()

    # ------------------------------------------------------------------
    # Master Map
    # ------------------------------------------------------------------

    def _load_master_map(self) -> dict:
        map_path = os.path.join("app", "data", "master_tech_map.json")
        try:
            if os.path.exists(map_path):
                with open(map_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            logger.warning("master_tech_map.json bulunamadı — sadece alias/birebir eşleşme yapılacak.")
            return {}
        except Exception as e:
            logger.error(f"Master map yükleme hatası: {e}")
            return {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def verify(self, cv_skills_dict: dict, github_evidence: dict) -> dict:
        results: dict = {}
        total_cv_skills = 0
        total_weighted_score = 0.0

        proven_libraries = set(github_evidence.keys())

        for category, skills in cv_skills_dict.items():
            # Kategori içi deduplikasyon
            seen_in_category: set[str] = set()
            category_results = []

            for skill in skills:
                skill_lower = skill.lower().strip()

                # Daha önce bu kategoride işlendiyse atla
                if skill_lower in seen_in_category:
                    continue
                seen_in_category.add(skill_lower)

                # Kavramsal terimler score'a dahil edilmez
                if skill_lower in SKIP_CV_TERMS:
                    logger.debug(f"Skipped CV term: {skill_lower}")
                    continue

                total_cv_skills += 1
                best_weight, found_sources = self._find_in_evidence(
                    skill_lower, github_evidence, proven_libraries
                )

                if best_weight > 0:
                    status = "verified" if best_weight >= 0.8 else "partially_verified"
                    category_results.append({
                        "skill": skill,
                        "status": status,
                        "confidence": round(best_weight, 2),
                        "sources": found_sources,
                    })
                    total_weighted_score += best_weight
                else:
                    category_results.append({
                        "skill": skill,
                        "status": "unverified",
                        "confidence": 0,
                        "sources": [],
                    })

            if category_results:
                results[category] = category_results

        final_score = (
            round((total_weighted_score / total_cv_skills) * 100, 2)
            if total_cv_skills > 0 else 0
        )

        return {
            "overall_verification_score": final_score,
            "detailed_report": results,
            "summary": {
                "total_skills_claimed": total_cv_skills,
                "verified_count": sum(
                    1 for cat in results.values()
                    for s in cat if s["status"] == "verified"
                ),
                "partially_verified_count": sum(
                    1 for cat in results.values()
                    for s in cat if s["status"] == "partially_verified"
                ),
                "bonus_skills": self._extract_bonus(cv_skills_dict, github_evidence),
            },
        }

    # ------------------------------------------------------------------
    # Core matching logic
    # ------------------------------------------------------------------

    def _find_in_evidence(
        self,
        skill_lower: str,
        github_evidence: dict,
        proven_libraries: set,
    ) -> tuple[float, list]:
        """
        3 katmanlı eşleştirme:
          1. Birebir eşleşme
          2. Alias tablosu üzerinden eşleşme
          3. Master Map üzerinden dolaylı eşleşme
          4. Substring fallback (uzun string'ler için)
        Her katmanda bulunan en yüksek ağırlık döndürülür.
        """
        best_weight = 0.0
        found_sources: list[str] = []

        # --- 1. Birebir ---
        w, src = self._check_key(skill_lower, github_evidence)
        if w > best_weight:
            best_weight, found_sources = w, src

        # --- 2. Alias ---
        # skill_lower'ın canonical karşılığını bul
        canonical = REVERSE_ALIASES.get(skill_lower)
        if canonical:
            # canonical'ı dene
            w, src = self._check_key(canonical, github_evidence)
            if w > best_weight:
                best_weight, found_sources = w, src
            # canonical'ın tüm alias'larını dene
            for alias in SKILL_ALIASES.get(canonical, []):
                w, src = self._check_key(alias, github_evidence)
                if w > best_weight:
                    best_weight, found_sources = w, src

        # --- 3. Master Map (dolaylı kanıt) ---
        # Örn: CV'de "python" var, GitHub'da "pandas" var → master_map["pandas"] içinde "python" geçiyorsa eşleş
        if best_weight < 1.0:
            for lib, related_techs in self.master_map.items():
                if lib in proven_libraries and skill_lower in related_techs:
                    w, src = self._check_key(lib, github_evidence)
                    # Dolaylı kanıt olduğu için ağırlığı biraz düşür
                    w *= 0.95
                    if w > best_weight:
                        best_weight = w
                        found_sources = list(set(found_sources + src))

        # --- 4. Substring fallback ---
        # Sadece birebir + alias bulamadıysak ve skill yeterince uzunsa dene
        if best_weight == 0 and len(skill_lower) >= 5:
            for gh_skill in proven_libraries:
                # "entity framework" CV'de, "entity framework core" GitHub'da → substring match
                if skill_lower in gh_skill or gh_skill in skill_lower:
                    w, src = self._check_key(gh_skill, github_evidence)
                    w *= 0.85   # substring match cezası
                    if w > best_weight:
                        best_weight = w
                        found_sources = src

        return round(best_weight, 4), found_sources

    def _check_key(self, key: str, github_evidence: dict) -> tuple[float, list]:
        """Verilen key'i github_evidence'da arar, ağırlık ve kaynakları döndürür."""
        if key in github_evidence:
            sources = github_evidence[key]
            weight = max(self.weights.get(s, 0.1) for s in sources)
            return weight, list(sources)
        return 0.0, []

    # ------------------------------------------------------------------
    # Bonus skills
    # ------------------------------------------------------------------

    def _extract_bonus(self, cv_skills_dict: dict, github_evidence: dict) -> list[str]:
        """
        GitHub'da 'direct' veya 'infra' kanıtı olan ama CV'de geçmeyen skill'leri döndürür.
        Claude ile internal/utility paketleri filtreler.
        """
        # CV'deki tüm skill'leri ve alias'larını topla
        cv_set: set[str] = set()
        for skills in cv_skills_dict.values():
            for s in skills:
                s_lower = s.lower().strip()
                cv_set.add(s_lower)
                canonical = REVERSE_ALIASES.get(s_lower)
                if canonical:
                    cv_set.add(canonical)
                    for alias in SKILL_ALIASES.get(canonical, []):
                        cv_set.add(alias)

        # CV'de olmayan, direct/infra kanıtlı, URL olmayan adayları topla
        candidates = [
            skill for skill, evidence in github_evidence.items()
            if skill not in cv_set
            and not skill.startswith("http")
            and len(skill) >= 3
            and any(e in ["direct", "infra"] for e in evidence)
        ]

        if not candidates:
            return []

        # Claude'a tek seferde sor — internal paketleri filtrele
        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            skills_list = "\n".join(f"- {s}" for s in candidates)

            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": (
                        "Aşağıdaki paket/kütüphane listesinden sadece "
                        "bir CV'de geçebilecek gerçek skill'leri döndür.\n"
                        "Kriter: framework, veritabanı, cloud servisi, "
                        "programlama dili veya tanınmış kütüphane (pandas, pytorch, spacy vb.) olmalı.\n"
                        "ALMA: certifi, urllib3, pycparser gibi internal/utility paketleri, "
                        "build araçları, type stub'ları, HTTP adaptörleri, "
                        "encoding kütüphaneleri, logging yardımcıları.\n"
                        "Sadece virgülle ayrılmış liste döndür, açıklama yapma.\n\n"
                        f"Liste:\n{skills_list}"
                    )
                }]
            )

            raw = response.content[0].text.strip()
            return sorted([s.strip().lower() for s in raw.split(",") if s.strip()])

        except Exception as e:
            logger.error(f"Bonus filtreleme hatası: {e}")
            return sorted(candidates)  # hata olursa ham listeyi döndür