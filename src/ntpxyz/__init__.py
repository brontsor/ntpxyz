# ntpxyz/__init__.py marks this directory as a package and allows imports
"""ntpxyz - The NTP Statistics Toolkit

Currently, ntpxyz parses the following ntp statistics files and generates meaningful
plots:

    loopstats - Clock sync
    sysstats - Network traffic
    usestats - Host utilization

The plots are saved to disk. Optionally, plots can be sent to a telegram chat, a
useful feature in DMZ enviornments without access to local, trusted networks.

ntpxyz supports many options, which can be sourced from the command-line and also
from a json configuration file. The program can be run ad-hoc by the user or it can
be configured for unattended batch execution.

If a user loads a json config, any individual argument value present in the
config file will be overridden by the same argument if passed in via cli at runtime.

The architecture is suited for additional parse, plot, and utility functions in the
future.

"""

from __future__ import annotations

from importlib.metadata import version

__version__ = version("ntpxyz")

__all__ = [
    "__version__",
]
