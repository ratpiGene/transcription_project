from transcription.utils import format_time


def test_format_time_exact_seconds():
    assert format_time(62) == "00:01:02,000"


def test_format_time_with_milliseconds():
    assert format_time(62.345) == "00:01:02,345"


def test_format_time_large_value():
    assert format_time(3723.12) == "01:02:03,120"
