"""Rates and fractions of a parsed stats frame.

Plots call these. A label does not get to invent the formula.
"""

from __future__ import annotations

import pandas as pd


def cpu_fraction(
    user_seconds: pd.Series,
    system_seconds: pd.Series,
    since_reset: pd.Series,
) -> pd.Series:
    """CPU time used, as a fraction of the reset interval.

    ``ru_utime`` and ``ru_stime`` are seconds, not percents. Multiply
    by 100 only at the label, and say that you did.
    """
    reset = pd.to_numeric(since_reset, errors="raise")
    if (reset <= 0).any():
        raise ValueError("since_reset must be greater than zero")
    used = pd.to_numeric(user_seconds, errors="raise") + pd.to_numeric(
        system_seconds, errors="raise"
    )
    return used / reset


def per_second(count: pd.Series, since_reset: pd.Series) -> pd.Series:
    """Count divided by the reset interval, in events per second."""
    reset = pd.to_numeric(since_reset, errors="raise")
    if (reset <= 0).any():
        raise ValueError("since_reset must be greater than zero")
    return pd.to_numeric(count, errors="raise") / reset
