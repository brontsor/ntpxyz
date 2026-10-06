"""Golden lines are the spec. A non-empty frame is not.

Field names and units come from the writers, not from column count
alone:

- ntpd 4.2.8 ntp_util.c record_sys_stats, 13 fields, index 4 is
  packets for this host.
- NTPsec 1.2.1 ntp_util.c record_sys_stats, same 13 fields, index 4
  is packets processed. Width does not say which writer it was.
- NTPsec 1.2.2 added NTPv1 as field 14. That width is unique.
"""

from __future__ import annotations

import pandas as pd
import pytest

from ntpxyz.schema import (
    AmbiguousLayout,
    UnknownLayout,
    identify_layout,
)


# MJD 61319 is 2026-10-06. 75709.659 s past UTC midnight is 21:01:49.659.
LOOP_LINE = "61319 75709.659 0.000034823 -0.554337 0.000004469 0.001594 6"

# ntpd 4.2.8 sample shape, 13 fields. Index 4 is packets for this host.
CLASSIC_SYS_LINE = "50928 2132.543 3600 81965 9546 56 512 540 10 4 147 1 2"

# NTPsec 1.2.1 writer. Same width. Index 4 is packets processed.
NTPSEC_13_LINE = "61319 73766.659 3600 3319 431 408 55 0 2888 0 0 0 0"

# NTPsec 1.2.2+ writer. The last field is NTPv1.
NTPSEC_14_LINE = (
    "61319 73766.659 3600 128409 126054 100214 25845 9 2 0 5 3114 775 681"
)

USE_LINE = "61319 73766.659 3600 3.207 12.552 0 0 0 0 472 130618 13 0 16936"


def test_loopstats_golden_line_names_every_field() -> None:
    layout = identify_layout("loopstats", LOOP_LINE)

    assert layout.dialect == "loopstats"
    assert layout.names == (
        "mjd",
        "seconds",
        "offset",
        "drift",
        "jitter",
        "wander",
        "poll",
    )
    assert layout.units["offset"] == "s"
    assert layout.units["drift"] == "PPM"
    assert layout.units["jitter"] == "s"
    assert layout.units["wander"] == "PPM"
    assert layout.units["poll"] == "log2_s"
    assert layout.meanings["wander"] != layout.meanings["offset"]


def test_sysstats_13_columns_is_refused() -> None:
    with pytest.raises(AmbiguousLayout) as caught:
        identify_layout("sysstats", NTPSEC_13_LINE)

    message = str(caught.value)
    assert "13" in message
    assert "ntpd-4.2.8" in message
    assert "ntpsec-1.2.1" in message


def test_sysstats_13_accepts_an_explicit_dialect() -> None:
    ntpsec = identify_layout("sysstats", NTPSEC_13_LINE, dialect="ntpsec-1.2.1")
    classic = identify_layout("sysstats", CLASSIC_SYS_LINE, dialect="ntpd-4.2.8")

    assert ntpsec.names[4] == "packets_processed"
    assert classic.names[4] == "packets_for_this_host"
    assert "packets_processed" not in classic.names
    assert ntpsec.meanings["packets_processed"] != classic.meanings[
        "packets_for_this_host"
    ]


def test_sysstats_14_columns_is_ntpsec_with_ntpv1() -> None:
    layout = identify_layout("sysstats", NTPSEC_14_LINE)

    assert layout.dialect == "ntpsec-1.2.2"
    assert layout.names[-1] == "ntpv1_packets"
    assert layout.names[4] == "packets_processed"
    assert layout.units["ntpv1_packets"] == "#"
    assert layout.units["since_reset"] == "s"


def test_unknown_width_is_refused() -> None:
    with pytest.raises(UnknownLayout):
        identify_layout("sysstats", "50928 2132.543 3600 1 2 3")


def test_usestats_cpu_fields_are_seconds() -> None:
    layout = identify_layout("usestats", USE_LINE)

    assert layout.units["ru_utime"] == "s"
    assert layout.units["ru_stime"] == "s"
    assert layout.units["since_reset"] == "s"
    assert layout.units["ru_maxrss"] == "KB"
    assert "percent" not in layout.units["ru_utime"]


def test_loopstats_timestamp_is_mjd_plus_seconds_utc() -> None:
    from ntpxyz.parse import parse_stats

    frame = parse_stats("loopstats", _raw(LOOP_LINE))
    stamp = frame["timestamp"].iloc[0]

    assert stamp == pd.Timestamp("2026-10-06 21:01:49.659", tz="UTC")
    assert frame["offset"].iloc[0] == pytest.approx(0.000034823)
    assert frame["drift"].iloc[0] == pytest.approx(-0.554337)
    assert frame.attrs["dialect"] == "loopstats"


def test_signed_offset_is_kept() -> None:
    from ntpxyz.parse import parse_stats

    frame = parse_stats(
        "loopstats",
        _raw("61319 0.000 -0.000038648 -21.674 0.000001 0.001 4"),
    )

    assert frame["offset"].iloc[0] == pytest.approx(-0.000038648)
    assert frame["drift"].iloc[0] == pytest.approx(-21.674)


def test_ntpsec_14_names_the_processed_count() -> None:
    from ntpxyz.parse import parse_stats

    frame = parse_stats("sysstats", _raw(NTPSEC_14_LINE))

    assert frame["packets_processed"].iloc[0] == 126054
    assert frame["packets_received"].iloc[0] == 128409
    assert frame["ntpv1_packets"].iloc[0] == 681
    assert "packets_for_this_host" not in frame.columns
    assert frame.attrs["dialect"] == "ntpsec-1.2.2"


def test_sysstats_13_parse_refuses_without_a_dialect() -> None:
    from ntpxyz.parse import parse_stats

    with pytest.raises(AmbiguousLayout):
        parse_stats("sysstats", _raw(NTPSEC_13_LINE))


def test_explicit_dialect_names_the_13_column_host_field() -> None:
    from ntpxyz.parse import parse_stats

    ntpsec = parse_stats("sysstats", _raw(NTPSEC_13_LINE), dialect="ntpsec-1.2.1")
    classic = parse_stats("sysstats", _raw(CLASSIC_SYS_LINE), dialect="ntpd-4.2.8")

    assert ntpsec["packets_processed"].iloc[0] == 431
    assert classic["packets_for_this_host"].iloc[0] == 9546
    assert "packets_processed" not in classic.columns


def _raw(line: str) -> pd.DataFrame:
    return pd.DataFrame([line.split()])
