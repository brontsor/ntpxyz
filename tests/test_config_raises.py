"""Config loading raises. The CLI is the only exit."""

from __future__ import annotations

from pathlib import Path

import pytest

from ntpxyz.config import load_config_from_file


def test_a_missing_config_raises(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="File not found"):
        load_config_from_file(str(tmp_path / "missing.json"))
