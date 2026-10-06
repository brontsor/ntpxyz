"""Dialect belongs in the config. The command line still wins."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SYS_13 = "61319 43200.000 3600 100 40 30 10 0 5 0 0 0 0\n"


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO / "src")
    env["MPLBACKEND"] = "Agg"
    return subprocess.run(
        [sys.executable, "-m", "ntpxyz", *args],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_config_dialect_plots_a_13_column_file(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    out = tmp_path / "out"
    logs.mkdir()
    out.mkdir()
    (logs / "sysstats").write_text(SYS_13)
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "dialect": "ntpsec-1.2.1",
                "scandir": str(logs),
                "savedir": str(out),
                "savename": "fromcfg",
                "verbose": 3,
            }
        )
    )

    result = _run(tmp_path, "--loadconfig", str(config))

    assert result.returncode == 0, result.stderr
    assert (out / "fromcfg_sysstats.png").stat().st_size > 0


def test_cli_dialect_overrides_the_config(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    out = tmp_path / "out"
    logs.mkdir()
    out.mkdir()
    (logs / "sysstats").write_text(SYS_13)
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "dialect": "ntpsec-1.2.1",
                "savedir": str(out),
                "savename": "override",
                "verbose": 4,
            }
        )
    )

    result = _run(
        tmp_path,
        "--loadconfig",
        str(config),
        "--scandir",
        str(logs),
        "--dialect",
        "ntpd-4.2.8",
    )

    text = result.stdout + result.stderr
    assert result.returncode == 0, text
    assert "ntpd-4.2.8" in text
    assert (out / "override_sysstats.png").exists()
