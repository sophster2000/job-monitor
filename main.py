"""
Job Monitoring Agent
--------------------
Scrapes job listings from LinkedIn (Apify), Indeed (Apify), and a set of
URL-based job boards, scores each listing against your CV using Claude,
and sends WhatsApp notifications via Twilio for relevant matches.
"""
from scrapers import scrape_indeed_rss, scrape_url
from matcher import is_relevant, is_dutch_only
from notifier import send_whatsapp
from storage import is_seen, mark_seen, make_id, log_run
from config import SCRAPE_URLS, RELEVANCE_THRESHOLD


def process_jobs(jobs: list[dict]) -> tuple[int, int]:
    """Score and notify for a list of job dicts. Returns (new_count, matched_count)."""
    new_count = 0
    matched_count = 0

    for job in jobs:
        job_id = make_id(job.get("url", ""), job.get("title", ""))

        if is_seen(job_id):
            continue

        mark_seen(job_id)
        new_count += 1

        title = job.get("title", "").strip()
        if not title:
            continue

        # Skip jobs written entirely in Dutch
        if is_dutch_only(job):
            print(f"  [dutch] Skipping Dutch-only listing: {title}")
            continue

        try:
            relevant, score, reason = is_relevant(job)
        except Exception as e:
            print(f"[Matcher] Error scoring '{title}': {e}")
            continue

        status = "MATCH" if relevant else "skip"
        print(f"  [{status}] {score:.1f}/10 — {title} @ {job.get('company', 'N/A')}")

        if relevant:
            try:
                send_whatsapp(job, score, reason)
                matched_count += 1
            except Exception as e:
                print(f"[Notifier] Failed to send notification: {e}")

    return new_count, matched_count


def main():
    print("=" * 60)
    print("Job Monitor starting")
    print(f"Relevance threshold: {RELEVANCE_THRESHOLD}/10")
    print("=" * 60)

    total_new = 0
    total_matched = 0

    # --- Indeed (free RSS) ---
    try:
        indeed_jobs = scrape_indeed_rss()
        new, matched = process_jobs(indeed_jobs)
        total_new += new
        total_matched += matched
    except Exception as e:
        print(f"[Indeed] Scrape failed: {e}")

    # --- URL-based sites ---
    for url in SCRAPE_URLS:
        try:
            jobs = scrape_url(url)
            new, matched = process_jobs(jobs)
            total_new += new
            total_matched += matched
        except Exception as e:
            print(f"[WebScraper] Failed for {url}: {e}")

    log_run(total_new, total_matched)

    print("=" * 60)
    print(f"Done. New jobs seen: {total_new} | Matches notified: {total_matched}")
    print("=" * 60)


if __name__ == "__main__":
    main()
