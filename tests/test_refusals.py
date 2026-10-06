"""A file that could mean two things is a refusal, not a guess."""

from __future__ import annotations

import pandas as pd
import pytest

from ntpxyz.parse import parse_stats
from ntpxyz.schema import UnknownLayout, identify_layout

NTPSEC_14 = (
    "61319 73766.659 3600 128409 126054 100214 25845 9 2 0 5 3114 775 681"
)
NTPSEC_13 = "61319 73766.659 3600 3319 431 408 55 0 2888 0 0 0 0"


def _raw(line: str) -> pd.DataFrame:
    return pd.DataFrame([line.split()])


def test_a_dialect_that_does_not_own_the_width_is_refused() -> None:
    with pytest.raises(UnknownLayout):
        identify_layout("sysstats", NTPSEC_14, dialect="ntpsec-1.2.1")


def test_naming_a_14_column_file_as_classic_is_refused() -> None:
    with pytest.raises(UnknownLayout):
        parse_stats("sysstats", _raw(NTPSEC_14), dialect="ntpd-4.2.8")


def test_a_mixed_width_file_is_refused() -> None:
    mixed = pd.DataFrame([NTPSEC_13.split(), NTPSEC_14.split()])

    with pytest.raises(ValueError, match="mixed widths"):
        parse_stats("sysstats", mixed, dialect="ntpsec-1.2.1")


def test_an_empty_frame_is_refused() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_stats("loopstats", pd.DataFrame())


def test_a_letter_in_a_numeric_file_is_refused() -> None:
    with pytest.raises((ValueError, SystemExit)):
        parse_stats("loopstats", _raw("61319 1.0 not-a-number 0 0 0 4"))
