# capstone-ds
# 📊 Data Science Module - Capstone Project


---

## 📋 Daftar Tugas Data Science

| No | Tugas | Status | Output |
|----|-------|--------|--------|
| 1 | Mengumpulkan & menganalisis permasalahan, menentukan solusi utama | ✅ | Project Brief |
| 2 | Mendefinisikan pertanyaan bisnis yang dapat diukur | ✅ | Business Questions Document |
| 3 | Data Wrangling (Gathering, Assessing, Cleaning) | ⏳ | Clean Dataset |
| 4 | Exploratory Data Analysis (EDA) | ⏳ | Insights Report |
| 5 | Visualisasi data & explanatory analysis | ⏳ | Charts & Dashboard |
| 6 | Dashboard interaktif dengan Streamlit | ⏳ | Live Dashboard |
| 7 | Data Dictionary & dataset siap modeling | ⏳ | JSON for AI Engineer |

---

## 🚫 Larangan yang Harus Dihindari

| Larangan | Cara Menghindari | Status |
|----------|------------------|--------|
| Dataset siap pakai tanpa cleaning manual | Scraping sendiri dari LinkedIn + dokumentasi setiap step cleaning | ✅ |
| Analisis tanpa penjelasan markdown/teks | Setiap notebook memiliki markdown cells yang menjelaskan setiap step | ✅ |
| Kesimpulan tanpa visualisasi data | Setiap insight didukung oleh chart (matplotlib/seaborn/plotly) | ✅ |
| Dataset akhir belum siap untuk pemodelan | Validasi format output + Data Dictionary | ✅ |
| Data leakage (target ke fitur training) | **TIDAK ADA target variable** di dataset (unsupervised learning) | ✅ |

---

## ALUR DATA SCIENTIST


Pipeline ini mengalirkan data dari **sumber mentah (LinkedIn)** hingga menjadi **data bersih siap pakai** untuk AI Engineer. Tim Data Scientist bertanggung jawab penuh atas seluruh proses di bawah ini.

```
LinkedIn Jobs
     │
     ▼
┌─────────────────┐
│  Web Scraping   │  ← Selenium + ChromeDriver
│  (linkedinfix)  │     Login → Klik job → Ambil detail
└────────┬────────┘
         │ Raw CSV
         ▼
┌─────────────────┐
│ Basic Cleaning  │  ← Hapus duplikat, null, JD pendek
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Role Std.     │  ← Keyword mapping + Cosine Similarity
│ (Standardisasi) │     614 unique title → 12 kategori
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Skill Extraction│  ← Regex + master skill list (80+ skill)
│   (Enhanced)    │     dari job_description
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Skill Vector   │  ← Binary encoding top-50 skills
│   (Binary)      │     sebagai baseline untuk AI Engineer
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│      EDA        │  ← Distribusi role, top skills per role,
│                 │     skill gap analysis
└────────┬────────┘
         │
         ├──► CSV Lengkap   (untuk AI Engineer → Embedding)
         ├──► CSV Slim      (untuk review & dokumentasi)
         └──► Summary JSON  (untuk semua tim)
```

---

## Struktur Folder

```
capstone-ds/
│
├── scraping/
│   ├── linkedinfix.py          # Script utama scraping LinkedIn
│   └── data/
│       └── raw/                # Output mentah scraping (.csv per role)
│
├── preprocessing/
│   ├── preprocessing.py        # Script ETL utama (FILE INI)
│   └── data/
│       ├── raw/                # Input: CSV hasil scraping
│       └── processed/          # Output: CSV bersih + JSON summary
│
├── eda/
│   └── eda_notebook.ipynb      # Exploratory Data Analysis (Minggu 4)
│
└── README.md                   # Dokumen ini
```

---

## Penjelasan Setiap Tahap

### Stage 1 — Web Scraping

**Script:** `scraping/linkedinfix.py`  
**Output:** `data/raw/checkpoint_[role]_[timestamp].csv`

Scraper login ke LinkedIn menggunakan Selenium, membuka halaman pencarian job berdasarkan keyword role dan lokasi Indonesia, lalu mengklik setiap job card untuk mengambil detail. Setiap 25 job, scraper mengklik tombol Next untuk pindah halaman.

Field yang dikumpulkan:

| Field | Keterangan |
|---|---|
| `id` | Job ID dari LinkedIn |
| `title` | Judul job (raw, belum distandarisasi) |
| `company` | Nama perusahaan |
| `location` | Lokasi kerja |
| `job_description` | Deskripsi lengkap pekerjaan |
| `job_url` | Link job di LinkedIn |
| `extracted_skills` | Skill yang terdeteksi dari deskripsi |
| `skills_count` | Jumlah skill terdeteksi |
| `scraped_at` | Timestamp scraping |

---

### Stage 2 — Basic Cleaning

**Dilakukan di:** `preprocessing.py → load_and_clean()`

Proses pembersihan awal:
- Hapus baris duplikat berdasarkan `job_url`
- Hapus baris dengan `title` atau `company` kosong
- Filter `job_description` yang terlalu pendek (< 200 karakter) karena tidak informatif untuk embedding
- Bersihkan sisa HTML tags dari teks deskripsi

---

### Stage 3 — Role Standardization ⭐ Tantangan Utama

**Dilakukan di:** `preprocessing.py → standardize_role()`

Ini adalah tahap paling krusial. Data scraping menghasilkan ratusan variasi judul job yang sebenarnya merujuk ke peran yang sama. Contoh:

```
"Power BI Development"                → BI Developer
"Python Developer | Remote"           → Backend Developer
"AI & Data Engineer (Analytics)"      → Data Engineer
"Junior Fullstack Developer Intern"   → Fullstack Developer
"Software and QA Engineer - Intern"   → QA Engineer
```

**Pendekatan yang digunakan (sesuai saran domain expert):**

1. **Keyword Mapping** — Setiap kategori standar memiliki daftar kata kunci. Title yang mengandung kata kunci ini langsung dipetakan. Ini menangani ~85-90% kasus.

2. **Cosine Similarity (TF-IDF)** — Untuk title yang tidak cocok dengan kata kunci manapun, gunakan TF-IDF vectorizer dan hitung cosine similarity antara title dengan semua daftar kata kunci. Ini menangani kasus-kasus edge seperti singkatan atau penulisan tidak standar.

**Kategori standar yang digunakan:**

| Kategori | Contoh title yang dipetakan |
|---|---|
| Data Scientist | Data Scientist, ML Scientist, Research Scientist |
| Data Analyst | Data Analyst, Business Analyst, BI Analyst |
| Data Engineer | Data Engineer, ETL Engineer, Analytics Engineer |
| ML Engineer | ML Engineer, MLOps, AI Engineer, Deep Learning Eng |
| BI Developer | BI Developer, Power BI Dev, Tableau Developer |
| Backend Developer | Backend Dev, Python Dev, Java Dev, API Developer |
| Frontend Developer | Frontend Dev, React Dev, Vue Dev, UI Developer |
| Fullstack Developer | Fullstack, Full Stack, Full-Stack |
| DevOps Engineer | DevOps, Cloud Engineer, SRE, Platform Engineer |
| Mobile Developer | Android Dev, iOS Dev, Flutter Dev, React Native |
| QA Engineer | QA Engineer, Tester, Test Automation Engineer |
| Software Engineer | Software Engineer (fallback umum) |

---

### Stage 4 — Skill Extraction (Enhanced)

**Dilakukan di:** `preprocessing.py → extract_skills_enhanced()`

Re-ekstrak skill dari `job_description` menggunakan master list yang lebih lengkap (80+ skill) dibanding script scraper. Menggunakan regex word boundary agar tidak terjadi false positive (misalnya huruf `r` tidak ter-detect sebagai skill `R`).

**Kenapa re-ekstrak?** Script scraper menggunakan daftar skill yang terbatas. Di tahap ini kita gunakan daftar yang lebih komprehensif dan sudah divalidasi.

---

### Stage 5 — Skill Vector (Binary)

**Dilakukan di:** `preprocessing.py → build_skill_vector()`

Membuat representasi biner dari skill per job. Kolom `skill_python`, `skill_sql`, dst. berisi nilai 1 jika skill tersebut ada di job description, 0 jika tidak.

> **Catatan untuk AI Engineer:** Ini adalah baseline one-hot encoding. Kalian kemungkinan akan menggantinya dengan TF-IDF atau sentence embedding (BERT/SentenceTransformer) untuk representasi yang lebih kaya. Kolom ini tetap berguna sebagai fitur tambahan atau untuk validasi.

---

### Stage 6 — EDA

**Notebook:** `eda/eda_notebook.ipynb`  
**Target selesai:** Minggu 4 (untuk Streamlit dashboard)

Analisis yang dilakukan:
- Distribusi job per role dan per lokasi
- Top 10 skills per role
- Skill gap antar role (misalnya skill apa yang dimiliki Data Analyst tapi tidak ada di Data Scientist)
- Word cloud dari job description per role
- Trend skills (skill mana yang paling banyak diminta)

---

## Output untuk Setiap Tim

### → AI Engineer

File: `data/processed/linkedin_jobs_clean_[timestamp].csv`

Kolom kunci yang dibutuhkan:

| Kolom | Digunakan untuk |
|---|---|
| `job_description` | **Bahan baku embedding** (TF-IDF / BERT) |
| `standardized_role` | **Label klasifikasi** model |
| `extracted_skills` | **Input skill gap analysis** |
| `skill_*` (50 kolom) | Binary feature, baseline model |

### → Backend Developer

File: `data/processed/data_summary_[timestamp].json`

Berisi: distribusi role, top skills global, top skills per role. Berguna untuk seed data awal di database.

### → Frontend Developer

Struktur data yang bisa digunakan untuk mock data:
```json
{
  "role": "Data Scientist",
  "top_skills": ["python", "sql", "tensorflow", "pandas", "aws"],
  "job_count": 142
}
```

---

## Cara Menjalankan

### Requirement

```bash
pip install pandas scikit-learn selenium webdriver-manager openpyxl
```

### Scraping (kumpulkan data dulu)

```bash
cd scraping/
python linkedinfix.py
# Output: data/raw/checkpoint_*.csv
```

### Preprocessing

```bash
cd preprocessing/

# Edit INPUT_FILE di preprocessing.py sesuai path file kalian:
# INPUT_FILE = "data/raw/linkedin_jobs_raw.csv"

python preprocessing.py
# Output: data/processed/linkedin_jobs_clean_*.csv
#         data/processed/linkedin_jobs_slim_*.csv
#         data/processed/data_summary_*.json
```

---

## Konvensi Penamaan File

```
Raw data scraping    : checkpoint_[Role]_[YYYYMMDD_HHMMSS].csv
CSV bersih lengkap   : linkedin_jobs_clean_[YYYYMMDD_HHMMSS].csv
CSV bersih ringkas   : linkedin_jobs_slim_[YYYYMMDD_HHMMSS].csv
Summary JSON         : data_summary_[YYYYMMDD_HHMMSS].json
```

---

## Checklist Sebelum Serahkan ke AI Engineer

```
[ ] Total job ≥ 1.000 baris setelah cleaning
[ ] Tidak ada job dengan job_description kosong
[ ] Kolom standardized_role terisi semua (tidak ada NaN)
[ ] Kategori "Other" < 10% dari total data
[ ] extracted_skills sudah dalam format list Python
[ ] File CSV final sudah di-review minimal 50 baris secara manual
[ ] Data Dictionary sudah ditulis dan di-share ke semua tim
```

---

## Hubungan dengan Sistem Akhir

```
Data kita (CSV bersih)
        │
        ▼
AI Engineer: job_description → Embedding → Supabase Vector DB
                                              │
                              User input skill ┘
                              (cosine similarity search)
                                              │
                                              ▼
                                    Rekomendasi job + skill gap
                                              │
                                              ▼
                               Backend (Express) → Frontend (React)
```

**Singkatnya:** kualitas embedding — dan akhirnya kualitas rekomendasi ke user — sangat bergantung pada kebersihan `job_description` dan akurasi `standardized_role` yang kita hasilkan. Ini tanggung jawab kita sebagai Data Scientist.

---

*Terakhir diperbarui: April 2026 | CC26-PSU404*
