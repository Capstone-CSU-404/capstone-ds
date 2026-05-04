"""
ETL Pipeline - Data Preprocessing
Capstone Project: AI-Driven Career Pathing & Skill Gap Analyzer
Tim: CC26-PSU404 | Role: Data Scientist

Alur:
  Raw CSV (scraping) → Clean → Standardize Role → Enrich Skills → Output CSV

Output file ini adalah bahan baku untuk AI Engineer:
  - standardized_role  : label kategori role (untuk model klasifikasi)
  - job_description    : teks bersih (untuk embedding oleh AI Engineer)
  - extracted_skills   : list skill (untuk skill gap analysis)
  - skill_vector       : representasi biner skills (opsional, untuk AI Engineer)
"""

import pandas as pd
import ast
import re
import os
from datetime import datetime
from collections import Counter

# ── sklearn hanya dipakai jika keyword mapping tidak cukup ──
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("⚠️  scikit-learn tidak terinstall. Fallback cosine similarity dinonaktifkan.")
    print("    Jalankan: pip install scikit-learn")

# ════════════════════════════════════════════════════════════════
# KONFIGURASI
# ════════════════════════════════════════════════════════════════

INPUT_FILE  = "C:\\Users\\asus3\\Documents\\CPSTNPROJECT\\capstone-ds\\Data\\processed\\linkedin_jobs_20260421_215330_softdev.csv"      # ganti sesuai path file kalian
OUTPUT_DIR  = "C:\\Users\\asus3\\Documents\\CPSTNPROJECT\\capstone-ds\\Data_Wrangling\\Data_Fixed"
os.makedirs(OUTPUT_DIR, exist_ok=True)

MIN_JD_LENGTH = 100  # karakter minimum job_description agar dianggap valid

# ── Kategori role standar untuk project ini ──────────────────────
# Sesuaikan dengan scope project: IT roles only
STANDARD_ROLES = {
    "Data Scientist"     : ["data scientist", "ml scientist", "research scientist", "data science"],
    "Data Analyst"       : ["data analyst", "business analyst", "bi analyst", "business intelligence analyst"],
    "Data Engineer"      : ["data engineer", "etl engineer", "data pipeline", "analytics engineer"],
    "ML Engineer"        : ["machine learning engineer", "mlops", "ml engineer", "deep learning engineer", "ai engineer"],
    "BI Developer"       : ["bi developer", "business intelligence", "power bi", "bi development", "tableau developer", "looker"],
    "Backend Developer"  : ["backend developer", "back end developer", "backend engineer", "python developer",
                            "java developer", "golang developer", "api developer", "server side"],
    "Frontend Developer" : ["frontend developer", "front end developer", "frontend engineer", "ui developer",
                            "react developer", "vue developer", "angular developer"],
    "Fullstack Developer": ["fullstack", "full stack", "full-stack"],
    "DevOps Engineer"    : ["devops", "devsecops", "cloud engineer", "sre", "site reliability",
                            "infrastructure engineer", "platform engineer"],
    "Mobile Developer"   : ["mobile developer", "android developer", "ios developer", "flutter developer",
                            "react native", "mobile engineer"],
    "QA Engineer"        : ["qa engineer", "quality assurance", "tester", "test engineer",
                            "qa automation", "software tester"],
    "Software Engineer"  : ["software engineer", "software developer", "programmer", "developer"],  # fallback umum
}

# ── Daftar skill yang diperluas (lebih komprehensif dari scraper) ──
SKILLS_MASTER = {
    # Programming languages
    "python", "java", "javascript", "typescript", "golang", "go", "php", "swift",
    "kotlin", "scala", "r", "c++", "c#", "rust", "dart", "ruby", "bash", "shell",
    # Web frameworks
    "react", "angular", "vue", "nextjs", "nuxtjs", "django", "flask", "fastapi",
    "spring boot", "express", "nestjs", "laravel", "rails", "fiber", "gin",
    # Data & ML
    "tensorflow", "pytorch", "keras", "scikit-learn", "pandas", "numpy", "opencv",
    "huggingface", "transformers", "xgboost", "lightgbm", "catboost", "mlflow",
    "kubeflow", "dvc",
    # Databases
    "sql", "postgresql", "mysql", "mongodb", "redis", "elasticsearch", "cassandra",
    "dynamodb", "firebase", "mariadb", "sqlite", "neo4j", "supabase",
    # Cloud & DevOps
    "aws", "gcp", "azure", "docker", "kubernetes", "k8s", "jenkins", "gitlab ci",
    "github actions", "terraform", "ansible", "prometheus", "grafana", "helm",
    "argocd", "circleci",
    # Big Data
    "hadoop", "spark", "kafka", "airflow", "databricks", "snowflake", "dbt",
    "hive", "flink", "beam",
    # BI Tools
    "tableau", "power bi", "looker", "metabase", "superset", "qlik",
    # Mobile
    "flutter", "android", "ios", "react native", "xamarin",
    # Soft skills & metodologi
    "agile", "scrum", "kanban", "git", "linux", "rest api", "graphql",
    "microservices", "ci/cd", "tdd", "oop",
}


# ════════════════════════════════════════════════════════════════
# STEP 1: LOAD & BASIC CLEANING
# ════════════════════════════════════════════════════════════════

def load_and_clean(filepath: str) -> pd.DataFrame:
    print(f"\n{'='*55}")
    print("STEP 1: Load & Basic Cleaning")
    print(f"{'='*55}")

    df = pd.read_csv(filepath, encoding="utf-8-sig")
    print(f"  Raw data  : {len(df)} baris")

    # Hapus duplikat berdasarkan job_url (paling reliable)
    before = len(df)
    df = df.drop_duplicates(subset=["job_url"], keep="first")
    print(f"  Duplikat  : -{before - len(df)} baris dihapus")

    # Hapus baris yang title atau company kosong
    df = df.dropna(subset=["title", "company"])

    # Bersihkan whitespace di kolom teks
    for col in ["title", "company", "location", "job_description"]:
        if col in df.columns:
            df[col] = df[col].fillna("").str.strip()

    # Filter job_description yang terlalu pendek (tidak informatif)
    before = len(df)
    df = df[df["job_description"].str.len() >= MIN_JD_LENGTH]
    print(f"  JD pendek : -{before - len(df)} baris dihapus (< {MIN_JD_LENGTH} char)")

    # Bersihkan HTML tags sisa di job_description
    df["job_description"] = df["job_description"].apply(clean_html)

    print(f"  Hasil     : {len(df)} baris bersih")
    return df.reset_index(drop=True)


def clean_html(text: str) -> str:
    """Hapus HTML tags dan normalisasi whitespace."""
    text = re.sub(r"<[^>]+>", " ", text)           # hapus HTML tags
    text = re.sub(r"&[a-zA-Z]+;", " ", text)        # hapus HTML entities
    text = re.sub(r"\s+", " ", text)                 # normalisasi spasi
    return text.strip()


# ════════════════════════════════════════════════════════════════
# STEP 2: ROLE STANDARDIZATION
# Ini adalah tantangan utama — 614 unique title → ~12 kategori
# Logika: keyword matching dulu (cepat), cosine similarity sebagai fallback
# ════════════════════════════════════════════════════════════════

def standardize_role(title: str) -> str:
    """
    Mapping job title bebas → kategori standar.

    Contoh:
      "Power BI Development"           → "BI Developer"
      "Python Developer | Remote"      → "Backend Developer"
      "AI & Data Engineer (Analytics)" → "Data Engineer"
      "Junior Fullstack Dev Intern"    → "Fullstack Developer"
    """
    title_lower = title.lower().strip()

    # Step 1: Keyword exact/partial match (O(n) — cepat)
    for std_role, keywords in STANDARD_ROLES.items():
        if any(kw in title_lower for kw in keywords):
            return std_role

    # Step 2: TF-IDF cosine similarity sebagai fallback
    if SKLEARN_AVAILABLE:
        corpus     = [" ".join(v) for v in STANDARD_ROLES.values()]
        role_names = list(STANDARD_ROLES.keys())
        try:
            vec  = TfidfVectorizer(ngram_range=(1, 2))
            mat  = vec.fit_transform(corpus + [title_lower])
            sims = cosine_similarity(mat[-1], mat[:-1])[0]
            best_idx   = sims.argmax()
            best_score = sims[best_idx]
            if best_score >= 0.08:
                return role_names[best_idx]
        except Exception:
            pass

    return "Other"


def apply_role_standardization(df: pd.DataFrame) -> pd.DataFrame:
    print(f"\n{'='*55}")
    print("STEP 2: Role Standardization")
    print(f"{'='*55}")
    print(f"  Unique title sebelum : {df['title'].nunique()}")

    df["standardized_role"] = df["title"].apply(standardize_role)

    print(f"  Distribusi role standar:")
    dist = df["standardized_role"].value_counts()
    for role, count in dist.items():
        bar = "█" * (count // 5)
        print(f"    {role:<22} {count:>4}  {bar}")

    other_count = (df["standardized_role"] == "Other").sum()
    if other_count > 0:
        print(f"\n  ⚠️  {other_count} job masuk kategori 'Other' — perlu review manual")
        print("  Sample 'Other' titles:")
        others = df[df["standardized_role"] == "Other"]["title"].head(10).tolist()
        for t in others:
            print(f"    - {t}")

    return df


# ════════════════════════════════════════════════════════════════
# STEP 3: SKILL EXTRACTION (RE-EXTRACT DENGAN DAFTAR LEBIH LENGKAP)
# ════════════════════════════════════════════════════════════════

def extract_skills_enhanced(text: str) -> list:
    """
    Ekstrak skill dari job_description menggunakan SKILLS_MASTER.
    Lebih komprehensif dibanding script scraper.
    """
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for skill in SKILLS_MASTER:
        # Gunakan word boundary agar 'r' tidak match di 'react'
        pattern = r"\b" + re.escape(skill) + r"\b"
        if re.search(pattern, text_lower):
            found.append(skill)
    return sorted(set(found))


def parse_existing_skills(skills_str) -> list:
    """Parse kolom extracted_skills yang tersimpan sebagai string list."""
    if pd.isna(skills_str) or skills_str == "":
        return []
    try:
        result = ast.literal_eval(str(skills_str))
        return result if isinstance(result, list) else []
    except Exception:
        return []


def apply_skill_extraction(df: pd.DataFrame) -> pd.DataFrame:
    print(f"\n{'='*55}")
    print("STEP 3: Skill Extraction (Enhanced)")
    print(f"{'='*55}")

    # Re-ekstrak dari job_description dengan daftar skill yang lebih lengkap
    df["extracted_skills"] = df["job_description"].apply(extract_skills_enhanced)
    df["skills_count"]     = df["extracted_skills"].apply(len)

    print(f"  Rata-rata skill per job : {df['skills_count'].mean():.1f}")
    print(f"  Job tanpa skill         : {(df['skills_count'] == 0).sum()}")

    # Top skills overall
    all_skills = []
    for skills in df["extracted_skills"]:
        all_skills.extend(skills)
    top10 = Counter(all_skills).most_common(10)
    print(f"\n  Top 10 skills:")
    for skill, cnt in top10:
        pct = cnt / len(df) * 100
        print(f"    {skill:<20} {cnt:>4} jobs ({pct:.0f}%)")

    return df


# ════════════════════════════════════════════════════════════════
# STEP 4: BUAT SKILL VECTOR (BINARY)
# Ini output opsional untuk AI Engineer — bisa mereka buat sendiri
# tapi kita sediakan sebagai kemudahan
# ════════════════════════════════════════════════════════════════

def build_skill_vector(df: pd.DataFrame) -> pd.DataFrame:
    """
    Buat representasi biner skill per job.
    Kolom: skill_vec_python, skill_vec_sql, dst.

    Catatan untuk AI Engineer:
      Ini adalah ONE-HOT encoding sederhana.
      Kalian mungkin akan menggantinya dengan TF-IDF atau BERT embedding.
      Tapi kolom ini bisa jadi baseline yang berguna.
    """
    print(f"\n{'='*55}")
    print("STEP 4: Build Skill Vector (Binary)")
    print(f"{'='*55}")

    # Ambil top 50 skill saja (agar kolom tidak terlalu banyak)
    all_skills = []
    for skills in df["extracted_skills"]:
        all_skills.extend(skills)
    top_skills = [s for s, _ in Counter(all_skills).most_common(50)]

    for skill in top_skills:
        col_name = "skill_" + re.sub(r"[^a-z0-9]", "_", skill)
        df[col_name] = df["extracted_skills"].apply(lambda x: 1 if skill in x else 0)

    print(f"  Dibuat {len(top_skills)} kolom skill vector (top 50 skill)")
    return df


# ════════════════════════════════════════════════════════════════
# STEP 5: EDA RINGKAS
# ════════════════════════════════════════════════════════════════

def run_eda(df: pd.DataFrame):
    print(f"\n{'='*55}")
    print("STEP 5: EDA Ringkas")
    print(f"{'='*55}")

    print(f"\n  Total job bersih        : {len(df)}")
    print(f"  Unique company          : {df['company'].nunique()}")
    print(f"  Unique standardized role: {df['standardized_role'].nunique()}")

    print(f"\n  Top 5 Skills per Role:")
    for role in df["standardized_role"].unique():
        if role == "Other":
            continue
        role_df   = df[df["standardized_role"] == role]
        skills    = []
        for s in role_df["extracted_skills"]:
            skills.extend(s)
        top5 = [s for s, _ in Counter(skills).most_common(5)]
        print(f"    {role:<22} → {', '.join(top5)}")

    print(f"\n  Distribusi lokasi (top 5):")
    loc_counts = df["location"].value_counts().head(5)
    for loc, cnt in loc_counts.items():
        print(f"    {loc:<35} {cnt}")


# ════════════════════════════════════════════════════════════════
# STEP 6: SIMPAN OUTPUT
# ════════════════════════════════════════════════════════════════

def save_outputs(df: pd.DataFrame):
    print(f"\n{'='*55}")
    print("STEP 6: Simpan Output")
    print(f"{'='*55}")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    # ── A. CSV lengkap (dengan skill vector) untuk AI Engineer ──
    full_path = f"{OUTPUT_DIR}/linkedin_jobs_clean_{ts}.csv"
    df.to_csv(full_path, index=False, encoding="utf-8-sig")
    print(f"  CSV lengkap     → {full_path}")

    # ── B. CSV ringkas (tanpa skill vector columns) untuk EDA/review ──
    core_cols = [
        "id", "title", "standardized_role", "company", "location",
        "job_description", "extracted_skills", "skills_count",
        "job_url", "search_role", "scraped_at"
    ]
    slim_path = f"{OUTPUT_DIR}/linkedin_jobs_slim_{ts}.csv"
    df[core_cols].to_csv(slim_path, index=False, encoding="utf-8-sig")
    print(f"  CSV slim        → {slim_path}")

    # ── C. Summary JSON untuk AI Engineer ──
    all_skills = []
    for s in df["extracted_skills"]:
        all_skills.extend(s)
    skill_freq = Counter(all_skills)

    import json
    summary = {
        "generated_at"        : ts,
        "total_jobs"          : len(df),
        "unique_companies"    : int(df["company"].nunique()),
        "role_distribution"   : df["standardized_role"].value_counts().to_dict(),
        "top_50_skills"       : dict(skill_freq.most_common(50)),
        "avg_skills_per_job"  : round(df["skills_count"].mean(), 2),
        "skills_per_role"     : {},
    }
    for role in df["standardized_role"].unique():
        role_skills = []
        for s in df[df["standardized_role"] == role]["extracted_skills"]:
            role_skills.extend(s)
        top10 = dict(Counter(role_skills).most_common(10))
        summary["skills_per_role"][role] = top10

    json_path = f"{OUTPUT_DIR}/data_summary_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"  Summary JSON    → {json_path}")

    return full_path, slim_path


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════
 
def main():
    print("\n" + "═" * 55)
    print("ETL PIPELINE — DATA PREPROCESSING")
    print("Capstone CC26-PSU404 | Tim Data Scientist")
    print("═" * 55)
 
    # Jalankan pipeline
    df = load_and_clean(INPUT_FILE)
    df = apply_role_standardization(df)
    df = apply_skill_extraction(df)
    df = build_skill_vector(df)
    run_eda(df)
    full_path, slim_path = save_outputs(df)
 
    print("\n" + "═" * 55)
    print("PIPELINE SELESAI")
    print("═" * 55)
    print(f"\nOutput siap diserahkan ke AI Engineer:")
    print(f"  {full_path}")
    print(f"  {slim_path}")
    print(f"\nCatatan untuk AI Engineer:")
    print(f"  - Kolom 'job_description' = bahan baku untuk embedding")
    print(f"  - Kolom 'standardized_role' = label untuk klasifikasi")
    print(f"  - Kolom 'extracted_skills' = list skill per job")
    print(f"  - Kolom 'skill_*' = binary skill vector (baseline)")
 
 
if __name__ == "__main__":
    main()