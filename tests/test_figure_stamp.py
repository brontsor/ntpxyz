"""A figure should say which host, window, and writer it came from."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")

from matplotlib.figure import Figure

from ntpxyz.plot.common import stamp_figure


def test_stamp_names_the_run() -> None:
    fig = Figure()
    stamp_figure(
        fig,
        title="NTP usestats",
        savename="tock",
        period="rolling-day",
        dialect="ntpsec-1.2.1",
        span="2026-10-05 21:00 to 2026-10-06 21:00 UTC",
        generated="2026-10-06 21:03:00",
    )
    text = fig._suptitle.get_text()

    assert "tock" in text
    assert "rolling-day" in text
    assert "ntpsec-1.2.1" in text
    assert "2026-10-05 21:00 to 2026-10-06 21:00 UTC" in text
    assert "2026-10-06 21:03:00" in text
