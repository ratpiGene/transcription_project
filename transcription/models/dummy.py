from pathlib import Path
from transcription.models.base import BaseTranscriptionModel


class DummyModel(BaseTranscriptionModel):
    name = "dummy"

    def transcribe(self, audio_path: Path):
        return {
            "text": "Transcription factice pour tests.",
            "chunks": [
                {
                    "timestamp": (0.0, 1.0),
                    "text": "Transcription factice pour tests.",
                }
            ],
        }
