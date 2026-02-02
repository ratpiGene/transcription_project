import logging
import time
from pathlib import Path

from api import db
from api.storage import result_path
from transcription.audio import extract_audio
from transcription.srt_generator import generate_srt
from transcription.video_renderer import render_video
from transcription.models.registry import load_model

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("transcription_worker")


def process_job(job_id: str, output_type: str, model_name: str) -> None:
    job = db.get_job(job_id)
    if not job:
        logger.error("Job introuvable", extra={"job_id": job_id})
        return

    start_time = time.time()
    db.update_job(job_id, status="processing")
    db.add_event(job_id, "processing")

    try:
        input_path = Path(job["input_path"])
        base_name = input_path.stem
        audio_path = result_path(job_id, "wav")
        srt_path = result_path(job_id, "srt")
        video_path = result_path(job_id, "mp4")

        if input_path.suffix.lower() == ".mp4":
            extract_audio(input_path, audio_path)
        else:
            audio_path = input_path

        model = load_model(model_name)
        transcription = model.transcribe(audio_path)
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
            status="completed",
            output_path=output_path,
            result_text=result_text,
            duration_seconds=duration,
        )
        db.add_event(job_id, "completed")
    except Exception as exc:
        duration = time.time() - start_time
        db.update_job(job_id, status="failed", error=str(exc), duration_seconds=duration)
        db.add_event(job_id, "failed")
        logger.exception("Erreur traitement job", extra={"job_id": job_id})
