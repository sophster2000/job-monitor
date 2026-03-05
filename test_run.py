"""
Test run: scrapes the web-based sites and scores the first 3 jobs from each with Claude.
Skips Twilio entirely.
"""
import sys
sys.path.insert(0, ".")

from scrapers.web_scraper import scrape_url
from matcher import score_job
from config import SCRAPE_URLS

for url in SCRAPE_URLS:
    print(f"\n{'='*60}")
    jobs = scrape_url(url)
    print(f"Found {len(jobs)} jobs")
    if not jobs:
        continue
    print("Scoring first 2 with Claude:")
    for job in jobs[:2]:
        try:
            score, reason = score_job(job)
            marker = "MATCH" if score >= 7 else "skip"
            print(f"  [{marker}] {score:.1f}/10 — {job['title'][:60]}")
            print(f"           {reason}")
        except Exception as e:
            print(f"  [error] {e}")
