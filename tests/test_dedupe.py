"""Duplicate rows from NTP hardlinks should be counted, not silently eaten."""

from __future__ import annotations

import pandas as pd

from ntpxyz.io import drop_duplicate_rows


def test_drop_duplicate_rows_reports_how_many() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": [1, 1, 2],
            "offset": [0.1, 0.1, 0.2],
        }
    )

    cleaned, removed = drop_duplicate_rows(frame)

    assert removed == 1
    assert len(cleaned) == 2
    assert cleaned["offset"].tolist() == [0.1, 0.2]
