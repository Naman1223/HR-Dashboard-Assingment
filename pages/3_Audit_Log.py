import logging
import streamlit as st
import pandas as pd

logger = logging.getLogger("HRSystem.AuditLog")

st.set_page_config(
    page_title="Audit Log — Jhandewalas Foods",
    page_icon="📋",
    layout="wide"
)

st.title("📋 Outreach Audit Log")
st.caption("Complete outreach activity log.")

if "data" not in st.session_state or "outreach_log" not in st.session_state:
    st.warning("No audit log session available. Navigate to Home page first.")
    st.stop()

outreach_df = st.session_state.outreach_log

if outreach_df.empty:
    st.info("No outreach activity logged.")
else:
    try:
        total = len(outreach_df)
        sent = len(outreach_df[outreach_df["Send_Status"] == "Sent"])
        failed = len(outreach_df[outreach_df["Send_Status"] == "Failed"])
        pending = len(outreach_df[outreach_df["Send_Status"].isin(["Not sent", "Pending"])])
        approved = len(outreach_df[outreach_df["Approval_Status"] == "Approved"])

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Messages", total)
        c2.metric("Sent", sent)
        c3.metric("Failed", failed)
        c4.metric("Pending", pending)
        c5.metric("Approved", approved)

        st.divider()

        status_filter = st.selectbox(
            "Filter Status:",
            ["All", "Sent", "Failed", "Not sent", "Pending"]
        )

        display_df = outreach_df.copy()
        if status_filter != "All":
            display_df = display_df[display_df["Send_Status"] == status_filter]

        if "Created_At" in display_df.columns:
            display_df = display_df.sort_values("Created_At", ascending=False)

        st.dataframe(display_df, use_container_width=True, hide_index=True)

        failed_records = outreach_df[outreach_df["Send_Status"] == "Failed"]
        if not failed_records.empty:
            st.divider()
            st.subheader("Failed Sends Detail")
            for _, row in failed_records.iterrows():
                with st.expander(f"Outreach {row.get('Outreach_ID')} — Profile {row.get('Profile_ID')} ({row.get('Error_Code')})"):
                    st.write(f"**Error Code:** {row.get('Error_Code')}")
                    st.write(f"**Error Detail:** {row.get('Error_Detail')}")
                    st.write(f"**Timestamp:** {row.get('Created_At')}")
                    st.text(str(row.get("Message_Text", ""))[:250])
    except Exception as err:
        logger.exception("Error rendering audit log table")
        st.error("Error loading audit log entries.")
