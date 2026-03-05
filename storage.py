"""
SQLite-backed storage for tracking seen jobs and run stats across runs.
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
    con.execute(
        """CREATE TABLE IF NOT EXISTS run_stats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ran_at TEXT DEFAULT CURRENT_TIMESTAMP,
            new_jobs INTEGER,
            matched_jobs INTEGER
        )"""
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


def log_run(new_jobs: int, matched_jobs: int) -> None:
    with _conn() as con:
        con.execute(
            "INSERT INTO run_stats (new_jobs, matched_jobs) VALUES (?, ?)",
            (new_jobs, matched_jobs),
        )
        con.commit()


def get_stats_last_24h() -> dict:
    """Return aggregated stats from the last 24 hours."""
    with _conn() as con:
        row = con.execute(
            """SELECT COUNT(*), COALESCE(SUM(new_jobs), 0), COALESCE(SUM(matched_jobs), 0)
               FROM run_stats
               WHERE ran_at >= datetime('now', '-24 hours')"""
        ).fetchone()
    runs, new_jobs, matched_jobs = row if row else (0, 0, 0)
    return {"runs": runs, "new_jobs": new_jobs, "matched_jobs": matched_jobs}


def make_id(url: str, title: str = "") -> str:
    """Stable ID from URL (+ title fallback)."""
    raw = url.strip() or title.strip()
    return hashlib.sha1(raw.encode()).hexdigest()
