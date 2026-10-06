"""Test integrity of loopstats plotting

Tests
-----
test_compute_oadev_*: we generate some synthetic arrays that have a known output
    when run through compute_oadev, and then check the results against the known
    values.

"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from ntpxyz.plot.loopstats import (
    compute_oadev,
)  # Adjust import based on your package structure


@pytest.fixture
def synthetic_loopstats_constant() -> pd.DataFrame:
    """Fixture for constant phase data (expected OADEV = 0)."""
    dates = pd.date_range(
        start="2025-12-19", periods=16, freq="s"
    )  # 16 points, 1 Hz sampling
    offsets = np.zeros(16)  # Constant phase
    return pd.DataFrame({"timestamp": dates, "offset": offsets})


@pytest.fixture
def synthetic_loopstats_linear() -> pd.DataFrame:
    """Fixture for linear phase data (constant frequency, expected OADEV = 0)."""
    dates = pd.date_range(start="2025-12-19", periods=16, freq="s")  # 16 points, 1 Hz
    offsets = np.arange(16) * 0.1  # Linear phase (freq offset 0.1)
    return pd.DataFrame({"timestamp": dates, "offset": offsets})


@pytest.fixture
def synthetic_loopstats_small_nonlinear() -> pd.DataFrame:
    """Fixture for small non-linear phase data (manual calculation for known OADEV)."""
    dates = pd.date_range(start="2025-12-19", periods=4, freq="s")  # Small N=4, 1 Hz
    offsets = np.array([0.0, 0.0, 1.0, 1.0])  # Step-like for non-zero deviation
    return pd.DataFrame({"timestamp": dates, "offset": offsets})


def test_compute_oadev_constant(synthetic_loopstats_constant: pd.DataFrame) -> None:
    """Test OADEV is zero for constant phase."""
    tau, adev, error, n = compute_oadev(synthetic_loopstats_constant)
    assert len(tau) == len(adev) == len(error) == len(n), "Output arrays must align"
    assert np.allclose(adev, 0.0, atol=1e-8), "OADEV should be zero for constant phase"
    assert np.all(error >= 0), (
        "Errors should be non-negative"
    )  # Fixed: Allow zero for perfect data
    assert np.all(n > 0), "N should be positive"


def test_compute_oadev_linear(synthetic_loopstats_linear: pd.DataFrame) -> None:
    """Test OADEV is zero for linear phase (constant frequency)."""
    tau, adev, error, n = compute_oadev(synthetic_loopstats_linear)
    assert len(tau) == len(adev) == len(error) == len(n), "Output arrays must align"
    assert np.allclose(adev, 0.0, atol=1e-8), (
        "OADEV should be zero for constant frequency"
    )
    assert np.all(error >= 0), "Errors should be non-negative"  # Fixed: Allow zero
    assert np.all(n > 0), "N should be positive"


def test_compute_oadev_small_nonlinear(
    synthetic_loopstats_small_nonlinear: pd.DataFrame,
) -> None:
    """Test OADEV for small dataset with manual known value."""
    tau, adev, error, n = compute_oadev(synthetic_loopstats_small_nonlinear)
    assert len(tau) == 1, "For small N=4, 'octave' should only compute tau=1"
    assert np.allclose(tau, [1.0], atol=1e-8), "Tau should be [1.0]"
    assert np.allclose(adev, [0.7071067811865476], atol=1e-8), (
        "Expected OADEV ~ sqrt(0.5)"
    )
    assert np.allclose(error, [0.5], atol=1e-1), (
        "Expected error ~ 0.5 (adev / sqrt(n)); adjust atol if needed"
    )
    assert np.allclose(n, [2], atol=1e-8), "N=2 for tau=1 with N=4 points"


def test_compute_oadev_invalid_input() -> None:
    """Test error handling for invalid input (e.g., missing columns)."""
    invalid_df = pd.DataFrame(
        {"timestamp": pd.date_range(start="2025-12-19", periods=4, freq="s")}
    )  # No 'offset'
    with pytest.raises(KeyError):
        compute_oadev(invalid_df)


def test_one_hertz_tau_does_not_depend_on_timestamp_resolution() -> None:
    """Pandas may store datetimes as microseconds. Tau is still seconds."""
    offsets = np.array([0.0, 0.0, 1.0, 1.0])
    start = pd.Timestamp("2025-12-19")
    for unit in ("us", "ns"):
        stamps = pd.date_range(start, periods=4, freq="s").as_unit(unit)
        frame = pd.DataFrame({"timestamp": stamps, "offset": offsets})
        tau, _, _, _ = compute_oadev(frame)
        assert np.allclose(tau, [1.0], atol=1e-6), unit
