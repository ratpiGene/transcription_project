from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any


class BaseTranscriptionModel(ABC):
    name: str

    @abstractmethod
    def transcribe(self, audio_path: Path) -> Dict[str, Any]:
        raise NotImplementedError
