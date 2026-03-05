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


# ---------------------------------------------------------------------------
# Per-site extractors
# ---------------------------------------------------------------------------

def _extract_whoknowsginny(page: Page) -> list[dict]:
    page.wait_for_selector("a[href*='/job']", timeout=PLAYWRIGHT_TIMEOUT)
    jobs = []
    cards = page.query_selector_all("a[href*='/job']")
    seen = set()
    for card in cards:
        href = card.get_attribute("href") or ""
        if not href or href in seen:
            continue
        seen.add(href)
        url = href if href.startswith("http") else f"https://www.whoknowsginny.com{href}"
        title = card.inner_text().strip().split("\n")[0]
        jobs.append({"source": "WhoKnowsGinny", "title": title, "url": url, "company": "", "location": "", "description": ""})
    return jobs


def _extract_born4jobs(page: Page) -> list[dict]:
    page.wait_for_load_state("networkidle", timeout=PLAYWRIGHT_TIMEOUT)
    jobs = []
    cards = page.query_selector_all("article, .job-item, [class*='vacancy'], [class*='job']")
    for card in cards:
        title_el = card.query_selector("h2, h3, h4, .title, [class*='title']")
        link_el = card.query_selector("a")
        title = title_el.inner_text().strip() if title_el else card.inner_text().strip().split("\n")[0]
        href = link_el.get_attribute("href") if link_el else ""
        url = href if href and href.startswith("http") else f"https://born4jobs.nl{href}" if href else ""
        if title:
            jobs.append({"source": "Born4Jobs", "title": title, "url": url, "company": "", "location": "", "description": ""})
    return jobs


def _extract_showbizjobs(page: Page) -> list[dict]:
    page.wait_for_load_state("networkidle", timeout=PLAYWRIGHT_TIMEOUT)
    jobs = []
    listings = page.query_selector_all(".job-listing, article, [class*='job']")
    for item in listings:
        title_el = item.query_selector("h2, h3, .job-title, [class*='title']")
        link_el = item.query_selector("a")
        company_el = item.query_selector(".company, [class*='company']")
        title = title_el.inner_text().strip() if title_el else ""
        href = link_el.get_attribute("href") if link_el else ""
        url = href if href and href.startswith("http") else f"https://www.showbizjobs.com{href}" if href else ""
        company = company_el.inner_text().strip() if company_el else ""
        if title:
            jobs.append({"source": "ShowbizJobs", "title": title, "url": url, "company": company, "location": "Netherlands", "description": ""})
    return jobs


def _extract_filmvacatures(page: Page) -> list[dict]:
    page.wait_for_load_state("networkidle", timeout=PLAYWRIGHT_TIMEOUT)
    jobs = []
    items = page.query_selector_all(".vacancy, article, [class*='vacature'], [class*='job']")
    for item in items:
        title_el = item.query_selector("h2, h3, .title, [class*='title']")
        link_el = item.query_selector("a")
        title = title_el.inner_text().strip() if title_el else ""
        href = link_el.get_attribute("href") if link_el else ""
        url = href if href and href.startswith("http") else f"https://filmvacatures.nl{href}" if href else ""
        if title:
            jobs.append({"source": "FilmVacatures", "title": title, "url": url, "company": "", "location": "Netherlands", "description": ""})
    return jobs


def _extract_iamexpat(page: Page) -> list[dict]:
    page.wait_for_selector(".job-list-item, article, [class*='job']", timeout=PLAYWRIGHT_TIMEOUT)
    jobs = []
    items = page.query_selector_all(".job-list-item, article, [class*='job-item']")
    for item in items:
        title_el = item.query_selector("h2, h3, .job-title, [class*='title']")
        link_el = item.query_selector("a")
        company_el = item.query_selector(".company-name, [class*='company']")
        title = title_el.inner_text().strip() if title_el else ""
        href = link_el.get_attribute("href") if link_el else ""
        url = href if href and href.startswith("http") else f"https://www.iamexpat.nl{href}" if href else ""
        company = company_el.inner_text().strip() if company_el else ""
        if title:
            jobs.append({"source": "IAmExpat", "title": title, "url": url, "company": company, "location": "Amsterdam", "description": ""})
    return jobs


def _extract_englishjobsearch(page: Page) -> list[dict]:
    page.wait_for_load_state("networkidle", timeout=PLAYWRIGHT_TIMEOUT)
    jobs = []
    items = page.query_selector_all("article, .job, [class*='job-listing'], [class*='vacancy']")
    for item in items:
        title_el = item.query_selector("h2, h3, .title, [class*='title']")
        link_el = item.query_selector("a")
        title = title_el.inner_text().strip() if title_el else ""
        href = link_el.get_attribute("href") if link_el else ""
        url = href if href and href.startswith("http") else f"https://englishjobsearch.nl{href}" if href else ""
        if title:
            jobs.append({"source": "EnglishJobSearch", "title": title, "url": url, "company": "", "location": "Amsterdam", "description": ""})
    return jobs


def _extract_nationalevacaturebank(page: Page) -> list[dict]:
    page.wait_for_selector("[class*='vacancy'], [class*='job'], article", timeout=PLAYWRIGHT_TIMEOUT)
    jobs = []
    items = page.query_selector_all("[class*='vacancy-card'], [class*='job-card'], article")
    for item in items:
        title_el = item.query_selector("h2, h3, [class*='title']")
        link_el = item.query_selector("a")
        company_el = item.query_selector("[class*='company'], [class*='employer']")
        title = title_el.inner_text().strip() if title_el else ""
        href = link_el.get_attribute("href") if link_el else ""
        url = href if href and href.startswith("http") else f"https://www.nationalevacaturebank.nl{href}" if href else ""
        company = company_el.inner_text().strip() if company_el else ""
        if title:
            jobs.append({"source": "NationaleVacaturebank", "title": title, "url": url, "company": company, "location": "Netherlands", "description": ""})
    return jobs


def _generic_extract(page: Page, source: str) -> list[dict]:
    """Fallback: find job-like links heuristically."""
    page.wait_for_load_state("networkidle", timeout=PLAYWRIGHT_TIMEOUT)
    jobs = []
    links = page.query_selector_all("a")
    seen = set()
    job_pattern = re.compile(r"(job|vacature|vacancy|career|werk|position)", re.I)
    for link in links:
        href = link.get_attribute("href") or ""
        text = link.inner_text().strip()
        if len(text) < 5 or len(text) > 200:
            continue
        if href in seen:
            continue
        seen.add(href)
        if job_pattern.search(href) or job_pattern.search(text):
            url = href if href.startswith("http") else href
            jobs.append({"source": source, "title": text, "url": url, "company": "", "location": "", "description": ""})
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
            if extractor:
                jobs = extractor(page)
            else:
                jobs = _generic_extract(page, source)
        except Exception as e:
            print(f"[WebScraper] Error scraping {url}: {e}")
            jobs = []
        finally:
            browser.close()

    print(f"[WebScraper] Found {len(jobs)} jobs from {domain}")
    return jobs
