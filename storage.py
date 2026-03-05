"""
SQLite-backed storage for tracking seen jobs across runs.
Uses a simple table keyed by a stable job ID (URL or external ID).
"""
import sqlite3
import hashlib
from pathlib import Path

DB_PATH = Path(__file__).parent / "seen_jobs.db"


def _conn():
    con = sqlite3.connect(DB_PATH)
    con.execute(
        "CREATE TABLE IF NOT EXISTS seen_jobs (job_id TEXT PRIMARY KEY, first_seen TEXT DEFAULT CURRENT_TIMESTAMP)"
    )
    con.commit()
    return con


def is_seen(job_id: str) -> bool:
    with _conn() as con:
        row = con.execute("SELECT 1 FROM seen_jobs WHERE job_id = ?", (job_id,)).fetchone()
        return row is not None


def mark_seen(job_id: str) -> None:
    with _conn() as con:
        con.execute("INSERT OR IGNORE INTO seen_jobs (job_id) VALUES (?)", (job_id,))
        con.commit()


def make_id(url: str, title: str = "") -> str:
    """Stable ID from URL (+ title fallback)."""
    raw = url.strip() or title.strip()
    return hashlib.sha1(raw.encode()).hexdigest()
