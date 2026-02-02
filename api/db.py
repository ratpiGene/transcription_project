import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from api.settings import DB_PATH


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                filename TEXT NOT NULL,
                input_path TEXT NOT NULL,
                output_type TEXT,
                output_path TEXT,
                result_text TEXT,
                status TEXT NOT NULL,
                error TEXT,
                model_name TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                duration_seconds REAL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS job_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                event TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()


def _now() -> str:
    return datetime.utcnow().isoformat()


def create_job(job_id: str, filename: str, input_path: str) -> None:
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO jobs (id, filename, input_path, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (job_id, filename, input_path, "uploaded", _now(), _now()),
        )
        conn.commit()


def update_job(job_id: str, **fields: Any) -> None:
    if not fields:
        return
    fields["updated_at"] = _now()
    columns = ", ".join([f"{key} = ?" for key in fields.keys()])
    values = list(fields.values())
    with _connect() as conn:
        conn.execute(
            f"UPDATE jobs SET {columns} WHERE id = ?",
            (*values, job_id),
        )
        conn.commit()


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    with _connect() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    return dict(row) if row else None


def list_jobs(limit: int = 50) -> List[Dict[str, Any]]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(row) for row in rows]


def add_event(job_id: str, event: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO job_events (job_id, event, created_at) VALUES (?, ?, ?)",
            (job_id, event, _now()),
        )
        conn.commit()


def get_metrics() -> Dict[str, Any]:
    with _connect() as conn:
        total = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        avg_duration = conn.execute(
            "SELECT AVG(duration_seconds) FROM jobs WHERE duration_seconds IS NOT NULL"
        ).fetchone()[0]
        by_type = conn.execute(
            "SELECT output_type, COUNT(*) as count FROM jobs GROUP BY output_type"
        ).fetchall()
        by_status = conn.execute(
            "SELECT status, COUNT(*) as count FROM jobs GROUP BY status"
        ).fetchall()
        failed_by_type = conn.execute(
            "SELECT output_type, COUNT(*) as count FROM jobs WHERE status = 'failed' GROUP BY output_type"
        ).fetchall()
        pending_by_type = conn.execute(
            "SELECT output_type, COUNT(*) as count FROM jobs WHERE status IN ('queued', 'processing') GROUP BY output_type"
        ).fetchall()

    return {
        "total_jobs": total,
        "average_duration_seconds": avg_duration or 0.0,
        "by_type": {row[0] or "unknown": row[1] for row in by_type},
        "by_status": {row[0]: row[1] for row in by_status},
        "failed_by_type": {row[0] or "unknown": row[1] for row in failed_by_type},
        "pending_by_type": {row[0] or "unknown": row[1] for row in pending_by_type},
        "pending_total": sum(row[1] for row in pending_by_type),
        "failed_total": sum(row[1] for row in failed_by_type),
        "recent_responses": list_jobs(limit=20),
    }
