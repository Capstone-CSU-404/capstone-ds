#Install
pip install selenium
pip install pandas
pip install webdriver-manager
pip install openpyxl

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import time
import pandas as pd
import json
from datetime import datetime
import os

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
LINKEDIN_EMAIL    = "firmanadik09@gmail.com"   # ← ganti
LINKEDIN_PASSWORD = "Fak_1809"          # ← ganti

TARGET_JOB_ROLES = [
    "Data Scientist",
    "Machine Learning Engineer",
]

LOCATION       = "Indonesia"
JOBS_PER_ROLE  = 25   # target per role
OUTPUT_DIR     = r"C:\Users\asus3\Documents\YUBE"
os.makedirs(f"{OUTPUT_DIR}/raw",       exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/processed", exist_ok=True)

# ─────────────────────────────────────────────
# SETUP DRIVER
# ─────────────────────────────────────────────
def create_driver():
    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    return driver

driver = create_driver()
wait   = WebDriverWait(driver, 15)

# ─────────────────────────────────────────────
# STEP 1: LOGIN
# ─────────────────────────────────────────────
def login(email, password):
    driver.get("https://www.linkedin.com/login")
    time.sleep(2)
    wait.until(EC.presence_of_element_located((By.ID, "username"))).send_keys(email)
    driver.find_element(By.ID, "password").send_keys(password)
    driver.find_element(By.ID, "password").submit()
    time.sleep(4)
    print("✅ Login berhasil")

login(LINKEDIN_EMAIL, LINKEDIN_PASSWORD)

# ─────────────────────────────────────────────
# HELPER: Ekstrak skills dari deskripsi
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
# HELPER: Scroll panel kiri (job list)
# ─────────────────────────────────────────────
def scroll_job_list(container_el, times=3):
    for _ in range(times):
        driver.execute_script(
            "arguments[0].scrollTop = arguments[0].scrollHeight", container_el
        )
        time.sleep(2)

# ─────────────────────────────────────────────
# HELPER: Safe get text
# ─────────────────────────────────────────────
def safe_text(el, css, default=""):
    try:
        return el.find_element(By.CSS_SELECTOR, css).get_attribute("innerText").strip()
    except:
        return default

def safe_attr(el, css, attr, default=""):
    try:
        return el.find_element(By.CSS_SELECTOR, css).get_attribute(attr) or default
    except:
        return default

# ─────────────────────────────────────────────
# CORE: Scrape satu halaman hasil pencarian
# ─────────────────────────────────────────────
def scrape_jobs_for_role(role, location, target_count):
    keywords = role.replace(" ", "%20")
    loc_enc  = location.replace(" ", "%20")
    url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={loc_enc}"
    
    driver.get(url)
    time.sleep(4)
    print(f"\n🔍 Scraping: {role} | {location}")

    all_jobs_data = []
    page_start    = 0   # LinkedIn pagination: &start=0, 25, 50 ...

    while len(all_jobs_data) < target_count:
        # Buka halaman berikutnya jika perlu
        paginated_url = url + f"&start={page_start}"
        driver.get(paginated_url)
        time.sleep(4)

        # ── Temukan container list job (panel kiri) ──────────────────────
        container = None
        for sel in [
            "div.scaffold-layout__list",
            "div.jobs-search-results-list",
            "ul.jobs-search__results-list",
        ]:
            try:
                container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                break
            except:
                continue

        if not container:
            print("  ⚠️ Tidak menemukan container job list, skip halaman ini")
            break

        # Scroll container untuk load semua card
        scroll_job_list(container, times=4)

        # ── Ambil semua job card ─────────────────────────────────────────
        job_cards = []
        for sel in [
            "li.jobs-search-results__list-item",
            "li.scaffold-layout__list-item",
            "div.job-card-container",
        ]:
            job_cards = container.find_elements(By.CSS_SELECTOR, sel)
            if job_cards:
                print(f"  📋 {len(job_cards)} card ditemukan dengan selector: {sel}")
                break

        if not job_cards:
            print("  ⚠️ Tidak ada job card ditemukan di halaman ini")
            break

        # ── Proses tiap card ─────────────────────────────────────────────
        for idx, card in enumerate(job_cards):
            if len(all_jobs_data) >= target_count:
                break

            try:
                # Scroll card ke viewport
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", card)
                time.sleep(0.5)

                # Klik card → panel detail muncul di kanan
                try:
                    clickable = card.find_element(By.CSS_SELECTOR,
                        "a.job-card-list__title, a.job-card-container__link, a[data-control-name='jobcard_title']"
                    )
                    driver.execute_script("arguments[0].click();", clickable)
                except:
                    driver.execute_script("arguments[0].click();", card)

                time.sleep(3)   # tunggu detail panel load

                # ── Ekstrak data dari card (panel kiri) ──────────────────
                job_title    = safe_text(card, "a.job-card-list__title strong, a.job-card-list__title, h3")
                company_name = safe_text(card, "span.job-card-container__primary-description, h4, .artdeco-entity-lockup__subtitle")
                location_val = safe_text(card, "li.job-card-container__metadata-item, .job-card-container__metadata-wrapper li")
                job_url      = safe_attr(card, "a.job-card-list__title, a.job-card-container__link", "href")
                posted_date  = safe_attr(card, "time", "datetime")
                job_id       = card.get_attribute("data-job-id") or card.get_attribute("data-entity-urn") or ""

                # ── Ekstrak data dari panel detail (kanan) ────────────────
                jd_text      = ""
                applicants   = ""
                seniority    = ""
                emp_type     = ""
                job_func     = ""
                industries   = ""

                try:
                    # Tunggu panel detail muncul
                    detail_panel = wait.until(EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "div.jobs-search__job-details--wrapper, div.job-view-layout"
                    )))

                    # Job Description
                    try:
                        jd_el  = detail_panel.find_element(By.CSS_SELECTOR,
                            "div.jobs-description__content, div.description__text, article.jobs-description__container"
                        )
                        jd_text = jd_el.get_attribute("innerText").strip()
                    except:
                        pass

                    # Applicant count
                    try:
                        applicants = detail_panel.find_element(By.CSS_SELECTOR,
                            "span.jobs-unified-top-card__applicant-count, "
                            "figcaption.jobs-unified-top-card__subtitle-secondary-grouping span, "
                            "span[class*='applicant']"
                        ).get_attribute("innerText").strip()
                    except:
                        pass

                    # Criteria: seniority, emp type, function, industry
                    criteria_items = detail_panel.find_elements(By.CSS_SELECTOR,
                        "li.description__job-criteria-item"
                    )
                    for item in criteria_items:
                        try:
                            label = item.find_element(By.CSS_SELECTOR,
                                "h3.description__job-criteria-subheader"
                            ).text.strip().lower()
                            value = item.find_element(By.CSS_SELECTOR,
                                "span.description__job-criteria-text"
                            ).text.strip()
                            if "seniority"   in label: seniority  = value
                            elif "employment" in label: emp_type   = value
                            elif "function"   in label: job_func   = value
                            elif "industri"   in label or "industry" in label: industries = value
                        except:
                            continue

                except Exception as e:
                    print(f"    ⚠️ Detail panel error job {idx+1}: {e}")

                # ── Simpan record ─────────────────────────────────────────
                skills = extract_skills(jd_text)
                record = {
                    "id"               : job_id,
                    "title"            : job_title,
                    "company"          : company_name,
                    "location"         : location_val,
                    "posted_date"      : posted_date,
                    "applicant_count"  : applicants,
                    "job_description"  : jd_text,
                    "seniority"        : seniority,
                    "employment_type"  : emp_type,
                    "job_function"     : job_func,
                    "industries"       : industries,
                    "job_url"          : job_url,
                    "search_role"      : role,
                    "search_location"  : location,
                    "extracted_skills" : skills,
                    "skills_count"     : len(skills),
                    "scraped_at"       : datetime.now().isoformat(),
                }
                all_jobs_data.append(record)
                print(f"  ✅ [{len(all_jobs_data)}/{target_count}] {job_title} — {company_name}")

            except Exception as e:
                print(f"  ⚠️ Error pada card {idx+1}: {e}")
                continue

            time.sleep(1)

        # Pindah ke halaman berikutnya
        page_start += 25
        if page_start > 975:   # LinkedIn max ~1000 result
            break

    return all_jobs_data

# ─────────────────────────────────────────────
# STEP 2: JALANKAN UNTUK SEMUA ROLE
# ─────────────────────────────────────────────
all_jobs = []

for role in TARGET_JOB_ROLES:
    print(f"\n{'='*55}")
    print(f"📌 Role: {role}")
    print(f"{'='*55}")
    
    role_jobs = scrape_jobs_for_role(role, LOCATION, JOBS_PER_ROLE)
    all_jobs.extend(role_jobs)
    
    print(f"✅ Selesai {role}: {len(role_jobs)} jobs")
    print(f"📈 Total keseluruhan: {len(all_jobs)}")

    # Checkpoint per role
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    pd.DataFrame(role_jobs).to_csv(
        f"{OUTPUT_DIR}/raw/checkpoint_{role.replace(' ','_')}_{ts}.csv",
        index=False
    )
    time.sleep(3)

# ─────────────────────────────────────────────
# STEP 3: SIMPAN HASIL FINAL
# ─────────────────────────────────────────────
df = pd.DataFrame(all_jobs)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")

csv_path  = f"{OUTPUT_DIR}/processed/linkedin_jobs_{ts}.csv"
json_path = f"{OUTPUT_DIR}/processed/linkedin_jobs_{ts}.json"

df.to_csv(csv_path, index=False, encoding="utf-8-sig")

df_light = df.drop(columns=["job_description"], errors="ignore")
df_light.to_json(json_path, orient="records", indent=2, force_ascii=False)

print(f"\n✅ CSV  → {csv_path}  ({len(df)} baris)")
print(f"✅ JSON → {json_path}")

# ─────────────────────────────────────────────
# STEP 4: LAPORAN SKILLS
# ─────────────────────────────────────────────
from collections import Counter
all_skills_flat = []
for s in df["extracted_skills"].dropna():
    if isinstance(s, list):
        all_skills_flat.extend(s)

top_skills = Counter(all_skills_flat).most_common(20)
print("\n🔥 Top 20 Skills:")
for skill, cnt in top_skills:
    pct = cnt / len(df) * 100
    print(f"   {skill:<20} {cnt:>4} jobs  ({pct:.1f}%)")
driver.quit()
print("\n🏁 Selesai!")
