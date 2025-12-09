from pathlib import Path
from transcription.srt_generator import generate_srt


def test_generate_srt(tmp_path):
    fake_transcription = {
        "chunks": [
            {"timestamp": (0.0, 1.5), "text": "Hello world"},
            {"timestamp": (1.5, 3.0), "text": "How are you"},
        ]
    }

    srt_path = tmp_path / "test.srt"
    generate_srt(fake_transcription, srt_path)

    content = srt_path.read_text()

    assert "1" in content
    assert "00:00:00,000 --> 00:00:01,500" in content
    assert "Hello world" in content

    assert "2" in content
    assert "00:00:01,500 --> 00:00:03,000" in content
    assert "How are you" in content
