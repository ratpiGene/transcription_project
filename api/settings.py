from pathlib import Path
import os

BASE_DIR = Path(os.getenv("APP_BASE_DIR", Path.cwd()))
STORAGE_DIR = BASE_DIR / "storage"
UPLOAD_DIR = STORAGE_DIR / "uploads"
RESULT_DIR = STORAGE_DIR / "results"

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://subtitle:subtitle@postgres:5432/subtitle",
)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
DEFAULT_MODEL = os.getenv("TRANSCRIPTION_MODEL", "whisper")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

INFERENCE_URL = os.getenv("INFERENCE_URL", "http://inference:9000")

ALLOWED_EXTENSIONS = {".mp4", ".wav"}
