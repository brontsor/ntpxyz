"""A period filter has to be testable with a frozen clock."""

from __future__ import annotations

import pandas as pd
import pytest

from ntpxyz.time import compile_period


def test_compile_period_uses_the_clock_it_is_given() -> None:
    now = pd.Timestamp("2026-10-06 21:00:00", tz="UTC")

    interval = compile_period("rolling-day", now=now)

    assert interval.right == now
    assert interval.left == now - pd.Timedelta(days=1)


def test_compile_period_rejects_an_unknown_name() -> None:
    now = pd.Timestamp("2026-10-06 21:00:00", tz="UTC")

    with pytest.raises(ValueError):
        compile_period("last_day", now=now)
