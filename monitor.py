"""
Craigslist Object Monitor
================================
Check https://sfbay.craigslist.org/search/zip every 10 minutes
for interesting "objects" and email me if found.

requirements:
  pip install requests==2.31.0 beautifulsoup4==4.12.3

Gmail setup (required):
  1. Go to https://myaccount.google.com/apppasswords and create an App Password.
  2. replace the *MAIL* args below.
"""

import time
import smtplib
import logging
import requests

from typing import Optional, List, Dict
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from bs4 import BeautifulSoup
from datetime import datetime

# ─── Configuration ────────────────────────────────────────────────────────────

URL = "https://sfbay.craigslist.org/search/zip#search=2~gallery~0?format=rss"
KEYWORDS       = ["solar", "landscape wire", "gopher wire", "wire-mesh", "nursery pot", "plastic container"]
CHECK_INTERVAL_MINUTES = 10

GMAIL_SENDER    = "youremail@gmail.com"       # ← Your Gmail address
GMAIL_APP_PASSWORD = "xxxx xxxx xxxx xxxx"  # ← Your Gmail App Password (NOT your login password)
RECIPIENT_EMAIL = "youremail@gmail.com"       # ← Where to send the alert

# ─── Logging ──────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

# ─── Helpers ──────────────────────────────────────────────────────────────────

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}


def fetch_page(url: str) -> Optional[str]:
    """Download the page and return its text, or None on error."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        return resp.text
    except requests.RequestException as exc:
        log.error("Failed to fetch page: %s", exc)
        return None


def extract_listings(html: str) -> List[Dict]:
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for item in soup.select("li.cl-static-search-result")[:100]: #[:20]: # look at the first 20 listings
        title = item.get("title", "").strip()          # it's right on the <li> tag!
        link  = item.select_one("a")
        if title and link:
            results.append({
                "title": title,
                "url":   link.get("href", ""),
            })
    return results


def matches_keywords(listing: Dict, keywords: List[str]) -> bool:
    """Return True if any keyword appears in the listing title (case-insensitive)."""
    title_lower = listing["title"].lower()
    return any(kw.lower() in title_lower for kw in keywords)


def send_email(matches: List[Dict]) -> None:
    """Send an alert email listing all matched postings."""
    subject = f"[Craigslist Alert] Solar panels found – {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    lines = ["The following listings matched your keywords:\n"]
    for m in matches:
        lines.append(f"• {m['title']}\n  {m['url']}\n")
    body = "\n".join(lines)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = GMAIL_SENDER
    msg["To"]      = RECIPIENT_EMAIL
    msg.attach(MIMEText(body, "plain"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(GMAIL_SENDER, GMAIL_APP_PASSWORD)
            server.sendmail(GMAIL_SENDER, RECIPIENT_EMAIL, msg.as_string())
        log.info("Alert email sent to %s", RECIPIENT_EMAIL)
    except smtplib.SMTPException as exc:
        log.error("Failed to send email: %s", exc)


# ─── Main Loop ────────────────────────────────────────────────────────────────

def check_once() -> None:
    log.info("Checking %s …", URL)
    html = fetch_page(URL)
    if html is None:
        return

    listings = extract_listings(html)
    log.info("Found %d listings total.", len(listings))

    hits = [lst for lst in listings if matches_keywords(lst, KEYWORDS)]

    if hits:
        log.info("%d match(es) found! Sending email…", len(hits))
        for h in hits:
            log.info("  ✓ %s", h["title"])
        send_email(hits)

    else:
        log.info("No matches found. Will check again in %d minutes.", CHECK_INTERVAL_MINUTES)

    return hits


def main() -> None:
    log.info("Monitor started. Keywords: %s", KEYWORDS)
    log.info("Checking every %d minutes.", CHECK_INTERVAL_MINUTES)
    while True:
        check_once()
        time.sleep(CHECK_INTERVAL_MINUTES * 60)


if __name__ == "__main__":
    main()
