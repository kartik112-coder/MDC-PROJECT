
"""
SQLite knowledge base for the MIET Jammu chatbot.
Stores information collected from the official MIET website.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

DB_PATH = os.getenv("DATABASE_PATH", "data/miet_kb.sqlite3")


@contextmanager
def get_connection():
    folder = os.path.dirname(DB_PATH)

    if folder:
        os.makedirs(folder, exist_ok=True)

    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row

    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chunks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                url TEXT NOT NULL,
                category TEXT NOT NULL DEFAULT 'general',
                origin TEXT NOT NULL DEFAULT 'scraped',
                scraped_at TEXT NOT NULL
            )
        """)

        # Remove old unverified seed information.
        conn.execute(
            "DELETE FROM chunks WHERE origin = 'seed'"
        )


def seed_if_empty():
    """
    Compatibility function for the existing RAG code.

    Old seed information is no longer automatically inserted.
    Only scraped website information is used.
    """
    init_db()

    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS c FROM chunks"
        ).fetchone()["c"]

    return count


def get_all_chunks():
    init_db()

    with get_connection() as conn:
        rows = conn.execute("""
            SELECT id, title, content, url, category, origin, scraped_at
            FROM chunks
            WHERE origin = 'scraped'
            ORDER BY id
        """).fetchall()

    return [dict(row) for row in rows]


def replace_scraped_chunks(chunks):
    """
    Replace old scraped information with newly collected information.

    If scraping returns no results, keep the previous data instead
    of accidentally deleting the entire knowledge base.
    """

    init_db()

    if not chunks:
        print("No new scraped data received. Existing data preserved.")

        with get_connection() as conn:
            return conn.execute(
                "SELECT COUNT(*) FROM chunks WHERE origin = 'scraped'"
            ).fetchone()[0]

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:

        conn.execute(
            "DELETE FROM chunks WHERE origin = 'scraped'"
        )

        for chunk in chunks:

            title = str(chunk.get("title", "MIET Website Information"))
            content = str(chunk.get("content", "")).strip()
            url = str(chunk.get("url", "")).strip()
            category = str(chunk.get("category", "general"))

            if not content or not url:
                continue

            conn.execute("""
                INSERT INTO chunks
                (title, content, url, category, origin, scraped_at)
                VALUES (?, ?, ?, ?, 'scraped', ?)
            """, (
                title,
                content,
                url,
                category,
                now
            ))

        total = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE origin = 'scraped'"
        ).fetchone()[0]

    return total


if __name__ == "__main__":

    init_db()

    total = len(get_all_chunks())

    print("MIET database initialized successfully.")
    print(f"Database location: {DB_PATH}")
    print(f"Scraped information records: {total}")

    if total == 0:
        print("No scraped information found.")
        print("Run python scrape_miet.py to collect website information.")
