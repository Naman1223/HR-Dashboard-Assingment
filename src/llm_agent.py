import os
import re
import json
import time
import logging
from groq import Groq
from dotenv import load_dotenv

logger = logging.getLogger("HRSystem.LLMAgent")

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")
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


def _get_role_fields_for_ai(role_dict):
    return {
        "Role Title": role_dict.get("Role_Title", "Unknown"),
        "Department": role_dict.get("Department", "Unknown"),
        "Territory / Base": role_dict.get("Territory_or_Base", "Unknown"),
        "Must Have Skills": role_dict.get("Must_Have_Skills", "Not specified"),
        "Preferred Experience": role_dict.get("Preferred_Experience", "Not specified"),
        "Core Outcomes": role_dict.get("Core_Outcomes", "Not specified"),
        "Min Experience (yrs)": role_dict.get("Experience_Min_Yrs", "Not specified"),
        "Max Experience (yrs)": role_dict.get("Experience_Max_Yrs", "Not specified"),
    }


def _get_candidate_fields_for_ai(candidate_dict):
    def safe_val(val):
        if val is None or (isinstance(val, float) and str(val) == "nan") or not str(val).strip():
            return "Unknown"
        return str(val).strip()

    return {
        "Full Name": safe_val(candidate_dict.get("Full_Name")),
        "Current Title": safe_val(candidate_dict.get("Current_Title")),
        "Current Company": safe_val(candidate_dict.get("Current_Company")),
        "Location": safe_val(candidate_dict.get("Location")),
        "Total Experience": safe_val(candidate_dict.get("Total_Experience_Yrs")) + " years",
        "Industry": safe_val(candidate_dict.get("Industry")),
        "Skills": safe_val(candidate_dict.get("Skills")),
        "Education": safe_val(candidate_dict.get("Education")),
        "Open to Work": safe_val(candidate_dict.get("Open_To_Work")),
        "Notice Period": safe_val(candidate_dict.get("Notice_Period_Days")) + " days",
    }


def evaluate_candidate(role_dict, candidate_dict):
    if not client:
        return {
            "score": 0,
            "reasons": "AI evaluation unavailable (Missing GROQ_API_KEY)",
            "gaps": "Configure GROQ_API_KEY in .env file"
        }

    role_info = _get_role_fields_for_ai(role_dict)
    candidate_info = _get_candidate_fields_for_ai(candidate_dict)

    prompt = f"""
Evaluate candidate fit for the given role.

ROLE:
{json.dumps(role_info, indent=2)}

CANDIDATE:
{json.dumps(candidate_info, indent=2)}

RULES:
- Base evaluation only on supplied data. Do not hallucinate missing facts.
- Explicitly state known match vs inferred fit.
- Assign score 0-100 (0=unsuitable, 50=moderate, 80+=strong).
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

        return {
            "score": score,
            "reasons": payload.get("reasons", "No details provided."),
            "gaps": payload.get("gaps", "None noted.")
        }

    except json.JSONDecodeError as err:
        logger.error(f"Failed to parse LLM JSON payload: {err}")
        return {
            "score": 0,
            "reasons": "Failed to parse AI response payload",
            "gaps": "Formatting error in model response"
        }
    except Exception as err:
        logger.exception("Error evaluating candidate fit")
        return {
            "score": 0,
            "reasons": f"Error: {type(err).__name__}",
            "gaps": "Service unavailable or evaluation failed"
        }


def generate_outreach_message(role_dict, candidate_dict):
    if not client:
        return "Hi, we have an open role at Jhandewalas Foods that matches your profile. Let us know if you'd like to connect. (API key missing)"

    role_info = _get_role_fields_for_ai(role_dict)
    candidate_info = _get_candidate_fields_for_ai(candidate_dict)

    prompt = f"""
Draft a personalized cold outreach message for LinkedIn.

ROLE:
{json.dumps(role_info, indent=2)}

CANDIDATE:
{json.dumps(candidate_info, indent=2)}

RULES:
- Use verified facts only.
- Address candidate by name.
- Keep total length under 80 words.
- Professional tone.
- Output message body only.
"""

    try:
        response = _call_groq_with_retry(prompt)
        if not response or not response.choices:
            raise ValueError("Empty response from LLM provider")

        return response.choices[0].message.content.strip()

    except Exception as err:
        logger.exception("Error generating outreach message")
        return f"Error generating message: {type(err).__name__}. Please try again."
