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

import logging
import sys

import pandas as pd

from .io import EXPECTED_COLUMN_NUM


def parse_loopstats(loopstats: pd.DataFrame) -> pd.DataFrame:
    """Sanity check loopstats data and add column headers

    Args:
        loopstats: DataFrame with loopstats data, that has been loaded with
        load_stats_from_file and has dates prepared with convert_dates

    Returns:
        The modified DataFrame, now with column headers

    Raises:
        None
    """
    # we removed one column when we converted dates
    try:
        if loopstats.shape[1] != EXPECTED_COLUMN_NUM["loopstats"] - 1:
            logging.critical("Error parsing loopstats: invalid number of cols.")
            sys.exit(1)
        loopstats = loopstats.rename(
            columns={
                2: "offset",  # seconds
                3: "drift",  # PPM
                4: "jitter",  # s
                5: "wander",  # PPM
                6: "constant",  # log2s
            }
        )
        return loopstats

    except TypeError:
        logging.critical("parse_loopstats: TypeError on DataFrame manipulation")
        sys.exit(1)
    except ValueError:
        logging.critical("parse_loopstats: ValueError on DataFrame manipulation")
        sys.exit(1)
    except Exception:
        logging.critical("parse_loopstats: Exception on DataFrame manipulation")
        sys.exit(1)


def parse_sysstats(sysstats: pd.DataFrame) -> pd.DataFrame:
    """Sanity check sysstats data and add column headers

    Args:
        sysstats: DataFrame with sysstats data, that has been loaded with
        load_stats_from_file and has dates prepared with convert_dates
        it may or may not have a column with data for ntpv1, which we
        accommodate for

    Returns:
        The modified DataFrame, now with column headers

    Raises:
        None
    """
    # we removed one column when we converted dates
    try:
        if sysstats.shape[1] == EXPECTED_COLUMN_NUM["sysstats_new"] - 1:
            sysstats = sysstats.rename(
                columns={
                    2: "since_reset",  # seconds
                    3: "packets_received",
                    4: "packets_processed",
                    5: "current_version",
                    6: "old_version",
                    7: "access_denied",
                    8: "bad_format",
                    9: "bad_authentication",
                    10: "declined",
                    11: "rate_exceeded",
                    12: "kiss_o_death_packets",
                    13: "ntpv1_packets",  # only present in newer NTPsec sysstats
                }
            )
        elif sysstats.shape[1] == EXPECTED_COLUMN_NUM["sysstats"] - 1:
            sysstats = sysstats.rename(
                columns={
                    2: "since_reset",  # seconds
                    3: "packets_received",
                    4: "packets_processed",
                    5: "current_version",
                    6: "old_version",
                    7: "access_denied",
                    8: "bad_format",
                    9: "bad_authentication",
                    10: "declined",
                    11: "rate_exceeded",
                    12: "kiss_o_death_packets",
                }
            )
        else:
            logging.critical("parse_sysstats: invalid number of cols.")
            sys.exit(1)
        return sysstats

    except TypeError:
        logging.critical("parse_sysstats: TypeError on DataFrame manipulation")
        sys.exit(1)
    except ValueError:
        logging.critical("parse_sysstats: ValueError on DataFrame manipulation")
        sys.exit(1)
    except Exception:
        logging.critical("parse_sysstats: Exception on DataFrame manipulation")
        sys.exit(1)


def parse_usestats(usestats: pd.DataFrame) -> pd.DataFrame:
    """Sanity check usestats data and add column headers

    Args:
        usestats: DataFrame with usestats data, that has been loaded with
        load_stats_from_file and has dates prepared with convert_dates

    Returns:
        The modified DataFrame, now with column headers

    Raises:
        None
    """
    # we removed one column when we converted dates
    try:
        if usestats.shape[1] != EXPECTED_COLUMN_NUM["usestats"] - 1:
            logging.critical("Error parsing usestats: invalid number of cols.")
            sys.exit(1)
        usestats = usestats.rename(
            columns={
                2: "since_reset",  # seconds
                3: "ru_utime",  # CPU seconds - user mode
                4: "ru_stime",  # CPU seconds - system
                5: "ru_minflt",  # page faults - reclaim/soft (no I/O)
                6: "ru_majflt",  # page faults - I/O
                7: "ru_nswap",  # process swapped out
                8: "ru_inblock",  # file blocks in
                9: "ru_outblock",  # file blocks out
                10: "ru_nvcsw",  # context switches, wait
                11: "ru_nivcsw",  # context switches, preempts
                12: "ru_nsignals",  # signals
                13: "ru_maxrss",  # resident set size, kilobytes
            }
        )
        return usestats

    except TypeError:
        logging.critical("parse_usestats: TypeError on DataFrame manipulation")
        sys.exit(1)
    except ValueError:
        logging.critical("parse_usestats: ValueError on DataFrame manipulation")
        sys.exit(1)
    except Exception:
        logging.critical("parse_usestats: Exception on DataFrame manipulation")
        sys.exit(1)
