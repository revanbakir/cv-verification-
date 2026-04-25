import json
import os
import logging
import anthropic

logger = logging.getLogger(__name__)

# --- Sabitler ve Yapılandırma ---

SKIP_CV_TERMS = {
    "crud", "dto", "rest", "restful", "mvc", "oop", "solid",
    "design patterns", "microservices", "dependency injection",
    "async/await", "web api", "dbcontext", "repository pattern",
    "clean architecture", "tdd", "bdd", "agile", "scrum", "kanban",
    "ci/cd", "api", "sdk", "orm", "ioc", "di", "ddd",
}

SKILL_ALIASES: dict[str, list[str]] = {
    "sql server":       ["ms sql server", "mssql", "sqlserver", "ssms"],
    "entity framework": ["entity framework core", "efcore", "ef core", "ef"],
    "asp.net":          ["asp.net core", "asp.net web api", "aspnetcore", "asp.net mvc"],
    ".net":             [".net core", ".net framework", ".net 6", ".net 7", ".net 8", "dotnet"],
    "c#":               ["csharp", "c sharp"],
    "javascript":       ["js", "es6", "es2015", "ecmascript", "vanilla js"],
    "typescript":       ["ts"],
    "postgresql":       ["postgres", "psql", "pg"],
    "mongodb":          ["mongo"],
    "kubernetes":       ["k8s"],
    "github actions":   ["actions/checkout", "github-actions", "github workflow"],
    "aws":              ["amazon web services", "s3", "ec2", "lambda", "boto3"],
    "docker":           ["dockerfile", "docker-compose", "container"],
    "spring boot":      ["spring", "spring framework", "spring mvc"],
}

def _build_reverse_aliases() -> dict[str, str]:
    reverse: dict[str, str] = {}
    for canonical, aliases in SKILL_ALIASES.items():
        reverse[canonical] = canonical
        for alias in aliases:
            reverse[alias] = canonical
    return reverse

REVERSE_ALIASES = _build_reverse_aliases()

# --- Ana Verifier Sınıfı ---

class Verifier:
    def __init__(self):
        self.weights = {
            "direct":  1.0,   # requirements.txt, package.json, .csproj vb.
            "infra":   0.8,   # .tf, workflow, dockerfile
            "config":  0.6,   # .env, settings
            "mention": 0.4,   # README.md
        }
        self.master_map = self._load_master_map()

    def _load_master_map(self) -> dict:
        map_path = os.path.join("app", "data", "master_tech_map.json")
        try:
            if os.path.exists(map_path):
                with open(map_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Master map yükleme hatası: {e}")
            return {}

    def _expand_skills_with_evidence_hints(self, cv_skills_dict: dict) -> dict[str, list[str]]:
        """CV'deki her skill için GitHub'da aranabilecek dinamik ipuçlarını Claude'a ürettirir."""
        all_skills = list(set([
            skill.lower().strip()
            for skills in cv_skills_dict.values()
            for skill in skills
            if skill.lower().strip() and skill.lower().strip() not in SKIP_CV_TERMS
        ]))

        if not all_skills:
            return {}

        skills_list = "\n".join(f"- {s}" for s in all_skills)

        try:
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=1000,
                system="Sen bir teknik analiz asistanısın. Sadece 'teknoloji: kanit1, kanit2' formatında çıktı ver.",
                messages=[{
                    "role": "user",
                    "content": (
                        "Aşağıdaki teknolojilerin bir projede kullanıldığını kanıtlayan "
                        "paket adlarını, driver isimlerini veya env değişkenlerini listele.\n\n"
                        f"{skills_list}\n\n"
                        "Format: teknoloji: kanit1, kanit2, kanit3"
                    )
                }]
            )

            hints: dict[str, list[str]] = {}
            # API yanıtını doğru şekilde metne çeviriyoruz
            text_response = response.content[0].text
            for line in text_response.strip().splitlines():
                if ":" in line:
                    skill_key, raw_vals = line.split(":", 1)
                    vals = [v.strip().lower() for v in raw_vals.split(",") if v.strip()]
                    hints[skill_key.strip().lower()] = vals
            return hints
        except Exception as e:
            logger.error(f"Claude hint üretme hatası: {e}")
            return {}

    def _check_key(self, key: str, github_evidence: dict) -> tuple[float, list]:
        """GitHub evidence içinde anahtarı arar ve en yüksek ağırlığı döner."""
        if key in github_evidence:
            sources = github_evidence[key]
            weight = max(self.weights.get(s, 0.1) for s in sources)
            return weight, list(sources)
        return 0.0, []

    def _find_in_evidence(self, skill_lower: str, github_evidence: dict, 
                         proven_libraries: set, evidence_hints: dict) -> tuple[float, list]:
        """5 Katmanlı Eşleştirme Mantığı"""
        best_weight = 0.0
        found_sources = []

        # 1. Birebir Eşleşme
        w, src = self._check_key(skill_lower, github_evidence)
        if w > best_weight: best_weight, found_sources = w, src

        # 2. Statik Alias (SKILL_ALIASES)
        if best_weight < 1.0:
            canonical = REVERSE_ALIASES.get(skill_lower)
            if canonical:
                for alt in [canonical] + SKILL_ALIASES.get(canonical, []):
                    w, src = self._check_key(alt, github_evidence)
                    if w > best_weight: best_weight, found_sources = w, src

        # 3. Master Map (Dolaylı İlişki)
        if best_weight < 0.95:
            for lib, related in self.master_map.items():
                if lib in proven_libraries and skill_lower in related:
                    w, src = self._check_key(lib, github_evidence)
                    if w * 0.95 > best_weight:
                        best_weight, found_sources = w * 0.95, list(set(found_sources + src))

        # 4. Dinamik Claude Hintleri
        if best_weight < 0.9:
            for hint in evidence_hints.get(skill_lower, []):
                w, src = self._check_key(hint, github_evidence)
                if w * 0.9 > best_weight:
                    best_weight, found_sources = w * 0.9, list(set(found_sources + src))

        # 5. Substring Fallback
        if best_weight == 0 and len(skill_lower) >= 5:
            for gh_skill in proven_libraries:
                if skill_lower in gh_skill or gh_skill in skill_lower:
                    w, src = self._check_key(gh_skill, github_evidence)
                    if w * 0.8 > best_weight:
                        best_weight, found_sources = w * 0.8, src

        return round(best_weight, 4), found_sources

    def verify(self, cv_skills_dict: dict, github_evidence: dict) -> dict:
        # Dinamik ipuçlarını bir kez üret
        evidence_hints = self._expand_skills_with_evidence_hints(cv_skills_dict)
        
        results = {}
        total_cv_skills = 0
        total_weighted_score = 0.0
        proven_libraries = set(github_evidence.keys())

        # Sayacı tutmak için değişkenler
        verified_count = 0
        partially_verified_count = 0

        for category, skills in cv_skills_dict.items():
            category_results = []
            seen_in_category = set()

            for skill in skills:
                skill_lower = skill.lower().strip()
                if not skill_lower or skill_lower in SKIP_CV_TERMS or skill_lower in seen_in_category:
                    continue
                
                seen_in_category.add(skill_lower)
                total_cv_skills += 1

                best_weight, found_sources = self._find_in_evidence(
                    skill_lower, github_evidence, proven_libraries, evidence_hints
                )

                status = "unverified"
                if best_weight >= 0.8: 
                    status = "verified"
                    verified_count += 1
                elif best_weight > 0: 
                    status = "partially_verified"
                    partially_verified_count += 1

                category_results.append({
                    "skill": skill,
                    "status": status,
                    "confidence": round(best_weight, 2),
                    "sources": found_sources
                })
                total_weighted_score += best_weight

            if category_results:
                results[category] = category_results

        final_score = round((total_weighted_score / total_cv_skills * 100), 2) if total_cv_skills > 0 else 0

        return {
            "overall_verification_score": final_score,
            "detailed_report": results,
            "summary": {
                "total_skills_claimed": total_cv_skills,
                "verified_count": verified_count,            # Hata veren anahtar eklendi
                "partially_verified_count": partially_verified_count, # Hata veren anahtar eklendi
                "bonus_skills": self._extract_bonus(cv_skills_dict, github_evidence)
            }
        }
    


    def _extract_bonus(self, cv_skills_dict: dict, github_evidence: dict) -> list[str]:
        # 1. CV'deki tüm yetenekleri küçük harfe çevirip bir kümede topla (hızlı karşılaştırma için)
        cv_set = {s.lower().strip() for cats in cv_skills_dict.values() for s in cats}

        # 2. GitHub verisinden aday "bonus" yetenekleri belirle
        candidates = [
            skill for skill, src in github_evidence.items()
            if skill not in cv_set  # CV'de halihazırda yoksa
            and any(e in ["direct", "infra"] for e in src)  # Doğrudan veya altyapı kanıtı varsa
            and not skill.startswith("http")  # Link değilse
            and len(skill) > 2  # Çok kısa bir ifade değilse
        ]

        # Eğer aday yoksa boş liste dön
        if not candidates:
            return []

        try:
            # 3. Claude API'ye bağlan ve "gereksiz" paketleri filtrele
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            resp = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=500,
                messages=[{
                    "role": "user",
                    "content": (
                        "Sen bir teknik işe alım uzmanısın."
                        "Aşağıdaki paket/teknoloji listesinden sadece bir yazılımcının CV'sinde "
                        "bağımsız bir skill sayılması için şu kriterlerden birini karşılaması gerekir:\n"
                        "- Tanınmış bir framework, kütüphane veya platform olması\n"
                        "- Öğrenilmesi için zaman ve çaba gerektirmesi ve eğitiminin alınması gerekebileceği\n"
                        "- İş ilanlarında aranıyor olması\n\n"
                        "ALMA: Başka araçların çalışması için gereken alt bağımlılıklar, "
                        "yardımcı paketler, congfig/env araçları, şablon motorları, "
                        "HTTP alt katman kütüphaneleri - bunları kullanan geliştirici bile "
                        "farkında oladan kullanır, CV'ye yazmaz.\n\n"
                        "Sadece virgülle ayrılmış liste döndür, başına sonuna başka hiçbir şey yazma."
                        f"{', '.join(candidates)}"
                    )
                }]
            )
        
            # 4. Yanıtı temizle ve alfabetik sıralı liste olarak döndür
            raw = resp.content[0].text.strip()
            return sorted([s.strip().lower() for s in raw.split(",") if s.strip()])
        
        except Exception as e:
            logger.error(f"Bonus extraction hatası: {e}")
            return []

    

    