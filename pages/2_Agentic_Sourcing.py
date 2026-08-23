import uuid
import logging
import datetime
import pandas as pd
import streamlit as st

from src.llm_agent import evaluate_candidate, generate_outreach_message
from src.data_loader import save_outreach_log, get_clean_candidates, render_refresh_button
from src.connectors import LinkedInMockConnector
from src.ui_styles import (
    inject_styles, page_hero, section_header, badge,
    score_badge, score_bar_html, step_indicator,
    hard_criteria_card, soft_criteria_card, render_sidebar_toggle
)

logger = logging.getLogger("HRSystem.AgenticSourcing")

st.set_page_config(
    page_title="Agentic Sourcing — Jhandewalas Foods",
    page_icon="🤖",
    layout="wide"
)

inject_styles()
render_sidebar_toggle()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🤖 Agentic Sourcing")
    st.caption("AI-powered candidate matching & outreach")
    st.markdown("---")
    st.markdown("**⚙️ Demo Controls**")
    force_fail = st.checkbox("🔴 Simulate AUTH_401 Failure",
                             help="Forces the connector to return a simulated authentication failure on next send.")
render_refresh_button(sidebar=True)

# ── Guard ─────────────────────────────────────────────────────────────────────
if "data" not in st.session_state:
    st.warning("⚠️ Please navigate to the **Home** page to initialise data.")
    st.stop()

roles_df      = st.session_state.data.get("Open_Roles",           pd.DataFrame())
candidates_df = st.session_state.data.get("LinkedIn_Profile_Pool", pd.DataFrame())

if roles_df.empty or candidates_df.empty:
    st.error("Required datasets (Open Roles or Candidate Pool) are missing.")
    st.stop()

page_hero(
    "🤖",
    "Agentic Recruitment Sourcing & Outreach",
    "AI-powered candidate matching · Human-in-the-loop approval · Idempotent send with full audit trail"
)

# ── Determine current step for the step indicator ────────────────────────────
has_results  = "sourcing_results" in st.session_state and not st.session_state.sourcing_results.empty
has_msg      = any(k.startswith("msg_") for k in st.session_state)

if not has_results:
    current_step = 0
elif not has_msg:
    current_step = 2
else:
    current_step = 3

step_indicator(
    steps=["Select Role", "Review Criteria", "Run Sourcing", "Generate Message", "Approve & Send"],
    current=current_step,
)

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Role Selection
# ═══════════════════════════════════════════════════════════════════════════════
section_header("1️⃣", "Select an Open Role")

open_roles = roles_df[roles_df["Status"] == "Open"].reset_index(drop=True)
if open_roles.empty:
    st.warning("⚠️ No active open roles found in the workbook.")
    st.stop()

role_options = (
    open_roles["Role_ID"].astype(str) + " — " +
    open_roles["Role_Title"].astype(str) + " (" +
    open_roles["Territory_or_Base"].astype(str) + ")"
)

selected_label = st.selectbox(
    "Choose a role to source candidates for:",
    role_options.tolist(),
    key="role_selector"
)
selected_idx  = role_options.tolist().index(selected_label)
selected_role = open_roles.iloc[selected_idx]

# Detect role change and clear stale sourcing results
if st.session_state.get("sourcing_role_label") != selected_label:
    if "sourcing_results" in st.session_state:
        del st.session_state["sourcing_results"]
    for k in [k for k in st.session_state if k.startswith("msg_")]:
        del st.session_state[k]

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Role Requirements
# ═══════════════════════════════════════════════════════════════════════════════
section_header("2️⃣", "Role Requirements Breakdown")

col_hard, col_soft = st.columns(2)
with col_hard:
    hard_criteria_card(
        skills    = selected_role.get("Must_Have_Skills",    ""),
        exp_min   = selected_role.get("Experience_Min_Yrs", "?"),
        exp_max   = selected_role.get("Experience_Max_Yrs", "?"),
        territory = selected_role.get("Territory_or_Base",  "N/A"),
    )
with col_soft:
    soft_criteria_card(
        preferred = selected_role.get("Preferred_Experience", ""),
        outcomes  = selected_role.get("Core_Outcomes",        ""),
    )

st.markdown("<br>", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════════
# STEP 3 — Candidate Sourcing & Ranking
# ═══════════════════════════════════════════════════════════════════════════════
section_header("3️⃣", "Candidate Sourcing & AI Ranking")

if st.button("🔍 Run AI Sourcing for this Role", type="primary", use_container_width=True):
    with st.spinner("Deduplicating profiles → Applying experience filter → Running AI evaluation…"):
        try:
            raw_candidates   = candidates_df.copy()
            unique_candidates = get_clean_candidates(raw_candidates)
            dup_removed      = len(raw_candidates) - len(unique_candidates)

            if dup_removed > 0:
                st.markdown(
                    f"""<div class="hr-dup-box">
                        🔍 <strong>Duplicate Detection</strong>: {dup_removed} duplicate profile(s) identified and
                        removed before evaluation (URL + Name+Title composite key deduplication).
                        {len(unique_candidates)} unique profiles remain for scoring.
                    </div>""",
                    unsafe_allow_html=True,
                )

            role_exp_min = float(selected_role.get("Experience_Min_Yrs", 0) or 0)
            role_exp_max = float(selected_role.get("Experience_Max_Yrs", 99) or 99)

            eligible, ineligible = [], []
            for _, row in unique_candidates.iterrows():
                exp = row.get("Total_Experience_Yrs")
                if pd.isna(exp):
                    eligible.append(row)
                    continue
                exp_val = float(exp)
                if exp_val < (role_exp_min - 1) or exp_val > (role_exp_max + 2):
                    ineligible.append({
                        "Profile_ID": row.get("Profile_ID"),
                        "Name":       row.get("Full_Name"),
                        "Exp (yrs)":  exp_val,
                        "Reason":     f"Experience {exp_val}y outside role range {role_exp_min}–{role_exp_max}y",
                    })
                else:
                    eligible.append(row)

            if ineligible:
                with st.expander(f"🚫 Experience Filter — {len(ineligible)} profile(s) excluded"):
                    st.dataframe(pd.DataFrame(ineligible), use_container_width=True, hide_index=True)

            progress = st.progress(0, text="Evaluating candidates…")
            results  = []
            role_dict = selected_role.to_dict()

            for idx, row in enumerate(eligible):
                cand_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
                eval_res  = evaluate_candidate(role_dict, cand_dict)
                results.append({
                    "Profile_ID":  row.get("Profile_ID"),
                    "Name":        row.get("Full_Name"),
                    "Title":       row.get("Current_Title"),
                    "Experience":  row.get("Total_Experience_Yrs"),
                    "Location":    row.get("Location"),
                    "Open to Work":row.get("Open_To_Work"),
                    "AI Score":    eval_res.get("score", 0),
                    "Reasons":     eval_res.get("reasons", "N/A"),
                    "Gaps":        eval_res.get("gaps",    "N/A"),
                    "Email":       row.get("Email", ""),
                })
                progress.progress(
                    int((idx + 1) / max(len(eligible), 1) * 100),
                    text=f"Evaluated {idx + 1}/{len(eligible)} candidates…"
                )

            progress.empty()
            res_df = pd.DataFrame(results).sort_values("AI Score", ascending=False)
            st.session_state.sourcing_results     = res_df
            st.session_state.sourcing_role_label  = selected_label
            st.success(f"✅ Evaluated **{len(results)}** candidate(s). Results ranked below.")

        except Exception as err:
            logger.exception("Error executing candidate sourcing pipeline")
            st.error(f"Sourcing execution failed: {err}")

# ── Ranked Results ────────────────────────────────────────────────────────────
if "sourcing_results" in st.session_state:
    res_df = st.session_state.sourcing_results

    st.markdown(f"#### Ranked Shortlist — *{st.session_state.get('sourcing_role_label', '')}*")
    st.caption(f"{len(res_df)} candidate(s) evaluated · Sorted by AI Fit Score (highest first)")

    # Score cards
    for rank, (_, row) in enumerate(res_df.iterrows(), start=1):
        score  = int(row.get("AI Score", 0))
        if score >= 70:
            tier_badge = badge("Strong Fit", "green")
            border_col = "#10B981"
        elif score >= 45:
            tier_badge = badge("Moderate Fit", "amber")
            border_col = "#F59E0B"
        else:
            tier_badge = badge("Weak Fit", "red")
            border_col = "#EF4444"

        ow_badge = badge("Open to Work ✓", "green") if str(row.get("Open to Work","")).lower() == "yes" else badge("Not Open", "gray")

        st.markdown(
            f"""<div class="hr-score-card" style="border-color:{border_col}33;">
                {score_badge(score)}
                <div style="flex:1;">
                    <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">
                        <span style="font-weight:700;color:#F1F5F9;font-size:1rem;">#{rank} — {row.get('Name','')}</span>
                        {tier_badge} {ow_badge}
                    </div>
                    <div style="font-size:0.83rem;color:#64748B;margin-bottom:8px;">
                        {row.get('Title','')} &nbsp;·&nbsp; {row.get('Location','')} &nbsp;·&nbsp; {row.get('Experience','')} yrs exp
                    </div>
                    {score_bar_html(score)}
                    <div style="font-size:0.82rem;margin-top:8px;">
                        <span style="color:#10B981;font-weight:600;">✓ Fit: </span>
                        <span style="color:#CBD5E1;">{row.get('Reasons','N/A')}</span>
                    </div>
                    <div style="font-size:0.82rem;margin-top:4px;">
                        <span style="color:#F59E0B;font-weight:600;">△ Gaps: </span>
                        <span style="color:#94A3B8;">{row.get('Gaps','N/A')}</span>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Side-by-side comparison of top 2 ─────────────────────────────────────
    if len(res_df) >= 2:
        section_header("🆚", "Top-2 Candidate Comparison")
        top2 = res_df.head(2)
        cc1, cc2 = st.columns(2)
        for col, (_, row) in zip([cc1, cc2], top2.iterrows()):
            score = int(row.get("AI Score", 0))
            if score >= 70:
                tier_str = badge("Strong Fit", "green")
            elif score >= 45:
                tier_str = badge("Moderate Fit", "amber")
            else:
                tier_str = badge("Weak Fit", "red")

            with col:
                st.markdown(
                    f"""<div class="hr-compare-card">
                        <div class="cand-name">{row.get('Name','')}</div>
                        <div class="cand-title">{row.get('Title','')} · {row.get('Location','')} · {row.get('Experience','')} yrs</div>
                        <div style="margin-bottom:10px;">{tier_str}</div>
                        <div style="font-size:1.6rem;font-weight:800;margin-bottom:4px;color:#F1F5F9;">{score}<span style="font-size:0.9rem;color:#64748B;font-weight:400;"> / 100</span></div>
                        {score_bar_html(score)}
                        <div style="font-size:0.83rem;margin-top:12px;">
                            <div style="color:#10B981;font-weight:600;margin-bottom:4px;">✓ Strengths</div>
                            <div style="color:#CBD5E1;">{row.get('Reasons','N/A')}</div>
                        </div>
                        <div style="font-size:0.83rem;margin-top:8px;">
                            <div style="color:#F59E0B;font-weight:600;margin-bottom:4px;">△ Gaps</div>
                            <div style="color:#94A3B8;">{row.get('Gaps','N/A')}</div>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )

        st.markdown("<br>", unsafe_allow_html=True)

    # ═══════════════════════════════════════════════════════════════════════════
    # STEP 4 — Outreach Message Generation
    # ═══════════════════════════════════════════════════════════════════════════
    section_header("4️⃣", "Outreach Message Generation")

    names         = res_df["Name"].tolist()
    selected_name = st.selectbox("Select candidate to contact:", names, key="outreach_selector")

    if selected_name:
        cand_res   = res_df[res_df["Name"] == selected_name].iloc[0]
        profile_id = cand_res.get("Profile_ID")
        orig_cand  = candidates_df[candidates_df["Profile_ID"] == profile_id]

        if not orig_cand.empty:
            score = int(cand_res.get("AI Score", 0))
            if score >= 70:
                tier_str = badge("Strong Fit", "green")
                sc_cls   = "score-high"
            elif score >= 45:
                tier_str = badge("Moderate Fit", "amber")
                sc_cls   = "score-mid"
            else:
                tier_str = badge("Weak Fit", "red")
                sc_cls   = "score-low"

            st.markdown(
                f"""<div class="hr-card" style="margin-bottom:16px;">
                    <div style="display:flex;align-items:center;gap:14px;margin-bottom:12px;">
                        <div class="hr-score-badge {sc_cls}">{score}</div>
                        <div>
                            <div class="card-title">{selected_name}</div>
                            <div style="font-size:0.83rem;color:#64748B;">{cand_res.get('Title','')} · {cand_res.get('Location','')} · {cand_res.get('Experience','')} yrs exp</div>
                            <div style="margin-top:4px;">{tier_str}</div>
                        </div>
                    </div>
                    <div style="font-size:0.83rem;padding-top:10px;border-top:1px solid rgba(30,144,255,0.12);">
                        <span style="color:#10B981;font-weight:600;">✓ Fit: </span>
                        <span style="color:#CBD5E1;">{cand_res.get('Reasons','N/A')}</span>
                        <br><br>
                        <span style="color:#F59E0B;font-weight:600;">△ Gaps: </span>
                        <span style="color:#94A3B8;">{cand_res.get('Gaps','N/A')}</span>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )

            if st.button("✍️ Generate Personalised Outreach Message", use_container_width=True):
                with st.spinner("Drafting personalised message grounded on verified profile data…"):
                    try:
                        msg = generate_outreach_message(selected_role.to_dict(), orig_cand.iloc[0].to_dict())
                        st.session_state[f"msg_{profile_id}"] = msg
                    except Exception as err:
                        logger.exception("Error generating outreach text")
                        st.error(f"Failed to generate message: {err}")

        msg_key = f"msg_{profile_id}"
        if msg_key in st.session_state:
            st.markdown("<br>", unsafe_allow_html=True)
            st.info("📝 **AI-generated draft below** — review and edit before approving. Only verified profile facts are used; no details are fabricated.")
            edited_msg = st.text_area(
                "Review & Edit Message:",
                value=st.session_state[msg_key],
                height=160,
                key=f"edit_{profile_id}"
            )

            st.markdown("<br>", unsafe_allow_html=True)

            # ═══════════════════════════════════════════════════════════════════
            # STEP 5 — Approval & Send
            # ═══════════════════════════════════════════════════════════════════
            section_header("5️⃣", "Human Approval & Send")

            # Duplicate check summary
            log_df          = st.session_state.get("outreach_log", pd.DataFrame())
            same_role_sent  = pd.DataFrame()
            other_role_sent = pd.DataFrame()

            if not log_df.empty and "Profile_ID" in log_df.columns:
                past_sends = log_df[
                    (log_df["Profile_ID"] == profile_id) &
                    (log_df["Send_Status"] == "Sent")
                ]
                if not past_sends.empty:
                    same_role_sent  = past_sends[past_sends["Role_ID"] == selected_role["Role_ID"]]
                    other_role_sent = past_sends[past_sends["Role_ID"] != selected_role["Role_ID"]]

            if not same_role_sent.empty:
                st.markdown(
                    f"""<div class="hr-exception">
                        <span class="exc-tag">DUPLICATE BLOCKED</span>
                        This candidate was already successfully contacted for <strong>{selected_role['Role_ID']}</strong>.
                        Sending again would create a duplicate — blocked by idempotency guard.
                    </div>""",
                    unsafe_allow_html=True,
                )
            else:
                if not other_role_sent.empty:
                    other_roles = other_role_sent["Role_ID"].unique().tolist()
                    st.warning(
                        f"⚠️ **Cross-role notice**: This candidate was previously contacted for "
                        f"{', '.join(other_roles)}. Proceeding will contact them for a different role."
                    )

                if force_fail:
                    st.markdown(
                        '<div class="hr-dup-box">🔴 <strong>Failure mode active</strong> — next send will simulate AUTH_401 connector error.</div>',
                        unsafe_allow_html=True,
                    )

                if st.button("✅ Approve & Send Message", type="primary", use_container_width=True):
                    try:
                        connector = LinkedInMockConnector(force_fail=force_fail)
                        entry     = connector.send_message(profile_id, selected_role["Role_ID"], edited_msg)

                        if entry["Send_Status"] == "Failed":
                            st.error(
                                f"❌ **Send Failed** — Error Code: `{entry['Error_Code']}`\n\n"
                                f"{entry['Error_Detail']}\n\n"
                                f"Record logged as **Failed** in the Audit Log for retry."
                            )
                            logger.warning(f"Simulated send failure — Outreach_ID: {entry['Outreach_ID']}")
                        else:
                            st.success(
                                f"✅ **Message sent successfully!**\n\n"
                                f"Outreach ID: `{entry['Outreach_ID']}` · Channel: LinkedIn (Mock) · Status: Sent"
                            )
                            logger.info(f"Outreach sent: {entry['Outreach_ID']}")
                        
                        st.balloons() if entry["Send_Status"] == "Sent" else None
                        st.session_state.outreach_log = save_outreach_log(
                            st.session_state.outreach_log, entry
                        )
                    except Exception as err:
                        logger.exception("Error executing send operation")
                        st.error(f"Send operation failed: {err}")
