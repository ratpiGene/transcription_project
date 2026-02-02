import importlib
import json

import httpx

from api import db
from api.storage import upload_path
from worker.tasks import process_job


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class DummyClient:
    def __init__(self, payload):
        self._payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, *args, **kwargs):
        return DummyResponse(self._payload)


def test_process_job_dummy(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")

    from api import settings

    importlib.reload(settings)
    importlib.reload(db)

    db.init_db()

    job_id = "job-test"
    wav_path = upload_path(job_id, "sample.wav")
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    wav_path.write_bytes(b"RIFF....WAVEfmt ")

    db.create_job(job_id, "sample.wav", str(wav_path), "wav")

    dummy_payload = {
        "text": "Transcription factice",
        "chunks": [{"timestamp": (0.0, 1.0), "text": "Bonjour"}],
    }
    monkeypatch.setattr(httpx, "Client", lambda timeout=300.0: DummyClient(dummy_payload))

    process_job(job_id, "text", "dummy")

    job = db.get_job(job_id)
    assert job["status"] == "SUCCEEDED"
    assert job["result_text"]
