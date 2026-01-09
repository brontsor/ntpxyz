"""Allows for flexibility in the way we invoke

This enables the package to be run directly as a script via:
python -m ntpxyz

"""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":
    main()
