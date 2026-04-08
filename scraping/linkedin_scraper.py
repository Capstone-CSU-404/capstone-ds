#!/usr/bin/env python3
"""
Capstone Project: AI-Driven Career Pathing & Skills Gap Analyzer
Job Scraper for Indonesia Market - Target 1000+ job listings
"""
import asyncio
import pandas as pd
import json
import os
from datetime import datetime
from linkedin_scraper.scrapers.job_search import JobSearchScraper
from linkedin_scraper.scrapers.job import JobScraper
from linkedin_scraper.core.browser import BrowserManager


# Konfigurasi target job roles untuk Indonesia
TARGET_JOB_ROLES = [
    "Data Scientist",
    "Machine Learning Engineer",
    "AI Engineer",
    "Data Analyst",
    "Software Engineer",
    "Fullstack Developer",
    "Backend Developer",
    "Frontend Developer",
    "DevOps Engineer",
    "Cloud Engineer",
    "Mobile Developer",
    "Product Manager",
    "Data Engineer",
    "Business Intelligence Analyst",
    "IT Project Manager"
]

# Konfigurasi lokasi di Indonesia
LOCATIONS = [
    "Indonesia",
    "Jakarta",
    "Surabaya",
    "Bandung",
    "Yogyakarta",
    "Semarang",
    "Medan",
    "Bali",
    "Tangerang",
    "Bekasi"
]

# Target total jobs
TARGET_TOTAL_JOBS = 1000
JOBS_PER_ROLE = TARGET_TOTAL_JOBS // len(TARGET_JOB_ROLES)  # ~66 jobs per role


async def scrape_jobs_for_role(search_scraper, job_scraper, role, location, limit):
    """Scrape jobs untuk satu role dan location tertentu"""
    jobs_data = []
    
    try:
        print(f"  🔍 Searching: {role} in {location} (limit: {limit})")
        
        # Search for jobs - KODE PENTING TIDAK DIUBAH
        job_urls = await search_scraper.search(
            keywords=role,
            location=location,
            limit=limit
        )
        
        print(f"    ✓ Found {len(job_urls)} job URLs")
        
        # Scrape each job details - KODE PENTING TIDAK DIUBAH
        for idx, job_url in enumerate(job_urls):
            try:
                print(f"    📄 Scraping job {idx+1}/{len(job_urls)}...")
                
                # KODE PENTING - TIDAK DIUBAH
                job = await job_scraper.scrape(job_url)
                
                # Extract skills from description (tambahan untuk capstone)
                skills_extracted = extract_skills_from_description(job.job_description)
                
                # Store data
                job_record = {
                    'title': job.job_title,
                    'company': job.company,
                    'location': job.location,
                    'posted_date': job.posted_date,
                    'applicant_count': job.applicant_count,
                    'job_description': job.job_description,
                    'job_url': job_url,
                    'search_role': role,
                    'search_location': location,
                    'extracted_skills': skills_extracted,
                    'skills_count': len(skills_extracted),
                    'scraped_at': datetime.now().isoformat()
                }
                
                jobs_data.append(job_record)
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"    ⚠️ Error scraping job: {e}")
                continue
                
    except Exception as e:
        print(f"  ⚠️ Error searching jobs for {role} in {location}: {e}")
    
    return jobs_data


def extract_skills_from_description(description):
    """Extract technical skills from job description"""
    if not description:
        return []
    
    description_lower = description.lower()
    
    # Daftar skills yang umum dicari di Indonesia
    skills_list = {
        # Programming Languages
        'python', 'java', 'javascript', 'typescript', 'golang', 'ruby', 'php', 
        'swift', 'kotlin', 'scala', 'r', 'c++', 'c#', 'rust',
        
        # Frameworks & Libraries
        'react', 'angular', 'vue', 'django', 'flask', 'fastapi', 'spring boot',
        'express', 'nestjs', 'laravel', 'rails', 'tensorflow', 'pytorch',
        'keras', 'scikit-learn', 'pandas', 'numpy', 'opencv',
        
        # Databases
        'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch',
        'cassandra', 'dynamodb', 'firebase', 'mariadb',
        
        # Cloud & DevOps
        'aws', 'gcp', 'azure', 'docker', 'kubernetes', 'jenkins', 'gitlab ci',
        'github actions', 'terraform', 'ansible', 'prometheus', 'grafana',
        
        # Big Data & ML
        'hadoop', 'spark', 'kafka', 'airflow', 'databricks', 'snowflake',
        'tableau', 'power bi', 'looker', 'mlflow',
        
        # Mobile
        'ios', 'android', 'react native', 'flutter', 'xamarin',
        
        # Soft Skills (untuk kelengkapan)
        'agile', 'scrum', 'kanban', 'leadership', 'communication', 'teamwork'
    }
    
    extracted = []
    for skill in skills_list:
        if skill in description_lower:
            extracted.append(skill)
    
    return list(set(extracted))  # Remove duplicates


async def scrape_all_jobs():
    """Main function to scrape all jobs for capstone project"""
    
    print("="*70)
    print("CAPSTONE PROJECT: AI-Driven Career Pathing & Skills Gap Analyzer")
    print("Job Scraper for Indonesia Market")
    print(f"Target: {TARGET_TOTAL_JOBS} job listings")
    print("="*70)
    
    # Check if session exists
    if not os.path.exists("linkedin_session.json"):
        print("\n❌ Session file not found!")
        print("Please run session creator first:")
        print("  python create_session.py")
        return None
    
    all_jobs = []
    
    # KODE PENTING - BrowserManager tetap sama
    async with BrowserManager(headless=False) as browser:
        await browser.load_session("linkedin_session.json")
        print("✓ Session loaded successfully\n")
        
        # KODE PENTING - Scraper initialization tetap sama
        search_scraper = JobSearchScraper(browser.page)
        job_scraper = JobScraper(browser.page)
        
        # Scrape untuk setiap role
        for role in TARGET_JOB_ROLES:
            print(f"\n{'='*50}")
            print(f"📌 Scraping role: {role}")
            print(f"{'='*50}")
            
            role_jobs = []
            
            # Scrape di multiple locations untuk mencapai target
            jobs_needed = JOBS_PER_ROLE
            locations_to_try = LOCATIONS.copy()
            
            while len(role_jobs) < jobs_needed and locations_to_try:
                location = locations_to_try.pop(0)
                remaining = jobs_needed - len(role_jobs)
                limit = min(remaining + 10, 30)  # Ambil lebih untuk antisipasi error
                
                jobs = await scrape_jobs_for_role(
                    search_scraper, 
                    job_scraper, 
                    role, 
                    location, 
                    limit
                )
                
                role_jobs.extend(jobs)
                print(f"    📊 Total for {role} so far: {len(role_jobs)}/{jobs_needed}")
                
                # Delay antar lokasi
                await asyncio.sleep(2)
            
            all_jobs.extend(role_jobs)
            print(f"\n✅ Completed {role}: {len(role_jobs)} jobs collected")
            
            # Progress report
            total_so_far = len(all_jobs)
            print(f"📈 Overall progress: {total_so_far}/{TARGET_TOTAL_JOBS} ({total_so_far/TARGET_TOTAL_JOBS*100:.1f}%)")
            
            # Save checkpoint every 2 roles
            if TARGET_JOB_ROLES.index(role) % 2 == 0:
                save_checkpoint(all_jobs)
    
    return all_jobs


def save_checkpoint(jobs_data, checkpoint_name="checkpoint"):
    """Save intermediate results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save as CSV
    df = pd.DataFrame(jobs_data)
    csv_path = f"data/raw/{checkpoint_name}_{timestamp}.csv"
    df.to_csv(csv_path, index=False)
    
    # Save as JSON
    json_path = f"data/raw/{checkpoint_name}_{timestamp}.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(jobs_data, f, indent=2, ensure_ascii=False)
    
    print(f"  💾 Checkpoint saved: {len(jobs_data)} jobs")


def generate_report(jobs_data):
    """Generate comprehensive report for Data Science team"""
    
    df = pd.DataFrame(jobs_data)
    
    report = {
        'scraping_date': datetime.now().isoformat(),
        'total_jobs': len(df),
        'total_unique_companies': df['company'].nunique(),
        'jobs_by_role': df['search_role'].value_counts().to_dict(),
        'jobs_by_location': df['location'].value_counts().head(10).to_dict(),
        'average_skills_per_job': df['skills_count'].mean(),
        'top_skills': [],
        'skill_coverage': {}
    }
    
    # Extract all skills
    all_skills = []
    for skills_list in df['extracted_skills'].dropna():
        if isinstance(skills_list, list):
            all_skills.extend(skills_list)
    
    from collections import Counter
    skill_counts = Counter(all_skills)
    
    # Top 20 skills
    report['top_skills'] = skill_counts.most_common(20)
    
    # Skill coverage percentage
    for skill, count in skill_counts.most_common(30):
        report['skill_coverage'][skill] = round(count / len(df) * 100, 2)
    
    # Save report
    with open('data/processed/scraping_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print("\n" + "="*70)
    print("SCRAPING REPORT")
    print("="*70)
    print(f"\n📊 Total jobs collected: {len(df)}")
    print(f"🏢 Unique companies: {df['company'].nunique()}")
    print(f"📈 Average skills per job: {df['skills_count'].mean():.2f}")
    
    print(f"\n📋 Jobs by role:")
    for role, count in report['jobs_by_role'].items():
        print(f"   - {role}: {count}")
    
    print(f"\n🔥 Top 10 Required Skills:")
    for skill, count in report['top_skills'][:10]:
        print(f"   - {skill}: {count} jobs ({report['skill_coverage'][skill]}%)")
    
    print(f"\n📍 Top locations:")
    for loc, count in report['jobs_by_location'].items():
        print(f"   - {loc}: {count}")
    
    return report


async def main():
    """Main function - MODIFIKASI untuk capstone requirements"""
    
    # Create directories if not exist
    os.makedirs("data/raw", exist_ok=True)
    os.makedirs("data/processed", exist_ok=True)
    
    # Start scraping
    all_jobs = await scrape_all_jobs()
    
    if not all_jobs:
        print("\n❌ No jobs scraped. Please check your session and try again.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(all_jobs)
    
    # Save final results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # CSV for Data Science team
    csv_path = f"data/processed/linkedin_jobs_final_{timestamp}.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n✅ Final CSV saved: {csv_path}")
    
    # JSON for AI Engineer (clean version without long description)
    df_for_ai = df.drop(columns=['job_description'], errors='ignore')
    json_path = f"data/processed/jobs_for_training_{timestamp}.json"
    df_for_ai.to_json(json_path, orient='records', indent=2, force_ascii=False)
    print(f"✅ Training JSON saved: {json_path}")
    
    # Generate report
    report = generate_report(all_jobs)
    
    # Summary for team
    print("\n" + "="*70)
    print("✅ SCRAPING COMPLETED SUCCESSFULLY")
    print("="*70)
    print(f"\n📁 Output files:")
    print(f"   - Raw data: data/raw/")
    print(f"   - Processed CSV: {csv_path}")
    print(f"   - Training JSON: {json_path}")
    print(f"   - Scraping report: data/processed/scraping_report.json")
    
    print("\n📊 Data ready for:")
    print("   ✅ Data Science team → EDA & skill analysis")
    print("   ✅ AI Engineer → Model training")
    print("   ✅ Fullstack team → API integration")
    
    print(f"\n🎯 Target: {TARGET_TOTAL_JOBS} jobs")
    print(f"📈 Achieved: {len(all_jobs)} jobs")
    print(f"✅ Completion rate: {len(all_jobs)/TARGET_TOTAL_JOBS*100:.1f}%")


if __name__ == "__main__":
    asyncio.run(main())
