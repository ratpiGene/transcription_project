from unittest.mock import patch
from pathlib import Path
from transcription.whisper_engine import load_whisper_model, transcribe_audio


def test_load_whisper_model():
    # On ne teste pas en profondeur, juste que ça renvoie quelque chose
    model = load_whisper_model()
    assert model is not None


@patch("transcription.whisper_engine.pipeline")
def test_transcribe_audio(mock_pipeline):
    mock_model = lambda *args, **kwargs: {"text": "ok"}
    audio_path = Path("audio.wav")

    result = transcribe_audio(audio_path, mock_model)

    assert "text" in result
