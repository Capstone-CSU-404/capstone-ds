
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
# Logika: Tidak perlu login karena JobStreet publik
# ─────────────────────────────────────────────
TARGET_JOB_ROLES = [
    "web"]

LOCATION      = "indonesia"
JOBS_PER_ROLE = 50
MAX_PAGES     = 20   # JobStreet max ~20 halaman per search
OUTPUT_DIR    = r"C:\Users\asus3\Documents\CPSTNPROJECT\capstone-ds\Data"

os.makedirs(f"{OUTPUT_DIR}/raw",       exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/processed", exist_ok=True)

# ─────────────────────────────────────────────
# SKILLS LIST (sama seperti LinkedIn)
# ─────────────────────────────────────────────
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
    desc_lower = description.lower()
    return [s for s in SKILLS_LIST if s in desc_lower]

# ─────────────────────────────────────────────
# SETUP DRIVER
# Logika: Sama seperti LinkedIn, tapi TANPA login step.
# --disable-blink-features tetap diperlukan agar
# Cloudflare tidak mendeteksi ini sebagai bot.
# ─────────────────────────────────────────────
def create_driver():
    options = Options()
    # options.add_argument("--headless=new")  # Aktifkan saat production
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    # Sembunyikan tanda webdriver dari JavaScript
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver

# ─────────────────────────────────────────────
# HELPER: Safe get text dari elemen
# Logika: Sama persis dengan LinkedIn —
# try/except agar 1 field gagal tidak crash semua
# ─────────────────────────────────────────────
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
# HELPER: Scroll halaman
# Logika: JobStreet pakai infinite-scroll ringan,
# cukup scroll ke bawah 2x untuk trigger lazy load
# ─────────────────────────────────────────────
def scroll_page(driver, times=2):
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)
    # Scroll balik ke atas agar card pertama tetap ter-render
    driver.execute_script("window.scrollTo(0, 0)")
    time.sleep(0.5)

# ─────────────────────────────────────────────
# CORE: Scrape SATU halaman JobStreet
#
# PERBEDAAN BESAR dari LinkedIn:
# LinkedIn  → klik card → panel kanan muncul → ambil detail
# JobStreet → semua data ada di card listing langsung
#             (title, company, location, URL, salary)
#             job_description hanya ada di halaman detail
#             → kita buka tab baru untuk ambil deskripsi
# ─────────────────────────────────────────────
def scrape_one_page(driver, wait, role, location):
    results = []

    # Tunggu card muncul — selector utama JobStreet
    # article[data-automation="normalJob"] adalah setiap job card
    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'article[data-automation="normalJob"]')
        ))
    except:
        print("  ⚠️ Tidak ada job card di halaman ini")
        return results

    # Scroll untuk load lazy images / card tersembunyi
    scroll_page(driver, times=2)

    # Ambil semua job card di halaman
    job_cards = driver.find_elements(
        By.CSS_SELECTOR, 'article[data-automation="normalJob"]'
    )
    print(f"  📋 {len(job_cards)} card ditemukan")

    for idx, card in enumerate(job_cards):
        try:
            # ── AMBIL DATA DARI CARD LISTING ──────────────────────
            # Logika: JobStreet menyimpan job_id langsung di attribute
            # HTML: <article data-job-id="91574175" ...>
            job_id = card.get_attribute("data-job-id") or ""

            # HTML: <a data-automation="jobTitle">Software Engineer</a>
            job_title = safe_text(card, 'a[data-automation="jobTitle"]')

            # HTML: <a data-automation="jobCompany">PT XYZ</a>
            company = safe_text(card, 'a[data-automation="jobCompany"]')

            # HTML: <a data-automation="jobLocation">Jakarta Selatan</a>
            # Ada kemungkinan lebih dari 1 lokasi, ambil semua lalu join
            try:
                loc_els = card.find_elements(
                    By.CSS_SELECTOR, 'a[data-automation="jobLocation"]'
                )
                location_val = ", ".join(
                    [el.get_attribute("innerText").strip() for el in loc_els]
                )
            except:
                location_val = ""

            # URL dari href pada title link
            # HTML: <a href="/id/job/91574175?..." data-automation="jobTitle">
            raw_href = safe_attr(card, 'a[data-automation="jobTitle"]', "href")
            if raw_href.startswith("/"):
                job_url = "https://id.jobstreet.com" + raw_href.split("?")[0]
            elif raw_href.startswith("http"):
                job_url = raw_href.split("?")[0]
            else:
                job_url = ""

            # Bonus: Salary (tidak ada di LinkedIn!)
            # HTML: <span data-automation="jobSalary">Rp 8.000.000</span>
            salary = safe_text(card, 'span[data-automation="jobSalary"]')

            # ── AMBIL JOB DESCRIPTION (BUKA TAB BARU) ────────────
            # Logika: Di LinkedIn kita klik card → panel kanan muncul
            # Di JobStreet tidak ada panel kanan → kita buka URL detail
            # di tab baru agar list page tidak ter-navigate
            jd_text = ""
            if job_url:
                try:
                    # Buka tab baru
                    driver.execute_script("window.open(arguments[0], '_blank');", job_url)
                    driver.switch_to.window(driver.window_handles[-1])

                    # Tunggu description muncul
                    # HTML detail: <div data-automation="jobAdDetails">
                    wait.until(EC.presence_of_element_located(
                        (By.CSS_SELECTOR, '[data-automation="jobAdDetails"]')
                    ))
                    time.sleep(1)

                    jd_text = driver.find_element(
                        By.CSS_SELECTOR, '[data-automation="jobAdDetails"]'
                    ).get_attribute("innerText").strip()

                except Exception as e:
                    # Fallback: coba selector alternatif
                    try:
                        jd_text = driver.find_element(
                            By.CSS_SELECTOR, 
                            'div[class*="jobDescription"], section[class*="jobDescription"]'
                        ).get_attribute("innerText").strip()
                    except:
                        pass

                finally:
                    # Tutup tab detail, kembali ke list
                    driver.close()
                    driver.switch_to.window(driver.window_handles[0])
                    time.sleep(1.5)  # Jeda agar tidak rate-limited

            # ── EKSTRAK SKILLS & SIMPAN RECORD ───────────────────
            skills = extract_skills(jd_text)
            record = {
                "id"              : job_id,
                "title"           : job_title,
                "company"         : company,
                "location"        : location_val,
                "job_description" : jd_text,
                "job_url"         : job_url,
                "salary"          : salary,          # bonus dari JobStreet
                "search_role"     : role,
                "search_location" : location,
                "extracted_skills": skills,
                "skills_count"    : len(skills),
                "scraped_at"      : datetime.now().isoformat(),
            }
            results.append(record)
            print(f"  ✅ [{idx+1}] {job_title} — {company} | Skills: {len(skills)}")

        except Exception as e:
            print(f"  ⚠️ Error card {idx+1}: {e}")
            continue

    return results


# ─────────────────────────────────────────────
# MAIN: Scrape semua halaman per role
#
# PERBEDAAN BESAR dari LinkedIn:
# LinkedIn  → klik tombol "Next" yang ada di DOM
# JobStreet → ganti URL langsung dengan ?page=N
#             Lebih stabil, tidak bergantung DOM button
# ─────────────────────────────────────────────
def scrape_jobstreet_role(driver, role, location, target_count):
    all_jobs = []
    wait = WebDriverWait(driver, 15)

    # Encode role untuk URL: "data scientist" → "data-scientist"
    role_slug = role.strip().replace(" ", "-")
    loc_slug  = location.strip().replace(" ", "-")

    for page_num in range(1, MAX_PAGES + 1):
        if len(all_jobs) >= target_count:
            print(f"  🎯 Target {target_count} tercapai, stop.")
            break

        # JobStreet URL pattern:
        # /id/{role}-jobs/in-{location}?page=N&sortmode=ListedDate
        url = (
            f"https://id.jobstreet.com/id/{role_slug}-jobs"
            f"?sortmode=ListedDate&page={page_num}"
        )

        print(f"\n  📄 Halaman {page_num}: {url}")
        driver.get(url)
        time.sleep(3)  # Tunggu render awal

        # Cek apakah halaman masih ada jobnya
        # (kalau halaman kosong, jobstreet redirect atau tidak ada artikel)
        try:
            driver.find_element(
                By.CSS_SELECTOR, 'article[data-automation="normalJob"]'
            )
        except:
            print(f"  🏁 Tidak ada job di halaman {page_num}, berhenti.")
            break

        page_results = scrape_one_page(driver, wait, role, location)

        if not page_results:
            print(f"  🏁 Halaman {page_num} kosong, berhenti.")
            break

        all_jobs.extend(page_results)
        print(f"  📈 Total terkumpul: {len(all_jobs)}")

        # Delay antar halaman (penting untuk menghindari ban)
        time.sleep(3)

    return all_jobs


# ─────────────────────────────────────────────
# STEP 1: JALANKAN SEMUA ROLE
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
    print(f"📈 Total keseluruhan: {len(all_jobs)}")

    # Checkpoint CSV per role
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pd.DataFrame(role_jobs).to_csv(
        f"{OUTPUT_DIR}/raw/checkpoint_{role.replace(' ','_')}_{ts}.csv",
        index=False
    )
    time.sleep(5)  # Jeda antar role

# ─────────────────────────────────────────────
# STEP 2: SIMPAN HASIL FINAL
# ─────────────────────────────────────────────
df = pd.DataFrame(all_jobs)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

csv_path  = f"{OUTPUT_DIR}/processed/jobstreet_jobs_{ts}.csv"
json_path = f"{OUTPUT_DIR}/processed/jobstreet_jobs_{ts}.json"

df.to_csv(csv_path, index=False, encoding="utf-8-sig")
df.drop(columns=["job_description"], errors="ignore").to_json(
    json_path, orient="records", indent=2, force_ascii=False
)

print(f"\n✅ CSV  → {csv_path}  ({len(df)} baris)")
print(f"✅ JSON → {json_path}")

# ─────────────────────────────────────────────
# STEP 3: LAPORAN SKILLS
# ─────────────────────────────────────────────
from collections import Counter
all_skills_flat = []
for s in df["extracted_skills"].dropna():
    if isinstance(s, list):
        all_skills_flat.extend(s)

top_skills = Counter(all_skills_flat).most_common(20)
print("\n🔥 Top 20 Skills di JobStreet:")
for skill, cnt in top_skills:
    pct = cnt / len(df) * 100
    print(f"   {skill:<20} {cnt:>4} jobs  ({pct:.1f}%)")

driver.quit()
print("\n🏁 Selesai!")