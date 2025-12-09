from pathlib import Path
import ffmpeg


def render_video(input_video: Path, srt_path: Path, output_path: Path, embedded: bool = False) -> None:
    # Génération de la vidéo finale avec soft-sub ou hard-sub

    video_stream = ffmpeg.input(str(input_video))

    if not embedded:
        subtitle_stream = ffmpeg.input(str(srt_path))

        stream = ffmpeg.output(
            video_stream,
            subtitle_stream,
            str(output_path),
            **{"c": "copy", "c:s": "mov_text"},
            **{
                "metadata:s:s:0": "language=en",
                "metadata:s:s:1": f"title={srt_path.stem}",
            }
        )

    else:
        stream = ffmpeg.output(
            video_stream,
            str(output_path),
            vf=f"subtitles={str(srt_path)}"
        )

    ffmpeg.run(stream, overwrite_output=True)
