"""Parsing for NTP stats logs

Properly configured, NTP will write out various statistics to incremental log files.
The functions here help handle those files, they:
    1) Require DataFrame output from load_stats_from_file(), convert_dates()
    2) Perform a basic sanity check on the DataFrame
    3) Name all of the columns correctly
    4) Exit if an error is encountered

We currentlty handle a subset of all stats types

Public Functions
----------------
parse_loopstats : handles loopstats data
parse_sysstats : handles sysstats data, from 13 and 14 column sysstats files
parse_usestats : handles usestats data

Notes
-----

See Also
--------
ntpxyz.io.load_stats_from_file
ntpxyz.time.convert_dates

"""

from __future__ import annotations

import pandas as pd

from .schema import Layout, identify_layout
from .time import convert_dates


def parse_stats(
    stats_type: str,
    raw: pd.DataFrame,
    dialect: str | None = None,
) -> pd.DataFrame:
    """Name every field on a raw stats frame.

    ``raw`` is the frame ``load_stats_from_file`` returns: one row per
    line, columns still numbered, dates not yet converted. A mixed
    file is a refusal. A width that matches two writers is a refusal
    unless ``dialect`` names one of them.
    """
    if raw.empty:
        raise ValueError(f"{stats_type} frame is empty")
    numeric = raw.apply(pd.to_numeric, errors="raise")
    widths = numeric.notna().sum(axis=1).unique()
    if len(widths) != 1:
        raise ValueError(f"{stats_type} has mixed widths: {sorted(widths)}")
    sample = " ".join(str(value) for value in numeric.iloc[0].dropna().tolist())
    layout = identify_layout(stats_type, sample, dialect=dialect)
    dated = convert_dates(numeric.copy())
    return _apply_layout(dated, layout)


def _apply_layout(dated: pd.DataFrame, layout: Layout) -> pd.DataFrame:
    expected = len(layout.fields) - 1
    if dated.shape[1] != expected:
        raise ValueError(
            f"{layout.dialect} expects {expected} columns after the date join, "
            f"got {dated.shape[1]}"
        )
    names = layout.names[2:]
    renamed = dated.rename(columns=dict(zip(range(2, 2 + len(names)), names, strict=True)))
    renamed.attrs["dialect"] = layout.dialect
    renamed.attrs["units"] = layout.units
    return renamed


def _name_dated(
    stats_type: str,
    dated: pd.DataFrame,
    dialect: str | None = None,
) -> pd.DataFrame:
    """Name a frame whose first column is already a timestamp.

    Width is checked on the raw field count, which is the dated width
    plus the seconds column ``convert_dates`` removed. The timestamp
    already on the frame is kept.
    """
    if "timestamp" not in dated.columns:
        raise ValueError(f"{stats_type} frame has no timestamp column")
    raw_width = dated.shape[1] + 1
    probe = " ".join(["0", "0.0", *["0"] * (raw_width - 2)])
    layout = identify_layout(stats_type, probe, dialect=dialect)
    if len(layout.fields) != raw_width:
        raise ValueError(
            f"{layout.dialect} writes {len(layout.fields)} fields, "
            f"frame has {raw_width}"
        )
    names = layout.names[2:]
    renamed = dated.rename(columns=dict(zip(range(2, 2 + len(names)), names, strict=True)))
    renamed.attrs["dialect"] = layout.dialect
    renamed.attrs["units"] = layout.units
    return renamed


def parse_loopstats(loopstats: pd.DataFrame) -> pd.DataFrame:
    """Sanity check loopstats data and add column headers

    Args:
        loopstats: DataFrame with loopstats data, that has been loaded with
        load_stats_from_file and has dates prepared with convert_dates

    Returns:
        The modified DataFrame, now with column headers

    Raises:
        AmbiguousLayout: 13-column sysstats with no dialect.
        UnknownLayout: a width no writer emits.
        ValueError: mixed widths, or a frame that does not match the layout.
    """
    return _name_dated("loopstats", loopstats)


def parse_sysstats(
    sysstats: pd.DataFrame, dialect: str | None = None
) -> pd.DataFrame:
    """Sanity check sysstats data and add column headers

    Args:
        sysstats: DataFrame with sysstats data, that has been loaded with
        load_stats_from_file and has dates prepared with convert_dates
        it may or may not have a column with data for ntpv1, which we
        accommodate for

    Returns:
        The modified DataFrame, now with column headers

    Raises:
        AmbiguousLayout: 13-column sysstats with no dialect.
        UnknownLayout: a width no writer emits.
    """
    return _name_dated("sysstats", sysstats, dialect=dialect)


def parse_usestats(usestats: pd.DataFrame) -> pd.DataFrame:
    """Sanity check usestats data and add column headers

    Args:
        usestats: DataFrame with usestats data, that has been loaded with
        load_stats_from_file and has dates prepared with convert_dates

    Returns:
        The modified DataFrame, now with column headers

    Raises:
        UnknownLayout: a width no writer emits.
    """
    return _name_dated("usestats", usestats)
