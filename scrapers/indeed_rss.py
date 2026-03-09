"""
Free Indeed job scraper using Indeed's public RSS feeds.
No API key, no Apify credits — completely free.
"""
import xml.etree.ElementTree as ET
from urllib.parse import quote_plus
import httpx
from config import JOB_KEYWORDS

RSS_URL = "https://www.indeed.com/rss?q={q}&l=Netherlands&sort=date&fromage=7"
REQUEST_TIMEOUT = 15  # seconds per feed


def _parse_feed(xml_text: str, keyword: str) -> list[dict]:
    jobs = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return jobs
    for item in root.findall("./channel/item"):
        title_raw = (item.findtext("title") or "").strip()
        url = (item.findtext("link") or "").strip()
        description = (item.findtext("description") or "").strip()
        if not title_raw or not url:
            continue
        # Indeed titles are usually "Job Title - Company Name"
        if " - " in title_raw:
            title, company = title_raw.rsplit(" - ", 1)
        else:
            title, company = title_raw, ""
        jobs.append({
            "source": "Indeed",
            "title": title.strip(),
            "company": company.strip(),
            "location": "Netherlands",
            "description": description,
            "url": url,
        })
    return jobs


def scrape_indeed_rss() -> list[dict]:
    """Fetch Indeed RSS feeds for all job keywords. Returns deduplicated job list."""
    print("[Indeed RSS] Starting free RSS scrape...")
    seen_urls: set[str] = set()
    all_jobs: list[dict] = []

    with httpx.Client(timeout=REQUEST_TIMEOUT, follow_redirects=True) as client:
        for keyword in JOB_KEYWORDS:
            url = RSS_URL.format(q=quote_plus(keyword))
            try:
                resp = client.get(url)
                resp.raise_for_status()
                jobs = _parse_feed(resp.text, keyword)
                for job in jobs:
                    if job["url"] not in seen_urls:
                        seen_urls.add(job["url"])
                        all_jobs.append(job)
            except Exception as e:
                print(f"[Indeed RSS] Failed for '{keyword}': {e}")

    print(f"[Indeed RSS] Found {len(all_jobs)} unique jobs")
    return all_jobs
