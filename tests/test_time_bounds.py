"""A raw line becomes one UTC timestamp, or it is refused.

MJD 61319 is 2026-10-06. The seconds field is seconds past that
UTC midnight, not a timezone guess.
"""

from __future__ import annotations

import pandas as pd
import pytest

from ntpxyz.parse import parse_stats


def _raw(line: str) -> pd.DataFrame:
    return pd.DataFrame([line.split()])


def test_midnight_is_the_mjd_day_in_utc() -> None:
    frame = parse_stats("loopstats", _raw("61319 0.000 0.000001 0.1 0.000001 0.001 4"))

    assert frame["timestamp"].iloc[0] == pd.Timestamp("2026-10-06 00:00:00", tz="UTC")


def test_fractional_seconds_survive() -> None:
    frame = parse_stats(
        "loopstats",
        _raw("61319 75709.659 0.000034823 -0.554337 0.000004469 0.001594 6"),
    )

    assert frame["timestamp"].iloc[0] == pd.Timestamp(
        "2026-10-06 21:01:49.659", tz="UTC"
    )


def test_a_second_past_the_day_is_refused() -> None:
    with pytest.raises((ValueError, SystemExit)):
        parse_stats("loopstats", _raw("61319 86400.000 0 0 0 0 4"))


def test_a_negative_second_is_refused() -> None:
    with pytest.raises((ValueError, SystemExit)):
        parse_stats("loopstats", _raw("61319 -1.000 0 0 0 0 4"))


def test_a_date_before_ntp_existed_is_refused() -> None:
    with pytest.raises((ValueError, SystemExit)):
        parse_stats("loopstats", _raw("0 0.000 0 0 0 0 4"))
