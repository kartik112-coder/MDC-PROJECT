
"""
MIET Jammu Website Scraper
Collects, cleans, chunks and stores official MIET website information.
"""

import time
import urllib.robotparser
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

import database

BASE_URL = "https://mietjmu.in/"
USER_AGENT = "MIET-Student-Project-Chatbot/1.0"

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
    "User-Agent": USER_AGENT
}

CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
REQUEST_DELAY = 2


def get_robots_parser():
    parser = urllib.robotparser.RobotFileParser()
    parser.set_url(urljoin(BASE_URL, "robots.txt"))

    try:
        parser.read()
        return parser
    except Exception:
        print("Warning: Could not read robots.txt.")
        return None


def allowed_by_robots(parser, url):
    if parser is None:
        return False

    return parser.can_fetch(USER_AGENT, url)


def fetch_page(session, url):
    try:
        response = session.get(
            url,
            headers=HEADERS,
            timeout=20
        )

        response.raise_for_status()

        content_type = response.headers.get(
            "Content-Type", ""
        ).lower()

        if "text/html" not in content_type:
            print("  Skipped: Not an HTML page.")
            return None

        return response.text

    except requests.RequestException as error:
        print(f"  Skipped: {error.__class__.__name__}")
        return None


def clean_text(html):
    soup = BeautifulSoup(html, "html.parser")

    if soup.title and soup.title.string:
        title = soup.title.string.strip()
    else:
        title = "MIET Jammu"

    for tag in soup([
        "script",
        "style",
        "noscript",
        "header",
        "footer",
        "nav",
        "form",
        "svg"
    ]):
        tag.decompose()

    main = soup.find("main") or soup.find("article") or soup.body

    if main:
        text = main.get_text(separator=" ", strip=True)
    else:
        text = soup.get_text(separator=" ", strip=True)

    text = " ".join(text.split())

    return title, text


def split_into_chunks(text):
    chunks = []

    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE

        chunk = text[start:end].strip()

        if len(chunk) >= 120:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def scrape():
    collected = []

    robots_parser = get_robots_parser()

    with requests.Session() as session:

        for url, category in PAGES:

            print(f"\nFetching: {url}")

            if urlparse(url).netloc != urlparse(BASE_URL).netloc:
                print("  Skipped: Outside official domain.")
                continue

            if not allowed_by_robots(robots_parser, url):
                print("  Skipped: Robots.txt restriction.")
                continue

            html = fetch_page(session, url)

            if not html:
                continue

            title, text = clean_text(html)

            if len(text) < 120:
                print("  Skipped: Insufficient page content.")
                continue

            chunks = split_into_chunks(text)

            for number, chunk in enumerate(chunks, start=1):
                collected.append({
                    "title": f"{title} (Part {number})",
                    "content": chunk,
                    "url": url,
                    "category": category
                })

            print(f"  Collected {len(chunks)} chunks.")

            time.sleep(REQUEST_DELAY)

    if not collected:
        print("\nNo valid information collected.")
        print("Existing database information will be preserved.")
        return 0

    stored = database.replace_scraped_chunks(collected)

    total = len(database.get_all_chunks())

    print("\nScraping completed.")
    print(f"New chunks stored: {stored}")
    print(f"Total knowledge-base chunks: {total}")

    return stored


if __name__ == "__main__":
    scrape()
