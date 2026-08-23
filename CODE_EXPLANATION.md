# 📖 Complete Code Explanation Guide
## Jhandewalas Foods Limited — AI & Automation Engineer Assessment

This document provides a line-by-line breakdown and architectural explanation for the entire codebase. It is designed to help you explain every technical decision, error handling pattern, and logic choice to the interview panel.

---

## 1. Project Architecture & File Summary

The application is structured as a multi-page Streamlit portal supported by a modular Python backend:

```
jaipur assingment/
├── app.py                      # Main entry point: initializes session state & navigation
├── requirements.txt            # Python dependencies (streamlit, pandas, groq, python-dotenv, openpyxl)
├── .env                        # Environment variables (GROQ_API_KEY)
├── CODE_EXPLANATION.md         # Full line-by-line explanation guide
├── src/
│   ├── __init__.py             # Package marker file
│   ├── data_loader.py          # Data ingestion, ETL cleaning, and validation rules
│   └── llm_agent.py            # Groq AI client, rate-limit retries, and prompt formatting
└── pages/
    ├── 1_Dashboard.py          # HR Management Dashboard (KPIs, Charts, Exceptions)
    ├── 2_Agentic_Sourcing.py   # AI Candidate Sourcing & Outreach Workflow
    └── 3_Audit_Log.py          # Historic and Session Audit Logs
```

---

## 2. File 1: `app.py` (Main Application Entry Point)

### Code & Line Explanation:

- **Lines 1–6**:
  ```python
  import logging
  import streamlit as st
  import pandas as pd
  from src.data_loader import load_data
  ```
  *Explanation:* Imports `logging` for structured error tracking, `streamlit` for the UI, `pandas` for data structures, and our custom `load_data` helper from `src.data_loader`.

- **Lines 8–12**:
  ```python
  logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  )
  logger = logging.getLogger("HRSystem.App")
  ```
  *Explanation:* Initializes the global Python logging system. Standardizes log timestamps, levels (INFO/WARNING/ERROR), and module tags across the app.

- **Lines 14–18**:
  ```python
  st.set_page_config(
      page_title="HR System — Jhandewalas Foods",
      page_icon="👥",
      layout="wide"
  )
  ```
  *Explanation:* Sets the browser tab title, favicon, and configures Streamlit to use the full screen width (`layout="wide"`). **Must be the first Streamlit call in the entry point.**

- **Lines 20–29**: Render the page headers, title, and bulleted introduction describing the available modules.

- **Lines 33–50**:
  ```python
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
  ```
  *Explanation:* Checks `st.session_state` to ensure data is loaded **only once** when the app starts. Storing the dataset in `session_state` keeps it in memory, avoiding slow Excel re-reads on page clicks. Creates an isolated in-memory copy of `Outreach_Log` so session actions don't mutate the raw Excel source file.

- **Lines 51–57**:
  ```python
          except Exception as err:
              logger.exception("Fatal error while initializing application data")
              st.error(f"Error loading system data: {err}")
  ```
  *Explanation:* Catches unexpected startup errors, logs the full stack trace for debugging via `logger.exception`, and displays a clean error banner to the user.

---

## 3. File 2: `src/data_loader.py` (ETL & Validation Pipeline)

### Code & Line Explanation:

- **`load_data()`**:
  ```python
  @st.cache_data
  def load_data():
  ```
  *Explanation:* `@st.cache_data` caches the returned dictionary in memory so Streamlit reuses it across reruns.

- **Excel Ingestion Loop**:
  ```python
  xls = pd.ExcelFile(DATA_FILE)
  for sheet in sheets:
      df = pd.read_excel(xls, sheet_name=sheet).dropna(how="all")
      data[sheet] = df
  ```
  *Explanation:* Opens the Excel workbook handle. Reads each sheet and applies `.dropna(how="all")` to strip completely blank padding rows present at the bottom of the sheets without removing valid rows with partial data.

- **Validation Audit Calls**:
  ```python
  exceptions.extend(_validate_employees(data.get("Employees", pd.DataFrame())))
  exceptions.extend(_validate_candidates(data.get("LinkedIn_Profile_Pool", pd.DataFrame())))
  ...
  ```
  *Explanation:* Runs dedicated validation functions on each dataset. Instead of dropping broken records silently, validation findings are formatted as plain-English strings and appended to `data["exceptions"]` for display on the Dashboard.

- **`_validate_employees(emp_df)`**:
  - Checks for missing `Department` (`emp_df["Department"].isna()`).
  - Checks for missing `Monthly_CTC` to prevent treating missing salaries as ₹0.
  - Parses `Date_of_Joining` with `pd.to_datetime(..., errors="coerce")`. If the original string was non-empty but parsed as `NaT` (Not-a-Time), it identifies invalid dates like `'2025/13/40'` (E031).
  - Flags joining dates set in the future.

- **`_validate_candidates(candidates_df)`**:
  - `candidates_df.duplicated(subset=["Profile_URL"], keep=False)`: Identifies conflicting profiles sharing identical URLs (e.g. P005 Kabir Jain & P006 Rohan Gupta).
  - Checks `Notes` for source annotations flagging duplicates (e.g. P033 Aarav M.).
  - Uses regex `re.compile(r"^[^@]+@[^@]+\.[^@]+$")` to detect malformed emails (e.g. P009 `invalid-email-format`).
  - Flags missing skills (P013), missing experience (P016), and missing phone numbers (P028).

- **`_validate_pipeline(pipeline_df, roles_df)`**:
  - Cross-references `pipeline_df["Role_ID"]` against valid `roles_df["Role_ID"]` set to catch unknown foreign keys (e.g. C008 referencing `R999`).
  - Flags entries with unassigned `Stage` values (e.g. C013).

- **`_validate_attendance(att_df, emp_df)`**:
  - Checks `att_df.duplicated(subset=["Employee_ID", "Date"], keep=False)` to flag duplicate daily logs for the same employee.
  - Verifies employee IDs exist in the master employee sheet.

- **`_check_hr_movements(emp_df, movements_df)`**:
  - Compares employees on `Notice` in `Employees` against `HR_Movements`. Flags the mismatch where 4 employees have notice/exit dates but `HR_Movements` contains 0 exit records.

- **`get_clean_candidates(candidates_df)`**:
  ```python
  df = df.drop_duplicates(subset=["Profile_URL"], keep="first")
  df["_name_key"] = df["Full_Name"].str.lower().str.strip() + "|" + df["Current_Title"].str.lower().str.strip()
  df = df.drop_duplicates(subset=["_name_key"], keep="first")
  ```
  *Explanation:* Pre-filters candidate pool for sourcing by deduplicating exact URLs and normalized `(Full_Name, Current_Title)` pairs.

---

## 4. File 3: `src/llm_agent.py` (Groq AI Agent & Rate-Limit Engine)

### Code & Line Explanation:

- **Client Initialization**:
  ```python
  load_dotenv()
  api_key = os.getenv("GROQ_API_KEY")
  client = Groq(api_key=api_key) if api_key else None
  ```
  *Explanation:* Loads environment variables from `.env`. Initializes the `Groq` client if `GROQ_API_KEY` is present; otherwise logs a warning and sets `client = None` (allowing mock fallback).

- **Rate-Limit Retry Mechanism (`_call_groq_with_retry`)**:
  ```python
  def _call_groq_with_retry(prompt, response_format=None, max_retries=4):
  ```
  - Calls Groq model `groq/compound-mini`.
  - Catches rate limit errors (HTTP 429 / `RESOURCE_EXHAUSTED` / `rate_limit`).
  - Uses regex `re.search(r"please try again in ([\d\.]+)s", err_str)` to extract the exact wait time requested by the API, adds a 0.5s safety buffer, and sleeps (`time.sleep`).
  - Implements exponential backoff if no time is provided (`delay *= 2.0`).

- **Data Minimization (`_get_role_fields_for_ai` & `_get_candidate_fields_for_ai`)**:
  - Extracts only essential fields needed for evaluation (Title, Skills, Experience, Industry).
  - Uses `safe_val()` helper to convert `None`, `NaN`, or empty strings to explicit `"Unknown"` values. This prevents the LLM from hallucinating values for missing fields.

- **`evaluate_candidate(role_dict, candidate_dict)`**:
  - Formats role and candidate data into a structured prompt.
  - Specifies JSON response format `response_format={"type": "json_object"}`.
  - Parses JSON output and validates `score` is an integer bounded between `0` and `100`.
  - Catches `json.JSONDecodeError` and general exceptions gracefully, logging details via `logger.exception`.

- **`generate_outreach_message(role_dict, candidate_dict)`**:
  - Prompts Groq to write a personalized LinkedIn message under 80 words using verified candidate facts.
  - Returns raw message string.

---

## 5. File 4: `pages/1_Dashboard.py` (HR Analytics & Exceptions)

### Code & Line Explanation:

- **Workforce Overview Metrics**:
  - Filters active, notice, and resigned employee counts from `emp_df`.
  - Calculates total open vacancies from `roles_df`.

- **Workforce Cost (Monthly CTC)**:
  - Converts `Monthly_CTC` to numeric using `pd.to_numeric(..., errors="coerce")`.
  - Calculates total monthly payroll over valid entries.
  - Displays a warning banner disclosing the exact count and IDs of employees with missing CTC rather than treating missing data as ₹0.

- **Headcount Breakdown Charts**:
  - Renders `st.bar_chart` for department and designation counts.
  - Displays a caption if employees (e.g. E008) are missing a department assignment.

- **Attendance Analytics**:
  - Summarizes status distribution (Present, Late, Absent, Leave, Field).
  - Calculates per-employee late rates: `Late Rate % = (Late Days / Total Days) * 100`.
  - Displays a table of employees exceeding the 15% late-rate threshold.

- **Probation & Movements**:
  - Filters active employees with `Probation_End >= Timestamp.now()`.
  - Displays HR movement breakdown and flags the notice vs. exit movement discrepancy.

- **Recruitment Pipeline & Stalled Candidates**:
  - Groups clean pipeline records by `Stage` and `Source`.
  - Calculates inactive days: `(Timestamp.now() - Last_Action_Date).days`.
  - Highlights candidates stalled for `>14 days`.

- **Data Quality Exceptions Panel**:
  - Iterates over `st.session_state.data["exceptions"]` and renders each finding inside an `st.expander`.

---

## 6. File 5: `pages/2_Agentic_Sourcing.py` (Recruitment Workflow)

### Code & Line Explanation:

- **Step 1: Role Selection**:
  - Populates dropdown from `open_roles["Role_ID"] + " — " + open_roles["Role_Title"]`. Changing the role requires no code modifications.

- **Step 2: Hard vs. Soft Criteria**:
  - Renders hard requirements (Must-Have Skills, Min/Max Exp, Territory) alongside soft AI criteria (Preferred Experience, Core Outcomes).

- **Step 3: Deterministic Pre-Filtering & AI Sourcing**:
  - Calls `get_clean_candidates()` to deduplicate candidate profiles.
  - Applies hard experience range check (`candidate_exp < min-1` or `candidate_exp > max+2`). Profiles outside this range are excluded before calling Groq to conserve tokens and API quota.
  - Passes remaining eligible profiles to `evaluate_candidate()` in `src.llm_agent`.
  - Sorts results by `AI Score` descending and displays ranked table.

- **Step 4 & 5: Message Generation & Idempotency Check**:
  - Generates message using `generate_outreach_message()`. Displays text in an editable `st.text_area`.
  - **Idempotency Safeguard**: Checks `st.session_state.outreach_log` for matching `(Profile_ID, Role_ID, Send_Status="Sent")`. Blocks duplicate dispatches for the same role.
  - **Failure Simulation**: If the "Simulate AUTH_401 Send Failure" checkbox is enabled, logs record as `Send_Status="Failed"` with `Error_Code="AUTH_401"` without marking it as sent.

---

## 7. File 6: `pages/3_Audit_Log.py` (Audit Trail)

### Code & Line Explanation:

- **Metrics Row**:
  - Displays total, sent, failed, pending, and approved message counts.

- **Filter & Sorting**:
  - Dropdown filters table by `Send_Status` (All, Sent, Failed, Pending).
  - Sorts log entries by `Created_At` descending.

- **Failed Sends Detail**:
  - Filters records with `Send_Status == "Failed"` and displays detailed expanders showing `Error_Code`, `Error_Detail`, timestamp, and message preview.

---

## 8. Technical Q&A for the Interview Panel

**Q: Why use Groq instead of OpenAI or Gemini?**
> "Groq provides ultra-low latency inference using specialized hardware (LPUs). Using `groq/compound-mini`, candidate evaluation and message drafting complete in milliseconds rather than seconds. We also implemented automatic 429 rate-limit retries with exponential backoff."

**Q: How does the system handle missing or dirty data?**
> "We enforce a principle of visible exception tracking. Invalid dates (like E031 '2025/13/40'), missing CTC salaries (E019), duplicate URLs (P005/P006), and orphan foreign keys (C008 -> R999) are never silently dropped or coerced. They are surfaced explicitly in the Data Quality Exceptions panel and disclosed in chart captions."

**Q: How is duplicate outreach prevented?**
> "We enforce idempotency server-side. Before dispatching any message, the system queries the outreach log for matching `(Profile_ID, Role_ID, Send_Status="Sent")`. Repeat sends for the same candidate and role are blocked immediately."

**Q: How do you prevent AI hallucinations in candidate evaluations?**
> "First, we minimize the prompt payload to essential fields. Second, any blank or NaN field is explicitly converted to the string `'Unknown'` using `safe_val()`. This forces the LLM to recognize missing data as an unknown factor that reduces confidence, rather than inventing candidate attributes."
