import os
import requests
from dotenv import load_dotenv

load_dotenv()


class ToolError(Exception):
    """Raised when a real external API call fails."""
    pass


def _normalize_adzuna_job(raw: dict) -> dict:
    return {
        "title": raw.get("title", "Unknown"),
        "company": (raw.get("company") or {}).get("display_name", "Unknown"),
        "location": (raw.get("location") or {}).get("display_name", "Remote"),
        "source": "Adzuna",
        "url": raw.get("redirect_url"),
    }


def search_jobs(criteria: dict) -> list[dict]:
    """Adzuna is the primary (and only) live source."""
    app_id = os.getenv("ADZUNA_APP_ID")
    app_key = os.getenv("ADZUNA_APP_KEY")
    country = os.getenv("ADZUNA_COUNTRY", "us")
    if not app_id or not app_key:
        raise ToolError("Missing ADZUNA_APP_ID/ADZUNA_APP_KEY in .env")

    role = criteria.get("role") or "engineer"
    location = criteria.get("location") or ""

    try:
        resp = requests.get(
            f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
            params={
                "app_id": app_id,
                "app_key": app_key,
                "what": role,
                "where": location,
                "results_per_page": 5,
            },
            timeout=10,
        )
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        raise ToolError(f"Adzuna request failed: {e}")

    results = resp.json().get("results", [])
    return [_normalize_adzuna_job(r) for r in results]


def apply_to_job(job: dict) -> str:
    """
    Real job boards don't offer a public 'submit application' API —
    this stays simulated. In a real product this would open job["url"]
    via a browser-automation tool (e.g. Playwright) or hand off to the
    user to apply manually. We keep the retry-loop demo intact here.
    """
    import random
    if random.random() < 0.3:
        raise ToolError(f"ApplyPortal-{job['company']} timed out")
    return f"Applied to {job['title']} at {job['company']}"


SOURCE_FUNCS = {
    "remoteco": search_jobs,
}