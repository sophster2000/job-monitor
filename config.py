import os
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

# Apify
APIFY_API_TOKEN = os.environ["APIFY_API_TOKEN"]

# Claude API
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# Twilio WhatsApp
TWILIO_ACCOUNT_SID = os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN = os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_WHATSAPP_FROM = os.environ["TWILIO_WHATSAPP_FROM"]  # e.g. "whatsapp:+14155238886"
TWILIO_WHATSAPP_TO = os.environ["TWILIO_WHATSAPP_TO"]      # e.g. "whatsapp:+64221231691"

# Job matching
RELEVANCE_THRESHOLD = float(os.getenv("RELEVANCE_THRESHOLD", "7.0"))

# CV content (can be set as env var or loaded from file)
CV_FILE = os.getenv("CV_FILE", "cv.txt")

# ---------------------------------------------------------------------------
# Job search keywords
# ---------------------------------------------------------------------------
JOB_KEYWORDS = [
    # Core experience
    "production coordinator",
    "event producer",
    "event manager",
    "event planner",
    "publicist",
    "logistics coordinator",
    "producer",
    "hospitality manager",
    "promotions coordinator",
    "targeted marketing",
    "assistant marketing manager",
    "executive assistant",
    # Media & entertainment
    "media relations",
    "international media",
    "international relations",
    "film production",
    "television production",
    "entertainment coordinator",
    "comedy production",
    # Communications & marketing
    "communications coordinator",
    "communications manager",
    "global marketing",
    "PR coordinator",
    "food PR",
    # Travel & hospitality
    "travel executive",
    "travel coordinator",
    "food and beverage coordinator",
    # Wider net
    "social impact coordinator",
    "non-profit coordinator",
    "solutions coordinator",
    "mid-level events",
]

SEARCH_LOCATION = "Netherlands"

# LinkedIn: one URL per keyword (Apify actor accepts a list)
def _linkedin_urls() -> list[str]:
    base = "https://www.linkedin.com/jobs/search/?keywords={kw}&location=Netherlands&f_TPR=r604800"
    return [base.format(kw=quote_plus(kw)) for kw in JOB_KEYWORDS]

LINKEDIN_SEARCH_URLS = _linkedin_urls()

# Indeed: one query dict per keyword
INDEED_SEARCH_QUERIES = [
    {"query": kw, "location": SEARCH_LOCATION}
    for kw in JOB_KEYWORDS
]

# Generic URL-based job sites to scrape
SCRAPE_URLS = [
    "https://www.whoknowsginny.com/explore",
    "https://born4jobs.nl/en/",
    "https://www.showbizjobs.com/jobs/location/country/nl",
    "https://filmvacatures.nl/",
    "https://www.iamexpat.nl/career/jobs-netherlands/amsterdam",
    "https://englishjobsearch.nl/in/amsterdam",
    "https://www.nationalevacaturebank.nl/",
]
