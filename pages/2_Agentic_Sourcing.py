import uuid
import logging
import datetime
import pandas as pd
import streamlit as st

from src.llm_agent import evaluate_candidate, generate_outreach_message
from src.data_loader import save_outreach_log, get_clean_candidates

logger = logging.getLogger("HRSystem.AgenticSourcing")

st.set_page_config(
    page_title="Agentic Sourcing — Jhandewalas Foods",
    page_icon="🤖",
    layout="wide"
)

st.title("🤖 Agentic Recruitment Sourcing & Outreach")

if "data" not in st.session_state:
    st.warning("Please navigate to the Home page to initialize data.")
    st.stop()

roles_df = st.session_state.data.get("Open_Roles", pd.DataFrame())
candidates_df = st.session_state.data.get("LinkedIn_Profile_Pool", pd.DataFrame())

if roles_df.empty or candidates_df.empty:
    st.error("Required datasets (Open Roles or Candidate Pool) are missing.")
    st.stop()

st.subheader("Step 1 — Select an Open Role")

open_roles = roles_df[roles_df["Status"] == "Open"].reset_index(drop=True)
if open_roles.empty:
    st.warning("No active open roles found.")
    st.stop()

role_options = (
    open_roles["Role_ID"].astype(str) + " — " +
    open_roles["Role_Title"].astype(str) + " (" +
    open_roles["Territory_or_Base"].astype(str) + ")"
)

selected_label = st.selectbox("Select Target Role:", role_options.tolist())
selected_idx = role_options.tolist().index(selected_label)
selected_role = open_roles.iloc[selected_idx]

st.divider()
st.subheader("Step 2 — Role Requirements")

col_hard, col_soft = st.columns(2)

with col_hard:
    st.markdown("#### 🔴 Hard Criteria")
    st.markdown("**Must-Have Skills:**")
    for skill in str(selected_role.get("Must_Have_Skills", "")).split(";"):
        s = skill.strip()
        if s:
            st.markdown(f"- {s}")
    st.markdown(f"**Exp Range:** {selected_role.get('Experience_Min_Yrs', '?')} – {selected_role.get('Experience_Max_Yrs', '?')} yrs")
    st.markdown(f"**Territory:** {selected_role.get('Territory_or_Base', 'N/A')}")

with col_soft:
    st.markdown("#### 🟡 Soft / AI Criteria")
    st.markdown("**Preferred Experience:**")
    for pref in str(selected_role.get("Preferred_Experience", "")).split(";"):
        p = pref.strip()
        if p:
            st.markdown(f"- {p}")
    st.markdown("**Core Outcomes:**")
    for outcome in str(selected_role.get("Core_Outcomes", "")).split(";"):
        o = outcome.strip()
        if o:
            st.markdown(f"- {o}")

st.divider()
st.subheader("Step 3 — Candidate Sourcing & Ranking")

with st.sidebar:
    st.markdown("---")
    st.markdown("**Demo Controls**")
    force_fail = st.checkbox("Simulate AUTH_401 Send Failure")

if st.button("🔍 Run AI Sourcing", type="primary"):
    with st.spinner("Processing candidate pool..."):
        try:
            unique_candidates = get_clean_candidates(candidates_df)
            
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
                        "Name": row.get("Full_Name"),
                        "Exp": exp_val,
                        "Reason": f"Experience ({exp_val} yrs) outside role range ({role_exp_min}-{role_exp_max} yrs)"
                    })
                else:
                    eligible.append(row)

            if ineligible:
                with st.expander(f"Excluded {len(ineligible)} profile(s) via experience filter"):
                    st.dataframe(pd.DataFrame(ineligible), use_container_width=True, hide_index=True)

            results = []
            role_dict = selected_role.to_dict()

            for row in eligible:
                cand_dict = row.to_dict() if hasattr(row, "to_dict") else dict(row)
                eval_res = evaluate_candidate(role_dict, cand_dict)
                results.append({
                    "Profile_ID": row.get("Profile_ID"),
                    "Name": row.get("Full_Name"),
                    "Title": row.get("Current_Title"),
                    "Experience": row.get("Total_Experience_Yrs"),
                    "Location": row.get("Location"),
                    "Open to Work": row.get("Open_To_Work"),
                    "AI Score": eval_res.get("score", 0),
                    "Reasons": eval_res.get("reasons", "N/A"),
                    "Gaps": eval_res.get("gaps", "N/A"),
                    "Email": row.get("Email", "")
                })

            res_df = pd.DataFrame(results).sort_values("AI Score", ascending=False)
            st.session_state.sourcing_results = res_df
            st.session_state.sourcing_role_label = selected_label
            st.success(f"Evaluated {len(results)} candidate(s) successfully.")
        except Exception as err:
            logger.exception("Error executing candidate sourcing pipeline")
            st.error(f"Sourcing execution failed: {err}")

if "sourcing_results" in st.session_state:
    res_df = st.session_state.sourcing_results
    st.markdown(f"#### Ranked Candidates for: _{st.session_state.get('sourcing_role_label', '')}_")
    
    cols = ["Name", "Title", "Experience", "Location", "Open to Work", "AI Score", "Reasons", "Gaps"]
    st.dataframe(res_df[[c for c in cols if c in res_df.columns]], use_container_width=True, hide_index=True)

    st.divider()
    st.subheader("Step 4 — Outreach Message Generation")

    names = res_df["Name"].tolist()
    selected_name = st.selectbox("Select Candidate:", names)

    if selected_name:
        cand_res = res_df[res_df["Name"] == selected_name].iloc[0]
        profile_id = cand_res.get("Profile_ID")
        orig_cand = candidates_df[candidates_df["Profile_ID"] == profile_id]

        if not orig_cand.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.metric("Fit Score", f"{cand_res['AI Score']} / 100")
                st.markdown(f"**Reasons:** {cand_res['Reasons']}")
            with c2:
                st.markdown(f"**Gaps:** {cand_res['Gaps']}")

            if st.button("✍️ Generate Message"):
                with st.spinner("Drafting personalized outreach..."):
                    try:
                        msg = generate_outreach_message(selected_role.to_dict(), orig_cand.iloc[0].to_dict())
                        st.session_state[f"msg_{profile_id}"] = msg
                    except Exception as err:
                        logger.exception("Error generating outreach text")
                        st.error(f"Failed to generate message: {err}")

        msg_key = f"msg_{profile_id}"
        if msg_key in st.session_state:
            edited_msg = st.text_area("Review & Edit Message:", value=st.session_state[msg_key], height=150)

            st.divider()
            st.subheader("Step 5 — Approval & Send")

            if st.button("✅ Approve & Send", type="primary"):
                try:
                    log_df = st.session_state.get("outreach_log", pd.DataFrame())
                    already_sent = pd.DataFrame()
                    if not log_df.empty and "Profile_ID" in log_df.columns:
                        already_sent = log_df[
                            (log_df["Profile_ID"] == profile_id) &
                            (log_df["Role_ID"] == selected_role["Role_ID"]) &
                            (log_df["Send_Status"] == "Sent")
                        ]

                    if not already_sent.empty:
                        st.error("Duplicate send blocked: candidate previously contacted for this role.")
                    else:
                        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        outreach_id = str(uuid.uuid4())[:8].upper()

                        if force_fail:
                            entry = {
                                "Outreach_ID": outreach_id,
                                "Profile_ID": profile_id,
                                "Role_ID": selected_role["Role_ID"],
                                "Created_At": ts,
                                "Channel": "LinkedIn",
                                "Message_Type": "Initial Outreach",
                                "Message_Text": edited_msg,
                                "Approval_Status": "Approved",
                                "Send_Status": "Failed",
                                "Sent_At": None,
                                "Response_Status": "N/A",
                                "Error_Code": "AUTH_401",
                                "Error_Detail": "Mock connector token expired"
                            }
                            st.error("Send failed (AUTH_401). Record logged as Failed.")
                            logger.warning(f"Simulated send failure for Outreach_ID: {outreach_id}")
                        else:
                            entry = {
                                "Outreach_ID": outreach_id,
                                "Profile_ID": profile_id,
                                "Role_ID": selected_role["Role_ID"],
                                "Created_At": ts,
                                "Channel": "LinkedIn",
                                "Message_Type": "Initial Outreach",
                                "Message_Text": edited_msg,
                                "Approval_Status": "Approved",
                                "Send_Status": "Sent",
                                "Sent_At": ts,
                                "Response_Status": "Pending",
                                "Error_Code": None,
                                "Error_Detail": None
                            }
                            st.success(f"Message sent successfully (Mock ID: {outreach_id}).")
                            logger.info(f"Outreach message sent: {outreach_id}")

                        st.session_state.outreach_log = save_outreach_log(st.session_state.outreach_log, entry)
                except Exception as err:
                    logger.exception("Error executing send operation")
                    st.error(f"Send operation failed: {err}")
