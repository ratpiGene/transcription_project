from pathlib import Path
import ffmpeg


def extract_audio(input_path: Path, output_path: Path) -> None:
    # extrait l'audio d'une vidéo et le save en wav
    stream = ffmpeg.input(str(input_path))
    stream = ffmpeg.output(stream, str(output_path))
    ffmpeg.run(stream, overwrite_output=True)