import os
import re
import ast
import glob
import pandas as pd
from datetime import datetime
from collections import Counter

# ─────────────────────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────────────────────
INPUT_DIR  = r"C:\Users\ADVAN\Downloads\dicodingcamp\capstoneproject\jobstreet\hasilhasil\raw"
OUTPUT_DIR = r"C:\Users\ADVAN\Downloads\dicodingcamp\capstoneproject\jobstreet\hasilhasil\processed"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ═════════════════════════════════════════════════════════════
# FUNGSI STANDARISASI
# ═════════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────────
# 1. NORMALIZE ROLE
# ─────────────────────────────────────────────────────────────
def normalize_role(role):
    if not isinstance(role, str) or role.strip() == "":
        return "Other"
    r = role.lower()

    if re.search(r'data\s*eng', r):                                      return 'Data Engineer'
    if re.search(r'data\s*sci', r):                                      return 'Data Scientist'
    if re.search(r'data\s*anal|business\s*anal', r):                     return 'Data Analyst'
    if re.search(r'machine\s*learn|ml\s*eng|ai\s*eng|mlops', r):        return 'ML Engineer'
    if re.search(r'bi\s*dev|business\s*intel|bi\s*eng', r):             return 'BI Developer'
    if re.search(r'frontend|front.end|front\s*end|web\s*dev|ui\s*dev',r):return 'Frontend Developer'
    if re.search(r'backend|back.end|back\s*end', r):                     return 'Backend Developer'
    if re.search(r'fullstack|full.stack|full\s*stack', r):               return 'Fullstack Developer'
    if re.search(r'mobile|android|ios|flutter|react\s*native', r):      return 'Mobile Developer'
    if re.search(r'devops|sre|site\s*reliab|platform\s*eng', r):        return 'DevOps Engineer'
    if re.search(r'sysadmin|system\s*admin|network|infra', r):          return 'IT Infrastructure'
    if re.search(r'qa\s*eng|quality\s*assur|tester|testing', r):        return 'QA Engineer'
    if re.search(r'system\s*anal|sys\s*anal|business\s*sys', r):        return 'System Analyst'
    if re.search(r'it\s*support|helpdesk|help\s*desk|technical\s*sup',r):return 'IT Support'
    if re.search(r'software\s*eng|developer|programmer', r):             return 'Software Engineer'
    if re.search(r'cloud|aws|gcp|azure\s*eng', r):                      return 'Cloud Engineer'
    if re.search(r'security|cyber|penetration|pentest', r):             return 'Cybersecurity'
    if re.search(r'product\s*man|pm\b', r):                             return 'Product Manager'
    if re.search(r'scrum|agile\s*coach|project\s*man', r):              return 'Project Manager'
    if re.search(r'business\s*dev|biz\s*dev|bd\b', r):                  return 'Business Development'
    return 'Other'


# ─────────────────────────────────────────────────────────────
# 2. NORMALIZE LOKASI  →  Provinsi / Kota standar
# ─────────────────────────────────────────────────────────────
LOCATION_MAP = {
    # ── DKI Jakarta ──────────────────────────────────────────
    r'jakarta|jaksel|jakpus|jakbar|jakut|jaktim|jak\b': 'DKI Jakarta',

    # ── Jawa Barat ───────────────────────────────────────────
    r'bandung|bekasi|depok|bogor|cimahi|sukabumi|karawang|purwakarta'
    r'|cirebon|tasikmalaya|garut|subang|cianjur|indramayu': 'Jawa Barat',

    # ── Banten ───────────────────────────────────────────────
    r'tangerang|banten|serang|cilegon|serpong|alam\s*sutera': 'Banten',

    # ── Jawa Tengah ──────────────────────────────────────────
    r'semarang|solo|surakarta|yogyakarta|jogja|magelang|kudus'
    r'|pekalongan|tegal|purwokerto|salatiga|klaten': 'Jawa Tengah',

    # ── D.I. Yogyakarta ──────────────────────────────────────
    r'yogyakarta|jogja|sleman|bantul|gunung\s*kidul|kulon\s*progo': 'D.I. Yogyakarta',

    # ── Jawa Timur ───────────────────────────────────────────
    r'surabaya|malang|sidoarjo|gresik|mojokerto|pasuruan|probolinggo'
    r'|jember|kediri|madiun|blitar|tulungagung|banyuwangi': 'Jawa Timur',

    # ── Sumatera ─────────────────────────────────────────────
    r'medan|deli\s*serdang|binjai|tebing\s*tinggi': 'Sumatera Utara',
    r'palembang|prabumulih|lubuklinggau': 'Sumatera Selatan',
    r'pekanbaru|dumai|riau': 'Riau',
    r'batam|kepri|kepulauan\s*riau|tanjung\s*pinang': 'Kepulauan Riau',
    r'padang|bukittinggi|sumatera\s*barat': 'Sumatera Barat',
    r'banda\s*aceh|aceh|lhokseumawe': 'Aceh',
    r'jambi': 'Jambi',
    r'lampung|bandar\s*lampung': 'Lampung',
    r'bengkulu': 'Bengkulu',

    # ── Kalimantan ───────────────────────────────────────────
    r'balikpapan|samarinda|bontang|kaltim|kalimantan\s*timur': 'Kalimantan Timur',
    r'banjarmasin|banjarbaru|kalsel|kalimantan\s*selatan': 'Kalimantan Selatan',
    r'pontianak|singkawang|kalbar|kalimantan\s*barat': 'Kalimantan Barat',
    r'palangka\s*raya|kalteng|kalimantan\s*tengah': 'Kalimantan Tengah',
    r'tarakan|nunukan|kaltara|kalimantan\s*utara': 'Kalimantan Utara',

    # ── Sulawesi ─────────────────────────────────────────────
    r'makassar|sulsel|sulawesi\s*selatan|gowa|maros': 'Sulawesi Selatan',
    r'manado|sulut|sulawesi\s*utara|tomohon|bitung': 'Sulawesi Utara',
    r'palu|sulteng|sulawesi\s*tengah': 'Sulawesi Tengah',
    r'kendari|sultra|sulawesi\s*tenggara': 'Sulawesi Tenggara',

    # ── Bali & Nusa Tenggara ─────────────────────────────────
    r'bali|denpasar|badung|gianyar|tabanan|singaraja': 'Bali',
    r'mataram|lombok|ntb|nusa\s*tenggara\s*barat': 'NTB',
    r'kupang|ntт|nusa\s*tenggara\s*timur': 'NTT',

    # ── Papua & Maluku ────────────────────────────────────────
    r'jayapura|papua': 'Papua',
    r'ambon|maluku': 'Maluku',

    # ── Remote / Global ──────────────────────────────────────
    r'remote|work\s*from\s*home|wfh|hybrid': 'Remote / WFH',
    r'singapore|singapura': 'Singapura',
    r'malaysia|kuala\s*lumpur|kl\b': 'Malaysia',
}

def normalize_location(loc):
    if not isinstance(loc, str) or loc.strip() in ("", "Tidak Disebutkan"):
        return "Tidak Disebutkan"
    loc_lower = loc.lower()
    for pattern, province in LOCATION_MAP.items():
        if re.search(pattern, loc_lower):
            return province
    return "Lainnya"


# ─────────────────────────────────────────────────────────────
# 3. NORMALIZE SALARY  →  salary_min, salary_max (integer IDR)
# ─────────────────────────────────────────────────────────────
def clean_number(s):
    """Hapus titik ribuan, ganti koma desimal → int."""
    s = re.sub(r'[^\d,.]', '', s)
    s = s.replace('.', '').replace(',', '')
    return int(s) if s.isdigit() else None

def parse_salary(raw):
    """
    Input  : "Rp 5.000.000 - Rp 8.000.000" / "5jt-8jt" / "Tidak Disebutkan"
    Output : (salary_min, salary_max, salary_display)
    """
    if not isinstance(raw, str) or raw.strip() in ("", "Tidak Disebutkan", "nan"):
        return None, None, "Tidak Disebutkan"

    s = raw.strip()

    # Handle "jt" / "juta" shorthand  → kalikan 1_000_000
    juta_match = re.findall(r'(\d+(?:[.,]\d+)?)\s*(?:jt|juta)', s, re.IGNORECASE)
    if juta_match:
        nums = [int(float(n.replace(',', '.')) * 1_000_000) for n in juta_match]
        lo, hi = (min(nums), max(nums)) if len(nums) >= 2 else (nums[0], nums[0])
        return lo, hi, f"Rp {lo:,} – Rp {hi:,}".replace(",", ".")

    # Handle angka biasa (dengan atau tanpa range)
    nums = re.findall(r'\d[\d.,]*', s)
    cleaned = [clean_number(n) for n in nums]
    cleaned = [n for n in cleaned if n and n >= 100_000]   # minimal 100rb = valid IDR

    if not cleaned:
        return None, None, "Tidak Disebutkan"
    if len(cleaned) == 1:
        return cleaned[0], cleaned[0], f"Rp {cleaned[0]:,}".replace(",", ".")
    lo, hi = min(cleaned), max(cleaned)
    return lo, hi, f"Rp {lo:,} – Rp {hi:,}".replace(",", ".")


# ─────────────────────────────────────────────────────────────
# 4. NORMALIZE JOB LEVEL  (dari title & JD)
# ─────────────────────────────────────────────────────────────
def normalize_level(title, jd=""):
    text = f"{title} {jd}".lower()
    if re.search(r'senior|sr\.|lead|principal|staff\s*eng|expert', text): return 'Senior'
    if re.search(r'junior|jr\.|entry.level|fresh\s*grad|magang|intern', text): return 'Junior'
    if re.search(r'manager|head|director|vp\b|chief|c[to]o\b', text): return 'Managerial'
    if re.search(r'mid.level|medior|\bmid\b', text): return 'Mid'
    return 'Tidak Disebutkan'


# ═════════════════════════════════════════════════════════════
# PIPELINE
# ═════════════════════════════════════════════════════════════

# ── 1. Gabungkan ─────────────────────────────────────────────
csv_files = glob.glob(os.path.join(INPUT_DIR, "checkpoint_*.csv"))
print(f"📂 Ditemukan {len(csv_files)} file CSV")

frames = []
for f in csv_files:
    try:
        tmp = pd.read_csv(f, dtype=str)
        tmp["_source"] = os.path.basename(f)
        frames.append(tmp)
    except Exception as e:
        print(f"   ⚠️ Gagal baca {os.path.basename(f)}: {e}")

if not frames:
    raise SystemExit("❌ Tidak ada file yang berhasil dibaca. Cek INPUT_DIR.")

df = pd.concat(frames, ignore_index=True)
print(f"📊 Digabung        : {len(df):,} baris")

# ── 2. Cleaning dasar ────────────────────────────────────────
# Trim whitespace
str_cols = df.select_dtypes(include="object").columns
df[str_cols] = df[str_cols].apply(lambda c: c.str.strip())

# Duplikat
before = len(df)
if "id" in df.columns:
    mask = df["id"].notna() & (df["id"].str.strip() != "")
    df = pd.concat([
        df[mask].drop_duplicates(subset=["id"], keep="last"),
        df[~mask].drop_duplicates(subset=["title","company"], keep="last")
    ], ignore_index=True)
else:
    df = df.drop_duplicates(subset=["title","company"], keep="last")
print(f"🗑️  Duplikat        : {before-len(df):,} dihapus → {len(df):,}")

# Hapus baris tanpa title/company
df = df[df["title"].notna() & (df["title"] != "")]
df = df[df["company"].notna() & (df["company"] != "")]

# Isi kosong
df["job_description"] = df["job_description"].fillna("")
df["salary"]          = df["salary"].fillna("Tidak Disebutkan").replace("", "Tidak Disebutkan")
df["location"]        = df["location"].fillna("").replace("", "Tidak Disebutkan")

# Parse skills
def parse_skills(val):
    if isinstance(val, list): return val
    if not val or str(val).strip() in ("", "nan", "[]"): return []
    try: return ast.literal_eval(val)
    except: return []

df["extracted_skills"] = df["extracted_skills"].apply(parse_skills)

# ── 3. STANDARISASI ──────────────────────────────────────────
print("🔧 Standarisasi kolom...")

# Role
df["search_role_raw"] = df["search_role"].copy()   # simpan aslinya
df["search_role"]     = df["search_role"].apply(normalize_role)

# Lokasi
df["location_raw"]    = df["location"].copy()
df["location"]        = df["location"].apply(normalize_location)

# Salary
sal = df["salary"].apply(parse_salary)
df["salary_min"]      = sal.apply(lambda x: x[0])
df["salary_max"]      = sal.apply(lambda x: x[1])
df["salary_display"]  = sal.apply(lambda x: x[2])
df["salary_avg"]      = df[["salary_min","salary_max"]].mean(axis=1)

# Job Level
df["job_level"] = df.apply(
    lambda r: normalize_level(r.get("title",""), r.get("job_description","")), axis=1
)

# Skills count (refresh)
df["skills_count"] = df["extracted_skills"].apply(len)

# scraped_at
if "scraped_at" in df.columns:
    df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")

# Hapus helper kolom
df.drop(columns=["_source"], errors="ignore", inplace=True)

# ── 4. Urutan kolom yang rapi ─────────────────────────────────
COLS_ORDER = [
    "id","title","search_role","search_role_raw","job_level",
    "company","location","location_raw",
    "salary_display","salary_min","salary_max","salary_avg",
    "extracted_skills","skills_count",
    "job_url","job_description","search_location","scraped_at",
]
existing = [c for c in COLS_ORDER if c in df.columns]
extra    = [c for c in df.columns if c not in existing]
df       = df[existing + extra]

# ── 5. Simpan ─────────────────────────────────────────────────
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

out_csv  = os.path.join(OUTPUT_DIR, f"jobstreet_final_{ts}.csv")
out_json = os.path.join(OUTPUT_DIR, f"jobstreet_final_{ts}.json")


df.to_csv(out_csv, index=False, encoding="utf-8-sig")

df.drop(columns=["job_description"], errors="ignore").to_json(
    out_json, orient="records", indent=2, force_ascii=False
)


print(f"\n💾 CSV   : {out_csv}")
print(f"💾 JSON  : {out_json}")


# ── 6. Laporan ───────────────────────────────────────────────
flat = [s for row in df["extracted_skills"] for s in row]
print(f"""
{'='*55}
📋 RINGKASAN AKHIR
{'='*55}
Total jobs bersih   : {len(df):,}
Role unik           : {df['search_role'].nunique()}
Perusahaan unik     : {df['company'].nunique():,}
Lokasi unik         : {df['location'].nunique()}
Ada salary          : {df['salary_min'].notna().sum():,} ({df['salary_min'].notna().mean()*100:.1f}%)
Rata-rata skills    : {df['skills_count'].mean():.1f}
{'='*55}
""")

print("📌 Distribusi Role:")
print(df["search_role"].value_counts().to_string())

print("\n📍 Top 10 Lokasi:")
print(df["location"].value_counts().head(10).to_string())

print("\n🎯 Distribusi Job Level:")
print(df["job_level"].value_counts().to_string())

print("\n🔥 Top 20 Skills:")
for skill, cnt in Counter(flat).most_common(20):
    pct = cnt / len(df) * 100
    bar = "█" * int(pct / 2)
    print(f"   {skill:<20} {cnt:>4} ({pct:4.1f}%)  {bar}")

