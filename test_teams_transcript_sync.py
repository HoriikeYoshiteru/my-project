import datetime as dt
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from teams_transcript_sync import JST, LocalDest, place  # noqa: E402


def d(y, m, dd, h=0, mi=0):
    return dt.datetime(y, m, dd, h, mi, tzinfo=JST)


def test_weekly_first_half():
    p = place(d(2026, 9, 7, 13))
    assert p.rel_dir == "2026/01_週次定例/20260907_中国TSUチーム定例会/00_transcript"
    assert p.filename == "20260907_1300_前半.vtt"
    assert p.extra_dirs[0].endswith("10_議事録")


def test_weekly_second_half():
    assert place(d(2026, 9, 7, 17)).filename == "20260907_1700_後半.vtt"


def test_daily():
    p = place(d(2026, 9, 8, 9, 30))
    assert p.rel_dir == "2026/02_Daily/2026-W37/00_transcript"
    assert p.filename == "20260908_火.vtt"
    assert p.extra_dirs == ("2026/02_Daily/2026-W37/10_ログ",)


def test_utc_input_converted_to_jst():
    utc = dt.datetime(2026, 9, 7, 4, 0, tzinfo=dt.timezone.utc)  # = JST 13:00
    assert place(utc.astimezone(JST)).filename == "20260907_1300_前半.vtt"


def test_same_day_second_file():
    assert place(d(2026, 9, 9), 2).filename == "20260909_水_2.vtt"


def test_local_skip_existing(tmp_path):
    dst = LocalDest(str(tmp_path))
    assert dst.put("a/b.vtt", b"x", False) == "put"
    assert dst.put("a/b.vtt", b"y", False) == "skip"
    assert (tmp_path / "a/b.vtt").read_bytes() == b"x"
    assert dst.put("a/b.vtt", b"y", True) == "put"
