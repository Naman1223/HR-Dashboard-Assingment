import logging
import streamlit as st
import pandas as pd

logger = logging.getLogger("HRSystem.Dashboard")

st.set_page_config(
    page_title="HR Dashboard — Jhandewalas Foods",
    page_icon="📊",
    layout="wide"
)

st.title("📊 HR Management Dashboard")
st.caption("Live workforce analytics and exception tracking.")

if "data" not in st.session_state:
    st.warning("Data not loaded. Please navigate to the Home page first.")
    st.stop()

data = st.session_state.data
emp_df = data.get("Employees", pd.DataFrame())
att_df = data.get("Attendance_30D", pd.DataFrame())
roles_df = data.get("Open_Roles", pd.DataFrame())
hr_move_df = data.get("HR_Movements", pd.DataFrame())
pipeline_df = data.get("Recruitment_Pipeline", pd.DataFrame())
exceptions = data.get("exceptions", [])

st.subheader("📋 Workforce Overview")

if not emp_df.empty:
    try:
        valid_emp = emp_df[emp_df["Employee_ID"].notna()]

        active_count = len(valid_emp[valid_emp["Employment_Status"] == "Active"])
        notice_count = len(valid_emp[valid_emp["Employment_Status"] == "Notice"])
        resigned_count = len(valid_emp[valid_emp["Employment_Status"] == "Resigned"])
        total_count = len(valid_emp)

        open_vacancies = 0
        if not roles_df.empty and "Vacancies" in roles_df.columns:
            open_vacancies = int(pd.to_numeric(roles_df[roles_df["Status"] == "Open"]["Vacancies"], errors="coerce").sum())

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Total Employees", total_count)
        col2.metric("Active", active_count)
        col3.metric("On Notice", notice_count)
        col4.metric("Resigned/Left", resigned_count)
        col5.metric("Open Vacancies", open_vacancies)
    except Exception as err:
        logger.exception("Error rendering workforce overview metrics")
        st.error("Error computing workforce metrics.")

st.divider()
st.subheader("💰 Workforce Cost (Monthly CTC)")

if not emp_df.empty and "Monthly_CTC" in emp_df.columns:
    try:
        emp_df["Monthly_CTC_Numeric"] = pd.to_numeric(emp_df["Monthly_CTC"], errors="coerce")
        valid_ctc = emp_df[emp_df["Monthly_CTC_Numeric"].notna()]
        missing_ctc = emp_df[emp_df["Monthly_CTC_Numeric"].isna() & emp_df["Employee_ID"].notna()]
        total_ctc = valid_ctc["Monthly_CTC_Numeric"].sum()

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.metric(f"Total Monthly CTC ({len(valid_ctc)} employees)", f"₹ {total_ctc:,.0f}")
        with col_c2:
            if not missing_ctc.empty:
                st.warning(
                    f"⚠️ {len(missing_ctc)} employee(s) excluded (missing CTC) — "
                    f"IDs: {', '.join(missing_ctc['Employee_ID'].astype(str).tolist())}"
                )
    except Exception as err:
        logger.exception("Error computing monthly CTC summary")
        st.error("Error calculating workforce cost.")

st.divider()
st.subheader("👥 Headcount Breakdown")

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
            )
            st.bar_chart(dept_counts.set_index("Department"))

            missing_dept = emp_df["Department"].isna().sum()
            if missing_dept > 0:
                st.caption(f"⚠️ {missing_dept} employee(s) missing department assignment.")
        except Exception as err:
            logger.exception("Error rendering department headcount chart")

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
            )
            st.bar_chart(desig_counts.set_index("Designation"))
        except Exception as err:
            logger.exception("Error rendering designation headcount chart")

st.divider()
st.subheader("📅 Attendance Summary (Last 30 Days)")

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

        col_a1, col_a2 = st.columns(2)
        with col_a1:
            st.dataframe(att_summary, use_container_width=True, hide_index=True)

        with col_a2:
            st.markdown("**Late Attendance Indicators (>15% late-rate)**")
            total_days = att_df.groupby("Employee_ID")["Attendance_ID"].count()
            late_days = att_df[att_df["Status"] == "Late"].groupby("Employee_ID")["Attendance_ID"].count()

            late_df = pd.DataFrame({"Total Days": total_days, "Late Days": late_days}).fillna(0)
            late_df["Late Rate %"] = (late_df["Late Days"] / late_df["Total Days"] * 100).round(1)

            high_late = late_df[late_df["Late Rate %"] > 15].reset_index()
            if not high_late.empty:
                st.dataframe(high_late, use_container_width=True, hide_index=True)
            else:
                st.success("No employees exceed late threshold.")
    except Exception as err:
        logger.exception("Error computing attendance statistics")
        st.error("Error loading attendance summary.")

st.divider()
st.subheader("⏳ Probation Status")

if not emp_df.empty and "Probation_End" in emp_df.columns:
    try:
        emp_df["Probation_End_Parsed"] = pd.to_datetime(emp_df["Probation_End"], errors="coerce")
        on_probation = emp_df[
            (emp_df["Employment_Status"] == "Active") &
            (emp_df["Probation_End_Parsed"] >= pd.Timestamp.now())
        ].sort_values("Probation_End_Parsed")

        st.metric("Employees on Probation", len(on_probation))
        if not on_probation.empty:
            cols = ["Employee_ID", "Employee_Name", "Department", "Designation", "Probation_End"]
            st.dataframe(on_probation[[c for c in cols if c in on_probation.columns]], use_container_width=True, hide_index=True)
    except Exception as err:
        logger.exception("Error parsing probation data")

st.divider()
st.subheader("🔄 HR Movements")

if not hr_move_df.empty and "Movement_Type" in hr_move_df.columns:
    try:
        mv_summary = (
            hr_move_df.groupby("Movement_Type")["Movement_ID"]
            .count()
            .reset_index()
            .rename(columns={"Movement_ID": "Count"})
        )
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.dataframe(mv_summary, use_container_width=True, hide_index=True)
        with col_m2:
            notice_emp = emp_df[emp_df["Employment_Status"] == "Notice"] if not emp_df.empty else pd.DataFrame()
            exit_mov = hr_move_df[hr_move_df["Movement_Type"] == "Exit"]
            if not notice_emp.empty and exit_mov.empty:
                st.warning(
                    f"⚠️ {len(notice_emp)} employee(s) on Notice, but HR_Movements contains 0 Exit records."
                )

        with st.expander("View movement log details"):
            st.dataframe(hr_move_df, use_container_width=True, hide_index=True)
    except Exception as err:
        logger.exception("Error displaying HR movement details")

st.divider()
st.subheader("🚀 Recruitment Pipeline")

if not pipeline_df.empty:
    try:
        valid_roles = set(roles_df["Role_ID"].dropna().astype(str).tolist()) if not roles_df.empty else set()
        clean_mask = pipeline_df["Role_ID"].astype(str).isin(valid_roles) & pipeline_df["Stage"].notna()
        clean_pipe = pipeline_df[clean_mask]

        col_p1, col_p2 = st.columns(2)
        with col_p1:
            st.markdown("**By Stage**")
            if not clean_pipe.empty:
                st.bar_chart(clean_pipe.groupby("Stage")["Candidate_ID"].count())

        with col_p2:
            st.markdown("**By Source**")
            if not clean_pipe.empty:
                st.bar_chart(clean_pipe.groupby("Source")["Candidate_ID"].count())

        clean_pipe = clean_pipe.copy()
        clean_pipe["Last_Action_Parsed"] = pd.to_datetime(clean_pipe["Last_Action_Date"], errors="coerce")
        stalled = clean_pipe[(pd.Timestamp.now() - clean_pipe["Last_Action_Parsed"]).dt.days > 14]
        if not stalled.empty:
            st.markdown("**⚠️ Stalled Candidates (>14 days inactive)**")
            st.dataframe(stalled[["Candidate_ID", "Candidate_Name", "Role_ID", "Stage", "Last_Action_Date", "Owner"]], use_container_width=True, hide_index=True)
    except Exception as err:
        logger.exception("Error generating recruitment pipeline charts")

st.divider()
st.subheader("⚠️ Data Quality & Exceptions")

if exceptions:
    st.error(f"Detected **{len(exceptions)} data quality exceptions**.")
    for i, exc in enumerate(exceptions, start=1):
        with st.expander(f"Exception {i}: {exc[:70]}..."):
            st.write(exc)
else:
    st.success("No data quality exceptions detected.")
