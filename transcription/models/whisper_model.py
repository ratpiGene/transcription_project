from pathlib import Path
import torch
from transformers import pipeline

from transcription.models.base import BaseTranscriptionModel


class WhisperModel(BaseTranscriptionModel):
    name = "whisper"

    def __init__(self) -> None:
        device = 0 if torch.cuda.is_available() else -1
        dtype = torch.float16 if torch.cuda.is_available() else torch.float32
        self._model = pipeline(
            "automatic-speech-recognition",
            "openai/whisper-medium.en",
            torch_dtype=dtype,
            device=device,
        )

    def transcribe(self, audio_path: Path):
        return self._model(
            str(audio_path),
            chunk_length_s=28,
            return_timestamps=True,
        )
