# AI-Enabled HR Management System — Jhandewalas Foods Limited

> **Assignment Submission** | Candidate: Naman | Role: AI Engineer

---

## Table of Contents
1. [Overview](#overview)
2. [Live Demo Flow](#live-demo-flow)
3. [Setup & Run Instructions](#setup--run-instructions)
4. [Architecture](#architecture)
5. [Assumptions Made](#assumptions-made)
6. [Known Limitations](#known-limitations)
7. [Test Evidence & Error Cases](#test-evidence--error-cases)
8. [Time Spent](#time-spent)

---

## Overview

A Streamlit-based HR Management System that combines **rule-based analytics** with **LLM-powered agentic sourcing** to help Jhandewalas Foods manage their workforce and automate candidate outreach.

### Modules

| Module | Description |
|---|---|
| **HR Dashboard** | Live workforce KPIs, attendance heatmaps, recruitment pipeline, data-quality exceptions |
| **Agentic Sourcing** | AI-ranked candidate shortlisting, personalised outreach, human-in-the-loop approval |
| **Audit Log** | Complete outreach trail with send status, failure diagnostics, duplicate prevention |

---

## Live Demo Flow

Follow these steps during the live demonstration:

1. **Start the application** — run `streamlit run app.py` and open `http://localhost:8501`
2. **Navigate to Agentic Sourcing** and select **"Sales Officer - Uttar Pradesh"** from the role dropdown
3. **Review role criteria** — the system shows hard (must-have skills, experience, territory) and soft (AI-preferred traits) requirements parsed from the `Open_Roles` sheet
4. **Run AI Sourcing** — click "Run AI Sourcing for this Role"; Groq LLM evaluates each profile against role criteria and returns a ranked shortlist with scores (0–100)
5. **Explain score differences** — open at least two candidate cards and show why their scores differ (experience mismatch, territory fit, skills gap)
6. **Generate personalised message** — click "Generate Message" for the top candidate
7. **Edit & approve** — edit the draft, then click "Approve & Send"
8. **Show the Audit Log** — verify the outreach record appears with `Sent` status
9. **Duplicate prevention** — re-run sourcing; observe the deduplication banner showing how many profiles were removed before scoring
10. **Force a failure** — enable **"Simulate AUTH_401 Failure"** in the sidebar, approve a send, then check the Audit Log for the `Failed` badge and error diagnostics
11. **Change role** — switch to **"Area Sales Manager - Rajasthan"**; stale results clear automatically
12. **Open HR Dashboard** — review KPI cards (headcount, attendance rate, open roles, CTC), absentee alerts, and data-quality exceptions
13. **Architecture walk-through** — explain the component diagram and what would change before production deployment

---

## Setup & Run Instructions

### Prerequisites

- Python 3.10+
- A **Groq API key** (free tier works): https://console.groq.com

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/Naman1223/HR-Dashboard-Assingment.git
cd HR-Dashboard-Assingment

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set your Groq API key
# Windows (PowerShell)
$env:GROQ_API_KEY = "gsk_your_key_here"

# Linux / macOS
export GROQ_API_KEY="gsk_your_key_here"

# 4. Place the data file in the project root
# Ensure "Naman_AI_Engineer_Test_Sample_Data.xlsx" is present

# 5. Run
streamlit run app.py
```

Opens at `http://localhost:8501`.

### requirements.txt

```
streamlit
pandas
openpyxl
groq
```

---

## Architecture

```
+-------------------------------------------------------------+
|                    Streamlit Frontend                       |
|  +----------+  +------------------+  +------------------+  |
|  | app.py   |  | 1_Dashboard.py   |  | 2_Agentic_       |  |
|  | (Landing)|  | (HR Analytics)   |  |   Sourcing.py    |  |
|  +----------+  +------------------+  +------------------+  |
|                                       +------------------+  |
|   src/ui_styles.py  (shared CSS)      | 3_Audit_Log.py   |  |
|   injected via components.html+atob() +------------------+  |
+----------------------+--------------------------------------+
                       | Python function calls
          +------------v-----------+
          |    src/  Business Logic |
          |  +--------------------+ |
          |  | data_loader.py     | |  <- Excel -> DataFrame
          |  | load_data()        | |     validation + exceptions
          |  | validate_*()       | |
          |  +--------------------+ |
          |  +--------------------+ |
          |  | llm_agent.py       | |  <- Groq LLM (llama-3.3-70b)
          |  | evaluate_cand()    | |     structured JSON scoring
          |  | gen_outreach()     | |     personalised message gen
          |  +--------------------+ |
          |  +--------------------+ |
          |  | connectors.py      | |  <- LinkedIn mock connector
          |  | LinkedInMockConn.  | |     simulates send + auth errors
          |  +--------------------+ |
          +------------+-----------+
                       |
          +------------v-----------+
          | Excel Workbook (Data)  |
          | Open_Roles             |
          | LinkedIn_Profile_Pool  |
          | Employees              |
          | Attendance_30D         |
          | Recruitment_Pipeline   |
          | HR_Movements           |
          | Performance_Snapshot   |
          | Outreach_Log           |
          +------------------------+
```

### Key Design Decisions

| Decision | Rationale |
|---|---|
| **Groq + llama-3.3-70b** | Free API, low latency (~1-2s), strong structured JSON output |
| **Streamlit** | Rapid prototyping; no separate frontend/backend needed at demo scale |
| **Excel as data store** | Matches the supplied data format; no DB setup required |
| **CSS via components.html + atob()** | Streamlit strips style tags in modern versions; iframe script injection is the only reliable bypass |
| **Human-in-the-loop approval** | Outreach is never auto-sent; a human must review every message |
| **In-memory deduplication** | URL + Name+Title composite key prevents duplicate profiles being scored or messaged |

---

## Assumptions Made

1. **LinkedIn profile pool is a static snapshot** — in production this would be a live API; here it is the `LinkedIn_Profile_Pool` sheet.
2. **"Send" is mocked** — the `LinkedInMockConnector` simulates an API call; no real messages are sent.
3. **Groq API key is required** — LLM calls require a valid key; the app degrades gracefully if missing.
4. **Score threshold of 30** — candidates scoring below 30/100 are excluded from the shortlist as clearly unqualified.
5. **Open Roles sheet drives criteria** — `Hard_Skills`, `Experience_Min/Max`, `Territory`, `Preferred_Experience`, and `Core_Outcomes` columns are the single source of truth for role requirements.
6. **Attendance data covers last 30 days** — the `Attendance_30D` sheet is assumed to be pre-filtered.
7. **Outreach log is session-persistent** — persists within a Streamlit session but resets on server restart (no database).
8. **One message per candidate per role** — the system warns if a Profile_ID + Role_ID outreach record already exists.

---

## Known Limitations

| Limitation | Impact | Production Fix |
|---|---|---|
| No persistent database | Log resets on restart | SQLite / PostgreSQL backend |
| Groq rate limits | Scoring 20+ candidates may hit free-tier limits | Retry backoff + paid tier |
| LinkedIn connector is mocked | No real outreach sent | LinkedIn API / SMTP with OAuth |
| CSS injection via iframe script | May break in Streamlit Cloud sandboxes | Custom Streamlit component |
| Single-user session | No multi-user isolation | Add authentication layer |
| Excel I/O not transactional | Concurrent writes risk corruption | Database backend |
| LLM scores are non-deterministic | Same candidate may score differently | Cache results per (Profile_ID, Role_ID) |
| No CI/CD pipeline | Manual deploy only | GitHub Actions |

---

## Test Evidence & Error Cases

### Happy Path Verified
- Data loads from all 8 Excel sheets without errors
- Role selection populates hard/soft criteria cards correctly
- AI sourcing returns ranked candidates with scores 0-100
- Message generation produces role-contextual personalised text
- Approve & Send records a `Sent` entry in the Audit Log

### Duplicate Prevention Verified
- Running sourcing twice shows the deduplication banner
- Same Profile_ID + Role_ID combination triggers a duplicate outreach warning

### Auth Failure Simulation Verified
- Enabling "Simulate AUTH_401 Failure" toggle causes the send to log `Failed` with error code `AUTH_401`
- Appears in the Audit Log with the Diagnostic Detail section highlighted in red

### Role Switch State Clearing Verified
- Changing the role dropdown clears stale sourcing results and pending outreach drafts automatically

### Data Quality Exceptions Verified
- Missing department assignments detected and flagged
- Employees with zero attendance records generate an absentee alert
- Pipeline stage mismatches flagged in the exceptions panel

### Missing Data Resilience Verified
- Missing optional Excel sheets handled gracefully with empty DataFrames — no application crash

### Known Warning (Non-Critical)
- Streamlit >= 1.41 shows: `use_container_width will be removed after 2025-12-31`
- **Impact**: Warning only, no functional impact
- **Fix**: Replace with `width='stretch'` — deferred, not in scope for this demo

---

## Time Spent

| Phase | Hours |
|---|---|
| Requirement analysis & planning | ~1 h |
| Data pipeline (data_loader.py, validation) | ~1.5 h |
| LLM agent design & prompt engineering | ~2 h |
| Mock connector & audit logging | ~0.5 h |
| UI overhaul (all 4 pages + ui_styles.py) | ~3 h |
| CSS injection debugging (Streamlit sanitiser) | ~1 h |
| README & documentation | ~0.5 h |
| **Total** | **~9.5 h** |

---

*Built by Naman for Jhandewalas Foods Limited AI Engineer Assessment.*
