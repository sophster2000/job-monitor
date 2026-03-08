"""
Diagnostic script — validates web scrapers and prints ALL jobs unfiltered.
No Apify, no Claude API, no Twilio — runs for free.
Run locally: python debug.py
Run in GitHub Actions: python debug.py (via debug.yml workflow)
"""
import sys
from config import SCRAPE_URLS
from scrapers.web_scraper import scrape_url

print("=== SCRAPER DIAGNOSTIC (no filtering) ===\n")

summary = []

for url in SCRAPE_URLS:
    domain = url.split("//")[-1].split("/")[0].replace("www.", "")
    label = domain.split(".")[0].title()

    print(f"[{label}] {url}")

    try:
        jobs = scrape_url(url)
    except Exception as e:
        print(f"  ERROR: {e}")
        summary.append((label, "ERROR"))
        print()
        continue

    found = len(jobs)
    print(f"  Found: {found} jobs")

    if found == 0:
        summary.append((label, 0))
        print()
        continue

    print("  All jobs:")
    for i, job in enumerate(jobs, 1):
        desc = job.get("description", "").strip()
        desc_preview = (desc[:120] + "…") if len(desc) > 120 else (desc or "(no description)")
        print(f"    {i:>3}. [{job.get('title', '(no title)')}]  {job.get('url', '(no url)')}")
        print(f"         {desc_preview}")

    summary.append((label, found))
    print()

print("=== SUMMARY ===")
header = f"{'Site':<25} | {'Found':>5}"
print(header)
print("-" * len(header))
for label, found in summary:
    if found == "ERROR":
        print(f"{label:<25} | {'ERROR':>5}")
    elif found == 0:
        print(f"{label:<25} | {0:>5}   <- no jobs found")
    else:
        print(f"{label:<25} | {found:>5}")

sys.exit(0)
