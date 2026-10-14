"""
database.py - SQLite knowledge base for the MIET Jammu chatbot.
================================================================
Project : AI-Powered MIET Jammu Website Chatbot (BTech Semester Project)
Team    : Danish Sharma (2025A6R032), Kartik Sharma (2025A6R003),
          Dheeraj Thakur (2025A6R024)

This module owns everything related to the SQLite database:
  * creating the `chunks` table,
  * seeding it with a verified snapshot of content from https://mietjmu.in/,
  * reading chunks back for the RAG retriever in rag.py.

Every chunk keeps its SOURCE URL so the chatbot can show clickable
citations and never presents information without a source.

NOTE ON DATA HONESTY:
The seed rows below were taken from the official MIET Jammu homepage
(https://mietjmu.in/) at project build time. They are a starting
snapshot only - run `python scrape_miet.py` to refresh/extend the
knowledge base directly from the live website.
"""

import os
import sqlite3
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH", "data/miet_kb.sqlite3")


# ----------------------------------------------------------------------
# Connection helpers
# ----------------------------------------------------------------------
def get_connection() -> sqlite3.Connection:
    """Open a SQLite connection, creating the data folder if needed."""
    folder = os.path.dirname(DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the chunks table if it does not exist yet."""
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                title      TEXT NOT NULL,
                content    TEXT NOT NULL,
                url        TEXT NOT NULL,
                category   TEXT NOT NULL DEFAULT 'general',
                origin     TEXT NOT NULL DEFAULT 'seed',   -- 'seed' or 'scraped'
                scraped_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


# ----------------------------------------------------------------------
# Seed knowledge base (verified snapshot of mietjmu.in homepage content)
# ----------------------------------------------------------------------
SEED_CHUNKS = [
    {
        "title": "About MIET Jammu",
        "category": "about",
        "url": "https://mietjmu.in/",
        "content": (
            "MIET (Model Institute of Engineering and Technology), established in 1999, "
            "is the first private engineering college in Jammu and Kashmir. It is a UGC "
            "approved Autonomous Institution committed to academic excellence, innovation "
            "and research. MIET offers undergraduate, postgraduate and doctoral programs "
            "in Engineering and Technology, Business Administration, Commerce, and Law, "
            "with a cutting-edge curriculum, state-of-the-art infrastructure and industry "
            "collaboration. The institute's motto is 'Future Begins Here'."
        ),
    },
    {
        "title": "Campus location and contact",
        "category": "contact",
        "url": "https://mietjmu.in/",
        "content": (
            "The MIET campus is located at Kot Bhalwal, Jammu, Jammu and Kashmir. "
            "Official phone numbers, email addresses and the admission helpline are "
            "published on the Contact section of the official website mietjmu.in. "
            "For admission queries, students should use the contact details given on "
            "the official website or visit the campus admission office."
        ),
    },
    {
        "title": "Programs offered at MIET",
        "category": "academics",
        "url": "https://mietjmu.in/",
        "content": (
            "MIET Jammu offers undergraduate, postgraduate and doctoral programs across "
            "Engineering and Technology, Business Administration, Commerce, and Law. "
            "Engineering programs include B.Tech degrees such as Computer Science and "
            "Engineering and allied branches. The institute also offers a BA in "
            "Journalism and Mass Communication for careers in broadcasting and digital "
            "media. As a UGC autonomous institution, MIET designs its own industry "
            "aligned curriculum. The exact, up-to-date list of branches and seat "
            "intake is published on the official website mietjmu.in."
        ),
    },
    {
        "title": "Admissions at MIET Jammu",
        "category": "admissions",
        "url": "https://mietjmu.in/",
        "content": (
            "Admissions at MIET Jammu are announced on the official website mietjmu.in. "
            "The current homepage notice states that Freshmen Induction 2026 is now live, "
            "with the induction schedule, classwork details and important updates "
            "available on the website. Prospective students can apply to undergraduate, "
            "postgraduate and doctoral programs in Engineering, Business Administration, "
            "Commerce and Law. Admission eligibility, counselling process and application "
            "forms are published by the college on its official pages and admission office."
        ),
    },
    {
        "title": "Certification programs and fees (CCPE @ MIET)",
        "category": "fees",
        "url": "https://mietjmu.in/",
        "content": (
            "Under CCPE @ MIET, the following industry-aligned certification programs are "
            "currently active, each lasting 6 months, carrying 12 NEP/NCrF-aligned credits "
            "and a program fee of Rs. 40,000: (1) AI and ML Engineering Internship - "
            "hands-on AI/ML training with industry-grade projects; (2) AI Developer "
            "Program - Python, AI APIs, chatbot development and automation; (3) "
            "Cybersecurity Analyst Internship - SOC operations with QRadar and Splunk; "
            "(4) Business Analytics Program - Excel, SQL and Power BI dashboards; (5) "
            "Digital Marketing Program - SEO, Google Ads, Analytics and live campaigns. "
            "All are industry mentored and credit-based certifications."
        ),
    },
    {
        "title": "B.Tech tuition fee structure",
        "category": "fees",
        "url": "https://mietjmu.in/",
        "content": (
            "The detailed semester-wise B.Tech tuition fee structure is published "
            "officially by MIET Jammu through its admission office and official website. "
            "This knowledge base currently contains verified fee information only for "
            "the CCPE certification programs (Rs. 40,000 for 6-month, 12-credit "
            "programs). For exact degree program fees, students should consult the "
            "official fee notification on mietjmu.in or contact the admission office."
        ),
    },
    {
        "title": "Placements and career support",
        "category": "placements",
        "url": "https://mietjmu.in/",
        "content": (
            "MIET focuses on making students industry-ready through skill development, "
            "training and strong industry ties. The institute has a dedicated placement "
            "cell, and graduates are supported with opportunities from top recruiters "
            "to excel in a dynamic job market. The placement cell coordinates campus "
            "recruitment drives, training sessions and industry collaboration "
            "activities. Year-wise placement statistics and recruiter lists are "
            "published on the official website."
        ),
    },
    {
        "title": "Sports and campus facilities",
        "category": "campus",
        "url": "https://mietjmu.in/",
        "content": (
            "MIET encourages physical well-being with a basketball court, cricket nets, "
            "a futsal court and recreational amenities, fostering teamwork and overall "
            "student health. Campus life at MIET includes cultural activities, "
            "technical fests, student clubs and events hosted throughout the year."
        ),
    },
    {
        "title": "Recent events and activities at MIET",
        "category": "events",
        "url": "https://mietjmu.in/",
        "content": (
            "Recent events and activities highlighted by MIET Jammu (@mietjammu) include: "
            "the 1st Justice Dr. Adarsh Sein Anand National Moot Court Competition 2026, "
            "MicroEntrepreneurship Fest and its preliminary round, Programmer's Day "
            "(CodeX), a session on Protect Your Investments covering cyber security, "
            "financial frauds and investor awareness, the Leadership Talk Series, the "
            "Director's Merit List Award Ceremony 2026, an academic visit to the "
            "National Commission for Women, the DICE field visit of PM SHRI Schools, "
            "and the MIET Inspire Series Season 2 featuring Lt Col Narinder Singh Thakur."
        ),
    },
    {
        "title": "Notices: Freshmen Induction 2026",
        "category": "notices",
        "url": "https://mietjmu.in/",
        "content": (
            "IMPORTANT notice on the official MIET website: Freshmen Induction 2026 is "
            "now live. New students can view the induction schedule, classwork details "
            "and important updates on mietjmu.in. The website carries a 'Click here to "
            "view' link for the full induction information."
        ),
    },
    {
        "title": "Journalism and Mass Communication program",
        "category": "academics",
        "url": "https://mietjmu.in/",
        "content": (
            "MIET offers a BA in Journalism and Mass Communication. The program helps "
            "students launch careers in media and journalism, stepping into "
            "broadcasting, digital media and beyond. Details and the Know More link "
            "are available on the official MIET website."
        ),
    },
    {
        "title": "Examinations, timetables and academic calendar",
        "category": "examinations",
        "url": "https://mietjmu.in/",
        "content": (
            "As a UGC approved autonomous institution, MIET Jammu conducts its own "
            "examinations and publishes examination date sheets, timetables and the "
            "academic calendar through official notices on mietjmu.in and on campus "
            "notice boards. This knowledge base stores the notices collected by the "
            "scraper; the latest circulars should always be verified on the official "
            "website. The current homepage highlights the Freshmen Induction 2026 "
            "schedule and classwork details for new students."
        ),
    },
]


def seed_if_empty() -> int:
    """Insert the seed snapshot if the table has no rows. Returns row count."""
    init_db()
    with get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) AS c FROM chunks").fetchone()["c"]
        if count == 0:
            now = datetime.now(timezone.utc).isoformat()
            for item in SEED_CHUNKS:
                conn.execute(
                    "INSERT INTO chunks (title, content, url, category, origin, scraped_at) "
                    "VALUES (?, ?, ?, ?, 'seed', ?)",
                    (item["title"], item["content"], item["url"], item["category"], now),
                )
            conn.commit()
            count = len(SEED_CHUNKS)
    return count


def get_all_chunks() -> list[dict]:
    """Return every chunk as a plain dict (used by the retriever)."""
    init_db()
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT id, title, content, url, category, origin, scraped_at FROM chunks"
        ).fetchall()
    return [dict(r) for r in rows]


def replace_scraped_chunks(chunks: list[dict]) -> int:
    """Delete old scraped rows and insert fresh ones (used by scrape_miet.py)."""
    init_db()
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute("DELETE FROM chunks WHERE origin = 'scraped'")
        for c in chunks:
            conn.execute(
                "INSERT INTO chunks (title, content, url, category, origin, scraped_at) "
                "VALUES (?, ?, ?, ?, 'scraped', ?)",
                (c["title"], c["content"], c["url"], c.get("category", "general"), now),
            )
        conn.commit()
    return len(chunks)


if __name__ == "__main__":
    inserted = seed_if_empty()
    total = len(get_all_chunks())
    print(f"Database ready at {DB_PATH} - {total} chunks (seeded {inserted} this run).")
