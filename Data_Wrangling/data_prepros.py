

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

rcParams['figure.figsize'] = (12, 6)
rcParams['font.size']      = 11
sns.set_theme(style="whitegrid", palette="muted")

# ════════════════════════════════════════════════════════════
# KONFIGURASI
# ════════════════════════════════════════════════════════════
INPUT_FILE  = "C:\\Users\\asus3\\Documents\\CPSTNPROJECT\\capstone-ds\\Data_Wrangling\\Data_Fixed\\FinalFile_EDA.csv"       # ← file hasil merge + cleaning kamu
OUTPUT_DIR  = "C:\\Users\\asus3\\Documents\\CPSTNPROJECT\\capstone-ds\\Data_Wrangling\\Data_Fixed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ════════════════════════════════════════════════════════════
# STEP 1 — LOAD & VALIDASI
# ════════════════════════════════════════════════════════════
print("=" * 60)
print("STEP 1: Load & Validasi Data")
print("=" * 60)

df = pd.read_csv(INPUT_FILE, encoding="utf-8-sig")
print(f"  Shape awal     : {df.shape}")
print(f"  Unique titles  : {df['title'].nunique()}")
print(f"  Search roles   : {df['search_role'].value_counts().to_dict()}")
print(f"  JD min length  : {df['job_description'].str.len().min()}")

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
    "DevOps Engineer": [
        "devops", "devsecops", "cloud engineer", "site reliability",
        "sre engineer", "infrastructure engineer", "platform engineer",
        "system administrator", "sysadmin", "cloud architect", "mobile developer", "android developer", "ios developer",
        "flutter developer", "react native developer", "mobile engineer",
        "kotlin developer", "swift developer",
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
    "dart", "ruby", "bash", "shell", "perl",
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

# Ekstrak kota dari kolom location
def extract_city(location: str) -> str:
    if not location:
        return "Unknown"
    # Format umum: "Jakarta, Indonesia (On-site)" atau "Jakarta Metropolitan Area"
    city = location.split(",")[0].strip()
    city = city.replace("Metropolitan Area", "").strip()
    return city if city else "Unknown"

df["city"] = df["location"].apply(extract_city)

# Tipe kerja (on-site / remote / hybrid)
def extract_work_type(location: str) -> str:
    loc = location.lower()
    if "remote" in loc:   return "Remote"
    if "hybrid" in loc:   return "Hybrid"
    if "on-site" in loc or "onsite" in loc: return "On-site"
    return "Unknown"

df["work_type"] = df["location"].apply(extract_work_type)

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
        return "Manager/Lead"
    return "Mid-level"

df["seniority"] = df["title"].apply(extract_seniority)

# JD length sebagai proxy kompleksitas job
df["jd_length"] = df["job_description"].str.len()

print(f"  Kolom baru ditambahkan: city, work_type, seniority, jd_length")
print(f"\n  Work type distribution:")
print(df["work_type"].value_counts().to_string())
print(f"\n  Seniority distribution:")
print(df["seniority"].value_counts().to_string())

# ════════════════════════════════════════════════════════════
# STEP 6 — EDA & BUSINESS QUESTIONS
# ════════════════════════════════════════════════════════════
print("\n" + "=" * 60)
print("STEP 6: EDA — Business Questions")
print("=" * 60)

"""
Business Questions:
  BQ1. Role IT apa yang paling banyak tersedia di Indonesia?
  BQ2. Skill apa yang paling banyak diminta per role?
  BQ3. Kota mana yang paling banyak buka lowongan IT?
  BQ4. Bagaimana distribusi tipe kerja (remote/hybrid/on-site)?
  BQ5. Apa skill gap antara Data Scientist vs Data Analyst?
"""

fig_dir = f"{OUTPUT_DIR}/figures"
os.makedirs(fig_dir, exist_ok=True)

# ── BQ1: Distribusi Role ─────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 6))
role_counts = df[df["standardized_role"] != "Other"]["standardized_role"].value_counts()
bars = ax.barh(role_counts.index, role_counts.values, color=sns.color_palette("muted", len(role_counts)))
ax.set_xlabel("Jumlah Job Posting")
ax.set_title("BQ1: Distribusi Role IT yang Tersedia di Indonesia", fontweight="bold")
for bar, val in zip(bars, role_counts.values):
    ax.text(val + 5, bar.get_y() + bar.get_height()/2, str(val), va="center")
plt.tight_layout()
plt.savefig(f"{fig_dir}/BQ1_role_distribution.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✅ BQ1 chart saved")

# ── BQ2: Top 10 Skills Overall ───────────────────────────────
all_skills = []
for s in df["extracted_skills"]:
    all_skills.extend(s)
skill_freq = Counter(all_skills)
top20      = skill_freq.most_common(20)

fig, ax = plt.subplots(figsize=(12, 7))
skills_names = [s for s, _ in top20]
skills_vals  = [c for _, c in top20]
bars = ax.barh(skills_names[::-1], skills_vals[::-1], color=sns.color_palette("viridis", 20))
ax.set_xlabel("Frekuensi Muncul di Job Posting")
ax.set_title("BQ2: Top 20 Skills Paling Banyak Diminta (IT Jobs Indonesia)", fontweight="bold")
plt.tight_layout()
plt.savefig(f"{fig_dir}/BQ2_top_skills_overall.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✅ BQ2 chart saved")

# ── BQ3: Top 10 Kota ─────────────────────────────────────────
fig, ax = plt.subplots(figsize=(12, 5))
city_counts = df[df["city"] != "Unknown"]["city"].value_counts().head(10)
ax.bar(city_counts.index, city_counts.values, color=sns.color_palette("Set2", 10))
ax.set_xlabel("Kota")
ax.set_ylabel("Jumlah Job Posting")
ax.set_title("BQ3: Top 10 Kota dengan Lowongan IT Terbanyak", fontweight="bold")
ax.tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.savefig(f"{fig_dir}/BQ3_top_cities.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✅ BQ3 chart saved")

# ── BQ4: Work Type Distribution ──────────────────────────────
fig, ax = plt.subplots(figsize=(7, 7))
wt = df["work_type"].value_counts()
ax.pie(wt.values, labels=wt.index, autopct="%1.1f%%",
       colors=sns.color_palette("pastel"), startangle=90)
ax.set_title("BQ4: Distribusi Tipe Kerja (Remote / Hybrid / On-site)", fontweight="bold")
plt.tight_layout()
plt.savefig(f"{fig_dir}/BQ4_work_type.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✅ BQ4 chart saved")

# ── BQ5: Skill Gap — Data Scientist vs Data Analyst ──────────
def get_skill_pct(role_name):
    role_df = df[df["standardized_role"] == role_name]
    skills  = []
    for s in role_df["extracted_skills"]:
        skills.extend(s)
    total = len(role_df)
    return {skill: count / total for skill, count in Counter(skills).most_common(15)}

ds_skills = get_skill_pct("Data Scientist")
da_skills = get_skill_pct("Data Analyst")

all_keys = sorted(set(list(ds_skills.keys()) + list(da_skills.keys())), 
                  key=lambda x: -(ds_skills.get(x, 0) + da_skills.get(x, 0)))[:15]

x      = np.arange(len(all_keys))
width  = 0.35
fig, ax = plt.subplots(figsize=(14, 6))
ax.bar(x - width/2, [ds_skills.get(k, 0)*100 for k in all_keys], width,
       label="Data Scientist", color="#4C72B0")
ax.bar(x + width/2, [da_skills.get(k, 0)*100 for k in all_keys], width,
       label="Data Analyst",   color="#DD8452")
ax.set_xticks(x)
ax.set_xticklabels(all_keys, rotation=35, ha="right")
ax.set_ylabel("% Job Posting yang Menyebut Skill")
ax.set_title("BQ5: Skill Gap — Data Scientist vs Data Analyst", fontweight="bold")
ax.legend()
plt.tight_layout()
plt.savefig(f"{fig_dir}/BQ5_skill_gap_DS_vs_DA.png", dpi=150, bbox_inches="tight")
plt.close()
print("  ✅ BQ5 chart saved")

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
    "city", "work_type", "seniority", "jd_length",
    "job_description", "extracted_skills", "skills_count",
    "job_url", "search_role", "scraped_at"
]
final_path = f"{OUTPUT_DIR}/linkedin_jobs_final_{ts}.csv"
df[core_cols].to_csv(final_path, index=False, encoding="utf-8-sig")
print(f"  ✅ CSV final      → {final_path}  ({len(df)} baris)")

# ── B. JSON summary untuk semua tim ─────────────────────────
summary = {
    "generated_at"         : ts,
    "total_jobs"           : len(df),
    "unique_companies"     : int(df["company"].nunique()),
    "role_distribution"    : df["standardized_role"].value_counts().to_dict(),
    "work_type_distribution": df["work_type"].value_counts().to_dict(),
    "seniority_distribution": df["seniority"].value_counts().to_dict(),
    "top_cities"           : df["city"].value_counts().head(10).to_dict(),
    "top_50_skills"        : dict(skill_freq.most_common(50)),
    "avg_skills_per_job"   : round(df["skills_count"].mean(), 2),
    "skills_per_role"      : skills_per_role,
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
print(f"  Output figures       : {fig_dir}/")
print(f"  CSV final (AI Eng)   : {final_path}")
print(f"  Summary JSON         : {json_path}")
print(f"\n  Kolom final untuk AI Engineer:")
for col in core_cols:
    print(f"    - {col}")
print("\n✅ Pipeline selesai! Data siap diserahkan ke AI Engineer.")
