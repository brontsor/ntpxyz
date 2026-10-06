"""Generate loopstats plots and figure

Public Functions
----------------
compute_oadev : Compute overlapping Allan deviation (OADEV) from parsed loopstats data
plot_loopstats : Generate loopstats plots and figure

Notes
-----

See Also
--------

"""

from __future__ import annotations

from typing import Any

import allantools
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from numpy.typing import NDArray

from .common import ALPHA, POINT_LINESTYLE, POINT_MARKER, create_figure, setup_axis


def compute_oadev(
    loopstats: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Compute overlapping Allan deviation (OADEV) from parsed loopstats data.

    Args:
        loopstats: DataFrame as returned by parse_loopstats()
                   Must have a DatetimeIndex named "timestamp" (UTC, tz-aware or naive)

    Returns:
        tau:   array of averaging times τ in seconds (float)
        adev:  overlapping Allan deviation σ_y(τ) in seconds (float)
        error: estimated 1σ error bars (lower/upper are symmetric)
        n:     number of averages used for each τ

    The returned arrays are perfectly aligned (same length) and ready for direct
    plotting on log-log axes with plt.loglog(tau, adev) etc.
    """
    # 1. Extract phase data (offset in seconds) and timestamps
    phase: np.ndarray = loopstats["offset"].to_numpy(dtype=np.float64)
    timestamps: pd.Series | pd.DataFrame = loopstats["timestamp"]

    # 2. Compute the nominal sampling interval from the actual timestamps
    #    We use the median difference — robust against occasional gaps
    dt_ns: float = float(np.median(np.diff(timestamps.astype("int64"))))
    tau0: float = dt_ns / 1e9  # seconds, as float
    rate: float = 1.0 / tau0  # samples per second

    # 3. Let allantools do the heavy lifting (overlapping estimator)
    #    data_type="phase" → input is phase in seconds (not frequency)
    #    rate → tells it the original sampling rate
    #    taus="octave" is a good default: log-spaced, octave steps, up to ~N/3
    #    we ignore assignment due to allantools interface
    tau, adev, error, n = allantools.oadev(
        phase,
        rate=rate,
        data_type="phase",
        taus="octave",  # clear, nice spacing for plots
    )
    error = np.asarray(error)

    return tau, adev, error, n


def plot_loopstats(loopstats: pd.DataFrame) -> Figure:
    """Generate loopstats plots and figure

    Args:
        our prepared DataFrame of statistics data

    Returns:
        fig, : the generated Figure

    Raises:
        None
    """
    fig: Figure
    axs: NDArray[Any]  # the Any is to address mypy warnings
    fig, axs = create_figure(2, 2, title="NTP loopstats")

    # Add the main title to the entire figure

    # Top-left: Offset + Jitter
    axs[0, 0].plot(
        loopstats["timestamp"],
        loopstats["offset"] * 1000,
        marker=POINT_MARKER,
        linestyle=POINT_LINESTYLE,
        alpha=ALPHA,
        label="Offset",
    )
    axs[0, 0].plot(
        loopstats["timestamp"],
        loopstats["jitter"] * 1000,
        marker=POINT_MARKER,
        linestyle=POINT_LINESTYLE,
        alpha=ALPHA,
        label="Jitter",
    )
    setup_axis(axs[0, 0], "Offset vs. Jitter", ylabel="ms (10e-3 sec)")

    # Top-right: Offset histogram
    axs[0, 1].hist(loopstats["offset"] * 1000, bins=25, density=True, alpha=ALPHA)
    setup_axis(
        axs[0, 1],
        "Offset Distribution",
        xlabel="ms (10e-3 sec)",
        ylabel="P(ms)",
        show_legend=False,
        rotation="auto",
    )

    # Bottom-left: Drift + Wander
    axs[1, 0].plot(
        loopstats["timestamp"],
        loopstats["drift"],
        marker=POINT_MARKER,
        linestyle=POINT_LINESTYLE,
        alpha=ALPHA,
        label="Drift",
    )
    axs[1, 0].plot(
        loopstats["timestamp"],
        loopstats["wander"],
        marker=POINT_MARKER,
        linestyle=POINT_LINESTYLE,
        alpha=ALPHA,
        label="Wander",
    )
    setup_axis(axs[1, 0], "Drift vs. Wander", ylabel="PPM")

    # Bottom-right → Allan Deviation using allantools
    ax = axs[1, 1]

    try:
        tau, adev, err, _ = compute_oadev(loopstats)

        ax.loglog(
            tau,
            adev,
            marker="o",
            markersize=4,
            linestyle="-",
            linewidth=1.5,
            color="tab:blue",
            alpha=ALPHA,
            label="OADEV",
        )
        ax.fill_between(
            tau,
            adev - err,
            adev + err,
            color="tab:blue",
            alpha=0.15,
        )

        # Classic NTP poll interval guides
        for poll_sec, label in [(64, "64 s"), (256, "256 s"), (1024, "1024 s")]:
            if tau.min() <= poll_sec <= tau.max():
                ax.axvline(
                    poll_sec, color="red", linestyle="--", linewidth=1, alpha=0.5
                )

                # Place the label at a fixed data-coordinate height that is always
                # inside the plot
                y_label = adev.min() * 1.01

                ax.text(
                    poll_sec,
                    y_label,
                    f" {label}",
                    color="red",
                    va="bottom",  # anchor from the bottom of the text
                    ha="left",
                    fontsize=9,
                    bbox={
                        "boxstyle": "square",
                        "facecolor": "white",
                        "alpha": 0,
                        "edgecolor": "none",
                    },
                    zorder=10,
                )

        setup_axis(
            ax,
            title="Overlapping Allan Deviation",
            xlabel="Averaging time τ (seconds)",
            ylabel="OADEV (seconds), derived from offset, not the wander column",
            show_legend=False,
            rotation="auto",
        )

    except Exception as e:
        # Graceful fallback
        ax.text(
            0.5,
            0.5,
            f"Allan deviation failed:\n{e}",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color="red",
            fontsize=10,
            bbox={
                "boxstyle": "round",
                "facecolor": "mistyrose",
            },
        )
        setup_axis(
            ax,
            title="Allan Deviation (error)",
            xlabel="Averaging time τ (seconds)",
            ylabel="ADEV (seconds)",
            show_legend=False,
        )

    return fig
