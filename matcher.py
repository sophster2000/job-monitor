"""
Uses the Claude API to score each job listing against the user's CV.
Returns a score from 0–10 and a short explanation.
"""
import json
import anthropic
from config import ANTHROPIC_API_KEY, RELEVANCE_THRESHOLD

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


def _load_cv() -> str:
    from config import CV_FILE
    import os
    # Prefer env var, then file
    cv_env = os.getenv("CV_CONTENT", "")
    if cv_env:
        return cv_env
    try:
        with open(CV_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"CV not found. Set CV_CONTENT env var or place your CV at '{CV_FILE}'.")


_CV: str | None = None


def _get_cv() -> str:
    global _CV
    if _CV is None:
        _CV = _load_cv()
    return _CV


def score_job(job: dict) -> tuple[float, str]:
    """
    Score a job dict against the CV.
    Returns (score: float 0-10, reason: str).
    """
    cv = _get_cv()
    job_text = (
        f"Job Title: {job.get('title', '')}\n"
        f"Company: {job.get('company', '')}\n"
        f"Location: {job.get('location', '')}\n"
        f"Description:\n{job.get('description', 'No description available.')}"
    )

    prompt = f"""You are a career advisor evaluating job fit.

CV:
{cv}

---

Job Listing:
{job_text}

---

Score how well this job matches the candidate's CV on a scale from 0 to 10:
- 0-3: Poor match (different field, missing required skills)
- 4-6: Partial match (related field but gaps)
- 7-8: Good match (most skills align)
- 9-10: Excellent match (near-perfect fit)

Respond ONLY with valid JSON in this exact format:
{{"score": <number>, "reason": "<one sentence explanation>"}}"""

    message = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=150,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = message.content[0].text.strip()
    try:
        data = json.loads(raw)
        return float(data["score"]), data["reason"]
    except (json.JSONDecodeError, KeyError):
        # Try to extract score from raw text as fallback
        import re
        match = re.search(r'"score"\s*:\s*(\d+(?:\.\d+)?)', raw)
        score = float(match.group(1)) if match else 0.0
        return score, raw


def is_relevant(job: dict) -> tuple[bool, float, str]:
    """Returns (is_relevant, score, reason)."""
    score, reason = score_job(job)
    return score >= RELEVANCE_THRESHOLD, score, reason
