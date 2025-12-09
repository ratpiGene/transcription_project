from pathlib import Path
# mocking des appels ffmpeg
from unittest.mock import patch
from transcription.video_renderer import render_video

@patch("ffmpeg.run")
@patch("ffmpeg.output")
@patch("ffmpeg.input")
def test_render_video_soft(mock_input, mock_output, mock_run):
    render_video(Path("video.mp4"), Path("subs.srt"), Path("out.mp4"), embedded=False)

    assert mock_input.called
    assert mock_output.called
    assert mock_run.called


@patch("ffmpeg.run")
@patch("ffmpeg.output")
@patch("ffmpeg.input")
def test_render_video_hard(mock_input, mock_output, mock_run):
    render_video(Path("video.mp4"), Path("subs.srt"), Path("out.mp4"), embedded=True)

    assert mock_input.called
    assert mock_output.called
    assert mock_run.called
