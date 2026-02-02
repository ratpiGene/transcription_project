from typing import Dict, Tuple, Type

from transcription.models.base import BaseTranscriptionModel
from transcription.models.dummy import DummyModel
from transcription.models.whisper_model import WhisperModel

ModelKey = Tuple[str, str]

_REGISTRY: Dict[ModelKey, Type[BaseTranscriptionModel]] = {
    (WhisperModel.name, "v1"): WhisperModel,
    (DummyModel.name, "v1"): DummyModel,
}

_model_cache: Dict[ModelKey, BaseTranscriptionModel] = {}


def load_model(name: str, version: str = "v1") -> BaseTranscriptionModel:
    key = (name, version)
    model_class = _REGISTRY.get(key)
    if not model_class:
        raise ValueError(f"Modèle inconnu: {name}:{version}")
    if key not in _model_cache:
        _model_cache[key] = model_class()
    return _model_cache[key]
