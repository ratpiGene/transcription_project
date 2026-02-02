import logging
import time
import uuid
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from api import db
from api.models import RunRequest, JobStatus
from api.queue import get_queue
from api.settings import ALLOWED_EXTENSIONS, DEFAULT_MODEL
from api.storage import upload_path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("transcription_api")

app = FastAPI(title="Subtitle Application")

REQUEST_COUNT = Counter(
    "api_requests_total", "Total API requests", ["endpoint", "status"]
)
REQUEST_LATENCY = Histogram(
    "api_request_latency_seconds", "API request latency", ["endpoint"]
)


def track_request(endpoint: str, start: float, status_code: int) -> None:
    REQUEST_COUNT.labels(endpoint=endpoint, status=str(status_code)).inc()
    REQUEST_LATENCY.labels(endpoint=endpoint).observe(time.time() - start)


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.post("/upload")
async def upload(file: UploadFile = File(...)) -> JSONResponse:
    start = time.time()
    try:
        suffix = Path(file.filename).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise HTTPException(status_code=400, detail="Format de fichier non supporté")
        job_id = str(uuid.uuid4())
        destination = upload_path(job_id, file.filename)
        with destination.open("wb") as buffer:
            buffer.write(await file.read())
        db.create_job(job_id, file.filename, str(destination))
        db.add_event(job_id, "uploaded")
        response = JSONResponse({"job_id": job_id})
        track_request("/upload", start, response.status_code)
        return response
    except HTTPException as exc:
        track_request("/upload", start, exc.status_code)
        raise


@app.post("/jobs/{job_id}/run")
def run_job(job_id: str, payload: RunRequest) -> JSONResponse:
    start = time.time()
    job = db.get_job(job_id)
    if not job:
        track_request("/jobs/{job_id}/run", start, 404)
        raise HTTPException(status_code=404, detail="Job introuvable")
    output_type = payload.output_type
    model_name = payload.model_name or DEFAULT_MODEL
    queue = get_queue()
    queue.enqueue("worker.tasks.process_job", job_id, output_type, model_name)
    db.update_job(job_id, status="queued", output_type=output_type, model_name=model_name)
    db.add_event(job_id, "queued")
    response = JSONResponse({"job_id": job_id, "status": "queued"})
    track_request("/jobs/{job_id}/run", start, response.status_code)
    return response


@app.get("/jobs/{job_id}/status", response_model=JobStatus)
def job_status(job_id: str) -> JobStatus:
    start = time.time()
    job = db.get_job(job_id)
    if not job:
        track_request("/jobs/{job_id}/status", start, 404)
        raise HTTPException(status_code=404, detail="Job introuvable")
    response = JobStatus(
        job_id=job_id,
        status=job["status"],
        output_type=job.get("output_type"),
        output_path=job.get("output_path"),
        result_text=job.get("result_text"),
        error=job.get("error"),
    )
    track_request("/jobs/{job_id}/status", start, 200)
    return response


@app.get("/jobs/{job_id}/result")
def job_result(job_id: str):
    start = time.time()
    job = db.get_job(job_id)
    if not job:
        track_request("/jobs/{job_id}/result", start, 404)
        raise HTTPException(status_code=404, detail="Job introuvable")
    if job["status"] != "completed":
        track_request("/jobs/{job_id}/result", start, 409)
        raise HTTPException(status_code=409, detail="Job non terminé")
    if job.get("output_type") == "text":
        response = JSONResponse({"text": job.get("result_text", "")})
        track_request("/jobs/{job_id}/result", start, response.status_code)
        return response
    output_path = job.get("output_path")
    if not output_path or not Path(output_path).exists():
        track_request("/jobs/{job_id}/result", start, 404)
        raise HTTPException(status_code=404, detail="Résultat non trouvé")
    response = FileResponse(output_path, filename=Path(output_path).name)
    track_request("/jobs/{job_id}/result", start, response.status_code)
    return response


@app.get("/jobs/{job_id}/preview", response_class=HTMLResponse)
def job_preview(job_id: str) -> HTMLResponse:
    start = time.time()
    job = db.get_job(job_id)
    if not job:
        track_request("/jobs/{job_id}/preview", start, 404)
        raise HTTPException(status_code=404, detail="Job introuvable")
    if job["status"] != "completed":
        track_request("/jobs/{job_id}/preview", start, 409)
        raise HTTPException(status_code=409, detail="Job non terminé")
    content = f"<h2>Résultat {job_id}</h2>"
    if job.get("output_type") == "text":
        content += f"<pre>{job.get('result_text', '')}</pre>"
    else:
        content += f"<a href='/jobs/{job_id}/result'>Télécharger</a>"
    response = HTMLResponse(content=content)
    track_request("/jobs/{job_id}/preview", start, response.status_code)
    return response


@app.get("/admin/metrics")
def admin_metrics() -> JSONResponse:
    start = time.time()
    metrics = db.get_metrics()
    response = JSONResponse(metrics)
    track_request("/admin/metrics", start, response.status_code)
    return response


@app.get("/metrics")
def prometheus_metrics():
    data = generate_latest()
    return HTMLResponse(content=data, media_type=CONTENT_TYPE_LATEST)
