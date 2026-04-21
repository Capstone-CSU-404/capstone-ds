from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
from datetime import datetime
import os

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
TARGET_JOB_ROLES = [
    "data scientist",
    "data analyst",
]

LOCATION      = "indonesia"
JOBS_PER_ROLE = 500
OUTPUT_DIR    = r"C:\Users\asus3\Documents\CPSTNPROJECT\capstone-ds\Data"

os.makedirs(f"{OUTPUT_DIR}/raw",       exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/processed", exist_ok=True)

SKILLS_LIST = {
    'python','java','javascript','typescript','golang','php','swift','kotlin',
    'scala','r','c++','c#','rust','react','angular','vue','django','flask',
    'fastapi','spring boot','express','tensorflow','pytorch','keras',
    'scikit-learn','pandas','numpy','sql','postgresql','mysql','mongodb',
    'redis','elasticsearch','aws','gcp','azure','docker','kubernetes',
    'hadoop','spark','kafka','airflow','tableau','power bi','flutter',
    'android','ios','agile','scrum','git','linux','bash',
}

def extract_skills(description):
    if not description:
        return []
    return [s for s in SKILLS_LIST if s in description.lower()]

# ─────────────────────────────────────────────
# SETUP DRIVER
# ─────────────────────────────────────────────
def create_driver():
    options = Options()
    # options.add_argument("--headless=new")  # Aktifkan saat production
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

def safe_text(parent, css, default=""):
    try:
        return parent.find_element(By.CSS_SELECTOR, css).get_attribute("innerText").strip()
    except:
        return default

def safe_attr(parent, css, attr, default=""):
    try:
        return parent.find_element(By.CSS_SELECTOR, css).get_attribute(attr) or default
    except:
        return default

# ─────────────────────────────────────────────
# HELPER: Scroll panel KIRI (job list)
#
# Logika sama dengan LinkedIn — container job list
# perlu di-scroll agar semua card ter-load.
# Di JobStreet containernya adalah div hasil pencarian,
# bukan body, jadi kita scroll element-nya langsung.
# ─────────────────────────────────────────────
def scroll_job_list(driver, times=3):
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)
    driver.execute_script("window.scrollTo(0, 0)")
    time.sleep(0.5)

# ─────────────────────────────────────────────
# CORE: Scrape SATU halaman JobStreet
#
# PERSAMAAN dengan LinkedIn:
# - Klik card → panel kanan muncul (detail job)
# - Ambil deskripsi dari panel kanan
# - Tidak perlu buka tab baru (lebih cepat & stabil)
#
# PERBEDAAN dari LinkedIn:
# - Tidak perlu login
# - Selector card: article[data-automation="normalJob"]
#   bukan li.jobs-search-results__list-item
# - Selector deskripsi: div.kx2b1u0
#   bukan div.jobs-description__content
# - Panel kanan JobStreet berisi data-automation yang clean
# ─────────────────────────────────────────────
def scrape_one_page(driver, wait, role, location):
    results = []

    # Tunggu card muncul
    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'article[data-automation="normalJob"]')
        ))
    except:
        print("  ⚠️ Tidak ada job card di halaman ini")
        return results

    scroll_job_list(driver, times=3)

    # Ambil semua job card
    # HTML: <article data-automation="normalJob" data-job-id="91574175">
    job_cards = driver.find_elements(
        By.CSS_SELECTOR, 'article[data-automation="normalJob"]'
    )
    print(f"  📋 {len(job_cards)} card ditemukan")

    for idx, card in enumerate(job_cards):
        try:
            # ── DATA DARI CARD (panel kiri) ──────────────────────
            # Job ID langsung dari attribute HTML
            # HTML: <article data-job-id="91574175">
            job_id = card.get_attribute("data-job-id") or ""

            # Title
            # HTML: <a data-automation="jobTitle">Software Engineer</a>
            job_title = safe_text(card, 'a[data-automation="jobTitle"]')

            # Company
            # HTML: <a data-automation="jobCompany">PT XYZ</a>
            company = safe_text(card, 'a[data-automation="jobCompany"]')

            # Location — bisa lebih dari 1 (Jakarta Selatan, Jakarta Raya)
            # HTML: <a data-automation="jobLocation">Jakarta Selatan</a>
            try:
                loc_els = card.find_elements(
                    By.CSS_SELECTOR, 'a[data-automation="jobLocation"]'
                )
                location_val = ", ".join(
                    el.get_attribute("innerText").strip() for el in loc_els
                )
            except:
                location_val = ""

            # URL job
            raw_href = safe_attr(card, 'a[data-automation="jobTitle"]', "href")
            if raw_href.startswith("/"):
                job_url = "https://id.jobstreet.com" + raw_href.split("?")[0]
            elif raw_href.startswith("http"):
                job_url = raw_href.split("?")[0]
            else:
                job_url = ""

            # Salary (bonus — tidak ada di LinkedIn!)
            # HTML: <span data-automation="jobSalary">Rp 8.000.000</span>
            salary = safe_text(card, 'span[data-automation="jobSalary"]')

            # ── KLIK CARD → BUKA PANEL KANAN ────────────────────
            # KOREKSI dari versi sebelumnya:
            # JobStreet PUNYA panel kanan, sama persis dengan LinkedIn.
            # Kita klik title card → panel kanan load → ambil deskripsi.
            # TIDAK perlu buka tab baru (lebih cepat & tidak ribet).
            #
            # HTML panel kanan (dari paste HTML detail):
            # h1[data-automation="job-detail-title"]   → title
            # span[data-automation="advertiser-name"]  → company
            # a[data-automation="job-detail-location"] → lokasi
            # div.kx2b1u0                              → job description ← kunci!
            jd_text = ""

            try:
                # Scroll card ke viewport dulu
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", card
                )
                time.sleep(0.3)

                # Klik title card (bukan apply button)
                clickable = card.find_element(
                    By.CSS_SELECTOR, 'a[data-automation="jobTitle"]'
                )
                driver.execute_script("arguments[0].click();", clickable)
                time.sleep(2.5)  # Tunggu panel kanan render

                # Tunggu panel kanan muncul
                # Dari HTML paste: div.kx2b1u0 adalah container deskripsi
                wait.until(EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.kx2b1u0")
                ))

                # Ambil job description dari panel kanan
                jd_text = driver.find_element(
                    By.CSS_SELECTOR, "div.kx2b1u0"
                ).get_attribute("innerText").strip()

                # Verifikasi tambahan: cek judul di panel kanan
                # sesuai dengan card yang diklik (guard terhadap panel lama)
                panel_title = safe_text(
                    driver,
                    'h1[data-automation="job-detail-title"]'
                )
                if panel_title and job_title and panel_title not in job_title:
                    print(f"    ⚠️ Panel mismatch, skip JD untuk: {job_title}")
                    jd_text = ""

            except Exception as e:
                print(f"    ⚠️ Gagal ambil detail panel job {idx+1}: {e}")

            # ── EKSTRAK SKILLS & SIMPAN ──────────────────────────
            skills = extract_skills(jd_text)
            record = {
                "id"              : job_id,
                "title"           : job_title,
                "company"         : company,
                "location"        : location_val,
                "job_description" : jd_text,
                "job_url"         : job_url,
                "salary"          : salary,
                "search_role"     : role,
                "search_location" : location,
                "extracted_skills": skills,
                "skills_count"    : len(skills),
                "scraped_at"      : datetime.now().isoformat(),
            }
            results.append(record)
            print(f"  ✅ [{len(results)}] {job_title} — {company} | Skills: {len(skills)}")

        except Exception as e:
            print(f"  ⚠️ Error card {idx+1}: {e}")
            continue

        time.sleep(0.8)  # Jeda kecil antar card

    return results


# ─────────────────────────────────────────────
# MAIN: Paginasi dengan tombol "Selanjutnya"
#
# KOREKSI dari versi sebelumnya:
# JobStreet PUNYA tombol "Selanjutnya" (seperti LinkedIn).
# Kita pakai klik tombol sebagai strategi utama,
# dengan fallback URL ?page=N jika tombol tidak ditemukan.
#
# Mengapa pakai klik tombol?
# → Lebih aman: tombol hanya muncul jika halaman berikutnya ada
# → Konsisten dengan behavior user asli (anti-bot lebih jinak)
#
# Mengapa ada fallback URL?
# → Jika tombol gagal ditemukan/diklik (flaky), URL tetap bisa dipakai
# ─────────────────────────────────────────────
def click_next_button(driver, wait):
    """
    Klik tombol 'Selanjutnya' di JobStreet.
    HTML: <span>...<span class="_36523feh">Selanjutnya</span>...</span>
    Tombol ini wrap dalam elemen yang bisa diklik.
    Kita pakai XPath karena Selenium CSS tidak support :contains()
    """
    try:
        # XPath: cari elemen yang mengandung teks "Selanjutnya"
        # dan merupakan bagian dari tombol navigasi pagination
        next_btn = wait.until(EC.element_to_be_clickable((
            By.XPATH,
            "//span[contains(@class,'_36523feh') and text()='Selanjutnya']"
            "/ancestor::a | "
            "//span[contains(@class,'_36523feh') and text()='Selanjutnya']"
            "/ancestor::button"
        )))
        driver.execute_script("arguments[0].scrollIntoView();", next_btn)
        driver.execute_script("arguments[0].click();", next_btn)
        print("  ➡️ Klik tombol Selanjutnya")
        time.sleep(3)
        return True
    except:
        return False


def scrape_jobstreet_role(driver, role, location, target_count):
    all_jobs  = []
    wait      = WebDriverWait(driver, 15)
    page_num  = 1

    role_slug = role.strip().replace(" ", "-")
    # URL halaman pertama
    url = f"https://id.jobstreet.com/id/{role_slug}-jobs?sortmode=ListedDate"

    print(f"\n🌐 Membuka: {url}")
    driver.get(url)
    time.sleep(4)

    while len(all_jobs) < target_count:
        print(f"\n  📄 Halaman {page_num}")

        # Pastikan ada job card
        try:
            driver.find_element(
                By.CSS_SELECTOR, 'article[data-automation="normalJob"]'
            )
        except:
            print(f"  🏁 Tidak ada job card di halaman {page_num}, berhenti.")
            break

        # Scrape halaman ini
        page_results = scrape_one_page(driver, wait, role, location)

        if not page_results:
            print(f"  🏁 Halaman {page_num} kosong, berhenti.")
            break

        all_jobs.extend(page_results)
        print(f"  📈 Total: {len(all_jobs)} / {target_count}")

        if len(all_jobs) >= target_count:
            break

        # ── PAGINASI: Coba klik "Selanjutnya" dulu ──────────────
        # Fallback: kalau gagal, pakai URL langsung
        success = click_next_button(driver, wait)

        if not success:
            # Fallback: langsung navigate ke page berikutnya via URL
            page_num += 1
            fallback_url = (
                f"https://id.jobstreet.com/id/{role_slug}-jobs"
                f"?sortmode=ListedDate&page={page_num}"
            )
            print(f"  ⚠️ Tombol gagal, fallback URL: {fallback_url}")
            driver.get(fallback_url)
            time.sleep(3)
        else:
            page_num += 1

        # Cek apakah URL berubah (konfirmasi pindah halaman)
        # Jika URL sama berarti sudah halaman terakhir
        time.sleep(2)

    return all_jobs


# ─────────────────────────────────────────────
# JALANKAN SEMUA ROLE
# ─────────────────────────────────────────────
driver   = create_driver()
all_jobs = []

for role in TARGET_JOB_ROLES:
    print(f"\n{'='*55}")
    print(f"📌 Role: {role}")
    print(f"{'='*55}")

    role_jobs = scrape_jobstreet_role(driver, role, LOCATION, JOBS_PER_ROLE)
    all_jobs.extend(role_jobs)

    print(f"✅ Selesai '{role}': {len(role_jobs)} jobs")

    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pd.DataFrame(role_jobs).to_csv(
        f"{OUTPUT_DIR}/raw/checkpoint_{role.replace(' ','_')}_{ts}.csv",
        index=False
    )
    time.sleep(5)

# ─────────────────────────────────────────────
# SIMPAN FINAL
# ─────────────────────────────────────────────
df  = pd.DataFrame(all_jobs)
ts  = datetime.now().strftime("%Y%m%d_%H%M%S")

df.to_csv(
    f"{OUTPUT_DIR}/processed/jobstreet_jobs_{ts}.csv",
    index=False, encoding="utf-8-sig"
)
df.drop(columns=["job_description"], errors="ignore").to_json(
    f"{OUTPUT_DIR}/processed/jobstreet_jobs_{ts}.json",
    orient="records", indent=2, force_ascii=False
)

print(f"\n✅ Total: {len(df)} jobs tersimpan")

# Laporan Skills
from collections import Counter
flat = [s for row in df["extracted_skills"].dropna()
        if isinstance(row, list) for s in row]
print("\n🔥 Top 20 Skills:")
for skill, cnt in Counter(flat).most_common(20):
    print(f"   {skill:<20} {cnt:>4} jobs  ({cnt/len(df)*100:.1f}%)")

driver.quit()
print("\n🏁 Selesai!")