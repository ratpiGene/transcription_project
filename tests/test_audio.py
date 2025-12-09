from unittest.mock import patch
from pathlib import Path
from transcription.audio import extract_audio


@patch("ffmpeg.run")
@patch("ffmpeg.output")
@patch("ffmpeg.input")
def test_extract_audio(mock_input, mock_output, mock_run):
    input_path = Path("video.mp4")
    output_path = Path("audio.wav")

    extract_audio(input_path, output_path)

    mock_input.assert_called_once_with(str(input_path))
    mock_output.assert_called_once()
    mock_run.assert_called_once()
