"""
scrape_miet.py - Collect content from the official MIET Jammu website.
======================================================================
Project : AI-Powered MIET Jammu Website Chatbot (BTech Semester Project)

Uses Requests + BeautifulSoup to:
  1. Check robots.txt and respect access restrictions.
  2. Download a list of official pages from https://mietjmu.in/.
  3. Clean the visible text (remove scripts, styles, menus).
  4. Split the text into overlapping chunks (good for RAG retrieval).
  5. Store the chunks with their SOURCE URL in the SQLite database.

Run on Windows:
    python scrape_miet.py

Pages that are missing or blocked are skipped politely - the chatbot
keeps working with whatever verified content is available.
"""

import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import database

BASE_URL = "https://mietjmu.in/"

# Candidate official pages to collect. Unreachable pages are skipped
# automatically, so this list is safe to extend.
PAGES = [
    ("https://mietjmu.in/", "about"),
    ("https://mietjmu.in/about-us/", "about"),
    ("https://mietjmu.in/admissions/", "admissions"),
    ("https://mietjmu.in/academics/", "academics"),
    ("https://mietjmu.in/departments/", "academics"),
    ("https://mietjmu.in/placements/", "placements"),
    ("https://mietjmu.in/contact-us/", "contact"),
    ("https://mietjmu.in/notices/", "notices"),
    ("https://mietjmu.in/examination/", "examinations"),
]

HEADERS = {
    "User-Agent": (
        "MIET-Student-Project-Chatbot/1.0 (BTech semester project; "
        "educational use; contact via college)"
    )
}

CHUNK_SIZE = 900      # characters per chunk
CHUNK_OVERLAP = 150   # characters shared between neighbouring chunks
REQUEST_DELAY = 2.0   # polite delay between requests (seconds)


def allowed_by_robots(url: str) -> bool:
    """Respect website access restrictions declared in robots.txt."""
    try:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(urljoin(BASE_URL, "/robots.txt"))
        rp.read()
        return rp.can_fetch(HEADERS["User-Agent"], url)
    except Exception:
        # If robots.txt cannot be read, stay conservative but allow the
        # public homepage which we know is intended for visitors.
        return url.rstrip("/") == BASE_URL.rstrip("/")


def fetch_page(url: str) -> str | None:
    """Download one page; return HTML or None on any failure."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        if resp.status_code == 200 and "text/html" in resp.headers.get("Content-Type", ""):
            return resp.text
        print(f"  [skip] {url} -> HTTP {resp.status_code}")
    except requests.RequestException as exc:
        print(f"  [skip] {url} -> {exc.__class__.__name__}")
    return None


def clean_text(html: str) -> tuple[str, str]:
    """Return (page_title, cleaned_visible_text) from raw HTML."""
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.string or "MIET Jammu").strip() if soup.title else "MIET Jammu"

    # Remove non-content elements.
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
        tag.decompose()

    text = soup.get_text(separator=" ")
    # Normalise whitespace.
    words = text.split()
    return title, " ".join(words)


def split_into_chunks(text: str) -> list[str]:
    """Split long text into overlapping chunks for better retrieval."""
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()
        if len(chunk) > 120:  # ignore tiny fragments
            chunks.append(chunk)
        start = end - CHUNK_OVERLAP
    return chunks


def scrape() -> int:
    """Scrape all allowed pages and store chunks in SQLite."""
    collected: list[dict] = []

    for url, category in PAGES:
        print(f"Fetching {url}")
        if urlparse(url).netloc != urlparse(BASE_URL).netloc:
            print("  [skip] outside official domain")
            continue
        if not allowed_by_robots(url):
            print("  [skip] disallowed by robots.txt")
            continue

        html = fetch_page(url)
        if not html:
            continue

        title, text = clean_text(html)
        for i, chunk in enumerate(split_into_chunks(text), start=1):
            collected.append(
                {
                    "title": f"{title} (part {i})",
                    "content": chunk,
                    "url": url,
                    "category": category,
                }
            )
        time.sleep(REQUEST_DELAY)

    stored = database.replace_scraped_chunks(collected)
    database.seed_if_empty()
    total = len(database.get_all_chunks())
    print(f"\nStored {stored} scraped chunks. Knowledge base now has {total} chunks.")
    return stored


if __name__ == "__main__":
    scrape()
