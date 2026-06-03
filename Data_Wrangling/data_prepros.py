import pandas as pd
import numpy as np
import ast
import re
import os
import json
from datetime import datetime
from collections import Counter
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib import rcParams


# ════════════════════════════════════════════════════════════
# KONFIGURASI
# ════════════════════════════════════════════════════════════
INPUT_FILE  = "C:\\Users\\asus3\\Documents\\CPSTNPROJECT\\capstone-ds\\Data_Wrangling\\Data_Fixed\\linkedin_adddatscien.csv"       # ← file hasil merge + cleaning kamu
OUTPUT_DIR  = "C:\\Users\\asus3\\Documents\\CPSTNPROJECT\\capstone-ds\\Data_Wrangling\\Data_Fixed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ════════════════════════════════════════════════════════════
# STEP 1 — LOAD & VALIDASI
# ════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 1: Load & Validasi Data")
print("=" * 60)

df = pd.read_csv(
    INPUT_FILE,
    sep=";",                  # ← separator titik koma
    encoding="utf-8-sig",     # ← handle BOM dari Excel
    engine="python",          # ← parser python lebih toleran
    on_bad_lines="skip",      # ← skip baris yang masih rusak
    quotechar='"',            # ← handle field yang di-quote
)

# ════════════════════════════════════════════════════════════
# STEP 2 — FILTER NOISE (job non-IT yang ikut ter-scrape)
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 2: Filter Noise (job non-IT)")
print("=" * 60)

# Kata kunci yang menandakan job NON-IT
NOISE_TITLE_KEYWORDS = [
    # Non-IT roles
    'finance intern', 'finance staff', 'finance analyst', 'financial planning',
    'hr intern', 'human resources intern', 'talent acquisition',
    'marketing intern', 'marketing staff',
    'accounting intern', 'accounting staff',
    'operations intern', 'operation administration',
    'legal intern', 'legal staff',
    'cargo crew', 'teller', 'area manager',
    'actuarial', 'management trainee',
    'business development intern', 'business development staff',
    'medical', 'nurse', 'doctor', 'pharmacist',
    'sales intern', 'sales staff', 'sales executive',
    'supply chain', 'logistic',
    # Terlalu generik / bukan IT
    'internship program', 'ignite internship',
    'labs bootcamp', 'tlm intern', 'flm',
]

# Kata kunci yang WAJIB ada di title/JD agar dianggap IT job
IT_KEYWORDS_IN_JD = [
    'software', 'developer', 'engineer', 'data', 'programming',
    'python', 'javascript', 'java', 'sql', 'database', 'cloud',
    'machine learning', 'artificial intelligence', 'web', 'mobile',
    'android', 'ios', 'backend', 'frontend', 'fullstack', 'devops',
    'analyst', 'scientist', 'tech', 'coding', 'api', 'system',
    'network', 'security', 'infrastructure', 'agile', 'scrum',
]

def is_noise(title: str) -> bool:
    t = title.lower().strip()
    return any(kw in t for kw in NOISE_TITLE_KEYWORDS)

def is_it_job(jd: str) -> bool:
    jd_lower = jd.lower()
    return any(kw in jd_lower for kw in IT_KEYWORDS_IN_JD)

before = len(df)

# Filter 1: hapus berdasarkan noise title keywords
df = df[~df['title'].apply(is_noise)]
print(f"  Setelah filter noise title : {len(df)} baris (hapus {before - len(df)})")

# Filter 2: pastikan job_description mengandung kata IT
before2 = len(df)
df = df[df['job_description'].apply(is_it_job)]
print(f"  Setelah filter JD non-IT   : {len(df)} baris (hapus {before2 - len(df)})")

print(f"  Total dihapus              : {before - len(df)} baris noise")

# ════════════════════════════════════════════════════════════
# STEP 3 — ROLE STANDARDIZATION (diperbaiki total)
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 3: Role Standardization")
print("=" * 60)

# Keyword mapping yang diperbaiki & diperluas berdasarkan data aktual
STANDARD_ROLES = {
    "Data Scientist": [
        "data scientist", "ml scientist", "research scientist",
        "data science", "scientist", "nlp engineer", "nlp scientist",
    ],
    "Data Analyst": [
        "data analyst", "business analyst", "product analyst",
        "analytics", "bi analyst", "reporting analyst",
        "financial analyst", "market analyst", "marketing analyst",
        "data analytics", "operation analyst", "supply analytics",
        "lead analyst", "bi developer", "business intelligence developer",
        "power bi", "tableau developer", "looker developer",
        "bi development", "bi specialist", "data visualization", "data viz", "dashboard developer",
    ],
    "Data Engineer": [
        "data engineer", "etl engineer", "data pipeline",
        "analytics engineer", "big data", "data platform",
        "data infrastructure", "data manager", "data collector",
    ],
    "ML Engineer": [
        "machine learning engineer", "ml engineer", "mlops",
        "ai engineer", "deep learning", "computer vision engineer",
        "llm engineer", "generative ai","AI",
    ],
    "Backend Developer": [
        "backend developer", "back-end developer", "backend engineer",
        "back end developer", "python developer", "java developer",
        "golang developer", "go developer", "php developer",
        "ruby developer", "api developer", "server side developer",
        "node developer", "laravel developer", "spring developer",
    ],
    "Frontend Developer": [
        "frontend developer", "front-end developer", "frontend engineer",
        "front end developer", "ui developer", "react developer",
        "vue developer", "angular developer", "web frontend",
        "ui engineer",
    ],
    "Fullstack Developer": [
        "fullstack", "full stack", "full-stack",
        "web developer", "web engineer",
    ],
    "Software Engineer": [  # fallback umum — taruh paling bawah
        "software engineer", "software developer", "programmer",
        "it engineer", "tech lead", "technical lead", "system analyst", "systems analyst", "it analyst",
        "business system analyst", "functional analyst", "solution architect", "software architect","qa engineer", "quality assurance", "quality engineer",
        "test engineer", "qa automation", "software tester",
        "automation tester", "sdet",
    ],
}

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_OK = True
except ImportError:
    SKLEARN_OK = False
    print("  ⚠️  scikit-learn tidak ada, fallback cosine similarity dinonaktifkan")

def standardize_role(title: str) -> str:
    t = title.lower().strip()
    # Keyword match: cek dari yang paling spesifik ke paling umum
    for role, keywords in STANDARD_ROLES.items():
        if any(kw in t for kw in keywords):
            return role
    # Cosine similarity fallback
    if SKLEARN_OK:
        corpus     = [" ".join(v) for v in STANDARD_ROLES.values()]
        role_names = list(STANDARD_ROLES.keys())
        try:
            vec  = TfidfVectorizer(ngram_range=(1, 2))
            mat  = vec.fit_transform(corpus + [t])
            sims = cosine_similarity(mat[-1], mat[:-1])[0]
            idx  = sims.argmax()
            if sims[idx] >= 0.08:
                return role_names[idx]
        except Exception:
            pass
    return "Other"

df["standardized_role"] = df["title"].apply(standardize_role)

print("  Distribusi standardized_role:")
dist = df["standardized_role"].value_counts()
for role, cnt in dist.items():
    bar = "█" * (cnt // 10)
    print(f"    {role:<22} {cnt:>4}  {bar}")

other_pct = (df["standardized_role"] == "Other").sum() / len(df) * 100
print(f"\n  'Other' = {other_pct:.1f}% dari total")

if other_pct > 10:
    print("  ⚠️  Other masih > 10%, sample di bawah untuk review manual:")
    others = df[df["standardized_role"] == "Other"]["title"].value_counts().head(15)
    for t, c in others.items():
        print(f"       {c}x  {t}")

# ════════════════════════════════════════════════════════════
# STEP 4 — SKILL EXTRACTION (master list lengkap)
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 4: Skill Extraction (Enhanced)")
print("=" * 60)

SKILLS_MASTER = {
    # Languages
    "python", "java", "javascript", "typescript", "golang", "go",
    "php", "swift", "kotlin", "scala", "r", "c++", "c#", "rust",
    "dart", "ruby", "bash", "shell", "perl",'php','html','css',
    # Web Frameworks
    "react", "angular", "vue", "nextjs", "nuxtjs", "django",
    "flask", "fastapi", "spring boot", "express", "nestjs",
    "laravel", "rails", "fiber", "gin", "svelte",
    # Data & ML
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas",
    "numpy", "opencv", "huggingface", "transformers", "xgboost",
    "lightgbm", "catboost", "mlflow", "kubeflow", "dvc",
    "langchain", "openai", "llm",
    # Databases
    "sql", "postgresql", "mysql", "mongodb", "redis",
    "elasticsearch", "cassandra", "dynamodb", "firebase",
    "mariadb", "sqlite", "neo4j", "supabase", "bigquery",
    # Cloud & DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s",
    "jenkins", "gitlab ci", "github actions", "terraform",
    "ansible", "prometheus", "grafana", "helm", "argocd",
    "circleci", "ci/cd",
    # Big Data
    "hadoop", "spark", "kafka", "airflow", "databricks",
    "snowflake", "dbt", "hive", "flink", "beam",
    # BI Tools
    "tableau", "power bi", "looker", "metabase", "superset", "qlik",
    # Mobile
    "flutter", "android", "ios", "react native", "xamarin",
    # Methodology
    "agile", "scrum", "kanban", "git", "linux", "rest api",
    "graphql", "microservices", "tdd", "oop", "solid",
}

def extract_skills(text: str) -> list:
    if not text:
        return []
    t = text.lower()
    found = []
    for skill in SKILLS_MASTER:
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, t):
            found.append(skill)
    return sorted(set(found))

df["extracted_skills"] = df["job_description"].apply(extract_skills)
df["skills_count"]     = df["extracted_skills"].apply(len)

print(f"  Rata-rata skill per job  : {df['skills_count'].mean():.1f}")
print(f"  Job tanpa skill terdeteksi: {(df['skills_count'] == 0).sum()}")

# ════════════════════════════════════════════════════════════
# STEP 5 — FEATURE ENGINEERING RINGAN
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 5: Feature Engineering")
print("=" * 60)

# Level seniority dari title
def extract_seniority(title: str) -> str:
    t = title.lower()
    if any(x in t for x in ["intern", "internship", "magang"]):
        return "Intern"
    if any(x in t for x in ["junior", "jr.", "entry", "fresh"]):
        return "Junior"
    if any(x in t for x in ["senior", "sr.", "lead", "principal", "staff"]):
        return "Senior"
    if any(x in t for x in ["manager", "head", "director", "vp", "chief", "architect"]):
        return "Manager/Head"
    return "Mid-level"

df["seniority"] = df["title"].apply(extract_seniority)

# JD length sebagai proxy kompleksitas job
df["jd_length"] = df["job_description"].str.len()

print(f"  Kolom baru ditambahkan: seniority, jd_length")
print(f"\n  Seniority distribution:")
print(df["seniority"].value_counts().to_string())

# ── Summary Skills per Role (untuk Data Dictionary) ──────────
skills_per_role = {}
for role in df["standardized_role"].unique():
    if role == "Other":
        continue
    role_skills = []
    for s in df[df["standardized_role"] == role]["extracted_skills"]:
        role_skills.extend(s)
    top10 = dict(Counter(role_skills).most_common(10))
    skills_per_role[role] = top10

# ════════════════════════════════════════════════════════════
# STEP 7 — SIMPAN OUTPUT FINAL
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 7: Simpan Output Final")
print("=" * 60)

ts = datetime.now().strftime("%Y%m%d_%H%M%S")

# ── A. CSV final untuk AI Engineer ──────────────────────────
core_cols = [
    "id", "title", "standardized_role", "company", "location",
    "seniority", "jd_length",
    "job_description", "extracted_skills", "skills_count",
    "job_url", "search_role", "search_location"
]
# Filter hanya kolom yang ada di df
core_cols = [c for c in core_cols if c in df.columns]
print(f"  Kolom yang disimpan: {core_cols}")
final_path = f"{OUTPUT_DIR}/linkedin_jobs_final_{ts}.csv"
df[core_cols].to_csv(final_path, index=False, encoding="utf-8-sig")
print(f"  ✅ CSV final      → {final_path}  ({len(df)} baris)")

# ── B. JSON summary untuk semua tim ─────────────────────────
# SESUDAH
summary = {
    "generated_at"          : ts,
    "total_jobs"            : len(df),
    "unique_companies"      : int(df["company"].nunique()),
    "role_distribution"     : df["standardized_role"].value_counts().to_dict(),
    "seniority_distribution": df["seniority"].value_counts().to_dict(),
    "avg_skills_per_job"    : round(df["skills_count"].mean(), 2),
    "skills_per_role"       : skills_per_role,
}
json_path = f"{OUTPUT_DIR}/data_summary_{ts}.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print(f"  ✅ Summary JSON   → {json_path}")

# ════════════════════════════════════════════════════════════
# RINGKASAN AKHIR
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("RINGKASAN PIPELINE")
print("=" * 60)
print(f"  Input awal           : 4.713 baris")
print(f"  Setelah filter noise : {len(df)} baris")
print(f"  Unique role standar  : {df['standardized_role'].nunique()}")
print(f"  Avg skills per job   : {df['skills_count'].mean():.1f}")
print(f"  CSV final (AI Eng)   : {final_path}")
print(f"  Summary JSON         : {json_path}")
print(f"\n  Kolom final untuk AI Engineer:")
for col in core_cols:
    print(f"    - {col}")
print("\n✅ Pipeline selesai! Data siap diserahkan ke AI Engineer.")
