import logging
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile, Form
from fastapi.responses import JSONResponse

from inference.registry import load_model

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("inference_server")

app = FastAPI(title="Inference Server")


@app.get("/health")
def health() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.post("/infer")
def infer(
    file: UploadFile = File(...),
    model_name: str = Form("whisper"),
    model_version: str = Form("v1"),
):
    suffix = Path(file.filename).suffix.lower()
    if suffix not in {".wav"}:
        raise HTTPException(status_code=400, detail="Seuls les fichiers wav sont acceptés")
    audio_path = Path("/tmp") / file.filename
    with audio_path.open("wb") as buffer:
        buffer.write(file.file.read())
    model = load_model(model_name, model_version)
    transcription = model.transcribe(audio_path)
    return JSONResponse(transcription)
