from typing import Dict, Type

from transcription.models.base import BaseTranscriptionModel
from transcription.models.whisper_model import WhisperModel
from transcription.models.dummy import DummyModel


_REGISTRY: Dict[str, Type[BaseTranscriptionModel]] = {
    WhisperModel.name: WhisperModel,
    DummyModel.name: DummyModel,
}


def load_model(name: str) -> BaseTranscriptionModel:
    model_class = _REGISTRY.get(name)
    if not model_class:
        raise ValueError(f"Modèle inconnu: {name}")
    return model_class()
