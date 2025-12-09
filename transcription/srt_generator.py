from pathlib import Path
from .utils import format_time
from .whisper_engine import CHUNK_LENGTH


def generate_srt(transcription: dict, srt_path: Path) -> None:
    # Conversion de la transcription Whisper en fichier SRT
    lines = []
    offset = 0

    for index, chunk in enumerate(transcription["chunks"]):
        start, end = chunk["timestamp"]

        if start > end:  # gestion cas anormal
            offset += CHUNK_LENGTH
            continue

        start += offset
        end += offset

        start_str = format_time(start)
        end_str = format_time(end)

        lines.append(str(index + 1))
        lines.append(f"{start_str} --> {end_str}")
        lines.append(chunk["text"].strip())
        lines.append("")

    srt_path.write_text("\n".join(lines), encoding="utf-8")
