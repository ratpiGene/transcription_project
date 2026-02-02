import json
import logging
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.templating import Jinja2Templates
from fastapi import Request
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

from api import db
from api.models import JobListResponse, JobStatus, MetricsResponse, RunRequest
from api.queue import get_queue
from api.settings import (
    ADMIN_PASSWORD,
    ADMIN_USERNAME,
    ALLOWED_EXTENSIONS,
    DEFAULT_MODEL,
)
from api.storage import upload_path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("transcription_api")
security = HTTPBasic()

templates = Jinja2Templates(directory="web/templates")

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


def require_admin(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    if not ADMIN_USERNAME or not ADMIN_PASSWORD:
        raise HTTPException(status_code=500, detail="Admin credentials not configured")
    is_valid = (
        credentials.username == ADMIN_USERNAME
        and credentials.password == ADMIN_PASSWORD
    )
    if not is_valid:
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def log_event(message: str, **payload: str) -> None:
    logger.info(json.dumps({"message": message, **payload}))


@app.on_event("startup")
def startup() -> None:
    db.init_db()


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/admin", response_class=HTMLResponse, dependencies=[Depends(require_admin)])
def admin_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("admin.html", {"request": request})


@app.post("/api/upload")
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
        db.create_job(job_id, file.filename, str(destination), suffix.lstrip("."))
        db.add_event(job_id, "uploaded")
        log_event("job_uploaded", job_id=job_id, filename=file.filename)
        response = JSONResponse({"job_id": job_id})
        track_request("/api/upload", start, response.status_code)
        return response
    except HTTPException as exc:
        track_request("/api/upload", start, exc.status_code)
        raise


def validate_output_type(input_type: str, output_type: str) -> None:
    if input_type == "wav" and output_type in {"embedded_video", "metadata_video"}:
        raise HTTPException(
            status_code=400,
            detail="Sortie vidéo non disponible pour une entrée audio.",
        )


@app.post("/api/jobs/{job_id}/run")
def run_job(job_id: str, payload: RunRequest) -> JSONResponse:
    start = time.time()
    job = db.get_job(job_id)
    if not job:
        track_request("/api/jobs/{job_id}/run", start, 404)
        raise HTTPException(status_code=404, detail="Job introuvable")
    output_type = payload.output_type
    validate_output_type(job["input_type"], output_type)
    model_name = payload.model_name or DEFAULT_MODEL
    queue = get_queue()
    queue.enqueue(
        "worker.tasks.process_job",
        job_id,
        output_type,
        model_name,
    )
    db.update_job(job_id, status="QUEUED", output_type=output_type, model_name=model_name)
    db.add_event(job_id, "queued")
    log_event("job_queued", job_id=job_id, output_type=output_type, model=model_name)
    response = JSONResponse({"job_id": job_id, "status": "QUEUED"})
    track_request("/api/jobs/{job_id}/run", start, response.status_code)
    return response


@app.get("/api/jobs/{job_id}/status", response_model=JobStatus)
def job_status(job_id: str) -> JobStatus:
    start = time.time()
    job = db.get_job(job_id)
    if not job:
        track_request("/api/jobs/{job_id}/status", start, 404)
        raise HTTPException(status_code=404, detail="Job introuvable")
    response = JobStatus(
        job_id=job_id,
        status=job["status"],
        output_type=job.get("output_type"),
        output_path=job.get("output_path"),
        result_text=job.get("result_text"),
        error=job.get("error"),
    )
    track_request("/api/jobs/{job_id}/status", start, 200)
    return response


@app.get("/api/jobs/{job_id}/result")
def job_result(job_id: str):
    start = time.time()
    job = db.get_job(job_id)
    if not job:
        track_request("/api/jobs/{job_id}/result", start, 404)
        raise HTTPException(status_code=404, detail="Job introuvable")
    if job["status"] != "SUCCEEDED":
        track_request("/api/jobs/{job_id}/result", start, 409)
        raise HTTPException(status_code=409, detail="Job non terminé")
    if job.get("output_type") == "text":
        response = JSONResponse({"text": job.get("result_text", "")})
        track_request("/api/jobs/{job_id}/result", start, response.status_code)
        return response
    output_path = job.get("output_path")
    if not output_path or not Path(output_path).exists():
        track_request("/api/jobs/{job_id}/result", start, 404)
        raise HTTPException(status_code=404, detail="Résultat non trouvé")
    response = FileResponse(output_path, filename=Path(output_path).name)
    track_request("/api/jobs/{job_id}/result", start, response.status_code)
    return response


@app.get("/api/jobs/{job_id}/preview", response_class=HTMLResponse)
def job_preview(job_id: str) -> HTMLResponse:
    start = time.time()
    job = db.get_job(job_id)
    if not job:
        track_request("/api/jobs/{job_id}/preview", start, 404)
        raise HTTPException(status_code=404, detail="Job introuvable")
    if job["status"] != "SUCCEEDED":
        track_request("/api/jobs/{job_id}/preview", start, 409)
        raise HTTPException(status_code=409, detail="Job non terminé")
    content = f"<h2>Résultat {job_id}</h2>"
    if job.get("output_type") == "text":
        content += f"<pre>{job.get('result_text', '')}</pre>"
    else:
        content += f"<a href='/api/jobs/{job_id}/result'>Télécharger</a>"
    response = HTMLResponse(content=content)
    track_request("/api/jobs/{job_id}/preview", start, response.status_code)
    return response


@app.get("/api/admin/metrics", response_model=MetricsResponse, dependencies=[Depends(require_admin)])
def admin_metrics() -> JSONResponse:
    start = time.time()
    metrics = db.get_metrics()
    response = JSONResponse(metrics)
    track_request("/api/admin/metrics", start, response.status_code)
    return response


@app.get("/api/admin/jobs", response_model=JobListResponse, dependencies=[Depends(require_admin)])
def admin_jobs(
    status: Optional[str] = Query(None),
    output_type: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> JobListResponse:
    jobs = db.list_jobs(limit=limit, offset=offset, status=status, output_type=output_type)
    items = [
        {
            "id": job["id"],
            "filename": job["filename"],
            "input_type": job["input_type"],
            "output_type": job["output_type"],
            "status": job["status"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
            "duration_seconds": job["duration_seconds"],
        }
        for job in jobs
    ]
    return JobListResponse(items=items, total=len(items))


@app.get("/api/admin/jobs/{job_id}/logs", dependencies=[Depends(require_admin)])
def admin_job_logs(job_id: str) -> JSONResponse:
    logs = db.list_events(job_id)
    return JSONResponse({"job_id": job_id, "events": logs})


@app.get("/metrics")
def prometheus_metrics():
    data = generate_latest()
    return HTMLResponse(content=data, media_type=CONTENT_TYPE_LATEST)
