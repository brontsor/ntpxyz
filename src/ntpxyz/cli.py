#!/usr/bin/env python3
"""Command Line Interface: arguments, configs, logging

Public Functions
----------------
setup_logging : setup logging config
change_logging_level : adjust logging level after startup
custom_excepthook : Custom Exception Hook
main : Setup and parse arguments, load file, branch to parse

Notes
-----

main will be simplified with the planned refactoring of:
- ntpxyz.io.load_stats_from_directory
- ntpxyz.io.load_config_from_file
and config parsing should be simplified with a migration to typer or click

See Also
--------

"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from importlib import metadata
from types import TracebackType
from typing import Any, cast

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.figure import Figure

from .config import Config, load_config_from_file, parse_config
from .io import (
    DEFAULT_OUTPUT,
    DEFAULT_OUTPUT_PREFIX,
    SUPPORTED_INPUTS,
    SUPPORTED_OUTPUTS,
    check_directory,
    ensure_trailing_slash,
    infer_type_from_path,
    load_stats_from_directory,
    load_stats_from_file,
    save_to_disk,
)
from .parse import parse_loopstats, parse_sysstats, parse_usestats
from .schema import AmbiguousLayout, UnknownLayout
from .plot.common import stamp_figure
from .plot.loopstats import plot_loopstats
from .plot.sysstats import plot_sysstats
from .plot.usestats import plot_usestats
from .telegram import send_to_telegram
from .time import VALID_PERIODS


def get_version() -> str:
    """Get the package version dynamically"""
    try:
        return metadata.version("ntpxyz")
    except metadata.PackageNotFoundError:
        return "dev"


def setup_logging(level: int = 3) -> None:
    """setup logging config

    Args:
        level: an int from 1-5
            1 == CRITICAL ... 5 == DEBUG

    Returns:
        None

    Raises:
        None
    """
    log_levels = {
        5: logging.DEBUG,
        4: logging.INFO,
        3: logging.WARNING,
        2: logging.ERROR,
        1: logging.CRITICAL,
    }
    level_num: int = log_levels.get(level, logging.WARNING)
    logging.basicConfig(
        level=level_num,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler()],
    )


def change_logging_level(level: int = 4) -> None:
    """adjust logging level after setup

    Args:
        level: an int from 1-5, verified by parser.add_argument
            1 == CRITICAL ... 5 == DEBUG

    Returns:
        None

    Raises:
        None
    """
    logger: logging.Logger = logging.getLogger()

    log_levels = {
        5: logging.DEBUG,
        4: logging.INFO,
        3: logging.WARNING,
        2: logging.ERROR,
        1: logging.CRITICAL,
    }
    level_num: int = log_levels.get(level, logging.INFO)
    logger.setLevel(level_num)

    for handler in logger.handlers:
        handler.setLevel(level_num)

    # Mute debug output from libraries
    if level_num == logging.DEBUG:
        logging.getLogger("findfont").setLevel(logging.INFO)

    # def custom_excepthook(exc_type, exc_value, exc_traceback) -> None:


def custom_excepthook(
    exc_type: type[BaseException],
    exc_value: BaseException,
    exc_traceback: TracebackType | None,
) -> None:
    """Custom Exception Hook

    We mask sys.excepthook with this to cover uncaught exceptions

    Args:
        See sys.excepthook

    Returns:
        See sys.excepthook

    Raises:
        See sys.excepthook
    """
    logging.exception(
        "Unhandled exception", exc_info=(exc_type, exc_value, exc_traceback)
    )
    print("Unexpected error, details logged.")
    sys.exit(1)


def _label_figure(
    fig: Figure,
    title: str,
    stats: pd.DataFrame,
    config: Config,
    generated: pd.Timestamp,
) -> None:
    """Stamp the chart with the run, not a second guess at the clock."""
    stamps = pd.to_datetime(stats["timestamp"], utc=True)
    span = (
        f"{stamps.min().strftime('%Y-%m-%d %H:%M')}"
        f" to {stamps.max().strftime('%Y-%m-%d %H:%M')} UTC"
    )
    stamp_figure(
        fig,
        title=title,
        savename=config["savename"],
        period=config["period"],
        dialect=str(stats.attrs.get("dialect", "")),
        span=span,
        generated=generated.strftime("%Y-%m-%d %H:%M:%S"),
    )


def main() -> None:
    """Setup and parse arguments, load file, convert dates, branch to parse
    Args:
        parsed via ArgumentParser below with help strings

    Returns:
        sys.exit(0) on successful completion
        sys.exit(1) on failed completion

    Raises:
        None
    """
    sys.excepthook = custom_excepthook
    setup_logging(4)

    # initialize defaults
    config: Config = Config(
        chat_id="",
        loadconfig="",
        period="",
        savedir="",
        saveformat="",
        savename="",
        scandir="",
        scanfile="",
        statstype="",
        dialect="",
        telegram_token="",
        telegram=False,
        verbose=4,
    )

    # parse arguments
    parser = argparse.ArgumentParser(
        prog="ntpxyz",
        description="""
            %(prog)s provides meaningful plots and easy exports of ntp stats logs.
            Currently, loopstats, sysstats, and usestats logs are supported.
            Log files can be specified directly or entire directories of stats logs
            can be scanned and parsed. The default behavior of %(prog)s is to generate
            plots for each type of stats file and save them in the current directory.
            The user can customize various option values, which can be
            passed in via command-line or sourced from a json config file.
            %(prog)s is designed to be run both interactively and also in unattended,
            schdeuled batch runs.
            """,
        epilog="""
            One of the following command-line options must be provided: --loadconfig,
            --scandir, or --scanfile.
            An option value sourced from file with --loadconfig will be overridden if a
            value for the same option is passed via command-line, allowing the user
            to set defaults for some options and provide dynamic values at will for
            others.
            """,
    )
    parser.add_argument(
        "-c",
        "--loadconfig",
        metavar="CFG",
        required=False,
        type=lambda x: x
        if os.path.isfile(x)
        else parser.error(f"{x!r} is not a valid file path"),
        help="load values from ConFiG file",
    )
    parser.add_argument(
        "-p",
        "--period",
        metavar="TIME",
        required=False,
        # type=str,
        type=lambda x: x
        if VALID_PERIODS.get(x, 0)
        else parser.error(
            f"{x!r} is not a valid period, use: {list(VALID_PERIODS.keys())!r}"
        ),
        help="specify a TIME period for scandir",
    )
    parser.add_argument(
        "-s",
        "--savedir",
        metavar="DIR",
        required=False,
        type=lambda x: x
        if check_directory(x, "write")
        else parser.error(f"{x!r} is not a valid directory path"),
        help="DIRectory in which to save output files",
    )
    parser.add_argument(
        # you need to add validation
        "-f",
        "--saveformat",
        metavar="FMT",
        required=False,
        type=lambda x: x
        if x in SUPPORTED_OUTPUTS
        else parser.error(f"FMT must be one of: {SUPPORTED_OUTPUTS!r}"),
        help=f"ForMaT of our output - one of: {SUPPORTED_OUTPUTS!r}",
    )
    parser.add_argument(
        "-n",
        "--savename",
        metavar="NAME",
        required=False,
        type=str,
        help=(f"prefix for output file NAME - default is {DEFAULT_OUTPUT_PREFIX!r}"),
    )
    parser.add_argument(
        "-d",
        "--scandir",
        metavar="DIR",
        required=False,
        type=lambda x: x
        if check_directory(x, "read")
        else parser.error(f"{x!r} is not a valid directory path"),
        help="scan a DIRectory for stats files and parse all valid matches",
    )
    parser.add_argument(
        "-l",
        "--scanfile",
        metavar="FILE",
        required=False,
        type=lambda x: x
        if os.path.isfile(x)
        else parser.error(f"{x!r} is not a valid file path"),
        help=(
            "path to a specific ntp statistics FILE for input"
            " - type is inferred from filename - this option overrides scandir"
        ),
    )
    parser.add_argument(
        "-y",
        "--statstype",
        metavar="TYPE",
        required=False,
        type=lambda x: x
        if any(y.startswith(x) for y in SUPPORTED_INPUTS)
        else parser.error(f"type must be one of: {SUPPORTED_INPUTS!r}"),
        help=(
            f"override detected stats type with one of: {SUPPORTED_INPUTS!r}"
            " - normally not required"
        ),
    )
    parser.add_argument(
        "-t",
        "--telegram",
        action="store_true",
        required=False,
        help="""
            send plot(s) to telegram - requires chat_id and telegram_token to be
            sourced from a ConFiG file
            """,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        metavar="1-5",
        required=False,
        type=int,
        choices=range(1, 6),
        help="set the logging level from 1 (Critical) to 5 (Debug), default 4 (Info)",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {get_version()}",
        help="Show version and exit",
    )
    parser.add_argument(
        "--dialect",
        metavar="DIALECT",
        required=False,
        choices=["ntpd-4.2.8", "ntpsec-1.2.1", "ntpsec-1.2.2"],
        help=(
            "name the sysstats writer when the width matches more than one. "
            "13 columns is ntpd-4.2.8 or ntpsec-1.2.1. 14 columns is ntpsec-1.2.2. "
            "A config file may set this. The command line wins."
        ),
    )
    args: argparse.Namespace = parser.parse_args()

    # parse arguments: first constraints
    if not args.loadconfig and not args.scandir and not args.scanfile:
        logging.critical(
            "One of the following must be provided as a command-line argument: "
            "--loadconfig, --scandir, or --scanfile. See --help for full useage."
        )
        sys.exit(1)
    elif args.scandir and args.scanfile:
        logging.critical(
            "The following arguments can't be combined: "
            "scandir and scanfile. See --help"
        )
        sys.exit(1)
    elif not args.loadconfig and args.telegram:
        logging.critical(
            "Telegram API keys must be loaded from a config file. See --help"
        )
        sys.exit(1)

    # parse arguments: only present in command line
    if args.scanfile:
        config["scanfile"] = args.scanfile
    if args.statstype:
        if args.statstype.startswith("loop"):
            config["statstype"] = "loopstats"
        elif args.statstype.startswith("sys"):
            config["statstype"] = "sysstats"
        elif args.statstype.startswith("use"):
            config["statstype"] = "usestats"

    # parse arguments: read in config file first
    # will will evaluate the rest of the cli arguments after config read
    if args.loadconfig:
        config["loadconfig"] = args.loadconfig
        values_in_config: list[str] = [
            "chat_id",
            "period",
            "savedir",
            "saveformat",
            "savename",
            "scandir",
            "dialect",
            "telegram",
            "telegram_token",
            "verbose",
        ]
        json_config: pd.DataFrame = load_config_from_file(config["loadconfig"])
        # cast-ing here to silence pyright
        cast(dict[str, Any], config).update(parse_config(values_in_config, json_config))

    if args.dialect:
        config["dialect"] = args.dialect
    if config["dialect"] and config["dialect"] not in (
        "ntpd-4.2.8",
        "ntpsec-1.2.1",
        "ntpsec-1.2.2",
    ):
        logging.critical(
            f"{config['dialect']!r} is not a known dialect. "
            "Use ntpd-4.2.8, ntpsec-1.2.1, or ntpsec-1.2.2."
        )
        sys.exit(1)

    # parse arguments: override config with values from the cli if they exist
    # we already validated --period if it was passed in via cli
    if args.period:
        config["period"] = args.period
    elif config["period"]:
        if not VALID_PERIODS.get(config["period"], 0):
            logging.critical(
                f"{config['period']!r} is not a valid period, use: {list(VALID_PERIODS.keys())!r}"
            )
            sys.exit(1)
    # if passed in, we've already checked savedir validity on the fs
    if args.savedir:
        config["savedir"] = args.savedir
    # if read in savedir from the config file, we need to check
    # it's validity just like we do with the cli argument
    elif config["savedir"]:
        if not check_directory(config["savedir"], "write"):
            logging.critical(f"{config['savedir']!r} is not a valid directory path")
            sys.exit(1)
    # otherwise we need to check the current directory for write privs
    elif not check_directory("", "write"):
        logging.critical("The local directory is not writeable - specify a --savedir")
        sys.exit(1)
    # in both cases, we make sure its a well formed dir string
    if config["savedir"]:
        # we just ensure that the string is bounded with a / at the end
        config["savedir"] = ensure_trailing_slash(config["savedir"])
    else:
        # if not passed, we default to the current directory
        config["savedir"] = ensure_trailing_slash("")
    # we checked saveformat on cli input
    if args.saveformat:
        config["saveformat"] = args.saveformat
    elif config["saveformat"]:
        if config["saveformat"] not in SUPPORTED_OUTPUTS:
            logging.critical(f"{config['saveformat']!r} is not a valid format")
            sys.exit(1)
    else:
        config["saveformat"] = DEFAULT_OUTPUT
    if args.savename:
        config["savename"] = args.savename
    elif not args.savename and not config["savename"]:
        # no value given
        config["savename"] = DEFAULT_OUTPUT_PREFIX
    # same logic as savedir
    if args.scandir:
        config["scandir"] = args.scandir
    elif config["scandir"]:
        if not check_directory(config["scandir"], "read"):
            logging.critical(f"{config['scandir']!r} is not a valid directory path")
            sys.exit(1)
    if args.telegram:
        config["telegram"] = True
        # should we disable telegram if it is set in the config and also cli?
    if args.verbose:
        config["verbose"] = args.verbose
    if config["verbose"]:
        change_logging_level(config["verbose"])

    # parse arguments: more constraints now that we have initialized config obj
    if config["period"] and not config["scandir"]:
        logging.critical('Argument "period" must be paired with scandir')
        sys.exit(1)
    elif not config["scandir"] and not config["scanfile"]:
        logging.critical("Either scanfile *or* scandir must be provided, neither given")
        sys.exit(1)
    elif config["telegram"] and not (config["telegram_token"] and config["chat_id"]):
        logging.critical(f"Telegram keys are not set: {config['loadconfig']!r}")
        sys.exit(1)
    if config["scandir"] and config["scanfile"]:
        logging.warning("scanfile provided at cli overrides scandir in config file")
        config["scandir"] = ""

    # the case-based code below will be simplified when we flatten the
    # file-ingestion logic:
    #  load_stats_from_directory() becomes load_stats()
    #   load_stats() just iterates once is the file list is of length 1
    #  load_stats_from_file() becomes read_file()
    #   read_file() is only called by load_stats(), which is called from main()
    # will need to refactor directory checking logic
    # parse a single 'scanstats' argument, or leave file vs dir for user

    fig: Figure = cast(Figure, None)
    stats: pd.DataFrame = pd.DataFrame()
    file_fmt: str = config["saveformat"]
    output_path: str
    telegram_status: tuple[bool, str]
    run_now: pd.Timestamp = pd.Timestamp.now(tz="UTC")

    # Pyright can't be sure we bind the value in the if/elif block below

    if config["scanfile"]:
        inferred_type: str = infer_type_from_path(config["scanfile"])

        # if we get a detected type of 'none', this is not a valid stats file
        logging.info(f"Inferred Type: {inferred_type!r}")
        if inferred_type == "none":
            logging.critical("load_stats_from_file returned type none")
            sys.exit(1)

        # parse arguments: if the user did not pass in a statstype, use the one
        # we detected. Otherwise, the user has overridden.
        # this would be a way to parse a uniquely named stats file that does
        # not pass our file-name based detection
        # Even if the user passes in another type, it still has to pass another
        # column check when it's passed to a parse_ function
        if not config["statstype"]:
            config["statstype"] = inferred_type
        stats = load_stats_from_file(config["statstype"], config["scanfile"])

        # run the plots
        logging.info(f"Plotting {config['statstype']!r}")
        title = f"NTP {config['statstype']}"
        if config["statstype"] == "loopstats":
            stats = parse_loopstats(stats)
            fig = plot_loopstats(stats)
        elif config["statstype"] == "sysstats":
            stats = parse_sysstats(stats, dialect=config["dialect"] or None)
            fig = plot_sysstats(stats)
        elif config["statstype"] == "usestats":
            stats = parse_usestats(stats)
            fig = plot_usestats(stats)
        logging.info(f"dialect={stats.attrs.get('dialect', '')}")
        _label_figure(fig, title, stats, config, run_now)

        # save the plot
        # replace this with argument value
        output_path = f"{config['savedir']}{config['savename']}_{inferred_type}"
        save_to_disk(fig, output_path, file_fmt)
        logging.info(f"Saved plots to: {output_path}.{file_fmt}")
        plt.close(fig)

        # send to telegram, if configured
        if config["telegram"]:
            logging.info("Sending to Telegram...")
            telegram_status = send_to_telegram(
                config["telegram_token"],
                config["chat_id"],
                f"{output_path}.{file_fmt}",
                f"{config['statstype']}",
            )
            if telegram_status[0]:
                logging.info(f"Telegram send OK : {telegram_status[1]!r}")
            else:
                logging.error(f"Telegram send failed: {telegram_status[1]!r}")

    elif config["scandir"]:
        plotted: list[str] = []
        skipped: list[str] = []
        for stats_type in SUPPORTED_INPUTS:
            try:
                stats = load_stats_from_directory(
                    stats_type, config["scandir"], config["period"], now=run_now
                )
                logging.info(f"Plotting {stats_type}")
                title = f"NTP {stats_type}"
                if stats_type == "loopstats":
                    stats = parse_loopstats(stats)
                    fig = plot_loopstats(stats)
                elif stats_type == "sysstats":
                    stats = parse_sysstats(stats, dialect=config["dialect"] or None)
                    fig = plot_sysstats(stats)
                elif stats_type == "usestats":
                    stats = parse_usestats(stats)
                    fig = plot_usestats(stats)
                logging.info(f"dialect={stats.attrs.get('dialect', '')}")
                _label_figure(fig, title, stats, config, run_now)
            except (AmbiguousLayout, UnknownLayout, ValueError) as exc:
                logging.error(f"Skipping {stats_type}: {exc}")
                skipped.append(stats_type)
                continue
            except SystemExit:
                logging.error(f"Skipping {stats_type}: loader refused the file")
                skipped.append(stats_type)
                continue

            output_path = f"{config['savedir']}{config['savename']}_{stats_type}"
            save_to_disk(fig, output_path, file_fmt)
            logging.info(f"Saved plots to: {output_path}.{file_fmt}")
            plt.close(fig)
            plotted.append(stats_type)

            if config["telegram"]:
                logging.info("Sending to Telegram...")
                telegram_status = send_to_telegram(
                    config["telegram_token"],
                    config["chat_id"],
                    f"{output_path}.{file_fmt}",
                    f"{stats_type}",
                )
                if telegram_status[0]:
                    logging.info(f"Telegram send OK : {telegram_status[1]!r}")
                else:
                    logging.error(f"Telegram send failed: {telegram_status[1]!r}")

        if skipped:
            logging.warning(f"Skipped: {skipped}")
        if not plotted:
            logging.critical("No stats type could be plotted")
            sys.exit(1)

    # clean up and exit nicely
    logging.info("ntpxyz run complete - Happy Wandering")
    logging.shutdown()
    sys.exit(0)


""" Check Namespace
"""
if __name__ == "__main__":
    main()
