import logging
import streamlit as st
import pandas as pd
from src.data_loader import render_refresh_button
from src.ui_styles import inject_styles, page_hero, section_header, badge, render_sidebar_toggle

logger = logging.getLogger("HRSystem.AuditLog")

st.set_page_config(
    page_title="Audit Log — Jhandewalas Foods",
    page_icon="📋",
    layout="wide"
)

inject_styles()
render_sidebar_toggle()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📋 Audit Log")
    st.caption("Outreach activity trail & failure diagnostics")
render_refresh_button(sidebar=True)

# ── Guard ─────────────────────────────────────────────────────────────────────
if "data" not in st.session_state or "outreach_log" not in st.session_state:
    st.warning("⚠️ No session data found. Navigate to the **Home** page first.")
    st.stop()

page_hero(
    "📋",
    "Outreach Audit Log",
    "Complete outreach activity trail · Send status tracking · Failure diagnostics · Duplicate prevention evidence"
)

outreach_df = st.session_state.outreach_log

if outreach_df.empty:
    st.markdown("""
    <div class="hr-card" style="text-align:center;padding:40px;">
        <div style="font-size:2.5rem;margin-bottom:12px;">📭</div>
        <div style="font-size:1rem;font-weight:600;color:#E2E8F0;margin-bottom:6px;">No Outreach Activity Yet</div>
        <div style="font-size:0.85rem;color:#64748B;">
            Go to <strong>Agentic Sourcing</strong>, run AI sourcing for a role, generate a message,
            and approve a send to see records here.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    try:
        total    = len(outreach_df)
        sent     = len(outreach_df[outreach_df["Send_Status"] == "Sent"])
        failed   = len(outreach_df[outreach_df["Send_Status"] == "Failed"])
        pending  = len(outreach_df[outreach_df["Send_Status"].isin(["Not sent", "Pending"])])
        approved = len(outreach_df[outreach_df.get("Approval_Status", pd.Series()).eq("Approved")] if "Approval_Status" in outreach_df.columns else outreach_df)

        # ── KPI Row ───────────────────────────────────────────────────────────
        section_header("📊", "Activity Summary")

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Messages",  total)
        c2.metric("✅ Sent",          sent,   delta=f"{round(sent/total*100)}%" if total else "0%")
        c3.metric("❌ Failed",         failed, delta=f"{'⚠️ Retry needed' if failed else 'None'}", delta_color="inverse" if failed else "off")
        c4.metric("⏳ Pending",        pending)
        c5.metric("👍 Approved",       approved)

        st.markdown("<br>", unsafe_allow_html=True)

        # ── Filter & Table ────────────────────────────────────────────────────
        section_header("📄", "Message Log")

        col_f1, col_f2 = st.columns([1, 3])
        with col_f1:
            status_filter = st.selectbox(
                "Filter by Status:",
                ["All", "Sent", "Failed", "Not sent", "Pending"],
                key="audit_filter"
            )

        display_df = outreach_df.copy()
        if status_filter != "All":
            display_df = display_df[display_df["Send_Status"] == status_filter]

        if "Created_At" in display_df.columns:
            display_df = display_df.sort_values("Created_At", ascending=False)

        # Add styled status column
        def _status_html(s):
            s = str(s)
            if s == "Sent":
                return badge("Sent ✓", "green")
            elif s == "Failed":
                return badge("Failed ✗", "red")
            elif s in ("Pending", "Not sent"):
                return badge(s, "amber")
            return badge(s, "gray")

        # Render message rows as styled cards
        for _, row in display_df.iterrows():
            s_status = str(row.get("Send_Status", ""))
            if s_status == "Sent":
                b_html  = badge("Sent ✓", "green")
                icon    = "✅"
            elif s_status == "Failed":
                b_html  = badge("Failed ✗", "red")
                icon    = "❌"
            elif s_status in ("Pending", "Not sent"):
                b_html  = badge(s_status, "amber")
                icon    = "⏳"
            else:
                b_html  = badge(s_status, "gray")
                icon    = "📨"

            err_html = ""
            if s_status == "Failed":
                err_html = f"""
                <div style="margin-top:8px;padding:8px 12px;background:rgba(239,68,68,0.08);
                     border:1px solid rgba(239,68,68,0.2);border-radius:6px;font-size:0.8rem;">
                    <span style="color:#F87171;font-weight:600;">Error {row.get('Error_Code','?')}</span>
                    &nbsp;—&nbsp;<span style="color:#94A3B8;">{row.get('Error_Detail','')}</span>
                </div>"""

            msg_preview = str(row.get("Message_Text", ""))[:140] + ("…" if len(str(row.get("Message_Text", ""))) > 140 else "")

            st.markdown(
                f"""<div class="hr-card" style="margin-bottom:10px;">
                    <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;flex-wrap:wrap;">
                        <span style="font-size:1.1rem;">{icon}</span>
                        <span style="font-weight:700;color:#F1F5F9;font-size:0.95rem;">
                            Outreach <code style="background:rgba(30,144,255,0.1);padding:1px 6px;border-radius:4px;font-size:0.82rem;">
                            {row.get('Outreach_ID','—')}</code>
                        </span>
                        {b_html}
                        <span style="color:#64748B;font-size:0.8rem;margin-left:auto;">
                            {row.get('Created_At','')}
                        </span>
                    </div>
                    <div style="font-size:0.83rem;color:#94A3B8;margin-bottom:6px;">
                        Profile: <strong style="color:#CBD5E1;">{row.get('Profile_ID','—')}</strong>
                        &nbsp;·&nbsp; Role: <strong style="color:#CBD5E1;">{row.get('Role_ID','—')}</strong>
                        &nbsp;·&nbsp; Channel: {row.get('Channel','—')}
                    </div>
                    <div style="font-size:0.83rem;color:#64748B;font-style:italic;">
                        "{msg_preview}"
                    </div>
                    {err_html}
                </div>""",
                unsafe_allow_html=True,
            )

        st.caption(f"Showing {len(display_df)} of {total} total records.")

        # ── Raw table toggle ──────────────────────────────────────────────────
        with st.expander("📊 View raw data table"):
            st.dataframe(display_df, use_container_width=True, hide_index=True)

        # ── Failed Sends Deep Dive ────────────────────────────────────────────
        failed_records = outreach_df[outreach_df["Send_Status"] == "Failed"]
        if not failed_records.empty:
            st.markdown("<br>", unsafe_allow_html=True)
            section_header("🔴", "Failed Sends — Diagnostic Detail")
            st.info(
                "These records were logged but not delivered. "
                "In production, a retry queue would automatically re-attempt after token refresh or cooldown."
            )
            for _, row in failed_records.iterrows():
                st.markdown(
                    f"""<div class="hr-exception">
                        <span class="exc-tag">{row.get('Error_Code','ERR')}</span>
                        <strong>Outreach {row.get('Outreach_ID','—')}</strong>
                        &nbsp;(Profile: {row.get('Profile_ID','—')}, Role: {row.get('Role_ID','—')})
                        &nbsp;—&nbsp; {row.get('Error_Detail','')}
                        <br><span style="color:#64748B;font-size:0.78rem;">Logged at: {row.get('Created_At','')}</span>
                    </div>""",
                    unsafe_allow_html=True,
                )

    except Exception as err:
        logger.exception("Error rendering audit log")
        st.error(f"Error loading audit log: {err}")
