"""usestats counters are per second of the reset interval. RSS is not."""

from __future__ import annotations

import pandas as pd
import pytest

from ntpxyz.plot.usestats import plot_usestats


def _frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "timestamp": pd.date_range("2026-10-06", periods=1, freq="h", tz="UTC"),
            "since_reset": [3600],
            "ru_utime": [3.207],
            "ru_stime": [12.552],
            "ru_minflt": [7200],
            "ru_majflt": [0],
            "ru_nswap": [0],
            "ru_inblock": [0],
            "ru_outblock": [472],
            "ru_nvcsw": [130618],
            "ru_nivcsw": [13],
            "ru_nsignals": [0],
            "ru_maxrss": [16936],
        }
    )


def test_context_switches_are_per_second() -> None:
    fig = plot_usestats(_frame())
    wait = fig.axes[4]
    plotted = wait.lines[0].get_ydata()

    assert plotted[0] == pytest.approx(130618 / 3600)
    assert "per s" in wait.get_ylabel()


def test_max_rss_stays_in_kilobytes() -> None:
    fig = plot_usestats(_frame())
    memory = fig.axes[7]
    plotted = memory.lines[0].get_ydata()

    assert plotted[0] == pytest.approx(16936)
    assert memory.get_ylabel() == "KB"
