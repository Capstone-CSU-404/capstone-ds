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


# KONFIGURASI
TARGET_JOB_ROLES = [
    "Full Stack Developer"
]

LOCATION      = "indonesia"
JOBS_PER_ROLE = 2000
OUTPUT_DIR    = r"C:\Users\asus3\Documents\CPSTNPROJECT\capstone-ds\Data"

os.makedirs(f"{OUTPUT_DIR}/raw",       exist_ok=True)
os.makedirs(f"{OUTPUT_DIR}/processed", exist_ok=True)

SKILLS_LIST = {
    'python','java','javascript','typescript','golang','php','swift','kotlin',
    'scala','c++','c#','rust','react','angular','vue','django','flask',
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
# AMBIL JOB DESCRIPTION — ROBUST MULTI-SELECTOR
#
# JobStreet memakai CSS class yang di-hash (contoh: kx2b1u0),
# artinya class berubah setiap kali mereka deploy ulang website.
# Solusi: gunakan data-automation attribute (stabil) sebagai
# selector utama, dengan beberapa fallback berbasis struktur HTML.
# ─────────────────────────────────────────────

# Selector untuk menunggu panel kanan selesai load
JD_WAIT_SELECTORS = [
    # Paling stabil — pakai data-automation
    '[data-automation="jobDetailsPage"]',
    '[data-automation="job-detail-page"]',
    '[data-automation="jobAdDetails"]',

    # Fallback: section/article di panel detail
    'section[aria-label*="job"]',
    'div[id*="jobDetail"]',

    # Last resort: wrapper umum panel kanan
    'div[data-testid="job-detail"]',
    'div[data-testid="jobDetail"]',
]

# Selector untuk mengambil TEKS deskripsi pekerjaan
JD_CONTENT_SELECTORS = [
    # data-automation (paling stabil, tidak berubah saat redeploy)
    '[data-automation="jobAdDetails"]',
    '[data-automation="job-details-content"]',
    '[data-automation="jobDescription"]',

    # Fallback struktur semantik
    'div[id="jobDescription"]',
    'div[class*="jobDescription"]',
    'section[data-automation="jobAdDetails"]',

    # JobStreet AU/ID sering pakai FEA_ prefix di id
    'div[id*="FEA_VJOBS"]',

    # Fallback lebar: ambil semua konten panel detail
    '[data-automation="jobDetailsPage"] div:not([data-automation])',
]

def get_job_description(driver, wait):
    """
    Ambil teks job description dari panel kanan JobStreet.
    Mencoba berbagai selector secara berurutan.
    Return: string teks JD atau "" jika gagal.
    """
    # Step 1: Tunggu panel selesai load (coba tiap selector)
    panel_loaded = False
    for sel in JD_WAIT_SELECTORS:
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
            panel_loaded = True
            break
        except:
            continue

    if not panel_loaded:
        # Fallback: tunggu generic — minimal pastikan halaman tidak loading
        time.sleep(3)

    # Step 2: Coba ambil teks JD dari berbagai selector
    for sel in JD_CONTENT_SELECTORS:
        try:
            elements = driver.find_elements(By.CSS_SELECTOR, sel)
            if not elements:
                continue
            # Ambil elemen dengan teks terpanjang (hindari container kosong)
            texts = [
                el.get_attribute("innerText").strip()
                for el in elements
                if el.get_attribute("innerText") and len(el.get_attribute("innerText").strip()) > 50
            ]
            if texts:
                best = max(texts, key=len)
                if len(best) > 50:
                    return best
        except:
            continue

    # Step 3: Last resort — cari semua <p> atau <li> dalam panel detail
    try:
        container_xpaths = [
            "//div[contains(@data-automation,'job')]//p",
            "//section[contains(@data-automation,'job')]//p | //section[contains(@data-automation,'job')]//li",
            "//div[contains(@id,'jobDetail')]//p | //div[contains(@id,'jobDetail')]//li",
        ]
        for xpath in container_xpaths:
            els = driver.find_elements(By.XPATH, xpath)
            if els:
                combined = "\n".join(
                    el.get_attribute("innerText").strip()
                    for el in els
                    if el.get_attribute("innerText")
                )
                if len(combined) > 100:
                    return combined
    except:
        pass

    # Step 4: Screenshot debug (uncomment bila perlu diagnosis)
    # driver.save_screenshot(f"debug_jd_{int(time.time())}.png")

    return ""  # Benar-benar gagal


def scroll_job_list(driver, times=3):
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(1.5)
    driver.execute_script("window.scrollTo(0, 0)")
    time.sleep(0.5)


# ─────────────────────────────────────────────
# SCRAPE SATU HALAMAN
# ─────────────────────────────────────────────
def scrape_one_page(driver, wait, role, location):
    results = []

    try:
        wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, 'article[data-automation="normalJob"]')
        ))
    except:
        print("  ⚠️ Tidak ada job card di halaman ini")
        return results

    scroll_job_list(driver, times=3)

    job_cards = driver.find_elements(
        By.CSS_SELECTOR, 'article[data-automation="normalJob"]'
    )
    print(f"  📋 {len(job_cards)} card ditemukan")

    for idx, card in enumerate(job_cards):
        try:
            job_id    = card.get_attribute("data-job-id") or ""
            job_title = safe_text(card, 'a[data-automation="jobTitle"]')
            company   = safe_text(card, 'a[data-automation="jobCompany"]')

            try:
                loc_els = card.find_elements(
                    By.CSS_SELECTOR, 'a[data-automation="jobLocation"]'
                )
                location_val = ", ".join(
                    el.get_attribute("innerText").strip() for el in loc_els
                )
            except:
                location_val = ""

            raw_href = safe_attr(card, 'a[data-automation="jobTitle"]', "href")
            if raw_href.startswith("/"):
                job_url = "https://id.jobstreet.com" + raw_href.split("?")[0]
            elif raw_href.startswith("http"):
                job_url = raw_href.split("?")[0]
            else:
                job_url = ""

            salary  = safe_text(card, 'span[data-automation="jobSalary"]')
            jd_text = ""

            try:
                driver.execute_script(
                    "arguments[0].scrollIntoView({block:'center'});", card
                )
                time.sleep(0.4)

                clickable = card.find_element(
                    By.CSS_SELECTOR, 'a[data-automation="jobTitle"]'
                )
                driver.execute_script("arguments[0].click();", clickable)
                time.sleep(2.5)

                # ── PERBAIKAN UTAMA: pakai fungsi robust ──────────
                jd_text = get_job_description(driver, wait)

                if not jd_text:
                    print(f"    ⚠️ JD kosong untuk: {job_title} — coba buka tab baru")
                    # Fallback: buka URL langsung di tab baru
                    if job_url:
                        original_window = driver.current_window_handle
                        driver.execute_script(f"window.open('{job_url}', '_blank');")
                        driver.switch_to.window(driver.window_handles[-1])
                        time.sleep(3)
                        jd_text = get_job_description(driver, wait)
                        driver.close()
                        driver.switch_to.window(original_window)
                        time.sleep(1.5)

            except Exception as e:
                print(f"    ⚠️ Gagal ambil detail panel job {idx+1}: {e}")

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
            print(f"  ✅ [{len(results)}] {job_title} — {company} | "
                  f"JD: {'✓' if jd_text else '✗'} | Skills: {len(skills)}")

        except Exception as e:
            print(f"  ⚠️ Error card {idx+1}: {e}")
            continue

        time.sleep(0.8)

    return results


# ─────────────────────────────────────────────
# KLIK TOMBOL NEXT — MULTI-STRATEGY
# ─────────────────────────────────────────────
def click_next_button(driver, wait):
    """
    Klik tombol next/selanjutnya dengan beberapa strategi.
    JobStreet ID menggunakan "Selanjutnya", versi EN "Next".
    """
    strategies = [
        # Strategy 1: data-automation (paling stabil)
        (By.CSS_SELECTOR, '[data-automation="page-next"]'),
        (By.CSS_SELECTOR, '[data-automation="pagination-next"]'),
        (By.CSS_SELECTOR, 'a[data-automation="next"]'),

        # Strategy 2: aria-label
        (By.CSS_SELECTOR, 'a[aria-label="Next"]'),
        (By.CSS_SELECTOR, 'a[aria-label="Selanjutnya"]'),
        (By.CSS_SELECTOR, 'button[aria-label="Next"]'),

        # Strategy 3: teks Selanjutnya / Next (XPath)
        (By.XPATH, "//a[normalize-space(text())='Selanjutnya']"),
        (By.XPATH, "//a[normalize-space(text())='Next']"),
        (By.XPATH, "//button[normalize-space(text())='Selanjutnya']"),
        (By.XPATH, "//a[contains(@href,'page=')][last()]"),  # Link pagination terakhir

        # Strategy 4: span/li wrapper
        (By.XPATH, "//li[contains(@class,'next')]//a"),
        (By.XPATH, "//*[contains(@class,'next')]//a[@href]"),
        (By.XPATH,
         "//*[self::a or self::button]"
         "[.//*[contains(text(),'Selanjutnya')] or .//*[contains(text(),'Next')]]"
         ),
    ]

    for by, selector in strategies:
        try:
            el = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((by, selector))
            )
            driver.execute_script("arguments[0].scrollIntoView();", el)
            time.sleep(0.3)
            driver.execute_script("arguments[0].click();", el)
            print(f"  ➡️ Klik next berhasil ({selector})")
            time.sleep(3)
            return True
        except:
            continue

    return False


# ─────────────────────────────────────────────
# SCRAPE SATU ROLE
# ─────────────────────────────────────────────
def scrape_jobstreet_role(driver, role, location, target_count):
    all_jobs  = []
    wait      = WebDriverWait(driver, 15)
    page_num  = 1

    role_slug = role.strip().replace(" ", "-")
    url = f"https://id.jobstreet.com/id/{role_slug}-jobs?sortmode=ListedDate"

    print(f"\n🌐 Membuka: {url}")
    driver.get(url)
    time.sleep(4)

    while len(all_jobs) < target_count:
        print(f"\n  📄 Halaman {page_num}")

        try:
            driver.find_element(
                By.CSS_SELECTOR, 'article[data-automation="normalJob"]'
            )
        except:
            print(f"  🏁 Tidak ada job card di halaman {page_num}, berhenti.")
            break

        page_results = scrape_one_page(driver, wait, role, location)

        if not page_results:
            print(f"  🏁 Halaman {page_num} kosong, berhenti.")
            break

        all_jobs.extend(page_results)
        print(f"  📈 Total: {len(all_jobs)} / {target_count}")

        if len(all_jobs) >= target_count:
            break

        success = click_next_button(driver, wait)

        if not success:
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

        time.sleep(2)

    return all_jobs


# ─────────────────────────────────────────────
# MAIN
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

from collections import Counter
flat = [s for row in df["extracted_skills"].dropna()
        if isinstance(row, list) for s in row]
print("\n🔥 Top 20 Skills:")
for skill, cnt in Counter(flat).most_common(20):
    print(f"   {skill:<20} {cnt:>4} jobs  ({cnt/len(df)*100:.1f}%)")

driver.quit()
print("\n🏁 Selesai!")