from pathlib import Path
import os

BASE_DIR = Path(os.getenv("APP_BASE_DIR", Path.cwd()))
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
RESULT_DIR = STORAGE_DIR / "results"
DB_PATH = STORAGE_DIR / "jobs.db"

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DEFAULT_MODEL = os.getenv("TRANSCRIPTION_MODEL", "whisper")

ALLOWED_EXTENSIONS = {".mp4", ".wav"}
