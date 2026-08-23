# AI-Enabled HR Management System — Jhandewalas Foods Limited

> **Assignment Submission** | Candidate: Naman | Role: AI Engineer

Hi there! Welcome to my submission. This document walks through the HR Management System I built for Jhandewalas Foods, including how to run it, the architecture behind it, and the thought process that went into its design.

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

At its core, this is a Streamlit-based HR Management System. I designed it to help Jhandewalas Foods easily manage their workforce and automate candidate outreach. To do this, I combined traditional **rule-based analytics** with **LLM-powered agentic sourcing**. 

Here is a quick breakdown of the main modules I built into the app:

| Module | Description |
|---|---|
| **HR Dashboard** | Gives a bird's-eye view of the workforce with live KPIs, attendance heatmaps, the recruitment pipeline, and automatic data-quality exception alerts. |
| **Agentic Sourcing** | The AI brain of the app. It ranks candidate shortlists, drafts personalized outreach messages, and keeps a human in the loop for final approval. |
| **Audit Log** | A complete paper trail of our outreach efforts, tracking send statuses, catching duplicate messages, and providing diagnostics if a send fails. |

---

## Live Demo Flow

If we are walking through a live demo together, here is the step-by-step path we will take to see all the features in action:

1. **Start the application** — We'll run `streamlit run app.py` and open up `http://localhost:8501`.
2. **Navigate to Agentic Sourcing** — First, we'll select **"Sales Officer - Uttar Pradesh"** from the role dropdown.
3. **Review role criteria** — You'll see how the system pulls hard requirements (must-have skills, experience, territory) and soft requirements (AI-preferred traits) directly from the `Open_Roles` sheet.
4. **Run AI Sourcing** — We'll click "Run AI Sourcing for this Role." Behind the scenes, the Groq LLM evaluates each profile against our criteria and hands us back a ranked shortlist with scores from 0–100.
5. **Explain score differences** — We'll open a couple of candidate cards to see exactly *why* their scores differ (e.g., highlighting an experience mismatch, a great territory fit, or a skills gap).
6. **Generate a personalised message** — We'll click "Generate Message" for our top-ranked candidate.
7. **Edit & approve** — I'll show how a recruiter can manually tweak the AI's draft before hitting "Approve & Send."
8. **Show the Audit Log** — We'll jump over to the logs to verify that our outreach record safely registered with a `Sent` status.
9. **Test duplicate prevention** — If we try to re-run the sourcing, a deduplication banner will pop up, showing exactly how many duplicate profiles the system caught and removed before wasting LLM tokens on scoring them.
10. **Force a failure** — Just to show the error handling, I'll toggle **"Simulate AUTH_401 Failure"** in the sidebar, try to send a message, and show how the Audit Log catches it with a `Failed` badge and error diagnostics.
11. **Change the role** — We'll switch over to **"Area Sales Manager - Rajasthan"** to watch the system automatically clear out the old data and prep for a fresh search.
12. **Open the HR Dashboard** — We'll take a tour of the KPI cards (headcount, attendance rate, open roles, CTC), check out absentee alerts, and look at data-quality exceptions.
13. **Architecture walk-through** — Finally, we'll talk through the system components and discuss what I'd change to get this ready for production.

---

## Setup & Run Instructions

Want to run this on your own machine? Here is everything you need to get up and running.

### Prerequisites
- Python 3.10+
- A **Groq API key** (the free tier works perfectly): https://console.groq.com

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

# 5. Run the app
streamlit run app.py
```
*The app will automatically open in your browser at `http://localhost:8501`.*

### requirements.txt
```text
streamlit
pandas
openpyxl
groq
```

---

## Architecture

I wanted to keep the architecture straightforward but highly effective for a prototype. Here is a map of how the different parts of the application talk to each other:

```text
+-------------------------------------------------------------+
|                    Streamlit Frontend                       |
|  +----------+  +------------------+  +------------------+   |
|  | app.py   |  | 1_Dashboard.py   |  | 2_Agentic_       |   |
|  | (Landing)|  | (HR Analytics)   |  |   Sourcing.py    |   |
|  +----------+  +------------------+  +------------------+   |
|                                       +------------------+  |
|   src/ui_styles.py  (shared CSS)      | 3_Audit_Log.py   |  |
|   injected via components.html+atob() +------------------+  |
+----------------------+--------------------------------------+
                       | Python function calls
          +------------v-----------+
          |    src/  Business Logic|
          |  +--------------------+|
          |  | data_loader.py     ||  <- Excel -> DataFrame
          |  | load_data()        ||     validation + exceptions
          |  | validate_*()       ||
          |  +--------------------+|
          |  +--------------------+|
          |  | llm_agent.py       ||  <- Groq LLM (llama-3.3-70b)
          |  | evaluate_cand()    ||     structured JSON scoring
          |  | gen_outreach()     ||     personalised message gen
          |  +--------------------+|
          |  +--------------------+|
          |  | connectors.py      ||  <- LinkedIn mock connector
          |  | LinkedInMockConn.  ||     simulates send + auth errors
          |  +--------------------+|
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
Here is a quick look at why I chose the specific tools and workflows for this build:

| Decision | Rationale |
|---|---|
| **Groq + llama-3.3-70b** | It offers a free API, incredibly low latency (~1-2s), and is highly reliable at outputting structured JSON for scoring. |
| **Streamlit** | Perfect for rapid prototyping. It allowed me to build without needing to spin up a separate frontend and backend for a demo-scale app. |
| **Excel as data store** | It perfectly matches the supplied sample data format, meaning zero database setup is required to test the app. |
| **CSS via components.html + atob()** | Modern versions of Streamlit strip standard style tags. Using iframe script injection is the most reliable workaround to keep the UI looking polished. |
| **Human-in-the-loop approval** | I strongly believe outreach should never be 100% auto-sent. The system requires a human to review every single message. |
| **In-memory deduplication** | Using a composite key (URL + Name + Title) ensures we don't waste API tokens scoring duplicate profiles or accidentally spam candidates. |

---

## Assumptions Made

To build this prototype efficiently, I made a few practical assumptions about the data and the environment:

1. **LinkedIn profile pool is a static snapshot:** For this assignment, it's just the `LinkedIn_Profile_Pool` sheet. In production, we'd hook this up to a live API.
2. **"Send" is mocked:** The `LinkedInMockConnector` simulates an API call, meaning no actual messages are being sent to real people during this demo.
3. **Groq API key is required:** The LLM features won't work without it, though I made sure the app degrades gracefully if the key is missing.
4. **Score threshold of 30:** If a candidate scores below a 30/100, the system excludes them from the shortlist, assuming they are fundamentally unqualified.
5. **Open Roles sheet drives criteria:** The columns in this sheet (`Hard_Skills`, `Experience`, `Territory`, etc.) act as the single source of truth for what the AI looks for.
6. **Attendance data covers the last 30 days:** I assumed the `Attendance_30D` sheet comes pre-filtered.
7. **Outreach log is session-persistent:** Because there's no database, the log persists while the app is running but will reset if you restart the server.
8. **One message per candidate per role:** The system will actively warn you if a Profile_ID + Role_ID outreach record already exists.

---

## Known Limitations

No prototype is perfect! Here are the current limitations of this build, along with how I would fix them before taking this to a production environment:

| Limitation | Impact | Production Fix |
|---|---|---|
| No persistent database | Log resets on server restart | Swap Excel for a SQLite or PostgreSQL backend |
| Groq rate limits | Scoring 20+ candidates at once might hit free-tier API limits | Implement retry backoff logic and move to a paid API tier |
| LinkedIn connector is mocked | No real outreach is sent | Integrate the official LinkedIn API or SMTP with OAuth |
| CSS injection via iframe | Might break if hosted in Streamlit Cloud sandboxes | Build a custom Streamlit component for styling |
| Single-user session | No isolation between multiple users | Add an authentication and session management layer |
| Excel I/O isn't transactional | Concurrent writes could corrupt the file | Move entirely to a proper database backend |
| LLM scores are non-deterministic | The same candidate might score slightly differently on a re-run | Cache results per (Profile_ID, Role_ID) pair |
| No CI/CD pipeline | Deployments are strictly manual | Set up GitHub Actions for automated testing and deployment |

---

## Test Evidence & Error Cases

I thoroughly tested the application to make sure it handles both the happy paths and the edge cases. Here is what I've verified works smoothly:

### Happy Path Verified
- The data loads perfectly from all 8 Excel sheets without throwing errors.
- Selecting a role correctly populates the hard and soft criteria UI cards.
- The AI sourcing successfully returns ranked candidates with scores from 0-100.
- Message generation creates highly relevant, role-contextual personalized text.
- Clicking "Approve & Send" successfully writes a `Sent` entry into the Audit Log.

### Duplicate Prevention Verified
- If you run sourcing twice, the system successfully triggers the deduplication banner.
- Attempting to message the same Profile_ID + Role_ID combination successfully triggers a duplicate outreach warning.

### Auth Failure Simulation Verified
- Toggling "Simulate AUTH_401 Failure" successfully forces a fail state, logging `Failed` with the error code `AUTH_401`.
- The failure clearly appears in the Audit Log, highlighting the Diagnostic Detail section in red for easy troubleshooting.

### Role Switch State Clearing Verified
- Changing the role in the dropdown safely clears out stale sourcing results and any pending outreach drafts.

### Data Quality Exceptions Verified
- The dashboard successfully detects and flags employees missing department assignments.
- Employees with zero attendance records correctly generate an absentee alert.
- Pipeline stage mismatches are accurately caught and flagged in the exceptions panel.

### Missing Data Resilience Verified
- If optional Excel sheets are missing, the system handles it gracefully by generating empty DataFrames rather than crashing.

### Known Warning (Non-Critical)
- *Note:* If you are running Streamlit >= 1.41, your terminal might show: `use_container_width will be removed after 2025-12-31`. 
- **Impact**: This is just a deprecation warning and has no functional impact on the app.
- **Fix**: I'll eventually replace it with `width='stretch'`, but I deferred it as it's out of scope for this current demo.

---

## Time Spent

Curious about the effort involved? Here is a transparent breakdown of how I spent my time on this assessment, totaling roughly **9.5 hours**:

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

*Built with care by Naman for the Jhandewalas Foods Limited AI Engineer Assessment.*
