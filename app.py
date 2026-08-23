import logging
import streamlit as st
import pandas as pd
from src.data_loader import load_data

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

st.title("🏢 AI-Enabled HR System")
st.markdown("**Jhandewalas Foods Limited** — Practical Assessment")

st.markdown("""
Welcome to the HR Management Portal. Use the sidebar menu to navigate:

- 📊 **Dashboard**: View workforce metrics, attendance, pipeline, and data issues
- 🤖 **Agentic Sourcing**: AI candidate matching and outreach generation
- 📋 **Audit Log**: Review historic and session outreach logs
""")

st.divider()

if "data" not in st.session_state:
    with st.spinner("Loading HR datasets..."):
        try:
            dataset = load_data()
            if dataset:
                st.session_state.data = dataset
                if "Outreach_Log" in dataset and not dataset["Outreach_Log"].empty:
                    st.session_state.outreach_log = dataset["Outreach_Log"].copy()
                else:
                    st.session_state.outreach_log = pd.DataFrame()
                logger.info("Dataset successfully loaded into session state.")
                st.success("Data loaded successfully. Use the sidebar to navigate.")
            else:
                logger.warning("load_data() returned empty dataset.")
                st.error("Unable to load data. Please ensure the Excel file is present.")
        except Exception as err:
            logger.exception("Fatal error while initializing application data")
            st.error(f"Error loading system data: {err}")
else:
    st.success("System ready. Select a module from the sidebar.")
