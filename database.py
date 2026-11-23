
"""
SQLite knowledge base for the MIET Jammu chatbot.
Stores verified information collected from the official MIET website.
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

        conn.execute(
            "DELETE FROM chunks WHERE origin = 'seed'"
        )


def seed_if_empty():
    init_db()

    with get_connection() as conn:
        count = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE origin = 'scraped'"
        ).fetchone()[0]

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
    Replace existing scraped information only when valid new
    information is available. Existing data is preserved if
    scraping produces no valid records.
    """

    init_db()

    valid_chunks = []

    for chunk in chunks:
        title = str(
            chunk.get("title", "MIET Website Information")
        ).strip()

        content = str(
            chunk.get("content", "")
        ).strip()

        url = str(
            chunk.get("url", "")
        ).strip()

        category = str(
            chunk.get("category", "general")
        ).strip()

        if not content or not url:
            continue

        if not url.startswith("https://mietjmu.in/"):
            continue

        valid_chunks.append({
            "title": title,
            "content": content,
            "url": url,
            "category": category
        })

    if not valid_chunks:
        print("No valid new information. Existing data preserved.")
        return len(get_all_chunks())

    now = datetime.now(timezone.utc).isoformat()

    with get_connection() as conn:

        conn.execute(
            "DELETE FROM chunks WHERE origin = 'scraped'"
        )

        for chunk in valid_chunks:
            conn.execute("""
                INSERT INTO chunks
                (title, content, url, category, origin, scraped_at)
                VALUES (?, ?, ?, ?, 'scraped', ?)
            """, (
                chunk["title"],
                chunk["content"],
                chunk["url"],
                chunk["category"],
                now
            ))

        total = conn.execute(
            "SELECT COUNT(*) FROM chunks WHERE origin = 'scraped'"
        ).fetchone()[0]

    print("Knowledge base updated:", total, "chunks")

    return total


if __name__ == "__main__":
    init_db()

    chunks = get_all_chunks()

    print("MIET database initialized.")
    print("Database location:", DB_PATH)
    print("Stored chunks:", len(chunks))
