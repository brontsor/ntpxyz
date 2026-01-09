# ntpxyz/plot/__init__.py
"""
Plotting modules for ntpxyz.

This subpackage contains high-level plotting functions for each NTP statistics
type. Each function accepts a prepared pandas DataFrame and returns a fully
styled matplotlib figure ready for saving or display.

Available plotters:
plot_loopstats : Clock discipline, offset, frequency, and Allan deviation
plot_sysstats  : Network traffic, client versions, errors, and efficiency
plot_usestats  : System resource usage (CPU, memory, I/O, context switches)

Common utilities:
create_figure : Consistent figure creation with standard styling
setup_axis    : Apply ntpxyz look-and-feel to individual subplots
"""

from __future__ import annotations

# Re-export common helpers (optional, but very convenient)
from .common import ALPHA, GRID_ALPHA, PLOT_STYLE, create_figure, setup_axis

# Re-export the public plotting functions at the plot.* level
# This enables: from ntpxyz.plot import plot_loopstats
from .loopstats import plot_loopstats
from .sysstats import plot_sysstats
from .usestats import plot_usestats

__all__ = [
    "ALPHA",
    "GRID_ALPHA",
    "PLOT_STYLE",
    "create_figure",
    "plot_loopstats",
    "plot_sysstats",
    "plot_usestats",
    "setup_axis",
]
