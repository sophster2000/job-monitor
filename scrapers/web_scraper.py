"""
Generic web scraper using Playwright (handles JS-rendered pages).
Each supported domain has a tailored extraction function;
unknown domains fall back to a generic heuristic extractor.
"""
import re
from urllib.parse import urlparse
from playwright.sync_api import sync_playwright, Page

PLAYWRIGHT_TIMEOUT = 15000  # ms


def _domain(url: str) -> str:
    return urlparse(url).netloc.replace("www.", "")


def _wait_and_pause(page: Page, ms: int = 3000) -> None:
    """Give JS time to render after domcontentloaded."""
    page.wait_for_timeout(ms)


# ---------------------------------------------------------------------------
# Per-site extractors
# ---------------------------------------------------------------------------

def _extract_whoknowsginny(page: Page) -> list[dict]:
    _wait_and_pause(page)
    jobs = []
    seen = set()
    for link in page.query_selector_all("a[href]"):
        href = link.get_attribute("href") or ""
        if "/job" not in href or href in seen:
            continue
        seen.add(href)
        url = href if href.startswith("http") else f"https://www.whoknowsginny.com{href}"
        title = link.inner_text().strip().split("\n")[0]
        if title:
            jobs.append({"source": "WhoKnowsGinny", "title": title, "url": url, "company": "", "location": "", "description": ""})
    return jobs


def _extract_born4jobs(page: Page) -> list[dict]:
    # Dismiss cookie popup if present
    try:
        page.click("button:has-text('Toestemming')", timeout=5000)
    except Exception:
        pass
    _wait_and_pause(page, 2000)
    jobs = []
    seen = set()
    for link in page.query_selector_all("a[href]"):
        href = link.get_attribute("href") or ""
        if "born4jobs.nl" not in href and not href.startswith("/"):
            continue
        if href in seen:
            continue
        text = link.inner_text().strip()
        # Job links typically have multi-line text with a title
        lines = [l.strip() for l in text.split("\n") if l.strip()]
        if not lines or len(lines[0]) < 5:
            continue
        # Skip nav/footer links
        if href in ("/en/", "/", "") or "cv-templates" in href or "het-team" in href:
            continue
        # Only include links that look like job listings (contain a date or multi-word title)
        if len(lines) >= 2 or (len(lines) == 1 and len(lines[0].split()) >= 3):
            seen.add(href)
            url = href if href.startswith("http") else f"https://born4jobs.nl{href}"
            jobs.append({"source": "Born4Jobs", "title": lines[0], "url": url, "company": "", "location": "Netherlands", "description": ""})
    return jobs


def _extract_showbizjobs(page: Page) -> list[dict]:
    _wait_and_pause(page)
    jobs = []
    seen = set()
    for link in page.query_selector_all("a[href]"):
        href = link.get_attribute("href") or ""
        # Showbiz job links contain /jobs/ in the path
        if "/jobs/" not in href or href in seen:
            continue
        text = link.inner_text().strip().split("\n")[0]
        if not text or len(text) < 5:
            continue
        seen.add(href)
        url = href if href.startswith("http") else f"https://www.showbizjobs.com{href}"
        jobs.append({"source": "ShowbizJobs", "title": text, "url": url, "company": "", "location": "Netherlands", "description": ""})
    return jobs


def _extract_filmvacatures(page: Page) -> list[dict]:
    _wait_and_pause(page)
    jobs = []
    seen = set()
    for link in page.query_selector_all("a[href]"):
        href = link.get_attribute("href") or ""
        if not re.search(r"/prikborden/view/\d+", href) or href in seen:
            continue
        text = link.inner_text().strip().split("\n")[0]
        if not text or len(text) < 5:
            continue
        seen.add(href)
        url = href if href.startswith("http") else f"https://filmvacatures.nl{href}"
        jobs.append({"source": "FilmVacatures", "title": text, "url": url, "company": "", "location": "Netherlands", "description": ""})
    return jobs


def _extract_iamexpat(page: Page) -> list[dict]:
    _wait_and_pause(page, 3000)
    jobs = []
    seen = set()
    for link in page.query_selector_all("a[href]"):
        href = link.get_attribute("href") or ""
        # Job detail pages have path depth: /career/jobs-netherlands/<category>/<title>/<id>
        if not re.match(r"^/career/jobs-netherlands/[^/]+/[^/]+/[^/]+", href):
            continue
        if href in seen:
            continue
        seen.add(href)
        text = link.inner_text().strip()
        # Title is the first line
        title = text.split("\n")[0].strip()
        if not title:
            continue
        url = f"https://www.iamexpat.nl{href}"
        jobs.append({"source": "IAmExpat", "title": title, "url": url, "company": "", "location": "Amsterdam", "description": ""})
    return jobs


def _extract_englishjobsearch(page: Page) -> list[dict]:
    _wait_and_pause(page, 3000)
    jobs = []
    seen = set()
    for link in page.query_selector_all("a[href]"):
        href = link.get_attribute("href") or ""
        # Job links use /clickout/ pattern
        if "/clickout/" not in href or href in seen:
            continue
        text = link.inner_text().strip().split("\n")[0]
        if not text or text.lower() == "report probem":
            continue
        seen.add(href)
        url = f"https://englishjobsearch.nl{href}" if href.startswith("/") else href
        jobs.append({"source": "EnglishJobSearch", "title": text, "url": url, "company": "", "location": "Amsterdam", "description": ""})
    return jobs


def _extract_nationalevacaturebank(page: Page) -> list[dict]:
    # Accept cookie wall
    for selector in [
        "button:has-text('Akkoord')",
        "button:has-text('Accepteer')",
        "button:has-text('Alles accepteren')",
        "[id*='accept']",
        "[class*='accept']",
    ]:
        try:
            page.click(selector, timeout=4000)
            break
        except Exception:
            continue
    _wait_and_pause(page, 4000)
    jobs = []
    seen = set()
    for link in page.query_selector_all("a[href]"):
        href = link.get_attribute("href") or ""
        if href in seen:
            continue
        if not re.search(r"/(vacature|vacancy)/", href, re.I):
            continue
        text = link.inner_text().strip().split("\n")[0]
        if not text or len(text) < 5:
            continue
        seen.add(href)
        url = href if href.startswith("http") else f"https://www.nationalevacaturebank.nl{href}"
        jobs.append({"source": "NationaleVacaturebank", "title": text, "url": url, "company": "", "location": "Netherlands", "description": ""})
    return jobs


def _generic_extract(page: Page, source: str) -> list[dict]:
    """Fallback: find job-like links heuristically."""
    _wait_and_pause(page)
    jobs = []
    seen = set()
    job_pattern = re.compile(r"(job|vacature|vacancy|career|werk|position)", re.I)
    for link in page.query_selector_all("a[href]"):
        href = link.get_attribute("href") or ""
        text = link.inner_text().strip()
        if len(text) < 5 or len(text) > 200 or href in seen:
            continue
        seen.add(href)
        if job_pattern.search(href) or job_pattern.search(text):
            url = href if href.startswith("http") else href
            jobs.append({"source": source, "title": text.split("\n")[0], "url": url, "company": "", "location": "", "description": ""})
    return jobs


EXTRACTORS = {
    "whoknowsginny.com": _extract_whoknowsginny,
    "born4jobs.nl": _extract_born4jobs,
    "showbizjobs.com": _extract_showbizjobs,
    "filmvacatures.nl": _extract_filmvacatures,
    "iamexpat.nl": _extract_iamexpat,
    "englishjobsearch.nl": _extract_englishjobsearch,
    "nationalevacaturebank.nl": _extract_nationalevacaturebank,
}


def scrape_url(url: str) -> list[dict]:
    domain = _domain(url)
    extractor = EXTRACTORS.get(domain, None)
    source = domain

    print(f"[WebScraper] Scraping {domain}...")
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
        )
        try:
            page.goto(url, timeout=30000, wait_until="domcontentloaded")
            jobs = extractor(page) if extractor else _generic_extract(page, source)
        except Exception as e:
            print(f"[WebScraper] Error scraping {url}: {e}")
            jobs = []
        finally:
            browser.close()

    print(f"[WebScraper] Found {len(jobs)} jobs from {domain}")
    return jobs
