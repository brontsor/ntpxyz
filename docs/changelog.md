# ntpxyz

## Changelog

---

### 0.1.0

- Initial GitHub Release

### 0.1.2

The charts were occasionally sure about the wrong thing. This release makes them say what the file actually contains.

- A 13-column sysstats file no longer gets a guess. Tell ntpxyz who wrote it with `--dialect ntpd-4.2.8` or `--dialect ntpsec-1.2.1`. A 14-column file already knows: that extra column is NTPv1, added in NTPsec 1.2.2.
- The CPU chart was drawing seconds on a 0–100 percent axis, which made a busy clock look asleep. It now says seconds, and the line is visible.
- Offset and drift keep their sign. Fast and slow are not the same number.
- Charts no longer say "per hour" or "average" unless that is what the numbers are. If the file resets every 3600 seconds, the label says so. The dashed line is a median, and it admits it.
- A directory scan that is missing one stats type still plots the others. Telegram captions from that scan name the chart, instead of arriving blank.
- The example config used a period name the program does not accept, and a verbosity that was a word. Both are fixed.

Checked against two live clocks before this tag. The pictures matched the raw lines.

### 0.1.1

- added example config file: `./examples/config/config.json`
- added example plots: `./examples/plots/`
- updated README.md
