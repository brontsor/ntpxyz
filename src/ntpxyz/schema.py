"""Named layouts for NTP stats files.

A width is not a dialect. Two writers can emit the same number of
fields with different meanings, and one writer can change width
between releases. Callers get a named layout, or a refusal.
"""

from __future__ import annotations

from dataclasses import dataclass


class LayoutError(ValueError):
    """The line cannot be named without guessing."""


class UnknownLayout(LayoutError):
    """No registered writer emits this width."""


class AmbiguousLayout(LayoutError):
    """More than one writer emits this width."""


@dataclass(frozen=True)
class Field:
    name: str
    unit: str
    meaning: str


@dataclass(frozen=True)
class Layout:
    dialect: str
    stats_type: str
    fields: tuple[Field, ...]

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields)

    @property
    def units(self) -> dict[str, str]:
        return {field.name: field.unit for field in self.fields}

    @property
    def meanings(self) -> dict[str, str]:
        return {field.name: field.meaning for field in self.fields}


def _fields(*rows: tuple[str, str, str]) -> tuple[Field, ...]:
    return tuple(Field(*row) for row in rows)


_MJD = ("mjd", "MJD", "Modified Julian Day, days since 1858-11-17")
_SECONDS = ("seconds", "s", "seconds past UTC midnight")
_RESET = ("since_reset", "s", "seconds since the counters were last cleared")

_LOOP = _fields(
    _MJD,
    _SECONDS,
    ("offset", "s", "clock offset"),
    ("drift", "PPM", "frequency offset"),
    ("jitter", "s", "RMS jitter"),
    ("wander", "PPM", "RMS frequency jitter, not Allan deviation"),
    ("poll", "log2_s", "clock discipline time constant, log2 seconds"),
)

_SYS_13_SHARED = (
    _MJD,
    _SECONDS,
    _RESET,
    ("packets_received", "#", "packets received"),
)

_SYS_TAIL = (
    ("current_version", "#", "current protocol version packets"),
    ("old_version", "#", "older protocol version packets"),
    ("access_denied", "#", "access denied"),
    ("bad_format", "#", "bad length or format"),
    ("bad_authentication", "#", "bad authentication"),
    ("declined", "#", "declined"),
    ("rate_exceeded", "#", "rate exceeded"),
    ("kiss_o_death_packets", "#", "kiss-o'-death packets sent"),
)

# ntpd 4.2.8 monopt and ntp_util.c. Index 4 is replies to this host's
# own queries, not packets the daemon accepted.
_NTPD_428 = _fields(
    *_SYS_13_SHARED,
    ("packets_for_this_host", "#", "packets received in response to this host's queries"),
    *_SYS_TAIL,
)

# NTPsec 1.2.1 ntp_util.c record_sys_stats. Same width. Index 4 is
# stat_processed(), packets the daemon accepted.
_NTPSEC_121 = _fields(
    *_SYS_13_SHARED,
    ("packets_processed", "#", "packets processed"),
    *_SYS_TAIL,
)

# NTPsec 1.2.2 added stat_version1() as the last field. NEWS.adoc,
# 2022-12-28. Later 1.2.x releases, including 1.2.4, keep that field.
_NTPSEC_122 = _fields(
    *_SYS_13_SHARED,
    ("packets_processed", "#", "packets processed"),
    *_SYS_TAIL,
    ("ntpv1_packets", "#", "NTPv1 packets received"),
)

_USE = _fields(
    _MJD,
    _SECONDS,
    _RESET,
    ("ru_utime", "s", "CPU seconds in user mode since reset"),
    ("ru_stime", "s", "CPU seconds in system mode since reset"),
    ("ru_minflt", "#", "page faults, reclaim, no I/O"),
    ("ru_majflt", "#", "page faults, I/O"),
    ("ru_nswap", "#", "times the process was swapped out"),
    ("ru_inblock", "#", "file blocks in"),
    ("ru_outblock", "#", "file blocks out"),
    ("ru_nvcsw", "#", "context switches, wait"),
    ("ru_nivcsw", "#", "context switches, preempt"),
    ("ru_nsignals", "#", "signals received"),
    ("ru_maxrss", "KB", "maximum resident set size"),
)

_LAYOUTS: dict[tuple[str, str], Layout] = {
    ("loopstats", "loopstats"): Layout("loopstats", "loopstats", _LOOP),
    ("sysstats", "ntpd-4.2.8"): Layout("ntpd-4.2.8", "sysstats", _NTPD_428),
    ("sysstats", "ntpsec-1.2.1"): Layout("ntpsec-1.2.1", "sysstats", _NTPSEC_121),
    ("sysstats", "ntpsec-1.2.2"): Layout("ntpsec-1.2.2", "sysstats", _NTPSEC_122),
    ("usestats", "usestats"): Layout("usestats", "usestats", _USE),
}

# Widths that identify one dialect by themselves. 13 is absent on
# purpose: ntpd 4.2.8 and NTPsec 1.2.1 both write it.
_UNIQUE: dict[tuple[str, int], str] = {
    ("loopstats", 7): "loopstats",
    ("sysstats", 14): "ntpsec-1.2.2",
    ("usestats", 14): "usestats",
}

_AMBIGUOUS: dict[tuple[str, int], tuple[str, ...]] = {
    ("sysstats", 13): ("ntpd-4.2.8", "ntpsec-1.2.1"),
}


def identify_layout(stats_type: str, line: str, dialect: str | None = None) -> Layout:
    """Name the writer of one raw line.

    ``dialect`` is required when the width matches more than one
    writer. Passing a dialect that does not own that width is a
    refusal, not a rename.
    """
    width = len(line.split())
    if dialect is None:
        dialect = _dialect_for_width(stats_type, width)
    else:
        _require_dialect_owns_width(stats_type, dialect, width)
    try:
        return _LAYOUTS[(stats_type, dialect)]
    except KeyError as exc:
        raise UnknownLayout(
            f"no layout for {stats_type} dialect {dialect!r}"
        ) from exc


def _dialect_for_width(stats_type: str, width: int) -> str:
    unique = _UNIQUE.get((stats_type, width))
    if unique is not None:
        return unique
    choices = _AMBIGUOUS.get((stats_type, width))
    if choices is not None:
        listed = ", ".join(choices)
        raise AmbiguousLayout(
            f"{stats_type} width {width} matches {listed}; pass dialect"
        )
    raise UnknownLayout(f"{stats_type} width {width} matches no known writer")


def _require_dialect_owns_width(stats_type: str, dialect: str, width: int) -> None:
    layout = _LAYOUTS.get((stats_type, dialect))
    if layout is None:
        raise UnknownLayout(f"no layout for {stats_type} dialect {dialect!r}")
    if len(layout.fields) != width:
        raise UnknownLayout(
            f"{dialect} writes {len(layout.fields)} fields, line has {width}"
        )
