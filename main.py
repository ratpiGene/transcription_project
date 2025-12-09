from pathlib import Path
from transcription import (
    extract_audio,
    load_whisper_model,
    transcribe_audio,
    generate_srt,
    render_video,
)


def main(input_file: str) -> None:
    # Vars
    input_path = Path(input_file)
    base_name = input_path.stem  # ex: "input"
    audio_dir = Path("output_audio")
    subs_dir = Path("output_sub")
    video_dir = Path("output_video")

    # Checks
    audio_dir.mkdir(exist_ok=True)
    subs_dir.mkdir(exist_ok=True)
    video_dir.mkdir(exist_ok=True)

    # Output
    audio_path = audio_dir / f"{base_name}.wav"
    srt_path = subs_dir / f"{base_name}.en.srt"
    output_path = video_dir / f"{base_name}_subtitled.mp4"

    # Pipeline
    print("Chargement du modèle…")
    model = load_whisper_model()

    print(f"Extraction audio → {audio_path}")
    extract_audio(input_path, audio_path)

    print(f"Transcription → {srt_path}")
    transcription = transcribe_audio(audio_path, model)

    print("Génération SRT…")
    generate_srt(transcription, srt_path)

    print(f"Création de la vidéo → {output_path}")
    render_video(input_path, srt_path, output_path, embedded=False)

    # Prints cmd
    print("\nTranscription :")
    print(transcription["text"])


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage : python main.py <chemin_fichier_video>")
        sys.exit(1)

    input_file = sys.argv[1]
    main(input_file)
