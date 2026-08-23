import logging
import streamlit as st
import pandas as pd
from src.data_loader import load_data, render_refresh_button, ensure_data_loaded
from src.ui_styles import inject_styles, page_hero, section_header, render_sidebar_toggle

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("HRSystem.App")

st.set_page_config(
    page_title="HR System — Jhandewalas Foods",
    page_icon="👥",
    layout="wide"
)

inject_styles()
render_sidebar_toggle()

# ── Hero ──────────────────────────────────────────────────────────────────────
page_hero(
    "🏢",
    "AI-Enabled HR Management System",
    "Jhandewalas Foods Limited · Powered by Groq LLM + Rule-Based Analytics"
)

# ── Module cards ──────────────────────────────────────────────────────────────
section_header("🧭", "System Modules")

c1, c2, c3 = st.columns(3)

with c1:
    st.markdown("""<a href="./Dashboard" target="_self" style="text-decoration: none; color: inherit; display: block; height: 100%;">
        <div class="hr-module-card">
            <div class="mod-icon">📊</div>
            <div class="mod-title">HR Dashboard</div>
            <div class="mod-desc">Live workforce metrics, attendance analysis, recruitment pipeline, CTC summary, and data quality exception engine.</div>
        </div>
    </a>""", unsafe_allow_html=True)
    st.page_link("pages/1_Dashboard.py", label="Open HR Dashboard", icon="📊", use_container_width=True)

with c2:
    st.markdown("""<a href="./Agentic_Sourcing" target="_self" style="text-decoration: none; color: inherit; display: block; height: 100%;">
        <div class="hr-module-card">
            <div class="mod-icon">🤖</div>
            <div class="mod-title">Agentic Sourcing</div>
            <div class="mod-desc">AI-powered candidate matching, ranked shortlisting, personalised outreach generation, and human-in-the-loop approval flow.</div>
        </div>
    </a>""", unsafe_allow_html=True)
    st.page_link("pages/2_Agentic_Sourcing.py", label="Open Agentic Sourcing", icon="🤖", use_container_width=True)

with c3:
    st.markdown("""<a href="./Audit_Log" target="_self" style="text-decoration: none; color: inherit; display: block; height: 100%;">
        <div class="hr-module-card">
            <div class="mod-icon">📋</div>
            <div class="mod-title">Audit Log</div>
            <div class="mod-desc">Complete outreach activity trail with send status, failure diagnostics, duplicate prevention evidence, and retry records.</div>
        </div>
    </a>""", unsafe_allow_html=True)
    st.page_link("pages/3_Audit_Log.py", label="Open Audit Log", icon="📋", use_container_width=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Data loader ───────────────────────────────────────────────────────────────
section_header("⚙️", "System Initialisation")

dataset = ensure_data_loaded()

if dataset:
    emp_count = len(dataset.get("Employees", pd.DataFrame()))
    role_count = len(dataset.get("Open_Roles", pd.DataFrame()))
    cand_count = len(dataset.get("LinkedIn_Profile_Pool", pd.DataFrame()))
    exc_count  = len(dataset.get("exceptions", []))

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Employees Loaded",  emp_count)
    col_s2.metric("Open Roles",        role_count)
    col_s3.metric("Candidate Profiles", cand_count)
    col_s4.metric("Data Exceptions",   exc_count,
                  delta=f"{'⚠️ Review' if exc_count else '✅ Clean'}",
                  delta_color="off")

    st.success("✅ System initialized. Select a module from the **sidebar** or use the module cards above.")
else:
    logger.warning("load_data() returned empty dataset.")
    st.error("Unable to load data. Please ensure the Excel file is present.")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 Jhandewalas Foods HR")
    st.caption("AI-Enabled HR Management System")
    st.markdown("---")
    st.markdown("**📌 Quick Navigation**")
    st.page_link("app.py", label="Home Page", icon="🏢", use_container_width=True)
    st.page_link("pages/1_Dashboard.py", label="HR Dashboard", icon="📊", use_container_width=True)
    st.page_link("pages/2_Agentic_Sourcing.py", label="Agentic Sourcing", icon="🤖", use_container_width=True)
    st.page_link("pages/3_Audit_Log.py", label="Audit Log", icon="📋", use_container_width=True)

render_refresh_button(sidebar=True)
