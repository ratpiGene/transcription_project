from pathlib import Path
import torch
from transformers import pipeline

CHUNK_LENGTH = 28
MODEL_NAME = "openai/whisper-medium.en"
DEVICE = "cuda:0"


def load_whisper_model():
    # Chargement sur GPU si disponible
    return pipeline(
        "automatic-speech-recognition",
        MODEL_NAME,
        torch_dtype=torch.float16,
        device=DEVICE
    )


def transcribe_audio(audio_path: Path, model):
    # Transcription avec Whisper
    return model(
        str(audio_path),
        chunk_length_s=CHUNK_LENGTH,
        return_timestamps=True
    )
