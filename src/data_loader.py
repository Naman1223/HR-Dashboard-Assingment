import os
import re
import logging
import pandas as pd
import streamlit as st

logger = logging.getLogger("HRSystem.DataLoader")
DATA_FILE = "Naman_AI_Engineer_Test_Sample_Data.xlsx"

@st.cache_data
def load_data():
    if not os.path.exists(DATA_FILE):
        logger.error(f"Excel data file not found at path: {DATA_FILE}")
        st.error(f"Cannot find '{DATA_FILE}'. Please verify the file path.")
        return {}

    try:
        xls = pd.ExcelFile(DATA_FILE)
    except Exception as err:
        logger.exception(f"Failed to open Excel workbook {DATA_FILE}")
        st.error(f"Could not open Excel file: {err}")
        return {}

    data = {}
    exceptions = []
    sheets = ["Open_Roles", "LinkedIn_Profile_Pool", "Outreach_Log", 
              "Employees", "Attendance_30D", "Recruitment_Pipeline", 
              "HR_Movements", "Performance_Snapshot"]

    for sheet in sheets:
        try:
            df = pd.read_excel(xls, sheet_name=sheet).dropna(how="all")
            data[sheet] = df
        except Exception as err:
            logger.warning(f"Sheet '{sheet}' could not be loaded: {err}")
            data[sheet] = pd.DataFrame()
            if sheet != "Performance_Snapshot":
                exceptions.append(f"LOAD ERROR: Sheet '{sheet}' could not be read: {err}")

    try:
        exceptions.extend(_validate_employees(data.get("Employees", pd.DataFrame())))
        exceptions.extend(_validate_candidates(data.get("LinkedIn_Profile_Pool", pd.DataFrame())))
        exceptions.extend(_validate_pipeline(
            data.get("Recruitment_Pipeline", pd.DataFrame()),
            data.get("Open_Roles", pd.DataFrame())
        ))
        exceptions.extend(_validate_attendance(
            data.get("Attendance_30D", pd.DataFrame()),
            data.get("Employees", pd.DataFrame())
        ))
        exceptions.extend(_check_hr_movements(
            data.get("Employees", pd.DataFrame()),
            data.get("HR_Movements", pd.DataFrame())
        ))
    except Exception as err:
        logger.exception("Unexpected error while running dataset validation checks")
        exceptions.append(f"VALIDATION ERROR: Exception occurred during data audit: {err}")

    data["exceptions"] = exceptions
    return data


def _validate_employees(emp_df):
    issues = []
    if emp_df.empty:
        return issues

    try:
        missing_dept = emp_df[emp_df["Department"].isna()]
        if not missing_dept.empty:
            ids = missing_dept["Employee_ID"].astype(str).tolist()
            issues.append(f"EMPLOYEES: {len(ids)} employee(s) missing Department — IDs: {', '.join(ids)}")

        missing_ctc = emp_df[emp_df["Monthly_CTC"].isna()]
        if not missing_ctc.empty:
            ids = missing_ctc["Employee_ID"].astype(str).tolist()
            issues.append(f"EMPLOYEES: {len(ids)} employee(s) missing Monthly CTC — IDs: {', '.join(ids)}")

        if "Date_of_Joining" in emp_df.columns:
            parsed_dates = pd.to_datetime(emp_df["Date_of_Joining"], errors="coerce")
            invalid_mask = emp_df["Date_of_Joining"].notna() & parsed_dates.isna()
            bad_rows = emp_df[invalid_mask]
            for _, row in bad_rows.iterrows():
                issues.append(
                    f"EMPLOYEES: Employee {row.get('Employee_ID')} ({row.get('Employee_Name')}) "
                    f"has unparseable Date_of_Joining: '{row.get('Date_of_Joining')}'"
                )

            future_joiners = emp_df[parsed_dates > pd.Timestamp.now()]
            if not future_joiners.empty:
                ids = future_joiners["Employee_ID"].astype(str).tolist()
                issues.append(f"EMPLOYEES: {len(ids)} employee(s) have future joining dates — IDs: {', '.join(ids)}")

    except Exception as err:
        logger.error(f"Error in _validate_employees: {err}")

    return issues


def _validate_candidates(candidates_df):
    issues = []
    if candidates_df.empty:
        return issues

    try:
        dup_url_mask = candidates_df.duplicated(subset=["Profile_URL"], keep=False)
        dup_url_rows = candidates_df[dup_url_mask]
        if not dup_url_rows.empty:
            for url, group in dup_url_rows.groupby("Profile_URL"):
                ids = group["Profile_ID"].astype(str).tolist()
                names = group["Full_Name"].astype(str).tolist()
                issues.append(
                    f"CANDIDATES: Conflicting duplicate profile URL '{url}' shared by "
                    f"IDs: {', '.join(ids)} ({', '.join(names)})"
                )

        if "Notes" in candidates_df.columns:
            flagged = candidates_df[candidates_df["Notes"].astype(str).str.lower().str.contains("duplicate", na=False)]
            for _, row in flagged.iterrows():
                issues.append(
                    f"CANDIDATES: Profile {row.get('Profile_ID')} ({row.get('Full_Name')}) "
                    f"flagged in source notes: '{row.get('Notes')}'"
                )

        email_pattern = re.compile(r"^[^@]+@[^@]+\.[^@]+$")
        if "Email" in candidates_df.columns:
            for _, row in candidates_df.iterrows():
                email_str = str(row.get("Email", "")).strip()
                if email_str and email_str.lower() != "nan" and not email_pattern.match(email_str):
                    issues.append(
                        f"CANDIDATES: Candidate {row.get('Profile_ID')} ({row.get('Full_Name')}) "
                        f"has invalid email format: '{email_str}'"
                    )

        missing_skills = candidates_df[candidates_df["Skills"].isna() | (candidates_df["Skills"].astype(str).str.strip() == "")]
        if not missing_skills.empty:
            ids = missing_skills["Profile_ID"].astype(str).tolist()
            issues.append(f"CANDIDATES: {len(ids)} profile(s) missing Skills field — IDs: {', '.join(ids)}")

        missing_exp = candidates_df[candidates_df["Total_Experience_Yrs"].isna()]
        if not missing_exp.empty:
            ids = missing_exp["Profile_ID"].astype(str).tolist()
            issues.append(f"CANDIDATES: {len(ids)} profile(s) missing Total_Experience_Yrs — IDs: {', '.join(ids)}")

        if "Phone" in candidates_df.columns:
            missing_phone = candidates_df[candidates_df["Phone"].isna()]
            if not missing_phone.empty:
                ids = missing_phone["Profile_ID"].astype(str).tolist()
                issues.append(f"CANDIDATES: {len(ids)} profile(s) missing Phone number — IDs: {', '.join(ids)}")

    except Exception as err:
        logger.error(f"Error in _validate_candidates: {err}")

    return issues


def _validate_pipeline(pipeline_df, roles_df):
    issues = []
    if pipeline_df.empty:
        return issues

    try:
        if not roles_df.empty:
            valid_roles = set(roles_df["Role_ID"].dropna().astype(str).tolist())
            unknown_mask = ~pipeline_df["Role_ID"].astype(str).isin(valid_roles)
            unknown_rows = pipeline_df[unknown_mask]
            for _, row in unknown_rows.iterrows():
                issues.append(
                    f"PIPELINE: Candidate {row.get('Candidate_ID')} ({row.get('Candidate_Name')}) "
                    f"references non-existent Role_ID '{row.get('Role_ID')}'"
                )

        missing_stage = pipeline_df[pipeline_df["Stage"].isna()]
        for _, row in missing_stage.iterrows():
            issues.append(
                f"PIPELINE: Candidate {row.get('Candidate_ID')} ({row.get('Candidate_Name')}) has unassigned Stage"
            )

    except Exception as err:
        logger.error(f"Error in _validate_pipeline: {err}")

    return issues


def _validate_attendance(att_df, emp_df):
    issues = []
    if att_df.empty:
        return issues

    try:
        dup_att = att_df[att_df.duplicated(subset=["Employee_ID", "Date"], keep=False)]
        if not dup_att.empty:
            issues.append(f"ATTENDANCE: Detected {len(dup_att)} duplicate (Employee_ID, Date) attendance logs")

        if not emp_df.empty:
            valid_emp_ids = set(emp_df["Employee_ID"].dropna().astype(str).tolist())
            unknown_att = att_df[~att_df["Employee_ID"].astype(str).isin(valid_emp_ids)]
            if not unknown_att.empty:
                unknown_ids = unknown_att["Employee_ID"].unique().tolist()
                issues.append(f"ATTENDANCE: Records reference unlisted Employee IDs: {', '.join(map(str, unknown_ids))}")

    except Exception as err:
        logger.error(f"Error in _validate_attendance: {err}")

    return issues


def _check_hr_movements(emp_df, movements_df):
    issues = []
    if emp_df.empty or movements_df.empty:
        return issues

    try:
        notice_emp = emp_df[emp_df["Employment_Status"] == "Notice"]
        if not notice_emp.empty:
            exit_mov = movements_df[movements_df["Movement_Type"] == "Exit"]
            if exit_mov.empty:
                ids = notice_emp["Employee_ID"].astype(str).tolist()
                issues.append(
                    f"DATA MISMATCH: {len(notice_emp)} employee(s) on Notice with Exit Dates ({', '.join(ids)}), "
                    f"but HR_Movements contains 0 Exit records"
                )
    except Exception as err:
        logger.error(f"Error in _check_hr_movements: {err}")

    return issues


def save_outreach_log(log_df, new_row):
    try:
        updated = pd.concat([log_df, pd.DataFrame([new_row])], ignore_index=True)
        return updated
    except Exception as err:
        logger.error(f"Failed to append outreach record: {err}")
        return log_df


def get_clean_candidates(candidates_df):
    if candidates_df.empty:
        return candidates_df

    try:
        df = candidates_df.copy()
        if "Profile_URL" in df.columns:
            df = df.drop_duplicates(subset=["Profile_URL"], keep="first")

        df["_name_key"] = (
            df["Full_Name"].astype(str).str.lower().str.strip()
            + "|"
            + df["Current_Title"].astype(str).str.lower().str.strip()
        )
        df = df.drop_duplicates(subset=["_name_key"], keep="first").drop(columns=["_name_key"])
        return df.reset_index(drop=True)
    except Exception as err:
        logger.error(f"Candidate deduplication failed: {err}")
        return candidates_df


def reload_data(preserve_outreach=True):
    """
    Clears Streamlit data cache and re-reads the Excel file from disk.
    Updates st.session_state with fresh data.
    """
    try:
        load_data.clear()
        fresh_data = load_data()
        if fresh_data:
            st.session_state.data = fresh_data
            
            # Reset stale sourcing evaluations so new candidates/roles get evaluated cleanly
            if "sourcing_results" in st.session_state:
                del st.session_state["sourcing_results"]
            if "sourcing_role_label" in st.session_state:
                del st.session_state["sourcing_role_label"]
                
            # Manage outreach log
            if not preserve_outreach or "outreach_log" not in st.session_state or st.session_state.outreach_log.empty:
                if "Outreach_Log" in fresh_data and not fresh_data["Outreach_Log"].empty:
                    st.session_state.outreach_log = fresh_data["Outreach_Log"].copy()
                else:
                    st.session_state.outreach_log = pd.DataFrame()
            
            logger.info("Data successfully refreshed from Excel file.")
            return fresh_data
    except Exception as err:
        logger.exception(f"Failed to reload data: {err}")
    return None


def render_refresh_button(sidebar=True):
    """
    Renders a convenient 'Refresh Data from Excel' button with feedback and automatic rerun.
    """
    target = st.sidebar if sidebar else st
    with target:
        if sidebar:
            st.markdown("---")
            st.markdown("### 🔄 Data Sync")
        if st.button("🔄 Refresh Data from Excel", use_container_width=True, help="Re-read Excel workbook from disk to pick up any changes, new roles, or edits."):
            with st.spinner("Reloading data from Excel..."):
                res = reload_data()
                if res:
                    st.toast("✅ Data refreshed successfully from Excel!", icon="🔄")
                    st.success("Data reloaded!")
                    st.rerun()
                else:
                    st.error("Failed to reload data from Excel.")

