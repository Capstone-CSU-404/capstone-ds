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
import os
import re

# ─────────────────────────────────────────────
# KONFIGURASI
# ─────────────────────────────────────────────
TARGET_JOB_ROLES = [
    "Machine Learning"
]

LOCATION      = "Indonesia"
JOBS_PER_ROLE = 100
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
    # Tambahan agar tidak terdeteksi bot
    options.add_argument("--disable-infobars")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    )
    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

driver = create_driver()
wait   = WebDriverWait(driver, 15)

# ─────────────────────────────────────────────
# HELPER: Apply filter "Past week" via UI
# ─────────────────────────────────────────────
def apply_date_filter_past_week():
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

        # 2. Klik radio button "Past week"
        radio_clicked = False

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

        if not radio_clicked:
            try:
                label = driver.find_element(
                    By.CSS_SELECTOR, "label[for='timePostedRange-r604800']"
                )
                driver.execute_script("arguments[0].click();", label)
                time.sleep(1)
                print("  ✅ Radio 'Past week' diklik (via label CSS)")
                radio_clicked = True
            except:
                pass

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

        # 3. Klik "Show results"
        apply_selectors = [
            "//button[@aria-label='Apply current filter to show results']",
            "//button[contains(@aria-label, 'Apply current filter')]",
            "//button[contains(@aria-label, 'Apply current filters')]",
            "//button[contains(@data-tracking-control-name, 'filter_pill_apply')]",
            "//button[normalize-space(text())='Show results']",
            "//button[normalize-space(text())='Tampilkan hasil']",
            "//button[contains(., 'Show results') and contains(@class, 'artdeco-button--primary')]",
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
# HELPER: Cek redirect ke login
# ─────────────────────────────────────────────
def is_redirected_to_login():
    return "linkedin.com/login" in driver.current_url or \
           "linkedin.com/authwall" in driver.current_url

# ─────────────────────────────────────────────
# CORE: Scrape jobs untuk satu role
# ─────────────────────────────────────────────
def scrape_jobs_for_role(role, location, target_count):
    role_slug = role.lower().replace(" ", "-") + "-jobs"
    keywords  = role.replace(" ", "%20")
    loc_enc   = location.replace(" ", "%20")

    all_jobs_data = []
    seen_ids  = set()
    page_num  = 0

    while len(all_jobs_data) < target_count:

        # ── Buka halaman publik LinkedIn jobs ───────────────────────────
        url = (
            f"https://id.linkedin.com/jobs/{role_slug}"
            f"?location={loc_enc}"
            f"&f_TPR=r604800"
            f"&position=1"
            f"&pageNum={page_num}"
        )
        print(f"\n  🌐 Buka halaman {page_num + 1}: {url}")
        driver.get(url)
        time.sleep(3)

        # Cek redirect ke login
        if is_redirected_to_login():
            print("  ⚠️ Redirect ke login, mencoba format URL alternatif...")
            url = (
                f"https://www.linkedin.com/jobs/search/"
                f"?keywords={keywords}"
                f"&location={loc_enc}"
                f"&f_TPR=r604800"
                f"&start={page_num * 25}"
            )
            driver.get(url)
            time.sleep(3)
            if is_redirected_to_login():
                print("  ❌ Masih redirect ke login, scraping dihentikan.")
                break

        # ── Temukan container list job ───────────────────────────────────
        container = None
        for sel in [
            "ul.jobs-search__results-list",
            "div.scaffold-layout__list",
            "div.jobs-search-results-list",
        ]:
            try:
                container = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                print(f"  📦 Container ditemukan: {sel}")
                break
            except:
                continue

        if not container:
            print("  ⚠️ Container job list tidak ditemukan, stop.")
            break

        # Scroll untuk load semua card
        scroll_job_list(container, times=3)

        # ── Ambil semua job card ─────────────────────────────────────────
        job_cards = []
        for sel in [
            "li.jobs-search__results-list--container",
            "li",
            "li.jobs-search-results__list-item",
            "li.scaffold-layout__list-item",
        ]:
            candidates = container.find_elements(By.CSS_SELECTOR, sel)
            candidates = [
                c for c in candidates
                if c.find_elements(By.CSS_SELECTOR, "a[href*='/jobs/']")
            ]
            if candidates:
                job_cards = candidates
                print(f"  📋 {len(job_cards)} card ditemukan dengan selector: {sel}")
                break

        if not job_cards:
            print("  ⚠️ Tidak ada job card ditemukan, stop.")
            break

        # ── Proses tiap card ─────────────────────────────────────────────
        for idx, card in enumerate(job_cards):
            if len(all_jobs_data) >= target_count:
                break

            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", card
                )
                time.sleep(0.5)

                # Ambil data dasar dari card
                job_title = ""
                for sel in ["h3.base-search-card__title", "h3", "a strong"]:
                    job_title = safe_text(card, sel)
                    if job_title:
                        break

                company_name = ""
                for sel in ["h4.base-search-card__subtitle", "h4",
                            "span.job-card-container__primary-description",
                            ".artdeco-entity-lockup__subtitle"]:
                    company_name = safe_text(card, sel)
                    if company_name:
                        break

                location_val = ""
                for sel in ["span.job-search-card__location",
                            "span.job-card-container__metadata-item",
                            "ul.job-card-container__metadata-wrapper li span"]:
                    location_val = safe_text(card, sel)
                    if location_val:
                        break

                posted_date = safe_attr(card, "time", "datetime")

                job_url = ""
                for sel in ["a.base-card__full-link",
                            "a[href*='/jobs/view/']",
                            "a.job-card-list__title--link"]:
                    job_url = safe_attr(card, sel, "href")
                    if job_url:
                        break

                job_id = ""
                match = re.search(r'/jobs/view/(\d+)', job_url or "")
                if match:
                    job_id = match.group(1)

                # ── Deduplication ─────────────────────────────────────────
                unique_key = job_id if job_id else job_url
                if unique_key and unique_key in seen_ids:
                    print(f"  ⏭️  Skip duplikat: {job_title}")
                    continue
                if unique_key:
                    seen_ids.add(unique_key)

                # ── Klik card → ambil job description → back ──────────────
                jd_text = ""
                try:
                    link_el = None
                    for sel in ["a.base-card__full-link",
                                "a[href*='/jobs/view/']",
                                "a.job-card-list__title--link"]:
                        try:
                            link_el = card.find_element(By.CSS_SELECTOR, sel)
                            break
                        except:
                            continue

                    if link_el:
                        driver.execute_script("arguments[0].click();", link_el)
                        time.sleep(3)

                        if is_redirected_to_login():
                            print(f"  ⚠️ Redirect login saat klik job {idx+1}, skip description.")
                            driver.back()
                            time.sleep(2)
                        else:
                            for sel in [
                                "div.show-more-less-html__markup",
                                "div.description__text",
                                "div.jobs-description__content",
                                "article.jobs-description__container",
                                "div[class*='description']",
                            ]:
                                try:
                                    jd_el = wait.until(EC.presence_of_element_located(
                                        (By.CSS_SELECTOR, sel)
                                    ))
                                    jd_text = jd_el.get_attribute("innerText").strip()
                                    if jd_text:
                                        break
                                except:
                                    continue

                            driver.back()
                            time.sleep(2)

                except Exception as e:
                    print(f"    ⚠️ Gagal ambil description job {idx+1}: {e}")

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

        # ── Pindah ke halaman berikutnya via pageNum ──────────────────────
        page_num += 1
        print(f"  ➡️ Lanjut ke halaman {page_num + 1}...")
        time.sleep(2)

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