# ntpxyz

## Release Targets

---

### 0.1.0 Targets

- Initial GitHub Release

### 0.1.1 Targets

- example config files
- example plots
- update README.md with fixes and inline example plots

### 0.1.2 Targets

- Remove `ensure_trailing_slash` from `io.py`
- Add custom period definitions
- add period or log file span description to Figures
- synchronize or consolidate `mjd_to_timestamp` and `seconds_to_timedelta`
- add example plots and update README.md

### 0.1.3 Targets

- cleanup input and output directories:
  - take config from `~/.config/ntpxyz/config.json` first, and setup precedence
  - create and use `~/.cache/ntpxyz/` as default location before current dir for writes
  - evaluate use of `appdirs` or `platformdirs`
  - perform better file clean up, especially on Telegram send
- refactor `send_to_telegram()`
  - account for file size and format limits
  - add retry logic
  - normalize return behavior to align with other functions

### 0.1.4 Targets

- pytest: ensure robust testing of bits that will change with `load_stats_from_directory` refactor
- Refactor `load_stats_from_directory` to take either `dir` or `file`
  - `load_stats_from_directory` becomes `load_stats`
  - `load_stats_from_file` becomes `read_file` or `load_file`
  - take a single `scanstats` argument that is evaluated as `dir` or `file`
  - roll complexity and redundancy out of main
  - ensure `--period` works in all cases, esp with individual files
  - do lists of dirs
- refactor `load_stats_from_file()`
  - becomes `read_file` or `load_file`
  - give stats_type a default of none
  - if we pass in a stats type, we don't try to detect_stats_type
  - if we don't pass in a stats type, we detect_stats_type
  - validate `stats_type`
- update `pyproject.toml`
  - verify and update `[keywords]`
  - verify and update `[classifiers]`

### 0.2.x Targets

- add parsing of additional stats types
- refactor argument parsing to `typer`, `click`
- add export of stats data to sqlite
- add `--logfile` argument
- add reverse telegram flag
- define a single `NOW` and use that for all stamps and calculations per run
- incrementing or date-stamped file names
- last 30/60/90 days vs last 365
- addition of simple moving average to certain plots
- explore improving plots with 2 sets of data
- produce summary of stats dir (number of files, date range, types of stats files, gaps)
- Synchronize README.md, docstrings, argparse help, and other bits
  - Review and normalize all text in `--help`
  - Review error messages
- ensure all functions have basic exception handling
- expand use of try/accept statements
- evaluate GitHub actions
- `pytest`: setup a test_ script for each module
- `pytest`: explore generating fake data with pandas: valid, invalid, huge amounts
- `pytest`: generation of plots from good, bad, and sparse data
- `pytest`: explore pytest-cov and add to `pyproject.toml` if needed
- py.typed
- evaluate: we return str "none", should return None (impacts hints if you might return None)
- test if cust_excepthook always catches exceptions in sub-modules
- add proper exports to __init__.py
- add `__all__ = [...]` to modules
  - update test scripts accordingly

### Future Targets

- TUI
- Support for all stats logs
- configuration of more plot formats
- Display extended help information
- simple flag to identify and validate a stats file
- flag to log in UTC vs. Local time
- compare two time periods
- compare two stats files of the same type
  - timeframe aligned vs non timefram aligned
  - explore correlations
- combined PDF files
- set custom name masks for stats types
- concurrent plotting and parsing and sending
- evaluate named logging instance

### Sandbox

- plot function improvements:
  - enable/disable grid
- Function to display telegram config info
  - output the config values and add a link to github with instructions
- Dark Mode theme swap
- flag to simply verify config file values validity (telegram tokens)
- explore proplot as replacement for matplotlib styling
- improve accounting for KoD packets, which are outbound
- watermark/version tag embedded in plots
- more robust stats file identification and validation
- add validate of `stats_type` before execution of function:
  - `load_stats_from_directory`
  - `validate_stats`
- plot palette as global var
- explore other plot arrangements, like 1x4
- ntpstats LLM
- Faker for data generation
