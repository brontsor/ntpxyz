"""Directory scans must not double-count a hardlink or drift the window."""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

from ntpxyz.io import load_stats_from_directory
from ntpxyz.parse import parse_loopstats

INSIDE = "61319 43200.000 0.000010 0.1 0.000001 0.001 4\n"
EDGE = "61318 43200.000 0.000020 0.1 0.000001 0.001 4\n"
OUTSIDE = "61318 43199.000 0.000030 0.1 0.000001 0.001 4\n"
NOW = pd.Timestamp("2026-10-06 12:00:00", tz="UTC")


def test_period_window_keeps_the_edges_and_drops_the_second_before(
    tmp_path: Path,
) -> None:
    (tmp_path / "loopstats").write_text(INSIDE + EDGE + OUTSIDE)

    frame = parse_loopstats(
        load_stats_from_directory("loopstats", str(tmp_path), "rolling-day", now=NOW)
    )

    assert set(frame["offset"].tolist()) == {0.000010, 0.000020}


def test_a_hardlinked_hour_is_counted_once(tmp_path: Path, caplog) -> None:
    line = INSIDE
    (tmp_path / "loopstats").write_text(line)
    (tmp_path / "loopstats.202610").write_text(line)

    with caplog.at_level(logging.INFO):
        frame = load_stats_from_directory("loopstats", str(tmp_path), now=NOW)

    assert len(frame) == 1
    assert "Dropped 1 duplicate" in caplog.text
