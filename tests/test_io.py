"""Basic I/O tests, indirect basic testing of other modules

Tests
-----
test_check_directory
test_infer_type_from_path
test_load_stats_from_file
test_load_stats_from_directory

Notes
-----
We'll have to rethink I/O tests after load_stats_* consolidation and refactoring

"""

from __future__ import annotations

import os
from pathlib import Path
from typing import cast

import pandas as pd
import pytest
from matplotlib.figure import Figure

from ntpxyz.io import (
    DEFAULT_OUTPUT_PREFIX,
    SUPPORTED_INPUTS,
    check_directory,
    infer_type_from_path,
    load_stats_from_directory,
    load_stats_from_file,
    save_to_disk,
)
from ntpxyz.parse import parse_loopstats, parse_sysstats, parse_usestats
from ntpxyz.plot.loopstats import plot_loopstats
from ntpxyz.plot.sysstats import plot_sysstats
from ntpxyz.plot.usestats import plot_usestats

EXAMPLES_BASE: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "examples")
)


def test_check_directory(tmp_path: Path) -> None:
    assert check_directory(EXAMPLES_BASE)
    assert check_directory(str(tmp_path), "read")
    assert check_directory(str(tmp_path), "write")
    assert not check_directory("invalid")


@pytest.mark.parametrize("stats_type", SUPPORTED_INPUTS)
def test_infer_type_from_path(stats_type: str) -> None:
    assert (
        infer_type_from_path(f"{EXAMPLES_BASE}/logs/host-001/{stats_type}.199912")
        == stats_type
    )
    assert (
        infer_type_from_path(f"{EXAMPLES_BASE}/logs/host-002/{stats_type}.202510")
        == stats_type
    )  # Handles variants
    assert infer_type_from_path("invalid") == "none"


@pytest.mark.parametrize("stats_type", SUPPORTED_INPUTS)
@pytest.mark.parametrize("host_dir", ["host-001", "host-002"])
@pytest.mark.parametrize("file_extension", ["202510", "202511"])
def test_load_stats_from_file(
    stats_type: str, host_dir: str, file_extension: str
) -> None:
    file_path = os.path.join(
        EXAMPLES_BASE, "logs", host_dir, f"{stats_type}.{file_extension}"
    )
    stats: pd.DataFrame = load_stats_from_file(stats_type, file_path)
    min_lines: int = 700  # smallest complete month is ~700 rows
    assert not stats.empty
    assert stats.shape[0] > 0
    assert stats.shape[0] > min_lines
    assert "timestamp" in stats.columns


@pytest.mark.parametrize("stats_type", SUPPORTED_INPUTS)
@pytest.mark.parametrize("host_dir", ["host-001", "host-002"])
@pytest.mark.parametrize("period", [None])  # cant test periods on static data over time
def test_load_stats_from_directory(
    tmp_path: Path, stats_type: str, host_dir: str, period: str | None
) -> None:
    dir_path: str = os.path.join(EXAMPLES_BASE, "logs", host_dir)
    # interval = compile_period(period) if period else None
    stats: pd.DataFrame = load_stats_from_directory(stats_type, dir_path, period)
    min_lines: int = 1400  # smallest complete month is ~700 rows * 2 months
    assert not stats.empty
    assert stats.shape[0] > 0  # At least some rows from examples
    assert stats.shape[0] > min_lines
    assert "timestamp" in stats.columns  # post convert_dates

    fig: Figure = cast(Figure, None)

    if stats_type == "loopstats":
        fig = plot_loopstats(parse_loopstats(stats))
    elif stats_type == "sysstats":
        dialect = "ntpd-4.2.8" if stats.shape[1] == 12 else None
        fig = plot_sysstats(parse_sysstats(stats, dialect=dialect))
    elif stats_type == "usestats":
        fig = plot_usestats(parse_usestats(stats))

    file_path: Path = tmp_path / f"{DEFAULT_OUTPUT_PREFIX}_{stats_type}"

    save_to_disk(fig, str(file_path), file_fmt="png")

    saved_file_path: Path = file_path.with_suffix(".png")

    assert saved_file_path.exists(), f"File was not saved: {saved_file_path}"
    assert saved_file_path.stat().st_size > 0, "Saved file is empty"
