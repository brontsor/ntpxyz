"""Plot labels must match the units on the frame.

A seconds column drawn on a 0-100 axis, or a median labeled as an
average, is a misread even when the parsed number is right.
"""

from __future__ import annotations

import pandas as pd

from ntpxyz.plot.loopstats import plot_loopstats
from ntpxyz.plot.sysstats import plot_sysstats
from ntpxyz.plot.usestats import plot_usestats


def _stamps(rows: int = 4) -> pd.Series:
    return pd.Series(pd.date_range("2026-10-06", periods=rows, freq="h", tz="UTC"))


def _texts(fig) -> str:
    chunks = [fig.axes[0].figure._suptitle.get_text()]
    for axis in fig.axes:
        chunks.append(axis.get_title())
        chunks.append(axis.get_ylabel())
        chunks.append(axis.get_xlabel())
        for text in axis.get_legend_handles_labels()[1]:
            chunks.append(text)
    return "\n".join(chunks)


def test_usestats_cpu_axis_is_seconds_not_percent() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": _stamps(),
            "since_reset": [3600, 3600, 1800, 3600],
            "ru_utime": [3.207, 0.536, 1.0, 2.0],
            "ru_stime": [12.552, 1.609, 2.0, 4.0],
            "ru_minflt": 0,
            "ru_majflt": 0,
            "ru_nswap": 0,
            "ru_inblock": 0,
            "ru_outblock": [472, 10, 1, 1],
            "ru_nvcsw": [130618, 80, 1, 1],
            "ru_nivcsw": [13, 6, 1, 1],
            "ru_nsignals": 0,
            "ru_maxrss": [16936, 14000, 14000, 14000],
        }
    )

    labels = _texts(plot_usestats(frame))

    assert "Percent" not in labels
    assert "CPU seconds" in labels
    cpu = plot_usestats(frame).axes[0]
    assert cpu.get_ylim()[1] > 12.552


def test_sysstats_interval_is_labeled_not_assumed_hourly() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": _stamps(),
            "since_reset": [3600, 1800, 3600, 7200],
            "packets_received": [128409, 1000, 1000, 1000],
            "packets_processed": [126054, 900, 900, 900],
            "current_version": [100214, 1, 1, 1],
            "old_version": [25845, 1, 1, 1],
            "access_denied": [9, 0, 0, 0],
            "bad_format": [2, 0, 0, 0],
            "bad_authentication": 0,
            "declined": [5, 0, 0, 0],
            "rate_exceeded": [3114, 0, 0, 0],
            "kiss_o_death_packets": [775, 0, 0, 0],
            "ntpv1_packets": [681, 0, 0, 0],
        }
    )

    labels = _texts(plot_sysstats(frame))

    assert "Packets / Hour" not in labels
    assert "Hourly Avg" not in labels
    assert "interval" in labels
    assert "median" in labels


def test_loopstats_keeps_sign_and_names_oadev_as_derived() -> None:
    frame = pd.DataFrame(
        {
            "timestamp": _stamps(16),
            "offset": [-0.000038648] * 16,
            "drift": [-21.674] * 16,
            "jitter": [0.000001] * 16,
            "wander": [0.001] * 16,
            "constant": [4] * 16,
        }
    )

    labels = _texts(plot_loopstats(frame))

    assert "abs(Offset)" not in labels
    assert "derived from offset" in labels
    assert "not the wander column" in labels
