import math


def format_time(seconds: float) -> str:
    # Convertit un temps en secondes au format SRT HH:MM:SS,mmm.
    hours = math.floor(seconds / 3600)
    seconds %= 3600

    minutes = math.floor(seconds / 60)
    seconds %= 60

    milliseconds = round((seconds - math.floor(seconds)) * 1000)
    seconds = math.floor(seconds)

    return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
