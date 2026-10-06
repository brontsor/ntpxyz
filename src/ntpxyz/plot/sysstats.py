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

from ..metrics import per_second
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

    rates = sysstats.copy()
    for column in (
        "packets_received",
        "packets_processed",
        "packets_for_this_host",
        "current_version",
        "old_version",
        "access_denied",
        "bad_format",
        "bad_authentication",
        "declined",
        "rate_exceeded",
        "kiss_o_death_packets",
        "ntpv1_packets",
    ):
        if column in rates.columns:
            rates[column] = per_second(rates[column], rates["since_reset"])

    # Pre-compute total errors, already per second
    errors = pd.DataFrame(
        {
            "total": (
                rates["access_denied"]
                + rates["bad_format"]
                + rates["bad_authentication"]
                + rates["declined"]
                + rates["rate_exceeded"]
            )
        }
    )

    # Top-left: Total Packets Received (with error breakdown)
    median_received = rates["packets_received"].median()
    axs[0, 0].axhline(
        y=median_received,
        color="red",
        linestyle="--",
        linewidth=1,
        label=f"median: {median_received:.2f}",
    )
    axs[0, 0].stackplot(
        rates["timestamp"],
        [errors["total"], rates["packets_received"] - errors["total"]],
        labels=["Errors", "Good Packets"],
        alpha=ALPHA,
        step="pre",
    )
    setup_axis(
        axs[0, 0],
        title="Total Packets Received",
        ylabel="packets / s",
        ylim_bottom=0,
        reverse_legend=True,
    )

    # Top-right: NTP Client Versions
    old_median = rates["old_version"].median()
    current_median = rates["current_version"].median()

    if "ntpv1_packets" in rates.columns:
        v1_median = rates["ntpv1_packets"].median()
        axs[0, 1].stackplot(
            rates["timestamp"],
            [
                rates["ntpv1_packets"],
                rates["old_version"],
                rates["current_version"],
            ],
            labels=[
                f"NTPv1 (median: {v1_median:.2f})",
                f"NTPv2/3 (median: {old_median:.2f})",
                f"NTPv4 (median: {current_median:.2f})",
            ],
            alpha=ALPHA,
            step="pre",
        )
    else:
        axs[0, 1].stackplot(
            rates["timestamp"],
            [rates["old_version"], rates["current_version"]],
            labels=[
                f"NTPv2/3 (median: {old_median:.2f})",
                f"NTPv4 (median: {current_median:.2f})",
            ],
            alpha=ALPHA,
            step="pre",
        )
    setup_axis(
        axs[0, 1],
        title="NTP Client Versions",
        ylabel="packets / s",
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
        label=f"median: {median_errors:.2f}",
    )
    axs[1, 0].stackplot(
        rates["timestamp"],
        [
            rates["access_denied"],
            rates["bad_format"],
            rates["bad_authentication"],
            rates["declined"],
            rates["rate_exceeded"],
            rates["kiss_o_death_packets"],
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
        ylabel="packets / s",
        ylim_bottom=0,
        reverse_legend=True,
    )

    # Bottom-right: Processing Efficiency
    # ntpd 4.2.8 index 4 is replies to this host's queries. NTPsec
    # index 4 is packets the daemon accepted. Same plot, different
    # numerator, and the legend names which one.
    if "packets_processed" in sysstats.columns:
        numerator = sysstats["packets_processed"]
        ratio_name = "Processed / Received"
    else:
        numerator = sysstats["packets_for_this_host"]
        ratio_name = "Host replies / Received"
    efficiency = (numerator / sysstats["packets_received"]) * 100
    efficiency_median = efficiency.median()

    axs[1, 1].step(
        sysstats["timestamp"],
        efficiency,
        where="pre",
        linewidth=1.2,
        color="tab:blue",
        label=f"{ratio_name} (median {efficiency_median:.1f}%)",
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
