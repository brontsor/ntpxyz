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

import logging
import sys

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
        None
    """
    try:
        # we should never see timestamps from before ntp was released
        # or from the future
        lower_bound: pd.Timestamp = pd.Timestamp("1985-09-17")  # pyright: ignore[reportAssignmentType]
        # we shouldn't need +1 day, remove and test
        upper_bound: pd.Timestamp = pd.Timestamp.now() + pd.Timedelta(days=1)  # pyright: ignore[reportAssignmentType]
        timestamp: pd.Timestamp | pd.DatetimeIndex | pd.Series[pd.Timestamp] = (  # pyright: ignore[reportInvalidTypeArguments]
            pd.to_datetime(mjd, unit="D", origin="1858-11-17")
        )

        # for scalar timestamp
        if isinstance(timestamp, pd.Timestamp):
            if timestamp < lower_bound or timestamp > upper_bound:
                logging.critical(
                    f"mjd_to_timestamp: invalid date: {mjd!r},{timestamp!r}"
                )
                sys.exit(1)
            return timestamp

        # for a series or an array-like object of timestamps
        elif isinstance(timestamp, (pd.Series, pd.Index, np.ndarray)):
            invalid_mask = (timestamp < lower_bound) | (timestamp > upper_bound)
            if invalid_mask.any():
                # mjd_series: pd.Series = pd.Series(mjd)
                # invalid_values: pd.Series = mjd_series[invalid_mask]  # type: ignore[operator]
                logging.critical("mjd_to_timestamp: invalid dates encountered")
                sys.exit(1)
            return timestamp

    except pd.errors.ParserError:
        logging.critical(f"mjd_to_timestamp: Parsing error on: {mjd!r}")
        sys.exit(1)
    except TypeError:
        logging.critical(f"mjd_to_timestamp: TypeError: {type(mjd)!r}")
        sys.exit(1)
    except ValueError:
        logging.critical(f"mjd_to_timestamp: ValueError on: {mjd!r}")
        sys.exit(1)
    except Exception:
        logging.critical(f"mjd_to_timestamp: Exception on: {mjd!r}")
        sys.exit(1)


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
        None
    """
    try:
        # seconds will be at most < 1 day
        # we should never see negative timedeltas or
        # timedeltas of a day or greater
        lower_bound: pd.Timedelta | NaTType = pd.Timedelta(seconds=0)
        upper_bound: pd.Timedelta | NaTType = pd.Timedelta(days=1)
        time_of_day: pd.Timedelta | pd.Series[pd.Timedelta] | NaTType = pd.to_timedelta(  # pyright: ignore[reportInvalidTypeArguments]
            seconds, unit="s"
        )

        # for scalar timestamp
        if isinstance(time_of_day, pd.Timestamp):
            if time_of_day < lower_bound or time_of_day >= upper_bound:
                logging.critical(f"seconds_to_timedelta: invalid input: {seconds!r}")
                sys.exit(1)
            return time_of_day

        # for a series or an array-like object of Timedeltas
        elif isinstance(time_of_day, (pd.Series, pd.Index, np.ndarray)):
            invalid_mask: pd.Series[bool] = (time_of_day < lower_bound) | (  # type: ignore[operator]
                time_of_day >= upper_bound  # type: ignore[operator]
            )
            if invalid_mask.any():
                seconds_series: pd.Series = pd.Series(seconds)
                invalid_values: pd.Series = seconds_series[invalid_mask]  # pyright: ignore[reportAssignmentType]
                logging.critical(
                    f"seconds_to_timedelta: invalid input: {invalid_values.tolist()!r}"
                )
                sys.exit(1)
            return time_of_day

    except pd.errors.ParserError:
        logging.critical(f"seconds_to_timedelta: Parsing error on: {seconds!r}")
        sys.exit(1)
    except TypeError:
        logging.critical(f"seconds_to_timedelta: TypeError on: {type(seconds)!r}")
        sys.exit(1)
    except ValueError:
        logging.critical(f"seconds_to_timedelta: ValueError on: {seconds!r}")
        sys.exit(1)
    except Exception:
        logging.critical(f"seconds_to_timedelta: Exception on: {seconds!r}")
        sys.exit(1)

    # This line fixes Pyright — never executed, but makes the return type complete
    return pd.NaT  # or: raise RuntimeError("unreachable")


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
        None
    """
    try:
        full_timestamp = mjd_to_timestamp(stats[0]) + seconds_to_timedelta(stats[1])  # type: ignore [operator, arg-type]
        stats[0] = full_timestamp.dt.tz_localize("UTC")  # type: ignore[union-attr]
        stats = stats.drop(columns=[1])
        stats = stats.rename(columns={0: "timestamp"})
        return stats

    except TypeError:
        logging.critical("convert_dates: TypeError on DataFrame manipulation")
        sys.exit(1)
    except ValueError:
        logging.critical("convert_dates: ValueError on DataFrame manipulation")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"convert_dates: Exception on DataFrame manipulation {e!r}")
        sys.exit(1)


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
