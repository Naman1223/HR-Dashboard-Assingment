"""
src/ui_styles.py
Shared CSS injection and HTML helper utilities for the HR System UI.
Import inject_styles() at the top of every Streamlit page.

IMPORTANT: Streamlit strips <style> and <link> tags from st.markdown() even
with unsafe_allow_html=True. The only reliable injection method is to use
st.components.v1.html() with a <script> that appends a <style> node directly
into window.parent.document.head (same-origin, so allowed by the browser).
"""

import base64
import streamlit as st
import streamlit.components.v1 as components


def inject_styles():
    """
    Inject global CSS into the Streamlit app by dynamically appending a
    <style> element to the parent document's <head> via a script inside a
    zero-height iframe component. Uses base64 encoding to avoid any character
    escaping or syntax issues.
    """
    css = _build_css()
    b64_css = base64.b64encode(css.encode("utf-8")).decode("utf-8")
    components.html(
        f"""<script>
            (function() {{
                var existing = window.parent.document.getElementById('hr-system-styles');
                if (existing) {{ existing.remove(); }}
                var style = window.parent.document.createElement('style');
                style.id = 'hr-system-styles';
                style.textContent = atob("{b64_css}");
                window.parent.document.head.appendChild(style);
            }})();
        </script>""",
        height=0,
    )


def _build_css() -> str:
    """Return the full CSS string (no <style> wrapper needed)."""
    return """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base ───────────────────────────────────────────────────────────────── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* Main background */
.stApp {
    background: linear-gradient(135deg, #0D1B2A 0%, #1A2C42 50%, #0D1B2A 100%);
    min-height: 100vh;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0A1628 0%, #112240 100%);
    border-right: 1px solid rgba(30,144,255,0.2);
}
section[data-testid="stSidebar"] * {
    color: #CBD5E1 !important;
}
section[data-testid="stSidebar"] .stButton button {
    background: linear-gradient(135deg, #1E40AF, #1E90FF) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}

/* Hide default Streamlit chrome decoration */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #0D1B2A; }
::-webkit-scrollbar-thumb { background: #1E90FF44; border-radius: 3px; }

/* ── Typography ─────────────────────────────────────────────────────────── */
h1, h2, h3, h4, h5 { color: #F1F5F9 !important; font-weight: 700 !important; }

/* ── Streamlit native widget overrides ──────────────────────────────────── */
.stMetric {
    background: rgba(30, 144, 255, 0.06);
    border: 1px solid rgba(30, 144, 255, 0.18);
    border-radius: 12px;
    padding: 16px 18px !important;
    transition: transform 0.2s, box-shadow 0.2s;
}
.stMetric:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(30, 144, 255, 0.15);
}
.stMetric label { color: #94A3B8 !important; font-size: 0.78rem !important; font-weight: 500 !important; text-transform: uppercase; letter-spacing: 0.06em; }
.stMetric [data-testid="metric-value"] { color: #F1F5F9 !important; font-size: 1.9rem !important; font-weight: 800 !important; }

/* Buttons */
.stButton > button {
    border-radius: 10px !important;
    font-weight: 600 !important;
    transition: all 0.2s !important;
    border: 1px solid rgba(30,144,255,0.3) !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1E40AF, #1E90FF) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 15px rgba(30,144,255,0.3) !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(30,144,255,0.5) !important;
    transform: translateY(-1px) !important;
}
.stButton > button:not([kind="primary"]) {
    background: rgba(30,144,255,0.08) !important;
    color: #7DD3FC !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: rgba(30,144,255,0.18) !important;
}

/* Selectbox / text inputs */
.stSelectbox select, .stTextInput input, .stTextArea textarea {
    background: rgba(15, 30, 55, 0.8) !important;
    color: #E2E8F0 !important;
    border: 1px solid rgba(30,144,255,0.25) !important;
    border-radius: 8px !important;
}
div[data-baseweb="select"] > div {
    background: rgba(15, 30, 55, 0.9) !important;
    border: 1px solid rgba(30,144,255,0.25) !important;
    border-radius: 8px !important;
    color: #E2E8F0 !important;
}

/* Dataframe */
.stDataFrame { border-radius: 10px; overflow: hidden; border: 1px solid rgba(30,144,255,0.15) !important; }

/* Expander */
.streamlit-expanderHeader {
    background: rgba(30,144,255,0.06) !important;
    border: 1px solid rgba(30,144,255,0.15) !important;
    border-radius: 8px !important;
    color: #CBD5E1 !important;
    font-weight: 600 !important;
}

/* Alerts */
.stAlert { border-radius: 10px !important; }
div[data-testid="stNotification"] { border-radius: 10px; }

/* Divider */
hr { border-color: rgba(30,144,255,0.15) !important; margin: 1.5rem 0 !important; }

/* Spinner */
.stSpinner > div { border-top-color: #1E90FF !important; }

/* Checkbox */
.stCheckbox { color: #CBD5E1 !important; }

/* ── Custom component classes ────────────────────────────────────────────── */

/* Page hero banner */
.hr-page-hero {
    background: linear-gradient(135deg, rgba(30,64,175,0.25) 0%, rgba(30,144,255,0.1) 100%);
    border: 1px solid rgba(30,144,255,0.25);
    border-radius: 16px;
    padding: 24px 32px;
    margin-bottom: 24px;
}
.hr-page-hero h1 { margin: 0 0 4px 0 !important; font-size: 1.8rem !important; }
.hr-page-hero p { color: #94A3B8; margin: 0; font-size: 0.95rem; }

/* Section header */
.hr-section-title {
    display: flex;
    align-items: center;
    gap: 10px;
    margin: 8px 0 16px 0;
    padding-bottom: 10px;
    border-bottom: 2px solid rgba(30,144,255,0.2);
}
.hr-section-title span.icon {
    font-size: 1.3rem;
    background: rgba(30,144,255,0.15);
    border-radius: 8px;
    padding: 6px 8px;
}
.hr-section-title span.label {
    font-size: 1.05rem;
    font-weight: 700;
    color: #E2E8F0;
    letter-spacing: 0.01em;
}

/* Info card */
.hr-card {
    background: rgba(15, 30, 55, 0.75);
    border: 1px solid rgba(30,144,255,0.18);
    border-radius: 14px;
    padding: 20px 22px;
    margin-bottom: 14px;
    transition: box-shadow 0.2s;
}
.hr-card:hover { box-shadow: 0 4px 20px rgba(30,144,255,0.12); }
.hr-card .card-title { font-weight: 700; font-size: 1rem; color: #F1F5F9; margin-bottom: 8px; }
.hr-card .card-subtitle { font-size: 0.82rem; color: #64748B; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 0.05em; }

/* Hard criteria box */
.hr-hard-criteria {
    background: rgba(239,68,68,0.08);
    border: 1px solid rgba(239,68,68,0.25);
    border-left: 4px solid #EF4444;
    border-radius: 10px;
    padding: 16px 18px;
    height: 100%;
}
/* Soft criteria box */
.hr-soft-criteria {
    background: rgba(245,158,11,0.08);
    border: 1px solid rgba(245,158,11,0.25);
    border-left: 4px solid #F59E0B;
    border-radius: 10px;
    padding: 16px 18px;
    height: 100%;
}
/* Score card */
.hr-score-card {
    background: rgba(15,30,55,0.85);
    border: 1px solid rgba(30,144,255,0.2);
    border-radius: 12px;
    padding: 16px 18px;
    margin-bottom: 10px;
    display: flex;
    align-items: flex-start;
    gap: 14px;
}
.hr-score-badge {
    min-width: 56px;
    height: 56px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 1.1rem;
    flex-shrink: 0;
}
.score-high  { background: rgba(16,185,129,0.18); border: 2px solid #10B981; color: #10B981; }
.score-mid   { background: rgba(245,158,11,0.18); border: 2px solid #F59E0B; color: #F59E0B; }
.score-low   { background: rgba(239,68,68,0.18);  border: 2px solid #EF4444; color: #EF4444; }

/* Status badge */
.hr-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.badge-green  { background: rgba(16,185,129,0.18); color: #10B981; border: 1px solid rgba(16,185,129,0.35); }
.badge-red    { background: rgba(239,68,68,0.18);  color: #F87171; border: 1px solid rgba(239,68,68,0.35); }
.badge-amber  { background: rgba(245,158,11,0.18); color: #FCD34D; border: 1px solid rgba(245,158,11,0.35); }
.badge-blue   { background: rgba(30,144,255,0.18); color: #60A5FA; border: 1px solid rgba(30,144,255,0.35); }
.badge-gray   { background: rgba(100,116,139,0.18);color: #94A3B8; border: 1px solid rgba(100,116,139,0.35); }

/* Step indicator */
.hr-step-bar {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0;
    margin: 0 0 28px 0;
    padding: 16px 20px;
    background: rgba(15,30,55,0.6);
    border: 1px solid rgba(30,144,255,0.15);
    border-radius: 14px;
    flex-wrap: wrap;
}
.hr-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    min-width: 80px;
    padding: 0 6px;
}
.hr-step-circle {
    width: 34px; height: 34px;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.85rem;
}
.hr-step-circle.done   { background: #10B981; color: white; }
.hr-step-circle.active { background: linear-gradient(135deg,#1E40AF,#1E90FF); color: white; box-shadow: 0 0 12px rgba(30,144,255,0.5); }
.hr-step-circle.todo   { background: rgba(100,116,139,0.25); color: #64748B; border: 2px solid rgba(100,116,139,0.3); }
.hr-step-label { font-size: 0.7rem; color: #64748B; text-align: center; font-weight: 500; }
.hr-step-label.active  { color: #60A5FA; font-weight: 700; }
.hr-step-label.done    { color: #10B981; }
.hr-step-connector {
    width: 28px; height: 2px;
    background: rgba(100,116,139,0.25);
    flex-shrink: 0;
    margin-bottom: 18px;
}
.hr-step-connector.done { background: #10B981; }

/* Exception item */
.hr-exception {
    background: rgba(239,68,68,0.07);
    border: 1px solid rgba(239,68,68,0.2);
    border-left: 4px solid #EF4444;
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 8px;
    font-size: 0.87rem;
    color: #FCA5A5;
}
.hr-exception .exc-tag {
    display: inline-block;
    background: rgba(239,68,68,0.2);
    color: #FCA5A5;
    border-radius: 4px;
    padding: 1px 7px;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 8px;
    text-transform: uppercase;
}

/* Home module card */
.hr-module-card {
    background: rgba(15,30,55,0.8);
    border: 1px solid rgba(30,144,255,0.2);
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    transition: all 0.25s;
    cursor: pointer;
    height: 100%;
}
.hr-module-card:hover {
    border-color: rgba(30,144,255,0.5);
    box-shadow: 0 8px 32px rgba(30,144,255,0.18);
    transform: translateY(-4px);
}
.hr-module-card .mod-icon { font-size: 2.5rem; margin-bottom: 12px; }
.hr-module-card .mod-title { font-size: 1rem; font-weight: 700; color: #E2E8F0; margin-bottom: 6px; }
.hr-module-card .mod-desc  { font-size: 0.82rem; color: #64748B; line-height: 1.5; }

/* Duplicate warning box */
.hr-dup-box {
    background: rgba(30,144,255,0.08);
    border: 1px solid rgba(30,144,255,0.25);
    border-left: 4px solid #1E90FF;
    border-radius: 10px;
    padding: 12px 16px;
    margin: 10px 0;
    font-size: 0.87rem;
    color: #93C5FD;
}

/* Outreach log row */
.hr-log-row {
    display: flex;
    align-items: center;
    gap: 14px;
    padding: 12px 16px;
    background: rgba(15,30,55,0.7);
    border: 1px solid rgba(30,144,255,0.12);
    border-radius: 10px;
    margin-bottom: 8px;
}

/* Performance table */
.hr-perf-table th { color: #94A3B8 !important; font-size: 0.78rem !important; text-transform: uppercase; }
.hr-perf-table td { color: #E2E8F0 !important; font-size: 0.88rem !important; }

/* Comparison card */
.hr-compare-card {
    background: rgba(15,30,55,0.85);
    border: 1px solid rgba(30,144,255,0.2);
    border-radius: 14px;
    padding: 20px;
}
.hr-compare-card .cand-name { font-size: 1.05rem; font-weight: 700; color: #F1F5F9; margin-bottom: 4px; }
.hr-compare-card .cand-title { font-size: 0.82rem; color: #64748B; margin-bottom: 12px; }

/* Progress bar for score */
.hr-score-bar { margin: 8px 0 4px 0; }
.hr-score-bar-track {
    background: rgba(100,116,139,0.2);
    border-radius: 4px;
    height: 8px;
    width: 100%;
    overflow: hidden;
}
.hr-score-bar-fill {
    height: 100%;
    border-radius: 4px;
    transition: width 0.6s ease;
}
"""


# ── HTML HELPER FUNCTIONS ────────────────────────────────────────────────────

def page_hero(icon: str, title: str, subtitle: str):
    """Render a styled hero banner at the top of a page."""
    st.markdown(
        f"""<div class="hr-page-hero">
            <h1>{icon} {title}</h1>
            <p>{subtitle}</p>
        </div>""",
        unsafe_allow_html=True,
    )


def section_header(icon: str, label: str):
    """Render a coloured section divider with icon."""
    st.markdown(
        f"""<div class="hr-section-title">
            <span class="icon">{icon}</span>
            <span class="label">{label}</span>
        </div>""",
        unsafe_allow_html=True,
    )


def badge(text: str, color: str = "blue") -> str:
    """Return inline HTML for a coloured badge. color ∈ green|red|amber|blue|gray"""
    cls = f"badge-{color}"
    return f'<span class="hr-badge {cls}">{text}</span>'


def score_badge(score: int) -> str:
    """Return HTML for a circular score badge coloured by score tier."""
    if score >= 70:
        cls = "score-high"
    elif score >= 45:
        cls = "score-mid"
    else:
        cls = "score-low"
    return f'<div class="hr-score-badge {cls}">{score}</div>'


def score_bar_html(score: int) -> str:
    """Return HTML progress bar for a 0-100 score."""
    if score >= 70:
        color = "#10B981"
    elif score >= 45:
        color = "#F59E0B"
    else:
        color = "#EF4444"
    return f"""<div class="hr-score-bar">
        <div class="hr-score-bar-track">
            <div class="hr-score-bar-fill" style="width:{score}%;background:{color};"></div>
        </div>
    </div>"""


def exception_item(text: str) -> str:
    """Return HTML for a styled exception/data-quality alert row."""
    # Extract category tag (e.g. "EMPLOYEES:", "ATTENDANCE:", etc.)
    parts = text.split(":", 1)
    tag = parts[0].strip() if len(parts) > 1 else "ISSUE"
    body = parts[1].strip() if len(parts) > 1 else text
    return f"""<div class="hr-exception">
        <span class="exc-tag">{tag}</span>{body}
    </div>"""


def step_indicator(steps: list[str], current: int):
    """
    Render a horizontal step indicator.
    steps: list of step labels
    current: 0-based index of active step
    """
    html = '<div class="hr-step-bar">'
    for i, label in enumerate(steps):
        if i < current:
            circle_cls = "done"
            label_cls = "done"
            circle_content = "✓"
        elif i == current:
            circle_cls = "active"
            label_cls = "active"
            circle_content = str(i + 1)
        else:
            circle_cls = "todo"
            label_cls = ""
            circle_content = str(i + 1)

        html += f"""<div class="hr-step">
            <div class="hr-step-circle {circle_cls}">{circle_content}</div>
            <span class="hr-step-label {label_cls}">{label}</span>
        </div>"""

        if i < len(steps) - 1:
            conn_cls = "done" if i < current else ""
            html += f'<div class="hr-step-connector {conn_cls}"></div>'

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def hard_criteria_card(skills: str, exp_min, exp_max, territory: str):
    """Render the hard requirements card for a role."""
    skill_items = "".join(
        f"<li>{s.strip()}</li>"
        for s in str(skills).split(";") if s.strip()
    )
    st.markdown(
        f"""<div class="hr-hard-criteria">
            <div style="font-size:0.72rem;color:#F87171;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;">
                🔴 Hard Criteria
            </div>
            <div style="font-size:0.82rem;color:#94A3B8;margin-bottom:4px;font-weight:600;">Must-Have Skills</div>
            <ul style="color:#E2E8F0;font-size:0.88rem;margin:0 0 12px 0;padding-left:18px;">{skill_items}</ul>
            <div style="font-size:0.82rem;color:#94A3B8;margin-bottom:2px;font-weight:600;">Experience Range</div>
            <div style="color:#F1F5F9;font-size:0.95rem;font-weight:700;">{exp_min} – {exp_max} years</div>
            <div style="font-size:0.82rem;color:#94A3B8;margin:10px 0 2px;font-weight:600;">Territory</div>
            <div style="color:#F1F5F9;font-size:0.92rem;">{territory}</div>
        </div>""",
        unsafe_allow_html=True,
    )


def soft_criteria_card(preferred: str, outcomes: str):
    """Render the soft/AI requirements card for a role."""
    pref_items = "".join(
        f"<li>{p.strip()}</li>"
        for p in str(preferred).split(";") if p.strip()
    )
    outcome_items = "".join(
        f"<li>{o.strip()}</li>"
        for o in str(outcomes).split(";") if o.strip()
    )
    st.markdown(
        f"""<div class="hr-soft-criteria">
            <div style="font-size:0.72rem;color:#FCD34D;font-weight:700;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;">
                🟡 AI / Soft Criteria
            </div>
            <div style="font-size:0.82rem;color:#94A3B8;margin-bottom:4px;font-weight:600;">Preferred Experience</div>
            <ul style="color:#E2E8F0;font-size:0.88rem;margin:0 0 12px 0;padding-left:18px;">{pref_items}</ul>
            <div style="font-size:0.82rem;color:#94A3B8;margin-bottom:4px;font-weight:600;">Core Outcomes</div>
            <ul style="color:#E2E8F0;font-size:0.88rem;margin:0;padding-left:18px;">{outcome_items}</ul>
        </div>""",
        unsafe_allow_html=True,
    )


# ── Sidebar toggle ─────────────────────────────────────────────────────────────

def render_sidebar_toggle():
    """
    Renders a floating button (top-left) that hides/shows the Streamlit sidebar.
    Call this once per page, after inject_styles().
    Uses CSS injected into the parent document to collapse the sidebar panel,
    controlled by a session-state boolean `sidebar_hidden`.
    """
    if "sidebar_hidden" not in st.session_state:
        st.session_state.sidebar_hidden = False

    # Inject the hide/show CSS rule every render (state may have changed)
    _inject_sidebar_visibility(st.session_state.sidebar_hidden)

    # Floating toggle button
    icon = "▶" if st.session_state.sidebar_hidden else "◀"
    label = "Show Sidebar" if st.session_state.sidebar_hidden else "Hide Sidebar"

    st.markdown(
        f"""
        <style>
        .sidebar-fab-wrapper {{
            position: fixed;
            top: 14px;
            left: 14px;
            z-index: 99999;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Streamlit button rendered normally — we rely on Streamlit's own rerun cycle
    col_fab, _ = st.columns([0.08, 0.92])
    with col_fab:
        if st.button(icon, key="__sidebar_toggle_btn__", help=label, use_container_width=True):
            st.session_state.sidebar_hidden = not st.session_state.sidebar_hidden
            st.rerun()


def _inject_sidebar_visibility(hidden: bool):
    """
    Inject or remove CSS that collapses the sidebar.
    Uses the same iframe-script injection method as inject_styles().
    """
    if hidden:
        css = """
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        .stMainBlockContainer, .block-container {
            max-width: 100% !important;
            padding-left: 1rem !important;
        }
        """
    else:
        css = """
        section[data-testid="stSidebar"] {
            display: flex !important;
        }
        """

    b64_css = base64.b64encode(css.encode("utf-8")).decode("utf-8")
    components.html(
        f"""<script>
            (function() {{
                var existing = window.parent.document.getElementById('sidebar-toggle-styles');
                if (existing) {{ existing.remove(); }}
                var style = window.parent.document.createElement('style');
                style.id = 'sidebar-toggle-styles';
                style.textContent = atob("{b64_css}");
                window.parent.document.head.appendChild(style);
            }})();
        </script>""",
        height=0,
    )
