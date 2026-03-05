"""
Uses the Claude API to score each job listing against the user's CV.
Returns a score from 0–10 and a short explanation.
"""
import json
import re
import anthropic
from config import ANTHROPIC_API_KEY, RELEVANCE_THRESHOLD

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# Common Dutch words — if the description is overwhelmingly these, it's Dutch-only
_DUTCH_MARKERS = re.compile(
    r"\b(wij|jij|zijn|heeft|voor|naar|een|het|van|met|wat|als|maar|ook|dan|bij|aan|dat|wordt|kan|bent|heb|onze|zoeken|gevraagd|vereist|ervaring|werken|functie|vacature|solliciteer|bedrijf|omgeving|team|salaris|werkgever|fulltime|parttime)\b",
    re.IGNORECASE,
)
_ENGLISH_MARKERS = re.compile(
    r"\b(we|you|are|have|for|with|this|that|will|our|the|and|job|role|team|experience|required|looking|position|skills|company|please|apply|work|working)\b",
    re.IGNORECASE,
)


def is_dutch_only(job: dict) -> bool:
    """Return True if the job description appears to be Dutch-only."""
    text = " ".join([job.get("title", ""), job.get("description", "")])
    if len(text.strip()) < 20:
        return False
    dutch_hits = len(_DUTCH_MARKERS.findall(text))
    english_hits = len(_ENGLISH_MARKERS.findall(text))
    return dutch_hits > 5 and english_hits < 3


def _load_cv() -> str:
    from config import CV_FILE
    import os
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

    prompt = f"""You are a career advisor evaluating job fit for Sophie Krall.

CV:
{cv}

---

Job Listing:
{job_text}

---

Candidate preferences:
- Ideally based in Amsterdam or Utrecht (Netherlands). Remote roles are also great.
- If a job is in a different Dutch city (e.g. Rotterdam, Den Haag), it's acceptable but slightly less ideal — do not penalise heavily.
- Jobs outside the Netherlands that are not remote should be scored lower.

Language criteria:
- Sophie's Dutch is B1 (intermediate). She is a native English speaker.
- Prefer jobs conducted primarily in English or requiring only basic/no Dutch.
- If a job explicitly requires fluent/advanced Dutch (C1/C2 or "native Dutch"), reduce the score by 2-3 points.
- English-friendly or no Dutch requirement is a positive signal.

Score how well this job matches the candidate's CV on a scale from 0 to 10:
- 0-3: Poor match (different field, missing required skills, or requires advanced Dutch)
- 4-6: Partial match (related field but gaps, or Dutch level may be an issue)
- 7-8: Good match (most skills align, English-friendly, right location)
- 9-10: Excellent match (near-perfect fit, English role, Amsterdam/Utrecht/remote)

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
        match = re.search(r'"score"\s*:\s*(\d+(?:\.\d+)?)', raw)
        score = float(match.group(1)) if match else 0.0
        return score, raw


def is_relevant(job: dict) -> tuple[bool, float, str]:
    """Returns (is_relevant, score, reason)."""
    score, reason = score_job(job)
    return score >= RELEVANCE_THRESHOLD, score, reason
