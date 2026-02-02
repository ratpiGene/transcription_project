import importlib
from fastapi.testclient import TestClient


def test_upload_and_status(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_BASE_DIR", str(tmp_path))
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    from api import settings

    importlib.reload(settings)
    from api import app as app_module

    importlib.reload(app_module)

    class DummyQueue:
        def enqueue(self, *args, **kwargs):
            return None

    monkeypatch.setattr(app_module, "get_queue", lambda: DummyQueue())

    client = TestClient(app_module.app)

    file_content = b"RIFF....WAVEfmt "
    response = client.post(
        "/upload",
        files={"file": ("sample.wav", file_content, "audio/wav")},
    )
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    status = client.get(f"/jobs/{job_id}/status")
    assert status.status_code == 200
    assert status.json()["status"] == "uploaded"
