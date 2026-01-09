"""Generate sysstats plots and figure

Public Functions
----------------
plot_sysstats : Generate sysstats plots and figure

Notes
-----

See Also
--------

"""

from __future__ import annotations

from typing import Any

import pandas as pd
from matplotlib.figure import Figure
from numpy.typing import NDArray

from .common import ALPHA, create_figure, setup_axis


def plot_sysstats(sysstats: pd.DataFrame) -> Figure:
    """Generate sysstats plots and figure

    Args:
        our prepared DataFrame of statistics data

    Returns:
        fig : the generated Figure

    Raises:
        None
    """
    fig: Figure
    axs: NDArray[Any]  # the Any is to address mypy warnings
    fig, axs = create_figure(
        2, 2, sharex=True, title="NTP sysstats"
    )  # sharex=True is critical here!

    # Pre-compute total errors
    errors = pd.DataFrame(
        {
            "total": (
                sysstats["access_denied"]
                + sysstats["bad_format"]
                + sysstats["bad_authentication"]
                + sysstats["declined"]
                + sysstats["rate_exceeded"]
            )
        }
    )

    # Top-left: Total Packets Received (with error breakdown)
    median_received = sysstats["packets_received"].median()
    axs[0, 0].axhline(
        y=median_received,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"Hourly Avg: {median_received:.0f}",
    )
    axs[0, 0].stackplot(
        sysstats["timestamp"],
        [errors["total"], sysstats["packets_received"] - errors["total"]],
        labels=["Errors", "Good Packets"],
        alpha=ALPHA,
        step="pre",
    )
    setup_axis(
        axs[0, 0],
        title="Total Packets Received",
        ylabel="Packets / Hour",
        ylim_bottom=0,
        reverse_legend=True,
    )

    # Top-right: NTP Client Versions
    old_median = sysstats["old_version"].median()
    current_median = sysstats["current_version"].median()

    if "ntpv1_packets" in sysstats.columns:
        v1_median = sysstats["ntpv1_packets"].median()
        axs[0, 1].stackplot(
            sysstats["timestamp"],
            [
                sysstats["ntpv1_packets"],
                sysstats["old_version"],
                sysstats["current_version"],
            ],
            labels=[
                f"NTPv1 (Avg: {v1_median:.0f})",
                f"NTPv2/3 (Avg: {old_median:.0f})",
                f"NTPv4 (Avg: {current_median:.0f})",
            ],
            alpha=ALPHA,
            step="pre",
        )
    else:
        axs[0, 1].stackplot(
            sysstats["timestamp"],
            [sysstats["old_version"], sysstats["current_version"]],
            labels=[
                f"NTPv2/3 (Avg: {old_median:.0f})",
                f"NTPv4 (Avg: {current_median:.0f})",
            ],
            alpha=ALPHA,
            step="pre",
        )
    setup_axis(
        axs[0, 1],
        title="NTP Client Versions",
        ylabel="Packets / Hour",
        ylim_bottom=0,
        reverse_legend=True,
    )

    # Bottom-left: Detailed Errors
    median_errors = errors["total"].median()
    axs[1, 0].axhline(
        y=median_errors,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"Hourly Avg: {median_errors:.0f}",
    )
    axs[1, 0].stackplot(
        sysstats["timestamp"],
        [
            sysstats["access_denied"],
            sysstats["bad_format"],
            sysstats["bad_authentication"],
            sysstats["declined"],
            sysstats["rate_exceeded"],
            sysstats["kiss_o_death_packets"],
        ],
        labels=[
            "Access denied",
            "Bad length/format",
            "Bad authentication",
            "Declined",
            "Rate exceeded",
            "KoD packets (sent)",
        ],
        alpha=ALPHA,
        step="pre",
    )
    setup_axis(
        axs[1, 0],
        title="Error Breakdown",
        ylabel="Packets / Hour",
        ylim_bottom=0,
        reverse_legend=True,
    )

    # Bottom-right: Processing Efficiency
    efficiency = (sysstats["packets_processed"] / sysstats["packets_received"]) * 100
    efficiency_median = efficiency.median()

    axs[1, 1].step(
        sysstats["timestamp"],
        efficiency,
        where="pre",
        linewidth=1.2,
        color="tab:blue",
        label=f"Processed / Received (Avg {efficiency_median:.1f}%)",
    )
    axs[1, 1].fill_between(
        sysstats["timestamp"],
        efficiency,
        alpha=0.4,
        color="tab:blue",
        step="pre",
    )
    setup_axis(
        axs[1, 1],
        title="Network Efficiency",
        ylabel="Percent",
        ylim_bottom=0,
        ylim_top=100,
        # no reverse_legend here
    )

    return fig
