"""The command the user runs, not the functions under it.

A missing stats type, or a 13-column file with no dialect, must not
throw away the charts that were fine.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
LOOP = "61319 43200.000 0.000010 -0.5 0.000001 0.001 4\n"
SYS_13 = "61319 43200.000 3600 3319 431 408 55 0 2888 0 0 0 0\n"


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


def test_a_directory_with_only_loopstats_still_plots(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    out = tmp_path / "out"
    logs.mkdir()
    out.mkdir()
    (logs / "loopstats").write_text(LOOP)

    result = _run(
        tmp_path,
        "--scandir",
        str(logs),
        "--savedir",
        str(out),
        "--savename",
        "only",
    )

    assert result.returncode == 0, result.stderr
    assert (out / "only_loopstats.png").stat().st_size > 0
    assert not (out / "only_sysstats.png").exists()
    assert "Skipping sysstats" in result.stderr + result.stdout


def test_thirteen_columns_without_a_dialect_does_not_drop_loopstats(
    tmp_path: Path,
) -> None:
    logs = tmp_path / "logs"
    out = tmp_path / "out"
    logs.mkdir()
    out.mkdir()
    (logs / "loopstats").write_text(LOOP)
    (logs / "sysstats").write_text(SYS_13)

    result = _run(
        tmp_path,
        "--scandir",
        str(logs),
        "--savedir",
        str(out),
        "--savename",
        "bare",
    )

    assert result.returncode == 0, result.stderr
    assert (out / "bare_loopstats.png").exists()
    assert not (out / "bare_sysstats.png").exists()
    assert "13" in result.stderr + result.stdout


def test_an_unknown_period_is_refused_before_any_plot(tmp_path: Path) -> None:
    logs = tmp_path / "logs"
    logs.mkdir()
    (logs / "loopstats").write_text(LOOP)

    result = _run(tmp_path, "--scandir", str(logs), "--period", "last_day")

    assert result.returncode != 0
    assert not list(tmp_path.glob("*.png"))
