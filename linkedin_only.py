"""
LinkedIn-only job monitor — run once per day via linkedin-daily.yml.
Uses Apify credits, so kept separate from the free 2-hourly monitor.
"""
import sys
from scrapers.apify_scraper import scrape_linkedin
from main import process_jobs
from storage import log_run

print("=" * 60)
print("LinkedIn daily scrape starting")
print("=" * 60)

try:
    jobs = scrape_linkedin()
    new, matched = process_jobs(jobs)
    log_run(new, matched)
    print("=" * 60)
    print(f"Done. New jobs seen: {new} | Matches notified: {matched}")
    print("=" * 60)
except Exception as e:
    print(f"[LinkedIn] Fatal error: {e}")
    sys.exit(1)
