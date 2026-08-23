# 🏢 AI-Enabled HR Management & Agentic Recruitment System

An end-to-end AI-powered Human Resources and Talent Acquisition portal built for **Jhandewalas Foods Limited**. This system combines deterministic rule-based workforce analytics with LLM-powered candidate matching and personalized outreach automation.

---

## 📁 Project Structure

```text
jaipur assingment/
├── .env                                  # Environment variables (GROQ_API_KEY) [Ignored by Git]
├── .gitignore                            # Git ignore patterns (.env, __pycache__, .pyc)
├── README.md                             # Project overview and setup instructions
├── requirements.txt                      # Python dependencies
├── app.py                                # Streamlit application entry point & navigation
├── Naman_AI_Engineer_Test_Sample_Data.xlsx # HR master dataset (Employees, Roles, Profiles, Logs)
│
├── pages/                                # Multi-page Streamlit views
│   ├── 1_Dashboard.py                   # Workforce analytics, attendance, CTC & data audit
│   ├── 2_Agentic_Sourcing.py            # AI candidate sourcing, ranking & outreach generator
│   └── 3_Audit_Log.py                   # Historic and session outreach audit tracking
│
└── src/                                  # Core business logic & backend modules
    ├── __init__.py                       # Package initializer
    ├── connectors.py                     # Extensible outreach connector abstraction & mock adapter
    ├── data_loader.py                    # Excel loading, data validation, deduplication & live sync
    └── llm_agent.py                      # Groq LLM integration, candidate evaluation & outreach drafting
```

---

## ✨ Key Features & Capabilities

### 1. 📊 HR & Workforce Analytics Dashboard (`pages/1_Dashboard.py`)
- **Workforce Overview**: Real-time headcount split by Active, On Notice, Resigned, and Open Vacancies.
- **Compensation Analysis**: Total and average Monthly CTC breakdown by department with missing CTC reporting.
- **Attendance Anomalies (30D)**: Absenteeism rates, late arrival tracking (>15% threshold flagged), and zero-attendance employee detection.
- **Recruitment Pipeline Health**: Active pipeline candidates, stage breakdowns, and stalled application tracking (>14 days).
- **Data Quality & Exception Audit**: Automated checks for missing departments, corrupt/future dates, invalid email syntax, and orphaned records.

### 2. 🤖 Agentic Recruitment & Sourcing (`pages/2_Agentic_Sourcing.py`)
- **Role Selection & Requirement Breakdown**: Displays hard criteria (must-have skills, experience range, location) vs. soft/AI criteria (preferred experience, core outcomes).
- **Rule-Based Experience Filtering**: Filters out profiles outside acceptable role experience boundaries before invoking AI evaluation.
- **LLM Candidate Fit Evaluation**: Scores candidates on a 0–100 scale using Groq LLM (`groq/compound-mini`) with concise reasons and identified skill gaps.
- **AI-Powered Outreach Drafting**: Generates context-aware, personalized recruitment messages tailored to each candidate's profile.
- **Cross-Role Duplicate Contact Prevention**: 
  - Blocks duplicate outreach for the *same* role.
  - Warns recruiters if a candidate was previously contacted for a *different* role.
- **Connector Abstraction (`src/connectors.py`)**: Extensible interface decoupling UI actions from delivery channels (LinkedIn, Email, etc.), with mock `AUTH_401` error simulation.

### 3. 📋 Outreach Audit Logging (`pages/3_Audit_Log.py`)
- **Live Activity Tracking**: Real-time tracking of message statuses (`Sent`, `Failed`, `Pending`).
- **Failure Diagnostics**: Detailed drill-down for failed dispatches with error codes and descriptions.

### 4. 🔄 Live Excel Synchronization
- **One-Click Refresh**: Sidebar button on all pages to re-read the Excel file from disk, invalidate cache, and re-evaluate pipelines without restarting Streamlit.

---

## 🛠️ Tech Stack & Prerequisites

- **Frontend / UI**: [Streamlit](https://streamlit.io/)
- **Data Processing**: [Pandas](https://pandas.pydata.org/), [OpenPyXL](https://openpyxl.readthedocs.io/)
- **LLM Engine**: [Groq Cloud API](https://groq.com/) (`groq/compound-mini`)
- **Environment Management**: `python-dotenv`

---

## 🚀 Getting Started

### 1. Clone the Repository
```bash
git clone https://github.com/Naman1223/HR-Dashboard-Assingment.git
cd "jaipur assingment"
```

### 2. Set Up Virtual Environment & Dependencies
```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Create a `.env` file in the root directory:
```ini
GROQ_API_KEY=gsk_your_groq_api_key_here
```
*(Note: If no API key is provided, the system gracefully degrades to mock AI mode).*

### 4. Run the Streamlit Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🏛️ Architecture & Extensibility

- **Connector Abstraction**: Concrete connectors implement the `OutreachConnector` abstract base class in `src/connectors.py`. To plug in real LinkedIn or Email APIs, create a new class implementing `.send_message(profile_id, role_id, message_text)` without touching UI code.
- **Robust Error Handling & Rate Limiting**: Exponential backoff retry loop in `src/llm_agent.py` catches API rate limits (`429` / `resource_exhausted`) and retries seamlessly.
