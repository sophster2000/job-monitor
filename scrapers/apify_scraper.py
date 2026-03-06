"""
Apify-based scrapers for LinkedIn and Indeed.
Uses the Apify REST API to run actors and retrieve results.
"""
import time
import httpx
from config import APIFY_API_TOKEN, LINKEDIN_SEARCH_URLS, INDEED_SEARCH_QUERIES

APIFY_BASE = "https://api.apify.com/v2"
TIMEOUT = 300  # seconds to wait for actor run

# Correct actor IDs from Apify store
LINKEDIN_ACTOR = "bebity/linkedin-jobs-scraper"   # BHzefUZlZRKWxkTck
INDEED_ACTOR = "misceres/indeed-scraper"           # hMvNSpz3JnHgl5jkh


def _run_actor(actor_id: str, input_payload: dict) -> list[dict]:
    """Run an Apify actor synchronously and return dataset items."""
    headers = {"Authorization": f"Bearer {APIFY_API_TOKEN}"}

    resp = httpx.post(
        f"{APIFY_BASE}/acts/{actor_id}/runs",
        json=input_payload,
        headers=headers,
        timeout=30,
    )
    resp.raise_for_status()
    run_id = resp.json()["data"]["id"]

    # Poll until finished
    deadline = time.time() + TIMEOUT
    while time.time() < deadline:
        status_resp = httpx.get(
            f"{APIFY_BASE}/actor-runs/{run_id}",
            headers=headers,
            timeout=30,
        )
        status_resp.raise_for_status()
        status = status_resp.json()["data"]["status"]
        if status in ("SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"):
            break
        time.sleep(10)

    if status != "SUCCEEDED":
        print(f"[Apify] Actor {actor_id} run ended with status: {status}")
        return []

    dataset_id = status_resp.json()["data"]["defaultDatasetId"]
    items_resp = httpx.get(
        f"{APIFY_BASE}/datasets/{dataset_id}/items",
        headers=headers,
        params={"format": "json", "clean": True},
        timeout=60,
    )
    items_resp.raise_for_status()
    return items_resp.json()


def scrape_linkedin() -> list[dict]:
    """Scrape LinkedIn Jobs via Apify actor bebity/linkedin-jobs-scraper."""
    print("[LinkedIn] Starting Apify scrape...")
    raw = _run_actor(
        LINKEDIN_ACTOR,
        {
            "startUrls": [{"url": u} for u in LINKEDIN_SEARCH_URLS],
            "maxJobs": 50,
        },
    )
    jobs = []
    for item in raw:
        jobs.append({
            "source": "LinkedIn",
            "title": item.get("title", ""),
            "company": item.get("companyName", item.get("company", "")),
            "location": item.get("location", ""),
            "description": item.get("descriptionText", item.get("description", "")),
            "url": item.get("jobUrl", item.get("url", "")),
        })
    print(f"[LinkedIn] Found {len(jobs)} jobs")
    return jobs


def scrape_indeed() -> list[dict]:
    """Scrape Indeed via Apify actor misceres/indeed-scraper."""
    print("[Indeed] Starting Apify scrape...")
    results = []
    for query_cfg in INDEED_SEARCH_QUERIES:
        raw = _run_actor(
            INDEED_ACTOR,
            {
                "position": query_cfg["query"],
                "country": "NL",
                "location": query_cfg["location"],
                "maxItems": 50,
            },
        )
        for item in raw:
            results.append({
                "source": "Indeed",
                "title": item.get("positionName", item.get("title", "")),
                "company": item.get("company", ""),
                "location": item.get("location", ""),
                "description": item.get("description", ""),
                "url": item.get("url", item.get("jobUrl", "")),
            })
    print(f"[Indeed] Found {len(results)} jobs")
    return results
