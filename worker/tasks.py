import json
import logging
import os
import time
from pathlib import Path

import httpx

from api import db
from api.storage import result_path
from transcription.audio import extract_audio
from transcription.srt_generator import generate_srt
from transcription.video_renderer import render_video

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("transcription_worker")

INFERENCE_URL = os.getenv("INFERENCE_URL", "http://inference:9000")


def log_event(message: str, **payload: str) -> None:
    logger.info(json.dumps({"message": message, **payload}))


def run_inference(audio_path: Path, model_name: str) -> dict:
    with httpx.Client(timeout=300.0) as client:
        with audio_path.open("rb") as audio_file:
            files = {"file": (audio_path.name, audio_file, "audio/wav")}
            response = client.post(
                f"{INFERENCE_URL}/infer",
                data={"model_name": model_name},
                files=files,
            )
            response.raise_for_status()
            return response.json()


def process_job(job_id: str, output_type: str, model_name: str) -> None:
    job = db.get_job(job_id)
    if not job:
        log_event("job_missing", job_id=job_id)
        return

    start_time = time.time()
    db.update_job(job_id, status="RUNNING")
    db.add_event(job_id, "running")
    log_event("job_running", job_id=job_id, output_type=output_type)

    try:
        input_path = Path(job["input_path"])
        audio_path = result_path(job_id, "wav")
        srt_path = result_path(job_id, "srt")
        video_path = result_path(job_id, "mp4")

        if input_path.suffix.lower() == ".mp4":
            extract_audio(input_path, audio_path)
        else:
            audio_path = input_path

        transcription = run_inference(audio_path, model_name)
        generate_srt(transcription, srt_path)

        output_path = None
        result_text = transcription.get("text")

        if output_type == "embedded_video":
            render_video(input_path, srt_path, video_path, embedded=True)
            output_path = str(video_path)
        elif output_type == "metadata_video":
            render_video(input_path, srt_path, video_path, embedded=False)
            output_path = str(video_path)
        elif output_type == "subtitle":
            output_path = str(srt_path)
        elif output_type == "text":
            output_path = None
        else:
            raise ValueError("Type de sortie inconnu")

        duration = time.time() - start_time
        db.update_job(
            job_id,
            status="SUCCEEDED",
            output_path=output_path,
            result_text=result_text,
            duration_seconds=duration,
        )
        db.add_event(job_id, "succeeded")
        log_event("job_succeeded", job_id=job_id, duration_seconds=str(duration))
    except Exception as exc:
        duration = time.time() - start_time
        db.update_job(job_id, status="FAILED", error=str(exc), duration_seconds=duration)
        db.add_event(job_id, "failed")
        log_event("job_failed", job_id=job_id, error=str(exc))
        logger.exception("Erreur traitement job", extra={"job_id": job_id})
