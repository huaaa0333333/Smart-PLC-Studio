import json
import re
from typing import Dict

from core import utils
from core.prompts import get_code_reviewer_prompt


def review_generated_code(client, scl_code: str, csv_tags: str) -> Dict:
    """Use LLM to quantitatively evaluate generated SCL code and CSV variable table.

    Returns a dict with:
        - score: int (0-100)
        - feedback: str (human‑readable comments)
    """
    # Basic sanity checks before LLM call
    issues = []
    if not scl_code.strip():
        issues.append("SCL code is empty.")
    if not csv_tags.strip():
        issues.append("Variable table (CSV) is empty.")
    # Simple regex checks for common placeholder patterns
    if re.search(r"TODO|FIXME|\bpass\b", scl_code, re.IGNORECASE):
        issues.append("SCL code contains placeholder tokens (TODO/FIXME/pass).")
    # If any critical issue, we can assign low score without LLM
    if issues:
        feedback = "\n".join(issues)
        return {"score": 30, "feedback": feedback}

    # Build prompt for LLM evaluation
    prompt = get_code_reviewer_prompt(scl_code, csv_tags)
    try:
        # Call Gemini client using the correct V1 API
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        text = response.text.strip()
        # Clean up markdown JSON blocks if present
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        # Expect JSON response
        result = json.loads(text.strip())
        score = int(result.get("score", 0))
        feedback = result.get("feedback", "")
    except Exception as e:
        # Fallback if LLM does not return JSON or API call fails
        score = 50
        feedback = f"Unable to retrieve or parse AI reviewer response. Defaulting to moderate score. (Error: {e})"
    return {"score": score, "feedback": feedback}
