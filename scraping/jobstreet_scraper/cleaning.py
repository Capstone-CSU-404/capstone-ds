import os
import ast
import glob
import pandas as pd
from datetime import datetime
from collections import Counter
 
# ─────────────────────────────────────────────────────────────
# KONFIGURASI — sesuaikan path ini
# ─────────────────────────────────────────────────────────────
INPUT_DIR  = r"C:\Users\ADVAN\Downloads\dicodingcamp\capstoneproject\jobstreet\hasilhasil\raw"
OUTPUT_DIR = r"C:\Users\ADVAN\Downloads\dicodingcamp\capstoneproject\jobstreet\hasilhasil\processed"
 
os.makedirs(OUTPUT_DIR, exist_ok=True)
 
# ─────────────────────────────────────────────────────────────
# 1. GABUNGKAN SEMUA CSV
# ─────────────────────────────────────────────────────────────
csv_files = glob.glob(os.path.join(INPUT_DIR, "checkpoint_*.csv"))
print(f"📂 Ditemukan {len(csv_files)} file CSV:")
for f in csv_files:
    print(f"   • {os.path.basename(f)}")
 
frames = []
for f in csv_files:
    try:
        df_tmp = pd.read_csv(f, dtype=str)          # baca semua sebagai string dulu
        df_tmp["_source_file"] = os.path.basename(f)
        frames.append(df_tmp)
        print(f"   ✅ {os.path.basename(f)}: {len(df_tmp)} baris")
    except Exception as e:
        print(f"   ⚠️ Gagal baca {os.path.basename(f)}: {e}")
 
if not frames:
    raise SystemExit("❌ Tidak ada file yang berhasil dibaca. Cek INPUT_DIR.")
 
df = pd.concat(frames, ignore_index=True)
print(f"\n📊 Total setelah digabung : {len(df):,} baris")
print(f"   Kolom               : {list(df.columns)}")
 
# ─────────────────────────────────────────────────────────────
# 2. CLEANING
# ─────────────────────────────────────────────────────────────
 
# 2a. Hapus duplikat — prioritas: job_id unik; fallback: title+company
before = len(df)
if "id" in df.columns:
    # Hapus id kosong/null dulu dari pengecekan duplikat berdasarkan id
    mask_valid_id = df["id"].notna() & (df["id"].str.strip() != "")
    df_valid   = df[mask_valid_id].drop_duplicates(subset=["id"], keep="last")
    df_no_id   = df[~mask_valid_id].drop_duplicates(
        subset=["title", "company"], keep="last"
    )
    df = pd.concat([df_valid, df_no_id], ignore_index=True)
else:
    df = df.drop_duplicates(subset=["title", "company"], keep="last")
print(f"🗑️  Duplikat dihapus       : {before - len(df):,} baris → sisa {len(df):,}")
 
# 2b. Trim whitespace semua kolom teks
str_cols = df.select_dtypes(include="object").columns
df[str_cols] = df[str_cols].apply(lambda col: col.str.strip())
 
# 2c. Isi nilai kosong yang logis
df["salary"]          = df["salary"].replace("", "Tidak Disebutkan").fillna("Tidak Disebutkan")
df["job_description"] = df["job_description"].fillna("")
df["location"]        = df["location"].fillna("").replace("", "Tidak Disebutkan")
 
# 2d. Hapus baris yang title atau company benar-benar kosong
before = len(df)
df = df[df["title"].notna() & (df["title"] != "")]
df = df[df["company"].notna() & (df["company"] != "")]
print(f"🗑️  Baris tanpa title/co.  : {before - len(df):,} dihapus → sisa {len(df):,}")
 
# 2e. Hapus baris tanpa job_description (opsional — comment jika tidak mau)
before = len(df)
df = df[df["job_description"].str.len() > 10]
print(f"🗑️  JD kosong dihapus      : {before - len(df):,} baris → sisa {len(df):,}")
 
# 2f. Parse kolom extracted_skills dari string list → list Python
def parse_skills(val):
    if isinstance(val, list):
        return val
    if not val or str(val).strip() in ("", "nan", "[]"):
        return []
    try:
        return ast.literal_eval(val)
    except:
        return []
 
df["extracted_skills"] = df["extracted_skills"].apply(parse_skills)
df["skills_count"]     = df["extracted_skills"].apply(len)
 
# 2g. Normalise kolom scraped_at ke datetime
if "scraped_at" in df.columns:
    df["scraped_at"] = pd.to_datetime(df["scraped_at"], errors="coerce")
 
# 2h. Drop kolom helper
df.drop(columns=["_source_file"], errors="ignore", inplace=True)
 
# ─────────────────────────────────────────────────────────────
# 3. SIMPAN OUTPUT
# ─────────────────────────────────────────────────────────────
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
 
# CSV utama (semua kolom termasuk JD)
out_csv = os.path.join(OUTPUT_DIR, f"jobstreet_clean_{ts}.csv")
df.to_csv(out_csv, index=False, encoding="utf-8-sig")
print(f"\n💾 CSV tersimpan   : {out_csv}")
 
# JSON tanpa JD (ringan untuk analisis)
out_json = os.path.join(OUTPUT_DIR, f"jobstreet_clean_{ts}.json")
df.drop(columns=["job_description"], errors="ignore").to_json(
    out_json, orient="records", indent=2, force_ascii=False
)
print(f"💾 JSON tersimpan  : {out_json}")
 
# Excel ringkasan per role
out_xlsx = os.path.join(OUTPUT_DIR, f"jobstreet_clean_{ts}.xlsx")
with pd.ExcelWriter(out_xlsx, engine="openpyxl") as writer:
    # Sheet 1: data lengkap (tanpa JD agar file tidak terlalu besar)
    df.drop(columns=["job_description"], errors="ignore").to_excel(
        writer, sheet_name="Data", index=False
    )
    # Sheet 2: ringkasan per role
    summary = (
        df.groupby("search_role")
          .agg(
              jumlah_jobs   =("id",            "count"),
              ada_salary    =("salary",        lambda x: (x != "Tidak Disebutkan").sum()),
              rata_skills   =("skills_count",  "mean"),
          )
          .round(2)
          .reset_index()
    )
    summary.to_excel(writer, sheet_name="Ringkasan_Role", index=False)
 
    # Sheet 3: top skills keseluruhan
    flat_skills = [s for row in df["extracted_skills"] for s in row]
    skill_df = pd.DataFrame(
        Counter(flat_skills).most_common(50),
        columns=["skill", "jumlah_jobs"]
    )
    skill_df["persen"] = (skill_df["jumlah_jobs"] / len(df) * 100).round(1)
    skill_df.to_excel(writer, sheet_name="Top_Skills", index=False)
 
print(f"💾 Excel tersimpan : {out_xlsx}")
 
# ─────────────────────────────────────────────────────────────
# 4. LAPORAN SINGKAT
# ─────────────────────────────────────────────────────────────
print(f"""
{'='*55}
📋 RINGKASAN HASIL CLEANING
{'='*55}
Total jobs bersih      : {len(df):,}
Role unik              : {df['search_role'].nunique()}
Perusahaan unik        : {df['company'].nunique():,}
Ada salary             : {(df['salary'] != 'Tidak Disebutkan').sum():,} ({(df['salary'] != 'Tidak Disebutkan').mean()*100:.1f}%)
Ada job description    : {(df['job_description'].str.len() > 10).sum():,}
Rata-rata skills/job   : {df['skills_count'].mean():.1f}
{'='*55}
""")
 
print("🔥 Top 20 Skills:")
for skill, cnt in Counter(flat_skills).most_common(20):
    pct = cnt / len(df) * 100
    bar = "█" * int(pct / 2)
    print(f"   {skill:<18} {cnt:>4} jobs  ({pct:4.1f}%)  {bar}")
 
print("\n📌 Distribusi per Role:")
print(df["search_role"].value_counts().to_string())
 
print("\n✅ Selesai!")