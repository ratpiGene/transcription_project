import importlib
import wave

from api import db
from api.storage import upload_path
from worker.tasks import process_job


def test_process_job_dummy(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_BASE_DIR", str(tmp_path))
    from api import settings

    importlib.reload(settings)
    importlib.reload(db)

    db.init_db()

    job_id = "job-test"
    wav_path = upload_path(job_id, "sample.wav")
    wav_path.parent.mkdir(parents=True, exist_ok=True)

    with wave.open(str(wav_path), "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        wav_file.writeframes(b"\x00\x00" * 16000)

    db.create_job(job_id, "sample.wav", str(wav_path))

    process_job(job_id, "text", "dummy")

    job = db.get_job(job_id)
    assert job["status"] == "completed"
    assert job["result_text"]
