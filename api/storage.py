from pathlib import Path
from api.settings import UPLOAD_DIR, RESULT_DIR


def ensure_dirs() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    RESULT_DIR.mkdir(parents=True, exist_ok=True)


def upload_path(job_id: str, filename: str) -> Path:
    ensure_dirs()
    return UPLOAD_DIR / f"{job_id}_{filename}"


def result_path(job_id: str, suffix: str) -> Path:
    ensure_dirs()
    return RESULT_DIR / f"{job_id}.{suffix}"
