"""Width is not a dialect. validate_stats must not settle a 13-column file."""

from __future__ import annotations

import pandas as pd

from ntpxyz.io import validate_stats


def test_width_13_is_not_valid_sysstats_without_a_dialect() -> None:
    frame = pd.DataFrame([[float(i) for i in range(13)]])

    assert validate_stats("sysstats", frame) is False
