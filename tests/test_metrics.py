"""Rates and fractions are functions of a typed frame, not of an axis label."""

from __future__ import annotations

import pandas as pd
import pytest

from ntpxyz.metrics import cpu_fraction, per_second


def test_cpu_fraction_is_user_plus_system_over_reset() -> None:
    fraction = cpu_fraction(
        pd.Series([3.207]),
        pd.Series([12.552]),
        pd.Series([3600.0]),
    )

    assert fraction.iloc[0] == pytest.approx((3.207 + 12.552) / 3600)


def test_cpu_fraction_refuses_a_zero_reset() -> None:
    with pytest.raises(ValueError):
        cpu_fraction(pd.Series([1.0]), pd.Series([1.0]), pd.Series([0.0]))


def test_per_second_divides_by_the_reset_interval() -> None:
    rate = per_second(pd.Series([128409.0]), pd.Series([3600.0]))

    assert rate.iloc[0] == pytest.approx(128409 / 3600)
