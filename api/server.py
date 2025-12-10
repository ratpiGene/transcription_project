from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from pathlib import Path
import shutil
from transcription import (
    extract_audio,
    load_whisper_model,
    transcribe_audio,
    generate_srt,
    render_video,
)

app = FastAPI()
templates = Jinja2Templates(directory="web/templates")

MODEL = load_whisper_model()


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/transcribe")
async def transcribe_endpoint(
    request: Request,
    file: UploadFile,
    output_type: str = Form(...)
):
    # 1. Sauvegarde temporaire
    input_path = Path("temp_input") / file.filename
    input_path.parent.mkdir(exist_ok=True)
    
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    base_name = input_path.stem
    outputs = {}

    # 2. Pipeline commun
    audio_path = Path("output_audio") / f"{base_name}.wav"
    srt_path = Path("output_sub") / f"{base_name}.srt"
    video_path = Path("output_video") / f"{base_name}_subtitled.mp4"

    extract_audio(input_path, audio_path)
    transcription = transcribe_audio(audio_path, MODEL)
    generate_srt(transcription, srt_path)

    # 3. Selon output demandé
    if output_type == "embedded_video":
        render_video(input_path, srt_path, video_path, embedded=True)
        return FileResponse(path=video_path, filename=video_path.name, media_type="video/mp4")

    elif output_type == "metadata_video":
        render_video(input_path, srt_path, video_path, embedded=False)
        return FileResponse(path=video_path, filename=video_path.name, media_type="video/mp4")

    elif output_type == "subtitle":
        return FileResponse(path=srt_path, filename=srt_path.name, media_type="text/srt")

    elif output_type == "text":
        return {"text": transcription["text"]}

    return {"error": "Type de sortie inconnu"}
