"""The shipped example has to be a file the program will accept."""

from __future__ import annotations

import json
from pathlib import Path

from ntpxyz.time import VALID_PERIODS

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "config" / "config.json"


def test_example_config_uses_a_real_period_and_an_int_verbosity() -> None:
    data = json.loads(EXAMPLE.read_text())

    assert data["period"] in VALID_PERIODS
    assert isinstance(data["verbose"], int)
    assert "last_day" not in json.dumps(data)
