import logging
import streamlit as st
import pandas as pd
from src.data_loader import render_refresh_button, ensure_data_loaded
from src.ui_styles import (
    inject_styles, page_hero, section_header,
    badge, exception_item, render_sidebar_toggle
)

logger = logging.getLogger("HRSystem.Dashboard")

st.set_page_config(
    page_title="HR Dashboard — Jhandewalas Foods",
    page_icon="📊",
    layout="wide"
)

inject_styles()
render_sidebar_toggle()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Dashboard")
    st.caption("Workforce analytics & exception engine")
    st.markdown("---")
    st.markdown("**📌 Quick Navigation**")
    st.page_link("app.py", label="Home Page", icon="🏢", use_container_width=True)
    st.page_link("pages/1_Dashboard.py", label="HR Dashboard", icon="📊", use_container_width=True)
    st.page_link("pages/2_Agentic_Sourcing.py", label="Agentic Sourcing", icon="🤖", use_container_width=True)
    st.page_link("pages/3_Audit_Log.py", label="Audit Log", icon="📋", use_container_width=True)

render_refresh_button(sidebar=True)

# ── Data Init ─────────────────────────────────────────────────────────────────
data = ensure_data_loaded()
if not data:
    st.error("Unable to load system data. Please check Excel file.")
    st.stop()
emp_df      = data.get("Employees",            pd.DataFrame())
att_df      = data.get("Attendance_30D",        pd.DataFrame())
roles_df    = data.get("Open_Roles",            pd.DataFrame())
hr_move_df  = data.get("HR_Movements",          pd.DataFrame())
pipeline_df = data.get("Recruitment_Pipeline",  pd.DataFrame())
perf_df     = data.get("Performance_Snapshot",  pd.DataFrame())
exceptions  = data.get("exceptions",            [])

page_hero("📊", "HR Management Dashboard", "Live workforce analytics · Data quality engine · Recruitment pipeline")

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Workforce Overview
# ═══════════════════════════════════════════════════════════════════════════════
section_header("👥", "Workforce Overview")

if not emp_df.empty:
    try:
        valid_emp     = emp_df[emp_df["Employee_ID"].notna()]
        active_count  = len(valid_emp[valid_emp["Employment_Status"] == "Active"])
        notice_count  = len(valid_emp[valid_emp["Employment_Status"] == "Notice"])
        resigned_count= len(valid_emp[valid_emp["Employment_Status"] == "Resigned"])
        total_count   = len(valid_emp)
        open_vacancies= 0
        if not roles_df.empty and "Vacancies" in roles_df.columns:
            open_vacancies = int(pd.to_numeric(
                roles_df[roles_df["Status"] == "Open"]["Vacancies"], errors="coerce"
            ).sum())

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Total Headcount",   total_count)
        c2.metric("Active",            active_count,   delta=f"{round(active_count/total_count*100)}%")
        c3.metric("On Notice",         notice_count,   delta=f"{notice_count} flagged" if notice_count else "None", delta_color="inverse")
        c4.metric("Resigned / Left",   resigned_count)
        c5.metric("Open Vacancies",    open_vacancies, delta="Hiring open" if open_vacancies else "Fully staffed", delta_color="off")
    except Exception as err:
        logger.exception("Error rendering workforce overview")
        st.error("Error computing workforce metrics.")
else:
    st.info("No employee data available.")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Workforce Cost
# ═══════════════════════════════════════════════════════════════════════════════
section_header("💰", "Workforce Cost (Monthly CTC)")

if not emp_df.empty and "Monthly_CTC" in emp_df.columns:
    try:
        emp_df = emp_df.copy()
        emp_df["Monthly_CTC_Numeric"] = pd.to_numeric(emp_df["Monthly_CTC"], errors="coerce")
        valid_ctc   = emp_df[emp_df["Monthly_CTC_Numeric"].notna()]
        missing_ctc = emp_df[emp_df["Monthly_CTC_Numeric"].isna() & emp_df["Employee_ID"].notna()]
        total_ctc   = valid_ctc["Monthly_CTC_Numeric"].sum()
        avg_ctc     = valid_ctc["Monthly_CTC_Numeric"].mean() if len(valid_ctc) else 0

        c1, c2, c3 = st.columns(3)
        c1.metric(f"Total Monthly CTC", f"₹ {total_ctc:,.0f}", delta=f"{len(valid_ctc)} employees included")
        c2.metric("Average CTC / Employee", f"₹ {avg_ctc:,.0f}")
        c3.metric("Missing CTC Records", len(missing_ctc),
                  delta="⚠️ Excluded from total" if not missing_ctc.empty else "✅ All present",
                  delta_color="inverse" if not missing_ctc.empty else "off")

        if not missing_ctc.empty:
            with st.expander(f"⚠️ {len(missing_ctc)} employee(s) excluded — missing CTC data"):
                cols_show = ["Employee_ID", "Employee_Name", "Department", "Designation"]
                st.dataframe(missing_ctc[[c for c in cols_show if c in missing_ctc.columns]],
                             use_container_width=True, hide_index=True)
    except Exception as err:
        logger.exception("Error computing monthly CTC")
        st.error("Error calculating workforce cost.")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Headcount Breakdown
# ═══════════════════════════════════════════════════════════════════════════════
section_header("📊", "Headcount Breakdown")

col_ch1, col_ch2 = st.columns(2)

with col_ch1:
    st.markdown("**By Department**")
    if not emp_df.empty and "Department" in emp_df.columns:
        try:
            dept_counts = (
                emp_df[emp_df["Department"].notna()]
                .groupby("Department")["Employee_ID"]
                .count()
                .reset_index()
                .rename(columns={"Employee_ID": "Count"})
                .sort_values("Count", ascending=False)
            )
            st.bar_chart(dept_counts.set_index("Department"), color="#1E90FF")
            missing_dept = emp_df["Department"].isna().sum()
            if missing_dept > 0:
                st.markdown(
                    badge(f"⚠️ {missing_dept} employees missing department", "amber"),
                    unsafe_allow_html=True
                )
        except Exception as err:
            logger.exception("Error rendering department chart")

with col_ch2:
    st.markdown("**By Designation**")
    if not emp_df.empty and "Designation" in emp_df.columns:
        try:
            desig_counts = (
                emp_df[emp_df["Designation"].notna()]
                .groupby("Designation")["Employee_ID"]
                .count()
                .reset_index()
                .rename(columns={"Employee_ID": "Count"})
                .sort_values("Count", ascending=False)
            )
            st.bar_chart(desig_counts.set_index("Designation"), color="#10B981")
        except Exception as err:
            logger.exception("Error rendering designation chart")

st.markdown("<br>", unsafe_allow_html=True)

# ── Drill-down: Employee list with filters ────────────────────────────────────
with st.expander("🔍 Drill Down — Employee Records"):
    if not emp_df.empty:
        dept_opts = ["All"] + sorted(emp_df["Department"].dropna().unique().tolist())
        stat_opts = ["All"] + sorted(emp_df["Employment_Status"].dropna().unique().tolist())

        fd1, fd2 = st.columns(2)
        sel_dept = fd1.selectbox("Filter by Department:", dept_opts, key="dd_dept")
        sel_stat = fd2.selectbox("Filter by Status:",     stat_opts, key="dd_stat")

        filtered = emp_df.copy()
        if sel_dept != "All":
            filtered = filtered[filtered["Department"] == sel_dept]
        if sel_stat != "All":
            filtered = filtered[filtered["Employment_Status"] == sel_stat]

        show_cols = ["Employee_ID", "Employee_Name", "Department", "Designation",
                     "Employment_Status", "Date_of_Joining", "Monthly_CTC"]
        st.dataframe(filtered[[c for c in show_cols if c in filtered.columns]],
                     use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(filtered)} of {len(emp_df)} records")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Attendance (30 Days)
# ═══════════════════════════════════════════════════════════════════════════════
section_header("📅", "Attendance Summary — Last 30 Days")

if not att_df.empty and "Status" in att_df.columns:
    try:
        att_summary = (
            att_df.groupby("Status")["Attendance_ID"]
            .count()
            .reset_index()
            .rename(columns={"Attendance_ID": "Count"})
        )
        total_att = att_summary["Count"].sum()
        att_summary["Percentage"] = (att_summary["Count"] / total_att * 100).round(1)
        att_summary["Percentage"] = att_summary["Percentage"].apply(lambda x: f"{x}%")

        col_a1, col_a2 = st.columns([1, 1])
        with col_a1:
            st.markdown("**Attendance Status Distribution**")
            st.dataframe(att_summary, use_container_width=True, hide_index=True)

        with col_a2:
            # Late rate indicator
            st.markdown("**⚠️ High Late-Rate Employees (>15%)**")
            total_days = att_df.groupby("Employee_ID")["Attendance_ID"].count()
            late_days  = att_df[att_df["Status"] == "Late"].groupby("Employee_ID")["Attendance_ID"].count()
            late_df    = pd.DataFrame({"Total Days": total_days, "Late Days": late_days}).fillna(0)
            late_df["Late Rate %"] = (late_df["Late Days"] / late_df["Total Days"] * 100).round(1)
            high_late = late_df[late_df["Late Rate %"] > 15].reset_index()
            if not high_late.empty:
                st.dataframe(high_late, use_container_width=True, hide_index=True)
            else:
                st.success("✅ No employees exceed the late-rate threshold.")

        # Absenteeism: zero-present employees
        present_emp = set(att_df[att_df["Status"] == "Present"]["Employee_ID"].unique())
        if not emp_df.empty:
            all_emp = set(emp_df[emp_df["Employment_Status"] == "Active"]["Employee_ID"].dropna().unique())
            zero_present = all_emp - present_emp
            if zero_present:
                st.warning(
                    f"🚨 **Absenteeism Alert**: {len(zero_present)} active employee(s) have **zero Present days** "
                    f"in the last 30 days — IDs: {', '.join(str(e) for e in sorted(zero_present))}"
                )
    except Exception as err:
        logger.exception("Error computing attendance statistics")
        st.error("Error loading attendance summary.")
else:
    st.info("No attendance data available.")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Probation
# ═══════════════════════════════════════════════════════════════════════════════
section_header("⏳", "Probation Tracking")

if not emp_df.empty and "Probation_End" in emp_df.columns:
    try:
        emp_df["Probation_End_Parsed"] = pd.to_datetime(emp_df["Probation_End"], errors="coerce")
        now = pd.Timestamp.now()
        on_probation = emp_df[
            (emp_df["Employment_Status"] == "Active") &
            (emp_df["Probation_End_Parsed"] >= now)
        ].sort_values("Probation_End_Parsed").copy()

        ending_soon = on_probation[on_probation["Probation_End_Parsed"] <= now + pd.Timedelta(days=30)]

        c1, c2 = st.columns(2)
        c1.metric("Currently on Probation", len(on_probation))
        c2.metric("Ending within 30 Days",  len(ending_soon),
                  delta="Action required" if len(ending_soon) > 0 else "None upcoming",
                  delta_color="inverse" if len(ending_soon) > 0 else "off")

        if not on_probation.empty:
            cols = ["Employee_ID", "Employee_Name", "Department", "Designation", "Probation_End"]
            st.dataframe(
                on_probation[[c for c in cols if c in on_probation.columns]],
                use_container_width=True, hide_index=True
            )
    except Exception as err:
        logger.exception("Error parsing probation data")
else:
    st.info("Probation_End column not found in employee data.")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 6 — HR Movements
# ═══════════════════════════════════════════════════════════════════════════════
section_header("🔄", "HR Movements — Joiners & Exits")

if not hr_move_df.empty and "Movement_Type" in hr_move_df.columns:
    try:
        mv_summary = (
            hr_move_df.groupby("Movement_Type")["Movement_ID"]
            .count()
            .reset_index()
            .rename(columns={"Movement_ID": "Count"})
        )
        col_m1, col_m2 = st.columns([1, 1])
        with col_m1:
            st.dataframe(mv_summary, use_container_width=True, hide_index=True)
        with col_m2:
            notice_emp = emp_df[emp_df["Employment_Status"] == "Notice"] if not emp_df.empty else pd.DataFrame()
            exit_mov   = hr_move_df[hr_move_df["Movement_Type"] == "Exit"]
            if not notice_emp.empty and exit_mov.empty:
                st.warning(
                    f"⚠️ **Data Mismatch**: {len(notice_emp)} employee(s) on Notice, "
                    f"but HR_Movements has 0 Exit records."
                )
            elif not exit_mov.empty:
                st.success(f"✅ {len(exit_mov)} Exit record(s) logged in HR Movements.")

        with st.expander("📄 View full movement log"):
            st.dataframe(hr_move_df, use_container_width=True, hide_index=True)
    except Exception as err:
        logger.exception("Error displaying HR movements")
else:
    st.info("No HR movement data available.")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Recruitment Pipeline
# ═══════════════════════════════════════════════════════════════════════════════
section_header("🚀", "Recruitment Pipeline")

if not pipeline_df.empty:
    try:
        valid_roles  = set(roles_df["Role_ID"].dropna().astype(str).tolist()) if not roles_df.empty else set()
        clean_mask   = pipeline_df["Role_ID"].astype(str).isin(valid_roles) & pipeline_df["Stage"].notna()
        clean_pipe   = pipeline_df[clean_mask].copy()
        orphan_count = len(pipeline_df[~clean_mask])

        cp1, cp2, cp3 = st.columns(3)
        cp1.metric("Total in Pipeline",       len(pipeline_df))
        cp2.metric("With Valid Role",          len(clean_pipe))
        cp3.metric("Orphan / Invalid Records", orphan_count,
                   delta="⚠️ Data issue" if orphan_count else "✅ Clean",
                   delta_color="inverse" if orphan_count else "off")

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("**Pipeline by Stage**")
            if not clean_pipe.empty:
                st.bar_chart(clean_pipe.groupby("Stage")["Candidate_ID"].count(), color="#1E90FF")
        with col_p2:
            st.markdown("**Pipeline by Source**")
            if not clean_pipe.empty and "Source" in clean_pipe.columns:
                st.bar_chart(clean_pipe.groupby("Source")["Candidate_ID"].count(), color="#10B981")

        # Stalled candidates
        if "Last_Action_Date" in clean_pipe.columns:
            clean_pipe["Last_Action_Parsed"] = pd.to_datetime(clean_pipe["Last_Action_Date"], errors="coerce")
            stalled = clean_pipe[
                (pd.Timestamp.now() - clean_pipe["Last_Action_Parsed"]).dt.days > 14
            ]
            if not stalled.empty:
                st.warning(f"⚠️ **{len(stalled)} stalled candidate(s)** — no activity in >14 days")
                stall_cols = ["Candidate_ID", "Candidate_Name", "Role_ID", "Stage", "Last_Action_Date", "Owner"]
                st.dataframe(stalled[[c for c in stall_cols if c in stalled.columns]],
                             use_container_width=True, hide_index=True)
    except Exception as err:
        logger.exception("Error generating recruitment pipeline charts")
        st.error("Error loading recruitment pipeline.")
else:
    st.info("No pipeline data available.")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Sales Performance Snapshot
# ═══════════════════════════════════════════════════════════════════════════════
section_header("📈", "Sales Performance Snapshot")

if not perf_df.empty:
    try:
        st.caption(f"Loaded {len(perf_df)} records from Performance_Snapshot sheet.")
        st.dataframe(perf_df, use_container_width=True, hide_index=True)
    except Exception as err:
        logger.exception("Error displaying performance snapshot")
        st.error("Error loading performance data.")
else:
    st.info("Performance_Snapshot data not available or sheet is empty.")

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# SECTION 9 — Data Quality & Exceptions
# ═══════════════════════════════════════════════════════════════════════════════
section_header("⚠️", "Data Quality & Exception Engine")

if exceptions:
    st.error(f"**{len(exceptions)} data quality exception(s) detected** — review and resolve before reporting.")

    # Group by category
    groups: dict[str, list[str]] = {}
    for exc in exceptions:
        parts = exc.split(":", 1)
        cat = parts[0].strip() if len(parts) > 1 else "OTHER"
        groups.setdefault(cat, []).append(exc)

    for cat, items in groups.items():
        with st.expander(f"{cat} — {len(items)} issue(s)", expanded=False):
            for item in items:
                st.markdown(exception_item(item), unsafe_allow_html=True)
else:
    st.success("✅ **No data quality exceptions detected.** All datasets passed validation checks.")
