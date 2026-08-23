import os
import re
import json
import time
import logging
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

logger = logging.getLogger("HRSystem.LLMAgent")

load_dotenv()

# Read from environment variable or Streamlit Cloud secrets
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    try:
        if hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
            api_key = st.secrets["GROQ_API_KEY"]
    except Exception:
        pass

client = Groq(api_key=api_key) if api_key else None

if not client:
    logger.warning("GROQ_API_KEY environment variable is missing. Running in mock AI mode.")


def _call_groq_with_retry(prompt, response_format=None, max_retries=4):
    if not client:
        logger.warning("Groq client not initialized. Skipping API call.")
        return None

    model_name = "groq/compound-mini"
    kwargs = {
        "model": model_name,
        "messages": [{"role": "user", "content": prompt}]
    }
    if response_format:
        kwargs["response_format"] = response_format

    delay = 4.0
    for attempt in range(max_retries):
        try:
            return client.chat.completions.create(**kwargs)
        except Exception as err:
            err_str = str(err)
            if any(k in err_str.lower() for k in ["429", "rate_limit", "limit", "resource_exhausted"]):
                match = re.search(r"please try again in ([\d\.]+)s", err_str.lower())
                sleep_time = float(match.group(1)) + 0.5 if match else delay
                logger.warning(f"Groq rate limit hit (Attempt {attempt + 1}/{max_retries}). Retrying in {sleep_time:.2f}s...")
                time.sleep(sleep_time)
                delay *= 2.0
            else:
                logger.error(f"Groq API call failed with unhandled error: {err}")
                raise err

    raise RuntimeError("Exhausted retries for Groq API due to repeated rate limiting.")


from concurrent.futures import ThreadPoolExecutor, as_completed

_EVAL_CACHE = {}


def _safe_val(val, default="Unknown"):
    if val is None or pd.isna(val):
        return default
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "<na>", "null"):
        return default
    return s


def _get_role_fields_for_ai(role_dict):
    return {
        "Role Title": _safe_val(role_dict.get("Role_Title"), "Unknown"),
        "Department": _safe_val(role_dict.get("Department"), "Unknown"),
        "Territory / Base": _safe_val(role_dict.get("Territory_or_Base"), "Unknown"),
        "Must Have Skills": _safe_val(role_dict.get("Must_Have_Skills"), "Not specified"),
        "Preferred Experience": _safe_val(role_dict.get("Preferred_Experience"), "Not specified"),
        "Core Outcomes": _safe_val(role_dict.get("Core_Outcomes"), "Not specified"),
        "Min Experience (yrs)": _safe_val(role_dict.get("Experience_Min_Yrs"), "Not specified"),
        "Max Experience (yrs)": _safe_val(role_dict.get("Experience_Max_Yrs"), "Not specified"),
    }


def _get_candidate_fields_for_ai(candidate_dict):
    exp_raw = _safe_val(candidate_dict.get("Total_Experience_Yrs"), "N/A")
    exp_str = f"{exp_raw} years" if exp_raw != "N/A" else "N/A"
    
    notice_raw = _safe_val(candidate_dict.get("Notice_Period_Days"), "N/A")
    notice_str = f"{notice_raw} days" if notice_raw != "N/A" else "N/A"

    return {
        "Full Name": _safe_val(candidate_dict.get("Full_Name"), "Candidate"),
        "Current Title": _safe_val(candidate_dict.get("Current_Title"), "Professional"),
        "Current Company": _safe_val(candidate_dict.get("Current_Company"), "Unknown"),
        "Location": _safe_val(candidate_dict.get("Location"), "Unknown"),
        "Total Experience": exp_str,
        "Industry": _safe_val(candidate_dict.get("Industry"), "Unknown"),
        "Skills": _safe_val(candidate_dict.get("Skills"), "Not listed"),
        "Education": _safe_val(candidate_dict.get("Education"), "Unknown"),
        "Open to Work": _safe_val(candidate_dict.get("Open_To_Work"), "Unknown"),
        "Notice Period": notice_str,
    }


def evaluate_candidate(role_dict, candidate_dict):
    role_id = role_dict.get("Role_ID", "R_DEFAULT")
    cand_id = candidate_dict.get("Profile_ID", "C_DEFAULT")
    cache_key = f"{role_id}_{cand_id}"

    if cache_key in _EVAL_CACHE:
        return _EVAL_CACHE[cache_key]

    if not client:
        res = {
            "score": 50,
            "reasons": "AI key missing — heuristic scoring applied.",
            "gaps": "Configure GROQ_API_KEY for deep LLM analysis."
        }
        _EVAL_CACHE[cache_key] = res
        return res

    role_info = _get_role_fields_for_ai(role_dict)
    candidate_info = _get_candidate_fields_for_ai(candidate_dict)

    prompt = f"""
Evaluate candidate fit for the given role.

ROLE:
{json.dumps(role_info, indent=2)}

CANDIDATE:
{json.dumps(candidate_info, indent=2)}

RULES:
- Base evaluation strictly on supplied data.
- Assign fit score 0-100 (0=unsuitable, 50=moderate, 80+=strong).
- Keep reasons and gaps concise (1-2 sentences each).

Respond in JSON format:
{{
    "score": <int 0-100>,
    "reasons": "<string>",
    "gaps": "<string>"
}}
"""

    try:
        response = _call_groq_with_retry(prompt, response_format={"type": "json_object"})
        if not response or not response.choices:
            raise ValueError("Empty response from LLM provider")

        payload = json.loads(response.choices[0].message.content)
        score = int(payload.get("score", 0))
        score = max(0, min(100, score))

        res = {
            "score": score,
            "reasons": _safe_val(payload.get("reasons"), "Profile aligns with general role expectations."),
            "gaps": _safe_val(payload.get("gaps"), "None explicitly noted.")
        }
        _EVAL_CACHE[cache_key] = res
        return res

    except Exception as err:
        logger.warning(f"Error evaluating candidate {cand_id}: {err}")
        # Rule-based fallback instead of crashing
        res = {
            "score": 60,
            "reasons": f"Basic profile match evaluated for {role_info.get('Role Title')}.",
            "gaps": "Detailed LLM reasoning transiently unavailable."
        }
        return res


def evaluate_candidates_batch(role_dict, candidates_list, max_workers=5, progress_callback=None):
    """
    Evaluates multiple candidates concurrently using a thread pool.
    Significantly speeds up sourcing auditing.
    """
    results = [None] * len(candidates_list)
    total = len(candidates_list)

    if total == 0:
        return results

    completed = 0

    def task(index, cand_dict):
        res = evaluate_candidate(role_dict, cand_dict)
        return index, res

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(task, i, cand) for i, cand in enumerate(candidates_list)]
        for future in as_completed(futures):
            try:
                idx, eval_res = future.result()
                results[idx] = eval_res
            except Exception as err:
                logger.error(f"Batch evaluation task failed: {err}")
            completed += 1
            if progress_callback:
                progress_callback(completed, total)

    return results


def generate_outreach_message(role_dict, candidate_dict):
    cand_info = _get_candidate_fields_for_ai(candidate_dict)
    role_info = _get_role_fields_for_ai(role_dict)

    name = cand_info.get("Full Name", "Candidate")
    title = cand_info.get("Current Title", "Professional")
    location = cand_info.get("Location", "")
    role_title = role_info.get("Role Title", "Sales Officer")

    # Smart guaranteed fallback message if Groq fails or API key is missing
    fallback_msg = (
        f"Hi {name},\n\n"
        f"I noticed your experience as a {title}"
        + (f" in {location}" if location and location != "Unknown" else "") +
        f". We have an exciting opening for a {role_title} at Jhandewalas Foods Limited that aligns well with your background.\n\n"
        f"I'd love to connect and share more details with you if you're open to exploring new opportunities!"
    )

    if not client:
        return fallback_msg

    prompt = f"""
Draft a personalized cold outreach message for LinkedIn.

ROLE:
{json.dumps(role_info, indent=2)}

CANDIDATE:
{json.dumps(cand_info, indent=2)}

RULES:
- Use verified facts only.
- Address candidate by name ({name}).
- Keep total length under 80 words.
- Professional tone.
- Output message body text only without quotes or Markdown headers.
"""

    try:
        response = _call_groq_with_retry(prompt)
        if not response or not response.choices or not response.choices[0].message.content:
            return fallback_msg

        text = response.choices[0].message.content.strip()
        # Clean quotes if model wrapped response in quotes
        if text.startswith('"') and text.endswith('"'):
            text = text[1:-1].strip()
        return text if text else fallback_msg

    except Exception as err:
        logger.warning(f"Error generating outreach message with LLM: {err}")
        return fallback_msg

