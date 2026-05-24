from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from collections import Counter
from datetime import datetime
import time
import pandas as pd
import json
import os
import re


LINKEDIN_EMAIL    = "firmanadik09@gmail.com"       # ← ganti
LINKEDIN_PASSWORD = "Fak_1809"    # ← ganti

TARGET_JOB_ROLES = [
    "Software Engineer"
]

LOCATION      = "Indonesia"
JOBS_PER_ROLE = 1000
OUTPUT_DIR    = r"C:\Users\asus3\Documents\CPSTNPROJECT\capstone-ds\Data"

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
# HELPER: Apply filter "Past week" via UI
# ─────────────────────────────────────────────
def apply_date_filter_past_week():
    """
    Klik filter 'Past week' lewat UI LinkedIn.
    Menggunakan ID persis dari HTML:
      <input id="timePostedRange-r604800" value="r604800" name="date-posted-filter-value" type="radio">
      <label for="timePostedRange-r604800">Past week</label>
    """
    try:
        # 1. Klik tombol "Date posted" untuk buka dropdown filter
        date_filter_btn = None
        btn_selectors = [
            "//button[contains(@aria-label, 'Date posted')]",
            "//button[contains(@aria-label, 'Tanggal diposting')]",
            "//button[contains(normalize-space(.), 'Date posted')]",
            "//button[contains(normalize-space(.), 'Tanggal diposting')]",
        ]
        for selector in btn_selectors:
            try:
                date_filter_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, selector)
                ))
                print(f"  🗂️ Tombol filter ditemukan: {selector}")
                break
            except:
                continue

        if not date_filter_btn:
            print("  ⚠️ Tombol 'Date posted' tidak ditemukan, skip UI filter")
            return False

        driver.execute_script("arguments[0].click();", date_filter_btn)
        time.sleep(2)
        print("  🗂️ Dropdown 'Date posted' terbuka")

        # 2. Klik radio button "Past week" — 3 cara fallback
        radio_clicked = False

        # Cara 1: via ID langsung
        if not radio_clicked:
            try:
                radio = wait.until(EC.presence_of_element_located((
                    By.ID, "timePostedRange-r604800"
                )))
                driver.execute_script("arguments[0].click();", radio)
                time.sleep(1)
                print("  ✅ Radio 'Past week' diklik (via ID)")
                radio_clicked = True
            except:
                pass

        # Cara 2: via label for="timePostedRange-r604800"
        if not radio_clicked:
            try:
                label = driver.find_element(
                    By.CSS_SELECTOR,
                    "label[for='timePostedRange-r604800']"
                )
                driver.execute_script("arguments[0].click();", label)
                time.sleep(1)
                print("  ✅ Radio 'Past week' diklik (via label CSS)")
                radio_clicked = True
            except:
                pass

        # Cara 3: via input name="date-posted-filter-value" value="r604800"
        if not radio_clicked:
            try:
                radio = driver.find_element(
                    By.CSS_SELECTOR,
                    "input[name='date-posted-filter-value'][value='r604800']"
                )
                driver.execute_script("arguments[0].click();", radio)
                time.sleep(1)
                print("  ✅ Radio 'Past week' diklik (via CSS name+value)")
                radio_clicked = True
            except:
                pass

        if not radio_clicked:
            print("  ⚠️ Gagal klik radio 'Past week'")
            return False

        # 3. Klik "Show results" / "Tampilkan hasil" untuk apply filter
        apply_selectors = [
            "//button[contains(@aria-label, 'Apply current filters')]",
            "//button[contains(@data-tracking-control-name, 'filter_pill_apply')]",
            "//button[normalize-space(text())='Show results']",
            "//button[normalize-space(text())='Tampilkan hasil']",
            "//button[contains(., 'Show') and contains(@class, 'artdeco-button--primary')]",
            "//button[contains(., 'Tampilkan') and contains(@class, 'artdeco-button--primary')]",
        ]
        for selector in apply_selectors:
            try:
                apply_btn = wait.until(EC.element_to_be_clickable(
                    (By.XPATH, selector)
                ))
                driver.execute_script("arguments[0].click();", apply_btn)
                time.sleep(3)
                print("  ✅ Filter 'Past week' berhasil diterapkan")
                return True
            except:
                continue

        print("  ⚠️ Tombol 'Show results' tidak ditemukan")
        return False

    except Exception as e:
        print(f"  ⚠️ Error apply_date_filter_past_week: {e}")
        return False

# ─────────────────────────────────────────────
# HELPER: Ekstrak skills dari deskripsi
# ─────────────────────────────────────────────
SKILLS_LIST = {
    'python','java','javascript','typescript','golang','php','swift','kotlin',
    'scala','c++','c#','rust','react','angular','vue','django','flask',
    'fastapi','spring boot','express','tensorflow','pytorch','keras',
    'scikit-learn','pandas','numpy','sql','postgresql','mysql','mongodb',
    'redis','elasticsearch','aws','gcp','azure','docker','kubernetes',
    'hadoop','spark','kafka','airflow','tableau','laravel','power bi','flutter',
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
# HELPER: Safe get text / attr
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
# CORE: Scrape jobs untuk satu role
# ─────────────────────────────────────────────
def scrape_jobs_for_role(role, location, target_count):
    keywords = role.replace(" ", "%20")
    loc_enc  = location.replace(" ", "%20")

    # Buka halaman search tanpa filter tanggal dulu
    url = f"https://www.linkedin.com/jobs/search/?keywords={keywords}&location={loc_enc}"
    driver.get(url)
    time.sleep(4)
    print(f"\n🔍 Scraping: {role} | {location}")

    # ── Apply filter "Past week" via UI ─────────────────────────────────
    filter_ok = apply_date_filter_past_week()
    if filter_ok:
        print("  📅 Filter 'Past week' aktif")
    else:
        print("  ⚠️ Filter tidak teraplikasi via UI, lanjut tanpa filter tanggal")
    time.sleep(2)
    # ────────────────────────────────────────────────────────────────────

    all_jobs_data = []

    while len(all_jobs_data) < target_count:

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
            print("  ⚠️ Tidak menemukan container job list, stop.")
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
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", card
                )
                time.sleep(0.5)

                # Klik card → panel detail muncul di kanan
                try:
                    clickable = card.find_element(
                        By.CSS_SELECTOR, "a.job-card-list__title--link"
                    )
                    driver.execute_script("arguments[0].click();", clickable)
                except:
                    driver.execute_script("arguments[0].click();", card)

                time.sleep(3)

                # ── Ekstrak data dari card (panel kiri) ──────────────────
                job_title    = safe_text(card, "a.job-card-list__title--link strong")
                company_name = safe_text(card,
                    "span.job-card-container__primary-description, h4, "
                    ".artdeco-entity-lockup__subtitle"
                )
                location_val = safe_text(card,
                    "ul.job-card-container__metadata-wrapper li span"
                )
                job_url      = safe_attr(card, "a.job-card-list__title--link", "href")
                posted_date  = safe_attr(card, "time", "datetime")

                job_id = ""
                try:
                    job_id = card.find_element(
                        By.CSS_SELECTOR, "div[data-job-id]"
                    ).get_attribute("data-job-id")
                except:
                    match = re.search(r'/jobs/view/(\d+)', job_url or "")
                    job_id = match.group(1) if match else ""

                # ── Ekstrak data dari panel detail (kanan) ────────────────
                jd_text = ""
                try:
                    detail_panel = wait.until(EC.presence_of_element_located((
                        By.CSS_SELECTOR,
                        "div.jobs-search__job-details--wrapper, div.job-view-layout"
                    )))
                    try:
                        jd_el = detail_panel.find_element(By.CSS_SELECTOR,
                            "div.jobs-description__content, "
                            "div.description__text, "
                            "article.jobs-description__container"
                        )
                        jd_text = jd_el.get_attribute("innerText").strip()
                    except:
                        pass
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
                    "job_description"  : jd_text,
                    "job_url"          : job_url,
                    "search_role"      : role,
                    "search_location"  : location,
                    "extracted_skills" : skills,
                    "skills_count"     : len(skills),
                    "scraped_at"       : datetime.now().isoformat(),
                }
                all_jobs_data.append(record)
                print(
                    f"  ✅ [{len(all_jobs_data)}/{target_count}] "
                    f"{job_title} — {company_name}"
                )

            except Exception as e:
                print(f"  ⚠️ Error pada card {idx+1}: {e}")
                continue

            time.sleep(1)

        # ── Pindah ke halaman berikutnya ─────────────────────────────────
        try:
            next_btn = wait.until(EC.element_to_be_clickable((
                By.CSS_SELECTOR,
                "button[aria-label='View next page'], "
                "button[aria-label='Halaman berikutnya']"
            )))
            driver.execute_script("arguments[0].scrollIntoView();", next_btn)
            driver.execute_script("arguments[0].click();", next_btn)
            print("  ➡️ Pindah halaman berikutnya...")
            time.sleep(4)
        except:
            print("  ⚠️ Tidak ada tombol Next, scraping selesai untuk role ini.")
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
        f"{OUTPUT_DIR}/raw/checkpoint_{role.replace(' ', '_')}_{ts}.csv",
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
all_skills_flat = []
for s in df["extracted_skills"].dropna():
    if isinstance(s, list):
        all_skills_flat.extend(s)

top_skills = Counter(all_skills_flat).most_common(20)
print("\n🔥 Top 20 Skills:")
for skill, cnt in top_skills:
    pct = cnt / len(df) * 100 if len(df) > 0 else 0
    print(f"   {skill:<20} {cnt:>4} jobs  ({pct:.1f}%)")

driver.quit()
print("\n🏁 Selesai!")