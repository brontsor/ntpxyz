"""Shared helpers for plotting functions

Some of the graphing logic is abstracted and placed here.

Public Functions
----------------
create_figure : Apply constant formatting to figures
setup_axis : Apply consistent formatting to subplots

Notes
-----

See Also
--------

"""

from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from cycler import cycler
from matplotlib.axes import Axes
from matplotlib.figure import Figure

# Plotting constants
PLOT_STYLE: str = "seaborn-v0_8"
FIGSIZE: tuple[float, float] = (16, 10)
LAYOUT: str = "tight"
ALPHA: float = 0.8
GRID_ALPHA: float = 0.7
LEGEND_FONTSIZE: str = "medium"
XROT: int = 30
# Marker & linestyle semantics
POINT_MARKER: str = "."  # scatter-style (loopstats)
POINT_LINESTYLE: str = "none"
LINE_MARKER: str = "none"  # clean continuous lines (usestats)
LINE_STYLE: str = "-"
STACK_MARKER: str = "none"  # stackplot/step, marker ignored anyway


def create_figure(
    nrows: int,
    ncols: int,
    sharex: bool = False,
    title: str = "NTP Statistics",
) -> tuple[Figure, np.ndarray]:
    """Apply constant formatting to figures

    We make use of PLOT_STYLE, FIGSIZE and LAYOUT consts.

    Args:
        nrows: Number of rows
        ncols: Number of columns
        sharex: Whether to share x-axis (True for sysstats, false for loop and use)

    Returns:
        fig, axs tuple that is ready for plotting

    Rasies:
        None
    """
    plt.style.use(PLOT_STYLE)
    plt.rcParams["axes.prop_cycle"] = cycler(color=plt.cm.Set1.colors)  # type: ignore[attr-defined]
    fig, axs = plt.subplots(
        nrows,
        ncols,
        figsize=FIGSIZE,
        layout=LAYOUT,
        sharex=sharex,
    )
    now_ts: pd.Timestamp = pd.Timestamp.now(tz="UTC")
    now: str = now_ts.strftime("%Y-%m-%d %H:%M:%S")
    fig.suptitle(
        f"ntpxyz | {title} | Generated: {now} UTC\n",
        fontsize=16,
        fontweight="semibold",
        color="darkslategrey",
        alpha=0.98,
        # x=0.5,
        # y=0.965,  # perfect breathing room
        ha="center",
        va="top",
        # bbox=dict(
        #    boxstyle="round,pad=0.7",
        #    facecolor="white",
        #    alpha=0.6,
        #    edgecolor="none",
        # ),
    )
    return fig, axs


def setup_axis(
    ax: Axes,
    title: str,
    xlabel: str = "Timestamp (UTC)",
    ylabel: str | None = None,
    ylim_bottom: float | None = None,
    ylim_top: float | None = None,
    show_legend: bool = True,
    reverse_legend: bool = False,
    rotation: int | str | None = XROT,
) -> None:
    """Apply consistent formatting to subplots

    We make use of XROT, GRID_ALPHA, LEGEND_FONTSIZE

    Args:
        ax: the Axes to setup
        title: Plot title
        xlabel: x-axis label
        ylabel: y-axis label
        ylim_bottom: min y
        ylim_top: max y
        show_legend: show or hide the legend
        reverse_legend: better to reverse order for stackplots
    Returns:
        None, we operate diretly on the Axes

    Raises:
        None
    """
    ax.set_title(title)
    ax.title.set_fontweight("semibold")
    ax.set_xlabel(xlabel)
    if ylabel is not None:
        ax.set_ylabel(ylabel)

    ax.margins(x=0, y=0.02)
    ax.tick_params(axis="x", rotation=rotation)
    ax.grid(True, alpha=GRID_ALPHA)

    # Y-limits
    if ylim_bottom is not None or ylim_top is not None:
        cur_bottom, cur_top = ax.get_ylim()
        bottom = ylim_bottom if ylim_bottom is not None else cur_bottom
        top = ylim_top if ylim_top is not None else cur_top
        ax.set_ylim(bottom=bottom, top=top)

    # Legend
    if show_legend:
        handles, labels = ax.get_legend_handles_labels()
        if reverse_legend:
            # there's a better way to do this
            handles = handles[::-1]
            labels = labels[::-1]
        if handles:
            ax.legend(
                handles,
                labels,
                framealpha=0.85,
                fancybox=True,
                frameon=True,
                loc="lower left",
                fontsize=LEGEND_FONTSIZE,
            )
    elif hasattr(ax, "legend_") and ax.legend_ is not None:
        ax.legend_.remove()
