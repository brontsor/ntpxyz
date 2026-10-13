"""Operations for dealing with config files

Public Functions
----------------
load_config_from_file : open a config file, return a DataFrame with config values
parse_config : take the frame from load_config_from_file and extract requested values

Classes
-------
Config : centralize tracking of cli and json config elements

Notes
-----

See Also
--------

"""

from __future__ import annotations

import logging
from typing import TypedDict

import pandas as pd


# we instantiate a Config object to centralize tracking of cli and json config elements
class Config(TypedDict):
    chat_id: str  # config file only
    loadconfig: str  # cli only
    period: str
    savedir: str
    saveformat: str
    savename: str
    scandir: str
    scanfile: str  # cli only
    statstype: str  # cli only
    dialect: str  # cli only; required for a 13-column sysstats file
    telegram_token: str  # config file only
    telegram: bool
    verbose: int


def load_config_from_file(
    file_path: str,
) -> pd.DataFrame:
    """open a config file, return a DataFrame with config values

    Args:
        file_path: the location of the file to open.

    Returns:
        DataFrame containing key:value pairs
        index = key
        column 0 = value

    Raises:
        ValueError: the file cannot be read or parsed.
    """
    try:
        json_config: pd.DataFrame = pd.read_json(file_path, orient="index")
        json_config = json_config.rename(columns={0: "value"})
        return json_config
    except FileNotFoundError as exc:
        raise ValueError(f"config: File not found: {file_path!r}") from exc
    except PermissionError as exc:
        raise ValueError(
            f"config: Cannot load {file_path!r}: Permission denied"
        ) from exc
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"config: File is empty: {file_path!r}") from exc
    except pd.errors.ParserError as exc:
        raise ValueError(f"config: Error parsing file: {file_path!r}") from exc
    except Exception as exc:
        raise ValueError(f"config: Error parsing file: {file_path!r}") from exc


def parse_config(args: list[str], json_config: pd.DataFrame) -> dict[str, int | str]:
    """take the frame from load_config_from_file and extract requested values

    Args:
        args: a list of keys to extract from json_config
        json_config: the frame returned from load_config_from_file

    Returns:
        A Dict with key:pair values
        Extra keys in config file are ignored
        Requested keys with empty values are returned as ''
        Requested keys not present in the config are returned as ''

    Raises:
        ValueError: a requested key could not be read, or none were extracted.
    """
    config: dict[str, int | str] = {}

    for arg in args:
        try:
            logging.debug(f"parse_config: loading {arg!r} from config frame")
            config[arg] = json_config.loc[arg, "value"]  # type: ignore[assignment]
            if config[arg]:
                logging.debug(f"parse_config: located value for {arg!r}")
            else:
                logging.debug(f"parse_config: no value located for {arg!r}")
                config[arg] = ""
        except KeyError:
            logging.warning(f"parse_config: {arg!r} is not in the config")
            config[arg] = ""
        except NameError as exc:
            raise ValueError(
                f"parse_config: NameError reading config for {arg!r}"
            ) from exc
        except Exception as exc:
            raise ValueError(f"parse_config: Exception occurred: {exc!s}") from exc

    if config:
        return config
    raise ValueError("parse_config: No keys were extracted from config")
