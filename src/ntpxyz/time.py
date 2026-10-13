"""Constants and calculations realted to the passage of time

NTP has a unique way of storing timestamps in stats logs. We convert those to pandas
native formats for easy manupulation and calculation.

We also have to parse time-related arguments from the user, and handle those here.

Public Functions
----------------
mjd_to_timestamp : This method coverts MJD to a pd.Timestamp
seconds_to_timedelta : This method converts a number of seconds to a timedelta
convert_dates : Convert dates from ntp stats files into pd.Datetime
compile_period : Handler for the --period argument. Converts user input into pd.Interval

Notes
-----

See Also
--------
https://en.wikipedia.org/wiki/Julian_day

"""

from __future__ import annotations

import numpy as np
import pandas as pd
from pandas._libs import NaTType

VALID_PERIODS: dict[str, int] = {
    "rolling-day": 1,
    "rolling-week": 7,
    "rolling-month": 30,
    "rolling-quarter": 90,
    "rolling-year": 365,
}


def mjd_to_timestamp(
    mjd: int | list[pd.Timestamp] | np.ndarray | pd.Series,
) -> pd.Timestamp | pd.DatetimeIndex | pd.Series | NaTType:
    """This method coverts MJD to a pd.Timestamp
    ntp stats logs store timestamp in two columns. The first column is
    Modified Julian Date (MJD). MJD is the number of days since midnight on 1858-11-17

    Timestamps are kept naive in this function.

    Args:
        mjd: an integer value representing a number of days since MJD epoch
        accounts for both scalar and series inputs

    Returns:
        pd.Timestamp value representing the MJD date

    Raises:
        ValueError: the day is before NTP existed, or more than a day ahead.
    """
    lower_bound: pd.Timestamp = pd.Timestamp("1985-09-17")  # pyright: ignore[reportAssignmentType]
    upper_bound: pd.Timestamp = pd.Timestamp.now() + pd.Timedelta(days=1)  # pyright: ignore[reportAssignmentType]
    timestamp: pd.Timestamp | pd.DatetimeIndex | pd.Series[pd.Timestamp] = (  # pyright: ignore[reportInvalidTypeArguments]
        pd.to_datetime(mjd, unit="D", origin="1858-11-17")
    )

    if isinstance(timestamp, pd.Timestamp):
        if timestamp < lower_bound or timestamp > upper_bound:
            raise ValueError(f"mjd_to_timestamp: invalid date: {mjd!r},{timestamp!r}")
        return timestamp

    if isinstance(timestamp, (pd.Series, pd.Index, np.ndarray)):
        invalid_mask = (timestamp < lower_bound) | (timestamp > upper_bound)
        if invalid_mask.any():
            raise ValueError(f"mjd_to_timestamp: invalid date: {mjd!r}")
        return timestamp

    raise TypeError(f"mjd_to_timestamp: TypeError: {type(mjd)!r}")


def seconds_to_timedelta(
    seconds: float,
) -> pd.Timedelta | pd.TimedeltaIndex | pd.Series | NaTType:
    """This method converts a number of seconds to a timedelta
    ntp stats logs store timestamp in two columns. The second column is the number of
    seconds since midnight (partial day)

    Timestamps are kept naive in this function.

    Args:
        seconds: a number representing the number of seconds since midnight
        accounts for both scalar and series inputs

    Returns:
        pd.Timedelta value representing that length of time

    Raises:
        ValueError: the seconds are negative, or not strictly inside one day.
        TypeError: the value cannot be read as a timedelta.
    """
    lower_bound: pd.Timedelta | NaTType = pd.Timedelta(seconds=0)
    upper_bound: pd.Timedelta | NaTType = pd.Timedelta(days=1)
    time_of_day: pd.Timedelta | pd.Series[pd.Timedelta] | NaTType = pd.to_timedelta(  # pyright: ignore[reportInvalidTypeArguments]
        seconds, unit="s"
    )

    if isinstance(time_of_day, pd.Timedelta):
        if time_of_day < lower_bound or time_of_day >= upper_bound:
            raise ValueError(f"seconds_to_timedelta: {seconds!r} is outside one day")
        return time_of_day

    if isinstance(time_of_day, (pd.Series, pd.Index, np.ndarray)):
        invalid_mask: pd.Series[bool] = (time_of_day < lower_bound) | (  # type: ignore[operator]
            time_of_day >= upper_bound  # type: ignore[operator]
        )
        if invalid_mask.any():
            seconds_series: pd.Series = pd.Series(seconds)
            invalid_values: pd.Series = seconds_series[invalid_mask]  # pyright: ignore[reportAssignmentType]
            raise ValueError(
                f"seconds_to_timedelta: {invalid_values.tolist()!r} is outside one day"
            )
        return time_of_day

    raise TypeError(f"seconds_to_timedelta: TypeError on: {type(seconds)!r}")


def convert_dates(stats: pd.DataFrame) -> pd.DataFrame:
    """Convert dates from ntp stats files into pd.Datetime
    the first two columns in all ntp stats logs are:
    - date: stored in MJD format
    - time past midnight: stored in seconds with a decimal

    After calling functions that return naive timestamps, we localize the returned
    timestamps to UTC.

    Args:
        stats: a DataFrame with stats that has been loaded with load_stats_from_file()

    Returns:
        we return the modified DataFrame:
        - has a full timestamp in the first column
        - has the second column removed
        - We add a column name to the first column (0)
        - the remaining columns are numbered starting at 2, since we remove column 1

    Raises:
        ValueError: a day or a seconds field is outside the accepted range.
    """
    full_timestamp = mjd_to_timestamp(stats[0]) + seconds_to_timedelta(stats[1])  # type: ignore [operator, arg-type]
    stats[0] = full_timestamp.dt.tz_localize("UTC")  # type: ignore[union-attr]
    stats = stats.drop(columns=[1])
    stats = stats.rename(columns={0: "timestamp"})
    return stats


def compile_period(
    period: str,
    now: pd.Timestamp | None = None,
) -> pd.Interval[pd.Timestamp] | NaTType:
    """Handler for the --period argument. Converts user input into pd.Interval

    VALID_PERIODS is a Dict containing accepted period strings and their value in days.
    ``now`` freezes the right edge so a test can name the window.
    When it is omitted, the clock is read once, here.

    Args:
        period: str, represents a time period
        now: optional UTC timestamp. The window ends here.

    Returns:
        pd.Interval representing the users input

    Raises:
        ValueError: the period name is not in VALID_PERIODS.
    """

    if now is None:
        now = pd.Timestamp.now(tz="UTC")
    days: int = VALID_PERIODS.get(period, 0)
    if days == 0:
        raise ValueError(f"compile_period: Invalid period string: {period!r}")

    return pd.Interval(now - pd.Timedelta(days=days), now, closed="both")  # pyright: ignore[reportArgumentType]
