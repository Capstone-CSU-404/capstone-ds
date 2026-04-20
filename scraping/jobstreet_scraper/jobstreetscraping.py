import pandas as pd
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.python import ChromeDriverManager  # auto-download driver

# ─────────────────────────────────────────
# SETUP BROWSER
# Mengapa: Selenium membuka Chrome sungguhan
# sehingga JavaScript berjalan dan Cloudflare
# melihat request dari browser nyata.
# ─────────────────────────────────────────
def init_driver(headless=False):
    options = webdriver.ChromeOptions()
    
    if headless:
        options.add_argument("--headless=new")  # Mode tanpa jendela (production)
    
    # Opsi penting agar tidak terdeteksi bot
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-blink-features=AutomationControlled")  # ← Kunci!
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    # Sembunyikan tanda bahwa ini Selenium
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    
    return driver


# ─────────────────────────────────────────
# SCRAPE SATU HALAMAN
# ─────────────────────────────────────────
def scrape_page(driver, url, search_role, search_location):
    results = []
    
    driver.get(url)
    
    # Mengapa WebDriverWait: kita tunggu sampai elemen muncul di DOM
    # setelah React selesai render. Lebih andal dari time.sleep()
    try:
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-automation="jobListing"]'))
        )
    except:
        print("  Timeout atau tidak ada job di halaman ini")
        return results
    
    # Scroll ke bawah untuk trigger lazy loading
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
    time.sleep(2)
    
    job_cards = driver.find_elements(By.CSS_SELECTOR, '[data-automation="jobListing"]')
    print(f"  Ditemukan {len(job_cards)} job")
    
    for card in job_cards:
        try:
            # Ambil data dari card listing
            title = card.find_element(By.CSS_SELECTOR, '[data-automation="jobTitle"]').text
            
            try:
                company = card.find_element(By.CSS_SELECTOR, '[data-automation="jobCompany"]').text
            except:
                company = "N/A"
                
            try:
                location = card.find_element(By.CSS_SELECTOR, '[data-automation="jobLocation"]').text
            except:
                location = "N/A"
            
            try:
                job_url = card.find_element(By.CSS_SELECTOR, 'a[data-automation="jobTitle"]').get_attribute("href")
            except:
                job_url = "N/A"
            
            # ID unik dari URL
            job_id = job_url.split("/")[-1].split("?")[0] if job_url != "N/A" else "N/A"
            
            results.append({
                "id": job_id,
                "title": title,
                "company": company,
                "location": location,
                "job_description": "",  # Diisi nanti saat buka detail page
                "job_url": job_url,
                "search_role": search_role,
                "search_location": search_location,
                "extracted_skills": "",  # Diisi setelah scrape description
                "skills_count": 0,
                "scraped_at": datetime.now().isoformat()
            })
        except Exception as e:
            print(f"  Error parsing card: {e}")
            continue
    
    return results


# ─────────────────────────────────────────
# MAIN SCRAPER
# ─────────────────────────────────────────
def scrape_jobstreet(search_role="data scientist", search_location="jakarta", max_pages=3):
    base_url = f"https://id.jobstreet.com/id/{search_role.replace(' ', '-')}-jobs"
    all_results = []
    
    driver = init_driver(headless=False)  # headless=False dulu untuk debug
    
    try:
        for page_num in range(1, max_pages + 1):
            url = f"{base_url}?sortmode=ListedDate&page={page_num}"
            print(f"\nHalaman {page_num}: {url}")
            
            page_results = scrape_page(driver, url, search_role, search_location)
            all_results.extend(page_results)
            
            # Delay antar halaman (jangan terlalu cepat!)
            time.sleep(3)
            
    finally:
        driver.quit()
    
    return all_results


# Jalankan
if __name__ == "__main__":
    data = scrape_jobstreet(
        search_role="data scientist",
        search_location="jakarta",
        max_pages=2
    )
    
    df = pd.DataFrame(data)
    print(f"\nTotal job terkumpul: {len(df)}")
    print(df[["title", "company", "location"]].head(10))
    
    # Simpan sementara
    df.to_csv("jobstreet_raw.csv", index=False)
    print("Disimpan ke jobstreet_raw.csv")