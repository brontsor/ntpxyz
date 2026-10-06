"""Filesystem input / output handlers

Functions to handle the reading and writing of various files

Public Functions
----------------
check_directory : tests if an input string is a real directory on the filesystem
ensure_trailing_slash : Ensure a dir path ends with platform-appropriate separator
infer_type_from_path : Determine a stats type based on filename
validate_stats : for a given stats_type, validate the DataFrame matches some constraints
load_stats_from_file : open a file, perform basic sanity checks, return dataframe w
    file data
load_stats_from_directory : Load and combine all stats files of a given type from a
    directory
save_to_disk : Write a figure to disk

Notes
-----

See Also
--------

"""

from __future__ import annotations

import logging
import os
import pathlib
import sys

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from .time import compile_period, convert_dates

SUPPORTED_INPUTS: list[str] = ["loopstats", "sysstats", "usestats"]
SUPPORTED_OUTPUTS: list[str] = ["pdf", "png", "svg"]
DEFAULT_OUTPUT: str = SUPPORTED_OUTPUTS[1]
DEFAULT_OUTPUT_PREFIX: str = "ntpxyz"
EXPECTED_COLUMN_NUM: dict[str, int] = {
    "loopstats": 7,
    "sysstats": 13,
    "sysstats_new": 14,  # newer versions of NTPsec add a column
    "usestats": 14,
}


def check_directory(dir_path: str, mode: str = "read") -> bool:
    """tests if an input string is a real directory on the filesystem


    Args:
        dir_path: the path of the directory to check
        mode: if set to 'write', check write permissions
            note we don't actually make use of the default 'read' currently

    Returns:
        True, if dir_path is a directory and passes mode checks
        False otherwise

    Raises:
        None
    """
    try:
        path_to_check = pathlib.Path(dir_path)
    except TypeError:
        logging.error(f"check_directory: {dir_path!r} is not a valid path string")
        return False
    except Exception:
        logging.error(f"check_directory: Exception on {dir_path!r}")
        return False
    if not path_to_check.exists():
        logging.error(f"check_directory: {dir_path!r} does not exist")
        return False
    if not path_to_check.is_dir():
        logging.error(f"check_directory: {dir_path!r} is not a directory")
        return False
    if mode == "write" and not os.access(path_to_check, os.W_OK):
        logging.error(f"check_directory: {dir_path!r} is not writeable")
        return False

    return True


def ensure_trailing_slash(dir_path: str | os.PathLike[str]) -> str:
    """Ensure a dir path ends with platform-appropriate separator

    Args:
        dir_path (str): Directory path to process

    Returns:
        str: Path with a platform appropriate trailing separator

    Raises:
        None
    """
    # we are just checking the string, not the actual filesystem validity here
    # os.PathLike[str] is typed as an input as a safeguard
    # if a user ever does this, we error out
    if not isinstance(dir_path, str):
        logging.critical(
            f"ensure_trailing_slash: Invalid directory path: {dir_path!r} must be a string"
        )
        sys.exit(1)

    try:
        # Convert to Path object and ensure trailing separator
        path_to_check: pathlib.Path = pathlib.Path(dir_path)
        # Convert back to string with platform-specific separator
        return str(path_to_check) + os.sep
    except TypeError:
        logging.critical(f"ensure_trailing_slash: Invalid directory path: {dir_path!r}")
        sys.exit(1)
    except Exception:
        logging.critical(f"ensure_trailing_slash: Exception on: {dir_path!r}")
        sys.exit(1)


def infer_type_from_path(file_path: str) -> str:
    """Determine a stats type based on filename

    Right now, we rely on the filename to determine the type. The file name
    must contain the stats type. The following examples match for loopstats:
        loopstats
        loopstats.199912
        copy of loopstats.bak
    A file such as 'loop_stats' would not match.
    If checks fail, we return 'none'

    Args:
        file_path: the location of the stats file, same as passed to
            load_stats from file

    Returns:
        A string representing the stats type we would expect from this file:
            one of SUPPORTED_INPUTS or 'none'
            Note that validation is done in validate_stats, and SUPPORTED_INPUTS
            does not differentiate between 13/14 columns sysstats

    Raises:
        None
    """
    path: pathlib.Path = pathlib.Path(file_path)
    file_name: str = path.name
    matches: list[str] = []
    matches = [t for t in SUPPORTED_INPUTS if t.lower() in file_name.lower()]

    # primary match is on file name
    if len(matches) == 0:
        logging.debug(
            f"infer_type_from_path: Can't match stats type for file: {file_name!r}"
        )
        return "none"
    elif len(matches) > 1:
        # this would be a filename like 'loopstats_sysstats'
        logging.warning(f"infer_type_from_path: Poorly named file: {file_name!r}")
        return "none"
    else:
        return matches[0]


def validate_stats(stats_type: str, stats: pd.DataFrame) -> bool:
    """for a given stats_type, validate the DataFrame matches some constraints

    We perform a check to ensure all columns are numerical. This
    will need to be expanded and adjusted as we support more stats types.

    Before returning, we ensure that the stats DataFrame has the correct
    number of columns, and account for sysstats logs with 'ntpv1' column 14

    If checks fail, we return false, otherwise true

    Args:
        stats_type: the string returned from infer_type_from_path, which is
            going to be one of SUPPORTED_INPUTS
        stats: the DataFrame from load_stats_from_file

    Returns:
        bool

    Raises:
        None
    """
    # constraint errors
    # For currently supported file types, we expect only numerical values
    if stats.isnull().values.any():
        logging.warning(f"validate_stats:  Numeric data check failed: {stats_type!r}")
        return False
    # verify we've got the correct number of columns
    if (stats_type == "loopstats") and (
        stats.shape[1] == EXPECTED_COLUMN_NUM["loopstats"]
    ):
        return True
    elif (stats_type == "sysstats") and (
        stats.shape[1] == EXPECTED_COLUMN_NUM["sysstats"]
    ):
        return True
    elif (stats_type == "sysstats") and (
        stats.shape[1] == EXPECTED_COLUMN_NUM["sysstats_new"]
    ):
        return True
    elif (stats_type == "usestats") and (
        stats.shape[1] == EXPECTED_COLUMN_NUM["usestats"]
    ):
        return True
    else:
        logging.warning(f"validate_stats: Failed to match: {stats_type!r}")
        return False


def load_stats_from_file(stats_type: str, file_path: str) -> pd.DataFrame:
    """open a file, perform basic sanity checks, return dataframe w file data

    Args:
        stats_type: one of SUPPORTED_INPUTS or 'none'
        file_path: the location of the file to open. The file is expected to:
            have no header
            be space delimited
            contain only numerical data, which we store as float values

    Returns:
        DataFrame that has been:
            prepared by pd.read_csv()
            had its dates converted with convert_dates()

    Raises:
        None
    """
    try:
        stats = pd.read_csv(file_path, header=None, sep="\\s+", dtype=float)
    # filesystem errors
    # should never hit a FileNotFoundError here as we check on arg input
    except FileNotFoundError:
        logging.critical(f"load_stats_from_file: File not found: {file_path!r}")
        sys.exit(1)
    except PermissionError:
        logging.critical(
            f"load_stats_from_file: Cannot load {file_path!r}: Permission denied"
        )
        sys.exit(1)
    # parsing errors
    # we could pass on an EnptyDataError
    except pd.errors.EmptyDataError:
        logging.critical(f"load_stats_from_file: File is empty: {file_path!r}")
        sys.exit(1)
    except pd.errors.ParserError:
        logging.critical(f"load_stats_from_file: ParserError on file: {file_path!r}")
        sys.exit(1)
    # general handler
    except Exception:
        logging.critical(f"load_stats_from_file: Exception on file path: {file_path!r}")
        sys.exit(1)

    # future: if 'none' is passed in, we can try infer_type_from_path()
    # this would allow calling load_stats_from_file() w/o a stats argument
    # now: the check for 'none' already extant covers a condition where
    # none is passed in as a stats_type, which shouldn't happen
    if stats_type != "none":
        if validate_stats(stats_type, stats):
            stats = convert_dates(stats)
            return stats
        else:
            logging.critical(
                f"load_stats_from_file: validation failed for: {file_path!r}"
            )
            sys.exit(1)
    else:
        logging.critical(
            f"load_stats_from_file: unable to detect file type: {file_path!r}"
        )
        sys.exit(1)


def drop_duplicate_rows(stats: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Drop exact duplicate rows and report how many went away.

    NTP filegen hardlinks the current file under a dated name. A
    directory scan reads both and would otherwise plot the hour twice.
    """
    cleaned = stats.drop_duplicates().reset_index(drop=True)
    removed = len(stats) - len(cleaned)
    return cleaned, removed


def load_stats_from_directory(
    stats_type: str,
    dir_path: str,
    period: str | None = None,
    now: pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Load and combine all stats files of a given type from a directory
    Handles NTP hardlinks cleanly via drop_duplicates()

    Args:
        stats_type: one of SUPPORTED_INPUTS
        dir_path: a directory path string

    Returns:
        a DataFrame combining all of the stats data of type stats_type loaded
        from files in dir_path
        We exit on several error conditions

    Raises:
        None
    """
    if now is None:
        now = pd.Timestamp.now(tz="UTC")
    # directory is already checked for being valid on input from both
    # cli and config file, this check is redundant
    if not check_directory(dir_path, "read"):
        logging.critical(
            f"load_stats_from_directory: Directory not readable: {dir_path!r}"
        )
        sys.exit(1)

    dir_path_obj: pathlib.Path = pathlib.Path(dir_path)
    all_files: list[pathlib.Path] = sorted(
        f for f in dir_path_obj.iterdir() if f.is_file()
    )

    valid_files: list[pathlib.Path] = []
    for file in all_files:
        inferred_type: str = infer_type_from_path(str(file))
        if inferred_type == stats_type:
            valid_files.append(file)
            logging.debug(f"load_stats_from_directory: added {file!r}")

    if not valid_files:
        logging.critical(
            f"load_stats_from_directory: No {stats_type} files found in {dir_path}"
        )
        sys.exit(1)

    dfs: list[pd.DataFrame] = []
    for file in valid_files:
        df: pd.DataFrame = load_stats_from_file(stats_type, str(file))

        if df.empty:
            continue
        # df = convert_dates(df)
        dfs.append(df)
        logging.debug(f"load_stats_from_directory: {len(dfs)!r}")

    if not dfs:
        logging.critical(
            f"load_stats_from_directory: All {stats_type} files were empty or invalid in {dir_path}"
        )
        sys.exit(1)

    combined: pd.DataFrame = pd.concat(dfs, ignore_index=True)
    combined = combined.sort_values("timestamp").reset_index(drop=True)
    before_dedupe = len(combined)
    combined, removed = drop_duplicate_rows(combined)
    if removed:
        logging.info(
            f"Dropped {removed} duplicate rows from {before_dedupe} for {stats_type}"
        )
    logging.debug(f"load_stats_from_directory: {combined.head()}")

    if period:
        try:
            interval: pd.Interval[pd.Timestamp] = compile_period(period, now=now)  # type: ignore[assignment]
            mask: pd.Series = combined["timestamp"].between(
                interval.left, interval.right, inclusive="both"
            )
            before: int = len(combined)
            combined = combined[mask]  # pyright: ignore[reportAssignmentType]
            after: int = len(combined)
            logging.info(
                f"Period filter '{period}': kept {after}/{before} rows for {stats_type}"
            )
            if after == 0:
                logging.critical(
                    f"load_stats_from_directory: No data in requested period '{period}' for {stats_type} — nothing to plot"
                )
                sys.exit(1)
        except ValueError as e:
            logging.critical(
                f"load_stats_from_directory: Invalid period string '{period}': {e}"
            )
            sys.exit(1)

    # Defensive timestamp sanity checks. Same clock as the period filter.
    past_bound: pd.Timestamp = pd.Timestamp("1985-09-17", tz="UTC")  # pyright: ignore[reportAssignmentType]

    future_mask: pd.Series = combined["timestamp"] > now + pd.Timedelta(days=1)
    past_mask: pd.Series = combined["timestamp"] < past_bound

    if future_mask.any():
        logging.warning(
            f"load_stats_from_directory: {future_mask.sum()} rows have future timestamps (> +1 day) in {stats_type}"
        )
    if past_mask.any():
        logging.warning(
            f"load_stats_from_directory: {past_mask.sum()} rows are ancient {stats_type}"
        )

    return combined


def save_to_disk(fig: Figure, file_path: str, file_fmt: str = "png") -> None:
    """Write a figure to disk

    Args:
        fig: Figure
        file_path: the file name, without extension
        file_fmt: the file extension

    Returns:
        None, plot (figure) is saved to disk on successful completion

    Raises:
        None
    """
    try:
        fig.savefig(f"{file_path}.{file_fmt}")

    # filesystem errors
    except FileNotFoundError:
        logging.critical(f"save_to_disk: File not found: {file_path!r}")
        sys.exit(1)
    except PermissionError:
        logging.critical(f"save_to_disk: Load {file_path!r}: Permission denied")
        sys.exit(1)
    # parsing errors
    except ValueError as e:
        logging.critical(f"save_to_disk: Invalid savefig parameters: {str(e)!r}")
        sys.exit(1)
    except TypeError as e:
        logging.critical(f"save_to_disk: Bad arg type for savefig: {str(e)!r}")
        sys.exit(1)
    # plotting errors
    except RuntimeError as e:
        logging.critical(f"save_to_disk: Failed to render figure: {str(e)!r}")
        sys.exit(1)
    except Exception as e:
        logging.critical(f"save_to_disk: Exception {str(e)!r}")
        sys.exit(1)
    finally:
        plt.close(fig)
