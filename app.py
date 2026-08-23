import logging
import streamlit as st
import pandas as pd
from src.data_loader import load_data, render_refresh_button
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
    st.markdown("""<div class="hr-module-card">
        <div class="mod-icon">📊</div>
        <div class="mod-title">HR Dashboard</div>
        <div class="mod-desc">Live workforce metrics, attendance analysis, recruitment pipeline, CTC summary, and data quality exception engine.</div>
    </div>""", unsafe_allow_html=True)

with c2:
    st.markdown("""<div class="hr-module-card">
        <div class="mod-icon">🤖</div>
        <div class="mod-title">Agentic Sourcing</div>
        <div class="mod-desc">AI-powered candidate matching, ranked shortlisting, personalised outreach generation, and human-in-the-loop approval flow.</div>
    </div>""", unsafe_allow_html=True)

with c3:
    st.markdown("""<div class="hr-module-card">
        <div class="mod-icon">📋</div>
        <div class="mod-title">Audit Log</div>
        <div class="mod-desc">Complete outreach activity trail with send status, failure diagnostics, duplicate prevention evidence, and retry records.</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Data loader ───────────────────────────────────────────────────────────────
section_header("⚙️", "System Initialisation")

if "data" not in st.session_state:
    with st.spinner("Loading HR datasets from Excel workbook…"):
        try:
            dataset = load_data()
            if dataset:
                st.session_state.data = dataset
                if "Outreach_Log" in dataset and not dataset["Outreach_Log"].empty:
                    st.session_state.outreach_log = dataset["Outreach_Log"].copy()
                else:
                    st.session_state.outreach_log = pd.DataFrame()
                logger.info("Dataset successfully loaded into session state.")

                # Summary callout
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

                st.success("✅ All datasets loaded. Use the **sidebar** to navigate to a module.")
            else:
                logger.warning("load_data() returned empty dataset.")
                st.error("Unable to load data. Please ensure the Excel file is present.")
        except Exception as err:
            logger.exception("Fatal error while initialising application data")
            st.error(f"Error loading system data: {err}")
else:
    # Already loaded — show status
    dataset = st.session_state.data
    emp_count  = len(dataset.get("Employees", pd.DataFrame()))
    role_count = len(dataset.get("Open_Roles", pd.DataFrame()))
    cand_count = len(dataset.get("LinkedIn_Profile_Pool", pd.DataFrame()))
    exc_count  = len(dataset.get("exceptions", []))

    col_s1, col_s2, col_s3, col_s4 = st.columns(4)
    col_s1.metric("Employees",         emp_count)
    col_s2.metric("Open Roles",        role_count)
    col_s3.metric("Candidate Profiles", cand_count)
    col_s4.metric("Data Exceptions",   exc_count,
                  delta=f"{'⚠️ Review' if exc_count else '✅ Clean'}",
                  delta_color="off")

    st.success("✅ System ready. Select a module from the **sidebar**.")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🏢 Jhandewalas Foods HR")
    st.caption("AI-Enabled HR Management System")
    st.markdown("---")
    st.markdown("**📌 Navigation**")
    st.markdown("Use the pages listed above to navigate.")

render_refresh_button(sidebar=True)
