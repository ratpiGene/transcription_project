from pathlib import Path
from transcription import (
    extract_audio,
    load_whisper_model,
    transcribe_audio,
    generate_srt,
    render_video,
)


def main(input_file: str) -> None:
    input_path = Path(input_file)
    audio_path = Path(f"audio-{input_path.stem}.wav")
    srt_path = Path(f"sub-{input_path.stem}.en.srt")
    output_path = Path("output.mp4")

    print("Chargement du modèle…")
    model = load_whisper_model()

    print("Extraction audio…")
    extract_audio(input_path, audio_path)

    print("Transcription…")
    transcription = transcribe_audio(audio_path, model)

    print("Génération SRT…")
    generate_srt(transcription, srt_path)

    print("Création de la vidéo…")
    render_video(input_path, srt_path, output_path, embedded=False)

    print("\nTranscription :")
    print(transcription["text"])


if __name__ == "__main__":
    main("input.mp4")
