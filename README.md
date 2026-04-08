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

## 📁 Struktur Folder
s/
├── README.md # Dokumentasi ini
├── requirements.txt # Dependencies khusus DS
│
├── scraping/ # #1 Data Gathering
│ ├── linkedin_scraper.py # Script scraping LinkedIn
│ └── utils.py # Fungsi bantu scraping
│
├── notebooks/ # #3 Data Wrangling & #4 EDA
│ ├── 01_data_assessment.ipynb # Assessing Data (kualitas & struktur)
│ ├── 02_data_cleaning.ipynb # Cleaning Data
│ └── 03_eda_analysis.ipynb # Exploratory Data Analysis
│
├── data/
│ ├── raw/ # Data mentah hasil scraping
│ │ └── linkedin_jobs_.csv
│ ├── processed/ # Data setelah cleaning
│ │ └── cleaned_jobs_.csv
│ └── reference/ # #7 Data Dictionary
│ └── data_dictionary.json
│
├── dashboard/ # #6 Streamlit Dashboard
│ └── app.py # Aplikasi dashboard interaktif
│
├── reports/ # #5 Visualisasi & laporan
│ ├── business_questions.md # #2 Pertanyaan bisnis
│ ├── eda_visualizations.png # Chart hasil EDA
│ └── insights_summary.md # Ringkasan insight
│
└── output/ # Output untuk tim lain
└── training_data.json # Dataset siap untuk AI Engineer
