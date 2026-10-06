"""Generate usestats plots and figure

Public Functions
----------------
plot_usestats : Generate usestats plots and figure

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

from .common import ALPHA, LINE_MARKER, LINE_STYLE, create_figure, setup_axis


def plot_usestats(usestats: pd.DataFrame) -> Figure:
    """Generate usestats plots and data

    Args:
        our prepared DataFrame of statistics data

    Returns:
        fig : the generated Figure

    Raises:
        None
    """
    fig: Figure
    axs: NDArray[Any]  # the Any is to address mypy warnings
    fig, axs = create_figure(2, 4, sharex=True, title="NTP usestats")

    # Row 0
    axs[0, 0].plot(
        usestats["timestamp"],
        usestats["ru_utime"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="User",
    )
    axs[0, 0].plot(
        usestats["timestamp"],
        usestats["ru_stime"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="System",
    )
    setup_axis(
        axs[0, 0],
        "CPU Time",
        ylabel="CPU seconds",
        ylim_bottom=0,
    )

    axs[0, 1].plot(
        usestats["timestamp"],
        usestats["ru_minflt"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="Minor (no I/O)",
    )
    axs[0, 1].plot(
        usestats["timestamp"],
        usestats["ru_majflt"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="Major (I/O)",
    )
    setup_axis(axs[0, 1], "Page Faults", ylabel="Faults", ylim_bottom=0)

    axs[0, 2].plot(
        usestats["timestamp"],
        usestats["ru_nswap"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="Swaps",
    )
    setup_axis(
        axs[0, 2],
        "Process Swaps",
        ylabel="Count",
        ylim_bottom=0,
        show_legend=False,
    )

    axs[0, 3].plot(
        usestats["timestamp"],
        usestats["ru_inblock"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="In",
    )
    axs[0, 3].plot(
        usestats["timestamp"],
        usestats["ru_outblock"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="Out",
    )
    setup_axis(
        axs[0, 3],
        "File Blocks I/O",
        ylabel="Blocks",
        ylim_bottom=0,
    )

    # Row 1
    axs[1, 0].plot(
        usestats["timestamp"],
        usestats["ru_nvcsw"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="Voluntary",
    )
    setup_axis(
        axs[1, 0],
        "Context Switches (Wait)",
        ylabel="Count",
        ylim_bottom=0,
        show_legend=False,
    )

    axs[1, 1].plot(
        usestats["timestamp"],
        usestats["ru_nivcsw"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="Involuntary",
    )
    setup_axis(
        axs[1, 1],
        "Context Switches (Preempt)",
        ylabel="Count",
        ylim_bottom=0,
        show_legend=False,
    )

    axs[1, 2].plot(
        usestats["timestamp"],
        usestats["ru_nsignals"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="Signals",
    )
    setup_axis(
        axs[1, 2],
        "Signals Received",
        ylabel="Count",
        ylim_bottom=0,
        show_legend=False,
    )

    axs[1, 3].plot(
        usestats["timestamp"],
        usestats["ru_maxrss"],
        alpha=ALPHA,
        marker=LINE_MARKER,
        linestyle=LINE_STYLE,
        label="Max RSS",
    )
    setup_axis(
        axs[1, 3],
        "Memory Usage (Max RSS)",
        ylabel="KB",
        ylim_bottom=0,
        show_legend=False,
    )

    return fig
