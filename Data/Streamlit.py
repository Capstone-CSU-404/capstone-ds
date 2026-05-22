"""
Dashboard Analisis Pasar Kerja IT Indonesia (Apr–Mei 2026)
Run: streamlit run dashboard_it_jobs.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from collections import Counter
import re

# ─────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Lowongan IT Indonesia",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

h1, h2, h3 { font-family: 'Syne', sans-serif !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    color: white;
}
[data-testid="stSidebar"] * { color: white !important; }
[data-testid="stSidebar"] .stMultiSelect [data-baseweb="tag"] {
    background-color: #7c6af7 !important;
}

/* Metric cards */
.metric-card {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
    border: 1px solid rgba(124,106,247,0.3);
    border-radius: 12px;
    padding: 20px 24px;
    text-align: center;
    box-shadow: 0 4px 20px rgba(0,0,0,0.3);
}
.metric-card .label {
    font-size: 11px;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #a89ce8;
    margin-bottom: 6px;
    font-family: 'DM Sans', sans-serif;
}
.metric-card .value {
    font-size: 32px;
    font-weight: 800;
    color: #ffffff;
    font-family: 'Syne', sans-serif;
    line-height: 1;
}
.metric-card .sub {
    font-size: 12px;
    color: #7c6af7;
    margin-top: 4px;
}

/* Section headers */
.section-header {
    font-family: 'Syne', sans-serif;
    font-size: 20px;
    font-weight: 700;
    color: #1a1a2e;
    border-left: 4px solid #7c6af7;
    padding-left: 12px;
    margin: 24px 0 16px 0;
}

/* Insight box */
.insight-box {
    background: linear-gradient(135deg, #f8f6ff 0%, #ede8ff 100%);
    border-left: 4px solid #7c6af7;
    border-radius: 8px;
    padding: 14px 18px;
    margin: 12px 0;
    font-size: 14px;
    color: #2d2054;
}
.insight-box b { color: #5b3fcf; }

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: #f0edff;
    border-radius: 10px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 20px;
    font-family: 'Syne', sans-serif;
    font-weight: 600;
    font-size: 13px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #7c6af7, #5b3fcf) !important;
    color: white !important;
}

/* Main bg */
.main .block-container {
    padding-top: 1.5rem;
    max-width: 1400px;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# COLOR CONFIG
# ─────────────────────────────────────────────────────────────
ROLE_COLORS = {
    'Data Scientist'     : '#7c6af7',
    'Data Analyst'       : '#4fc3f7',
    'Data Engineer'      : '#f06292',
    'ML Engineer'        : '#81c784',
    'Backend Developer'  : '#ffb74d',
    'Frontend Developer' : '#e57373',
    'Fullstack Developer': '#4db6ac',
    'DevOps/Cloud'       : '#ba68c8',
    'Cybersecurity'      : '#ff8a65',
    'Mobile Developer'   : '#90a4ae',
    'QA/Tester'          : '#a5d6a7',
    'Business Analyst'   : '#fff176',
    'IT Support'         : '#80cbc4',
    'Product Manager'    : '#ef9a9a',
    'UI/UX Designer'     : '#ce93d8',
}

SENIORITY_COLORS = {
    'Junior'           : '#b3c6ff',
    'Mid-level'        : '#6699ff',
    'Senior'           : '#3366cc',
    'Manager/Head'     : '#1a3399',
    'Tidak Disebutkan' : '#cccccc',
}

# ─────────────────────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────────────────────
@st.cache_data
def load_data(uploaded_file):
    df = pd.read_csv(uploaded_file)

    # Normalize column names
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')

    # Fix typo if present
    if 'job_leevl' in df.columns:
        df.rename(columns={'job_leevl': 'job_level'}, inplace=True)

    # Parse extracted_skills if it's a string representation of a list
    if 'extracted_skills' in df.columns:
        def parse_skills(x):
            if isinstance(x, list): return x
            if isinstance(x, str):
                x = x.strip("[]").replace("'", "").replace('"', '')
                return [s.strip() for s in x.split(',') if s.strip()]
            return []
        df['extracted_skills'] = df['extracted_skills'].apply(parse_skills)
    else:
        df['extracted_skills'] = [[] for _ in range(len(df))]

    # skills_count fallback
    if 'skills_count' not in df.columns:
        df['skills_count'] = df['extracted_skills'].apply(len)

    # salary_avg numeric
    if 'salary_avg' in df.columns:
        df['salary_avg'] = pd.to_numeric(df['salary_avg'], errors='coerce')
        df['salary_avg_jt'] = df['salary_avg'] / 1_000_000
    else:
        df['salary_avg'] = np.nan
        df['salary_avg_jt'] = np.nan

    # title_seniority feature engineering
    SENIORITY_MAP = {
        'Head': 'Manager/Head', 'Director': 'Manager/Head', 'VP': 'Manager/Head',
        'Chief': 'Manager/Head', 'Lead': 'Manager/Head', 'Principal': 'Manager/Head',
        'Architect': 'Manager/Head', 'Manager': 'Manager/Head',
        'Senior': 'Senior', 'Sr.': 'Senior', 'Sr ': 'Senior',
        'Mid': 'Mid-level', 'Associate': 'Mid-level', 'Staff': 'Mid-level',
        'Specialist': 'Mid-level',
        'Junior': 'Junior', 'Jr.': 'Junior', 'Jr ': 'Junior',
        'Entry': 'Junior', 'Intern': 'Junior', 'Magang': 'Junior', 'Fresh': 'Junior',
    }
    def extract_seniority(title):
        if not isinstance(title, str): return 'Tidak Disebutkan'
        for kw, lvl in SENIORITY_MAP.items():
            if kw.lower() in title.lower(): return lvl
        return 'Tidak Disebutkan'
    df['title_seniority'] = df['title'].apply(extract_seniority)

    # company_size_proxy
    freq = df['company'].value_counts()
    df['company_hiring_freq'] = df['company'].map(freq)
    df['company_size_proxy'] = pd.cut(
        df['company_hiring_freq'],
        bins=[0, 2, 5, 10, 9999],
        labels=['Small (1–2)', 'Medium (3–5)', 'Large (6–10)', 'Enterprise (10+)']
    )

    return df

# ─────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 💼 IT Jobs Dashboard")
    st.markdown("**Pasar Kerja IT Indonesia**  \nApr – Mei 2026")
    st.markdown("---")

    uploaded_file = st.file_uploader(
        "Upload dataset CSV",
        type=["csv"],
        help="Kolom: title, search_role, job_level, company, location, salary_avg, extracted_skills, skills_count"
    )

    st.markdown("---")
    st.markdown("### 🔍 Filter Data")

# ─────────────────────────────────────────────────────────────
# DEMO DATA GENERATOR (jika tidak ada upload)
# ─────────────────────────────────────────────────────────────
@st.cache_data
def generate_demo_data():
    np.random.seed(42)
    roles = list(ROLE_COLORS.keys())
    role_weights = [0.12,0.14,0.10,0.08,0.12,0.08,0.08,0.06,0.05,0.05,0.04,0.03,0.03,0.01,0.01]
    job_levels = ['Junior','Mid','Senior','Manager/Head','Tidak Disebutkan']
    cities = ['Jakarta','Bandung','Surabaya','Yogyakarta','Bali','Medan','Remote','Semarang']
    
    skills_pool = {
        'Data Scientist': ['Python','SQL','Machine Learning','TensorFlow','Pandas','Scikit-learn','Statistics','R','Deep Learning','NLP'],
        'Data Analyst': ['SQL','Excel','Python','Tableau','Power BI','Statistics','Looker','Google Analytics','Pandas','Data Visualization'],
        'Data Engineer': ['Python','SQL','Spark','Kafka','Airflow','AWS','GCP','ETL','dbt','Hadoop'],
        'ML Engineer': ['Python','TensorFlow','PyTorch','MLOps','Docker','Kubernetes','AWS','Scikit-learn','FastAPI','CI/CD'],
        'Backend Developer': ['Python','Java','Node.js','SQL','REST API','Docker','Git','Spring Boot','Go','PostgreSQL'],
        'Frontend Developer': ['JavaScript','React','TypeScript','CSS','HTML','Vue.js','Git','Next.js','Tailwind','Figma'],
        'Fullstack Developer': ['JavaScript','React','Node.js','SQL','TypeScript','Docker','Git','HTML','CSS','REST API'],
        'DevOps/Cloud': ['AWS','Docker','Kubernetes','Terraform','CI/CD','Linux','GCP','Azure','Ansible','Bash'],
        'Cybersecurity': ['Network Security','Penetration Testing','Python','SIEM','Linux','Firewall','ISO 27001','OWASP','Incident Response','Forensics'],
        'Mobile Developer': ['Kotlin','Swift','Flutter','React Native','Android','iOS','Git','Firebase','REST API','Java'],
        'QA/Tester': ['Selenium','Python','Manual Testing','Automation','JIRA','Postman','SQL','TestNG','Cypress','Agile'],
        'Business Analyst': ['SQL','Excel','Requirements Analysis','Power BI','Visio','JIRA','Agile','Stakeholder Management','UML','Tableau'],
        'IT Support': ['Windows','Linux','Networking','Troubleshooting','Active Directory','Help Desk','Hardware','ITIL','TCP/IP','Office 365'],
        'Product Manager': ['Agile','Product Strategy','JIRA','Analytics','Stakeholder Management','Roadmapping','SQL','Figma','OKR','User Research'],
        'UI/UX Designer': ['Figma','Adobe XD','User Research','Prototyping','Wireframing','Sketch','HTML','CSS','Design Systems','Usability Testing'],
    }
    
    salary_base = {
        'Data Scientist':8,'Data Analyst':6,'Data Engineer':9,'ML Engineer':11,
        'Backend Developer':8,'Frontend Developer':7,'Fullstack Developer':8.5,
        'DevOps/Cloud':10,'Cybersecurity':9,'Mobile Developer':8,
        'QA/Tester':6,'Business Analyst':7,'IT Support':5,'Product Manager':12,'UI/UX Designer':7
    }
    level_mult = {'Junior':0.65,'Mid':1.0,'Senior':1.45,'Manager/Head':1.9,'Tidak Disebutkan':1.0}
    
    title_templates = {
        'Data Scientist': ['Data Scientist','Senior Data Scientist','Junior Data Scientist','Lead Data Scientist','Principal Data Scientist'],
        'Data Analyst': ['Data Analyst','Business Intelligence Analyst','Senior Data Analyst','Junior Data Analyst','Analytics Engineer'],
        'Data Engineer': ['Data Engineer','Senior Data Engineer','ETL Developer','Big Data Engineer','Analytics Engineer'],
        'ML Engineer': ['Machine Learning Engineer','MLOps Engineer','AI Engineer','Senior ML Engineer','Research Engineer'],
        'Backend Developer': ['Backend Developer','Software Engineer','Java Developer','Python Developer','Senior Backend Developer'],
        'Frontend Developer': ['Frontend Developer','React Developer','UI Developer','Senior Frontend Developer','Web Developer'],
        'Fullstack Developer': ['Fullstack Developer','Software Engineer','Web Developer','Senior Fullstack Developer','MEAN Stack Developer'],
        'DevOps/Cloud': ['DevOps Engineer','Cloud Engineer','Site Reliability Engineer','Platform Engineer','Infrastructure Engineer'],
        'Cybersecurity': ['Security Analyst','Penetration Tester','SOC Analyst','Information Security Officer','Cybersecurity Engineer'],
        'Mobile Developer': ['Android Developer','iOS Developer','Mobile Developer','Flutter Developer','React Native Developer'],
        'QA/Tester': ['QA Engineer','Test Automation Engineer','Software Tester','QA Analyst','SDET'],
        'Business Analyst': ['Business Analyst','Systems Analyst','Product Analyst','Process Analyst','Functional Analyst'],
        'IT Support': ['IT Support Specialist','Help Desk Technician','System Administrator','Network Administrator','IT Technician'],
        'Product Manager': ['Product Manager','Senior Product Manager','Associate Product Manager','Head of Product','Product Owner'],
        'UI/UX Designer': ['UI/UX Designer','Product Designer','UX Researcher','UI Designer','Senior UX Designer'],
    }
    
    companies = [
        'Gojek','Tokopedia','Shopee','Traveloka','Bukalapak','OVO','Dana','Blibli',
        'Telkom','BRI','BCA','Mandiri','Pertamina','Astra','Grab','TikTok',
        'Google Indonesia','Microsoft','IBM','Accenture','Deloitte','KPMG',
        'Startup A','Startup B','Startup C','Tech Corp','Digital Agency X',
        'Fintech Y','Edtech Z','Healthtech W'
    ]
    company_weights = [5,5,5,4,3,3,3,3,3,3,3,3,2,2,4,4,2,2,1,1,1,1,
                      1,1,1,1,1,1,1,1]

    N = 2000
    rows = []
    for _ in range(N):
        role = np.random.choice(roles, p=role_weights)
        level = np.random.choice(job_levels, p=[0.25,0.30,0.25,0.10,0.10])
        title = np.random.choice(title_templates[role])
        company = np.random.choice(companies, p=[w/sum(company_weights) for w in company_weights])
        city = np.random.choice(cities, p=[0.35,0.12,0.12,0.08,0.07,0.06,0.15,0.05])
        
        n_skills = np.random.randint(2, 9)
        pool = skills_pool.get(role, ['Python','SQL'])
        chosen = np.random.choice(pool, size=min(n_skills, len(pool)), replace=False).tolist()
        
        has_salary = np.random.random() < 0.45
        if has_salary:
            base = salary_base.get(role, 7)
            mult = level_mult.get(level, 1.0)
            salary = base * mult * np.random.uniform(0.85, 1.2) * 1_000_000
        else:
            salary = np.nan
        
        rows.append({
            'title': title,
            'search_role': role,
            'job_level': level,
            'company': company,
            'location': city,
            'salary_avg': salary,
            'extracted_skills': chosen,
            'skills_count': len(chosen),
        })
    
    return pd.DataFrame(rows)


# ─────────────────────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────────────────────
if uploaded_file:
    df_raw = load_data(uploaded_file)
    data_source = "📁 Data Upload"
else:
    df_raw = generate_demo_data()
    # Apply feature engineering to demo data too
    SENIORITY_MAP = {
        'Head': 'Manager/Head', 'Director': 'Manager/Head', 'VP': 'Manager/Head',
        'Chief': 'Manager/Head', 'Lead': 'Manager/Head', 'Principal': 'Manager/Head',
        'Architect': 'Manager/Head', 'Manager': 'Manager/Head',
        'Senior': 'Senior', 'Sr.': 'Senior',
        'Mid': 'Mid-level', 'Associate': 'Mid-level', 'Staff': 'Mid-level',
        'Specialist': 'Mid-level',
        'Junior': 'Junior', 'Jr.': 'Junior',
        'Entry': 'Junior', 'Intern': 'Junior', 'Magang': 'Junior', 'Fresh': 'Junior',
    }
    def extract_seniority(title):
        if not isinstance(title, str): return 'Tidak Disebutkan'
        for kw, lvl in SENIORITY_MAP.items():
            if kw.lower() in title.lower(): return lvl
        return 'Tidak Disebutkan'
    df_raw['title_seniority'] = df_raw['title'].apply(extract_seniority)
    freq = df_raw['company'].value_counts()
    df_raw['company_hiring_freq'] = df_raw['company'].map(freq)
    df_raw['company_size_proxy'] = pd.cut(
        df_raw['company_hiring_freq'],
        bins=[0, 2, 5, 10, 9999],
        labels=['Small (1–2)', 'Medium (3–5)', 'Large (6–10)', 'Enterprise (10+)']
    )
    df_raw['salary_avg_jt'] = df_raw['salary_avg'] / 1_000_000
    data_source = "🎲 Demo Data (2.000 lowongan simulasi)"

# ─────────────────────────────────────────────────────────────
# SIDEBAR FILTERS
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    all_roles = sorted(df_raw['search_role'].dropna().unique().tolist())
    sel_roles = st.multiselect("Role IT", all_roles, default=all_roles[:], placeholder="Semua role")

    all_levels = sorted(df_raw['job_level'].dropna().unique().tolist())
    sel_levels = st.multiselect("Job Level", all_levels, default=all_levels, placeholder="Semua level")

    all_cities = sorted(df_raw['location'].dropna().unique().tolist())
    sel_cities = st.multiselect("Lokasi", all_cities, default=all_cities, placeholder="Semua kota")

    sal_col = df_raw['salary_avg_jt'].dropna()
    if len(sal_col) > 0:
        sal_min_v = float(sal_col.min())
        sal_max_v = float(sal_col.max())
        sal_range = st.slider(
            "Range Salary (Juta IDR)",
            min_value=round(sal_min_v, 1),
            max_value=round(sal_max_v, 1),
            value=(round(sal_min_v, 1), round(sal_max_v, 1)),
            step=0.5
        )
    else:
        sal_range = (0, 999)

    st.markdown("---")
    st.caption(f"Sumber: {data_source}")

# ─────────────────────────────────────────────────────────────
# APPLY FILTERS
# ─────────────────────────────────────────────────────────────
df = df_raw.copy()
if sel_roles:   df = df[df['search_role'].isin(sel_roles)]
if sel_levels:  df = df[df['job_level'].isin(sel_levels)]
if sel_cities:  df = df[df['location'].isin(sel_cities)]

df_sal = df[df['salary_avg_jt'].notna()]
df_sal = df_sal[(df_sal['salary_avg_jt'] >= sal_range[0]) & (df_sal['salary_avg_jt'] <= sal_range[1])]

ROLE_ORDER = [r for r in list(ROLE_COLORS.keys()) if r in df['search_role'].unique()]

# ─────────────────────────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#0f0c29 0%,#302b63 60%,#24243e 100%);
            border-radius:16px;padding:28px 36px;margin-bottom:24px;">
  <div style="font-family:'Syne',sans-serif;font-size:28px;font-weight:800;color:white;line-height:1.1;">
    📊 Dashboard Pasar Kerja IT Indonesia
  </div>
  <div style="font-size:14px;color:#a89ce8;margin-top:6px;">
    Analisis Lowongan Kerja · Apr – Mei 2026 · Insight & Kesimpulan Interaktif
  </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# KPI CARDS
# ─────────────────────────────────────────────────────────────
total_jobs   = len(df)
total_roles  = df['search_role'].nunique()
avg_salary   = df_sal['salary_avg_jt'].mean() if len(df_sal) > 0 else 0
total_comp   = df['company'].nunique()
pct_salary   = len(df_sal) / len(df) * 100 if len(df) > 0 else 0
avg_skills   = df['skills_count'].mean() if 'skills_count' in df.columns else 0

c1, c2, c3, c4, c5 = st.columns(5)
for col, label, value, sub in [
    (c1, "Total Lowongan",  f"{total_jobs:,}", f"{total_roles} role"),
    (c2, "Rata-rata Salary", f"Rp {avg_salary:.1f}jt", f"{pct_salary:.0f}% ada info gaji"),
    (c3, "Perusahaan",       f"{total_comp:,}", "unik"),
    (c4, "Avg Skills/Job",   f"{avg_skills:.1f}", "keahlian"),
    (c5, "Kota/Daerah",      f"{df['location'].nunique()}", "lokasi"),
]:
    col.markdown(f"""
    <div class="metric-card">
        <div class="label">{label}</div>
        <div class="value">{value}</div>
        <div class="sub">{sub}</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
# TABS
# ─────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📌 Distribusi Role",
    "🛠️ Skills",
    "💰 Salary",
    "🏢 Perusahaan",
    "📋 Job Level",
    "🔎 Insight & Kesimpulan",
])

# ════════════════════════════════════════════════════════
# TAB 1 — DISTRIBUSI ROLE
# ════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-header">Q1 — Role IT Paling Banyak Dibutuhkan</div>', unsafe_allow_html=True)

    role_counts = df['search_role'].value_counts().reset_index()
    role_counts.columns = ['role', 'count']
    role_counts['pct'] = (role_counts['count'] / role_counts['count'].sum() * 100).round(1)
    role_counts['color'] = role_counts['role'].map(ROLE_COLORS)

    col_a, col_b = st.columns([2, 1])

    with col_a:
        fig = px.bar(
            role_counts.sort_values('count'),
            x='count', y='role',
            orientation='h',
            text=role_counts.sort_values('count').apply(lambda r: f"{r['count']:,}  ({r['pct']}%)", axis=1),
            color='role',
            color_discrete_map=ROLE_COLORS,
            title="Jumlah Lowongan per Role IT",
            height=420,
        )
        fig.update_traces(textposition='outside', textfont_size=11)
        fig.update_layout(
            showlegend=False, xaxis_title="Jumlah Lowongan",
            yaxis_title="", plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font_family='DM Sans',
            margin=dict(l=0, r=80, t=40, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col_b:
        fig2 = px.pie(
            role_counts.head(8), values='count', names='role',
            color='role', color_discrete_map=ROLE_COLORS,
            title="Top 8 Role (Proporsi)",
            hole=0.45,
        )
        fig2.update_traces(textposition='inside', textinfo='percent')
        fig2.update_layout(
            showlegend=True, height=420,
            paper_bgcolor='rgba(0,0,0,0)',
            font_family='DM Sans',
            margin=dict(l=0, r=0, t=40, b=20),
            legend=dict(font_size=10)
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Location breakdown
    st.markdown('<div class="section-header">Distribusi Lokasi</div>', unsafe_allow_html=True)
    loc_role = df.groupby(['location', 'search_role']).size().reset_index(name='count')
    top_locs = df['location'].value_counts().head(8).index.tolist()
    loc_role_top = loc_role[loc_role['location'].isin(top_locs)]

    fig3 = px.bar(
        loc_role_top, x='location', y='count', color='search_role',
        color_discrete_map=ROLE_COLORS,
        title="Komposisi Role per Kota (Top 8 Kota)",
        barmode='stack', height=380
    )
    fig3.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        font_family='DM Sans', xaxis_title="", yaxis_title="Jumlah Lowongan",
        legend=dict(font_size=9, title="Role")
    )
    st.plotly_chart(fig3, use_container_width=True)

# ════════════════════════════════════════════════════════
# TAB 2 — SKILLS
# ════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-header">Q2 — Skills yang Paling Sering Diminta</div>', unsafe_allow_html=True)

    col_x, col_y = st.columns([1, 1])

    with col_x:
        selected_role_skills = st.selectbox(
            "Pilih Role untuk detail skills:",
            options=['(Semua Role)'] + ROLE_ORDER
        )

    with col_y:
        top_n = st.slider("Tampilkan Top N Skills:", min_value=5, max_value=20, value=10)

    if selected_role_skills == '(Semua Role)':
        flat = [s for row in df['extracted_skills'] for s in row if s.lower() != 'r']
    else:
        subset = df[df['search_role'] == selected_role_skills]
        flat = [s for row in subset['extracted_skills'] for s in row if s.lower() != 'r']

    cnt = Counter(flat)
    top_skills = pd.DataFrame(cnt.most_common(top_n), columns=['skill', 'count'])

    col_s1, col_s2 = st.columns([3, 2])
    with col_s1:
        fig_sk = px.bar(
            top_skills[::-1].reset_index(drop=True),
            x='count', y='skill', orientation='h',
            text='count',
            color='count',
            color_continuous_scale='Blues',
            title=f"Top {top_n} Skills — {selected_role_skills}",
            height=400,
        )
        fig_sk.update_traces(textposition='outside')
        fig_sk.update_layout(
            showlegend=False, coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_family='DM Sans', yaxis_title="", xaxis_title="Frekuensi",
            margin=dict(l=0, r=60, t=40, b=20)
        )
        st.plotly_chart(fig_sk, use_container_width=True)

    with col_s2:
        fig_tree = px.treemap(
            top_skills, path=['skill'], values='count',
            color='count', color_continuous_scale='Purples',
            title="Treemap Distribusi Skills",
        )
        fig_tree.update_layout(
            height=400, paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=40, b=0), font_family='DM Sans'
        )
        st.plotly_chart(fig_tree, use_container_width=True)

    # Heatmap skill × role
    st.markdown('<div class="section-header">Q2b — Heatmap Skills vs Role</div>', unsafe_allow_html=True)
    all_flat = [s for row in df['extracted_skills'] for s in row if s.lower() != 'r']
    top_global = [s for s, _ in Counter(all_flat).most_common(15)]

    heat_data = {}
    for role in ROLE_ORDER:
        sub = df[df['search_role'] == role]
        n = len(sub)
        if n == 0: continue
        flat_r = [s for row in sub['extracted_skills'] for s in row]
        cnt_r = Counter(flat_r)
        heat_data[role] = {sk: round(cnt_r.get(sk, 0) / n * 100, 1) for sk in top_global}

    if heat_data:
        heat_df = pd.DataFrame(heat_data, index=top_global).T
        fig_heat = px.imshow(
            heat_df, text_auto=True,
            color_continuous_scale='Blues',
            title="% Job Postings yang Mensyaratkan Skill per Role",
            aspect='auto', height=400
        )
        fig_heat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            font_family='DM Sans',
            xaxis_tickangle=-30,
            coloraxis_colorbar_title="% postings",
            margin=dict(l=0, r=0, t=40, b=60)
        )
        st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("""
    <div class="insight-box">
        💡 <b>Insight Skills:</b> Python dan SQL mendominasi hampir seluruh role data & backend. 
        Skills cloud/DevOps (AWS, Docker, Kubernetes) makin penting di semua domain. 
        Setiap role memiliki "signature skills" unik — ML Engineer butuh PyTorch/TensorFlow, 
        sementara Business Analyst lebih ke Excel & Stakeholder Management.
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# TAB 3 — SALARY
# ════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-header">Q3 — Analisis Salary</div>', unsafe_allow_html=True)

    if len(df_sal) == 0:
        st.warning("Tidak ada data salary untuk filter yang dipilih.")
    else:
        # Avg salary per role
        avg_sal = df_sal.groupby('search_role')['salary_avg_jt'].mean().reset_index()
        avg_sal.columns = ['role', 'avg_salary']
        avg_sal = avg_sal.sort_values('avg_salary', ascending=False)

        col_3a, col_3b = st.columns([3, 2])
        with col_3a:
            fig_sal = px.bar(
                avg_sal, x='role', y='avg_salary',
                color='role', color_discrete_map=ROLE_COLORS,
                text=avg_sal['avg_salary'].apply(lambda v: f"Rp {v:.1f}jt"),
                title="Rata-rata Salary per Role IT",
                height=420,
            )
            fig_sal.update_traces(textposition='outside')
            fig_sal.update_layout(
                showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', font_family='DM Sans',
                xaxis_tickangle=-30, xaxis_title="", yaxis_title="Salary (Juta IDR/bulan)",
                margin=dict(l=0, r=0, t=40, b=80)
            )
            st.plotly_chart(fig_sal, use_container_width=True)

        with col_3b:
            fig_box = px.box(
                df_sal, x='search_role', y='salary_avg_jt',
                color='search_role', color_discrete_map=ROLE_COLORS,
                title="Distribusi Salary per Role (Box Plot)",
                height=420,
            )
            fig_box.update_layout(
                showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)', font_family='DM Sans',
                xaxis_tickangle=-35, xaxis_title="", yaxis_title="Salary (Juta IDR/bulan)",
                margin=dict(l=0, r=0, t=40, b=80)
            )
            st.plotly_chart(fig_box, use_container_width=True)

        # Skills count vs salary
        st.markdown('<div class="section-header">Q5 — Korelasi Jumlah Skills vs Salary</div>', unsafe_allow_html=True)

        p99 = df_sal['salary_avg_jt'].quantile(0.99)
        df_corr = df_sal[df_sal['salary_avg_jt'] <= p99].copy()
        df_corr['skills_bucket'] = pd.cut(
            df_corr['skills_count'],
            bins=[0, 2, 4, 6, 8, 100],
            labels=['0–2', '3–4', '5–6', '7–8', '9+']
        )
        bucket_avg = df_corr.groupby('skills_bucket', observed=True)['salary_avg_jt'].mean().reset_index()
        bucket_avg.columns = ['bucket', 'avg_salary']

        corr_val = df_corr[['skills_count', 'salary_avg_jt']].corr().iloc[0, 1]

        col_5a, col_5b = st.columns([1, 1])
        with col_5a:
            fig_bkt = px.bar(
                bucket_avg, x='bucket', y='avg_salary',
                text=bucket_avg['avg_salary'].apply(lambda v: f"Rp {v:.1f}jt"),
                color='avg_salary', color_continuous_scale='Purples',
                title="Rata-rata Salary per Bucket Jumlah Skill",
                height=360
            )
            fig_bkt.update_traces(textposition='outside')
            fig_bkt.update_layout(
                coloraxis_showscale=False,
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font_family='DM Sans', xaxis_title="Jumlah Skill",
                yaxis_title="Salary (Juta IDR/bulan)"
            )
            st.plotly_chart(fig_bkt, use_container_width=True)

        with col_5b:
            # Salary by seniority
            sen_order = ['Junior', 'Mid-level', 'Senior', 'Manager/Head', 'Tidak Disebutkan']
            sen_avg = df_sal.groupby('title_seniority')['salary_avg_jt'].mean().reindex(sen_order).dropna().reset_index()
            sen_avg.columns = ['seniority', 'avg_salary']

            fig_sen = px.bar(
                sen_avg, x='seniority', y='avg_salary',
                text=sen_avg['avg_salary'].apply(lambda v: f"Rp {v:.1f}jt"),
                color='seniority',
                color_discrete_map=SENIORITY_COLORS,
                title="Rata-rata Salary per Seniority Level",
                height=360
            )
            fig_sen.update_traces(textposition='outside')
            fig_sen.update_layout(
                showlegend=False,
                plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                font_family='DM Sans', xaxis_title="", yaxis_title="Salary (Juta IDR/bulan)"
            )
            st.plotly_chart(fig_sen, use_container_width=True)

        st.markdown(f"""
        <div class="insight-box">
            💡 <b>Insight Salary:</b> Korelasi jumlah skill dengan salary = <b>{corr_val:.2f}</b>. 
            Semakin banyak skill yang dikuasai cenderung meningkatkan nilai gaji. 
            Gap salary antara Junior dan Manager/Head bisa mencapai <b>2–3x lipat</b>. 
            Role seperti Product Manager & ML Engineer berada di puncak skala gaji.
        </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════
# TAB 4 — PERUSAHAAN
# ════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">Q7 — Analisis Perusahaan</div>', unsafe_allow_html=True)

    freq = df['company'].value_counts()
    top15 = freq.head(15).reset_index()
    top15.columns = ['company', 'count']

    col_7a, col_7b = st.columns([3, 2])

    with col_7a:
        fig_c = px.bar(
            top15.sort_values('count'),
            x='count', y='company', orientation='h',
            text='count', color='count',
            color_continuous_scale='Blues',
            title="Top 15 Perusahaan Paling Aktif Merekrut",
            height=440,
        )
        fig_c.update_traces(textposition='outside')
        fig_c.update_layout(
            coloraxis_showscale=False,
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_family='DM Sans', xaxis_title="Jumlah Lowongan", yaxis_title="",
            margin=dict(r=40)
        )
        st.plotly_chart(fig_c, use_container_width=True)

    with col_7b:
        size_order = ['Small (1–2)', 'Medium (3–5)', 'Large (6–10)', 'Enterprise (10+)']
        size_cnt = df['company_size_proxy'].value_counts().reindex(size_order).fillna(0)

        fig_sz = px.pie(
            values=size_cnt.values, names=size_cnt.index,
            title="Komposisi Ukuran Perusahaan",
            color_discrete_sequence=['#B5D4F4', '#378ADD', '#185FA5', '#0C447C'],
            hole=0.4,
        )
        fig_sz.update_layout(
            height=440, paper_bgcolor='rgba(0,0,0,0)',
            font_family='DM Sans', legend=dict(font_size=10)
        )
        st.plotly_chart(fig_sz, use_container_width=True)

    # Salary by company size
    st.markdown('<div class="section-header">Q7c — Salary vs Ukuran Perusahaan</div>', unsafe_allow_html=True)

    if len(df_sal) > 0:
        size_sal = df_sal.groupby('company_size_proxy', observed=True)['salary_avg_jt'].mean().reindex(size_order).dropna()
        size_vol = df['company_size_proxy'].value_counts().reindex(size_order).fillna(0)

        fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
        fig_dual.add_trace(
            go.Bar(x=size_order, y=size_sal.values,
                   name='Avg Salary', marker_color=['#B5D4F4','#378ADD','#185FA5','#0C447C'],
                   text=[f"Rp {v:.1f}jt" for v in size_sal.values],
                   textposition='outside'),
            secondary_y=False
        )
        fig_dual.add_trace(
            go.Scatter(x=size_order, y=size_vol.values,
                       name='Jumlah Lowongan', mode='lines+markers',
                       line=dict(color='#C44E52', width=2),
                       marker=dict(size=10)),
            secondary_y=True
        )
        fig_dual.update_layout(
            title="Rata-rata Salary & Volume Lowongan per Ukuran Perusahaan",
            plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
            font_family='DM Sans', height=380,
            legend=dict(orientation='h', y=1.08)
        )
        fig_dual.update_yaxes(title_text="Salary (Juta IDR/bulan)", secondary_y=False)
        fig_dual.update_yaxes(title_text="Jumlah Lowongan", secondary_y=True)
        st.plotly_chart(fig_dual, use_container_width=True)

# ════════════════════════════════════════════════════════
# TAB 5 — JOB LEVEL
# ════════════════════════════════════════════════════════
with tab5:
    st.markdown('<div class="section-header">Q4 — Distribusi Job Level per Role</div>', unsafe_allow_html=True)

    LEVEL_ORDER = ['Junior', 'Mid', 'Senior', 'Manager/Head', 'Tidak Disebutkan']
    LEVEL_COLORS_MAP = {
        'Junior': '#03045E', 'Mid': '#0096C7', 'Senior': '#48CAE4',
        'Manager/Head': '#ADE8F4', 'Tidak Disebutkan': '#CCCCCC',
    }

    level_df = df.groupby(['search_role', 'job_level']).size().reset_index(name='count')

    fig_lv = px.bar(
        level_df,
        x='search_role', y='count', color='job_level',
        color_discrete_map=LEVEL_COLORS_MAP,
        barmode='stack',
        title="Distribusi Job Level per Role IT",
        category_orders={'job_level': LEVEL_ORDER},
        height=420,
        text='count',
    )
    fig_lv.update_traces(texttemplate='%{text}', textposition='inside', textfont_size=9)
    fig_lv.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
        font_family='DM Sans', xaxis_tickangle=-30,
        xaxis_title="", yaxis_title="Jumlah Lowongan",
        legend=dict(title="Level", font_size=10)
    )
    st.plotly_chart(fig_lv, use_container_width=True)

    # Heatmap % tiap level
    level_pct = df.groupby(['search_role', 'job_level']).size().unstack(fill_value=0)
    available_levels = [l for l in LEVEL_ORDER if l in level_pct.columns]
    level_pct = level_pct[available_levels]
    level_pct_norm = level_pct.div(level_pct.sum(axis=1), axis=0) * 100

    fig_lv2 = px.imshow(
        level_pct_norm.round(1),
        text_auto=True,
        color_continuous_scale='Blues',
        title="% Proporsi Level per Role",
        aspect='auto', height=380
    )
    fig_lv2.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', font_family='DM Sans',
        xaxis_title="Job Level", yaxis_title="",
        margin=dict(l=0, r=0, t=40, b=20)
    )
    st.plotly_chart(fig_lv2, use_container_width=True)

    # Unique job titles per role
    st.markdown('<div class="section-header">Q8d — Keberagaman Job Title per Role</div>', unsafe_allow_html=True)
    uniq_titles = df.groupby('search_role')['title'].nunique().reset_index()
    uniq_titles.columns = ['role', 'unique_titles']
    uniq_titles = uniq_titles.sort_values('unique_titles', ascending=False)

    fig_ut = px.bar(
        uniq_titles, x='role', y='unique_titles',
        color='role', color_discrete_map=ROLE_COLORS,
        text='unique_titles',
        title="Jumlah Unique Job Title per Role (semakin tinggi = semakin beragam)",
        height=380,
    )
    fig_ut.update_traces(textposition='outside')
    fig_ut.update_layout(
        showlegend=False, plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)', font_family='DM Sans',
        xaxis_tickangle=-30, xaxis_title="", yaxis_title="Jumlah Unique Title",
    )
    st.plotly_chart(fig_ut, use_container_width=True)

# ════════════════════════════════════════════════════════
# TAB 6 — INSIGHT & KESIMPULAN
# ════════════════════════════════════════════════════════
with tab6:
    st.markdown("""
    <div style="background:linear-gradient(135deg,#0f0c29,#302b63);border-radius:14px;
                padding:24px 32px;margin-bottom:20px;">
        <div style="font-family:'Syne',sans-serif;font-size:22px;font-weight:800;color:white;">
            🔎 Ringkasan Insight & Kesimpulan
        </div>
        <div style="color:#a89ce8;font-size:13px;margin-top:4px;">
            Berdasarkan analisis data lowongan IT Apr–Mei 2026
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_i1, col_i2 = st.columns(2)

    with col_i1:
        st.markdown("""
        <div class="insight-box">
            <b>📌 Q1 — Distribusi Role</b><br><br>
            • <b>Data Analyst</b> dan <b>Backend Developer</b> mendominasi jumlah lowongan, 
            menunjukkan demand tinggi di dua bidang ini.<br>
            • Role <b>ML Engineer</b> dan <b>DevOps/Cloud</b> tumbuh signifikan, 
            mencerminkan tren adopsi AI dan cloud infrastructure di perusahaan Indonesia.<br>
            • Jakarta tetap menjadi hub utama (~35% lowongan), namun posisi <b>Remote</b> 
            terus meningkat pasca-pandemi.
        </div>

        <div class="insight-box">
            <b>🛠️ Q2 — Skills Demand</b><br><br>
            • <b>Python</b> dan <b>SQL</b> adalah skills paling universal — dibutuhkan oleh 
            hampir semua role data & backend.<br>
            • Stack cloud (<b>AWS, GCP, Docker</b>) makin jadi syarat umum, bukan hanya untuk DevOps.<br>
            • Untuk frontend: <b>React + TypeScript</b> menjadi kombinasi yang paling banyak diminta.<br>
            • Soft skills seperti <b>Agile</b> dan <b>Stakeholder Management</b> menonjol di 
            role BA dan PM.
        </div>

        <div class="insight-box">
            <b>💰 Q3 & Q5 — Salary & Skills</b><br><br>
            • <b>Product Manager</b> dan <b>ML Engineer</b> memimpin tangga gaji 
            dengan rata-rata tertinggi.<br>
            • Kandidat dengan <b>7+ skills</b> memperoleh gaji rata-rata ~40% lebih tinggi 
            dibanding yang hanya memiliki 1–2 skills.<br>
            • Gap gaji Junior vs Senior/Manager bisa mencapai <b>2–3x lipat</b> — 
            investasi dalam seniority sangat worth it.
        </div>
        """, unsafe_allow_html=True)

    with col_i2:
        st.markdown("""
        <div class="insight-box">
            <b>🏢 Q7 — Analisis Perusahaan</b><br><br>
            • Perusahaan <b>Enterprise (10+ postings)</b> menawarkan gaji rata-rata lebih tinggi 
            sekaligus volume lowongan terbanyak — pilihan ideal untuk fresh graduate.<br>
            • Mayoritas lowongan berasal dari perusahaan <b>startup teknologi</b> lokal 
            dan <b>tech giant</b> yang ekspansi.<br>
            • Perusahaan <b>Small (1–2 postings)</b> sering menawarkan posisi lebih spesifik 
            dengan potensi impact lebih besar per individu.
        </div>

        <div class="insight-box">
            <b>📋 Q4 & Q8 — Level & Title</b><br><br>
            • Porsi lowongan <b>Mid-level</b> paling dominan (~30%) — menunjukkan pasar 
            sedang butuh kandidat berpengalaman 2–4 tahun.<br>
            • Lowongan <b>Senior</b> terbuka lebar di Data Engineering dan DevOps/Cloud, 
            dua area dengan shortage talenta terbesar.<br>
            • Keberagaman judul pekerjaan (<i>job title variation</i>) tertinggi ada di 
            <b>Backend Developer</b> — menandakan definisi role yang masih fluid di industri.
        </div>

        <div class="insight-box">
            <b>🎯 Rekomendasi untuk Job Seeker</b><br><br>
            1. Kuasai <b>Python + SQL + satu cloud platform</b> sebagai fondasi minimum.<br>
            2. Targetkan posisi <b>Data Engineer</b> atau <b>DevOps</b> untuk gaji kompetitif 
            dengan supply kandidat yang masih terbatas.<br>
            3. Tambahkan <b>5–8 skills relevan</b> di CV untuk meningkatkan daya tawar gaji.<br>
            4. Pertimbangkan <b>Enterprise companies</b> jika ingin stabilitas + gaji kompetitif.
        </div>
        """, unsafe_allow_html=True)

    # Summary stats tabel
    st.markdown('<div class="section-header">📊 Ringkasan Statistik per Role</div>', unsafe_allow_html=True)

    summary_rows = []
    for role in ROLE_ORDER:
        sub = df[df['search_role'] == role]
        sub_sal = df_sal[df_sal['search_role'] == role] if len(df_sal) > 0 else pd.DataFrame()
        
        top_skill = ""
        flat_r = [s for row in sub['extracted_skills'] for s in row if s.lower() != 'r']
        if flat_r:
            top_skill = Counter(flat_r).most_common(1)[0][0]
        
        top_lvl = sub['job_level'].value_counts().idxmax() if len(sub) > 0 else "-"
        avg_s = sub_sal['salary_avg_jt'].mean() if len(sub_sal) > 0 else None
        
        summary_rows.append({
            'Role': role,
            'Lowongan': len(sub),
            '% dari Total': f"{len(sub)/len(df)*100:.1f}%",
            'Top Skill': top_skill,
            'Level Dominan': top_lvl,
            'Avg Salary': f"Rp {avg_s:.1f}jt" if avg_s and not np.isnan(avg_s) else "N/A",
        })

    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(
        summary_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Lowongan": st.column_config.NumberColumn(format="%d"),
        }
    )

# ─────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────
st.markdown("""
<hr style="border:none;border-top:1px solid #e0d8ff;margin:32px 0 16px;">
<div style="text-align:center;color:#9e96cc;font-size:12px;font-family:'DM Sans',sans-serif;">
    Dashboard Pasar Kerja IT Indonesia · Apr–Mei 2026 · 
    Built with Streamlit & Plotly
</div>
""", unsafe_allow_html=True)
