# ntpxyz

## Changelog

---

### 0.1.0

- Initial GitHub Release

### 0.1.4

This one does not redraw the charts you already checked. Those clocks store time in nanoseconds, and those pictures stay put.

- The tests used to be happy if a file produced a picture. They now check that a known line lands on the right second, that a file which could mean two things is refused, and that a missing stats type does not throw away the charts that were fine.
- Allan deviation was assuming every timestamp was counted in nanoseconds. On a clock that stores microseconds, one second was being read as a millisecond. It now measures the gap between the stamps it was given.

68 tests, green. No new pictures.

### 0.1.3

An hour is only an hour if the file says so. The packet charts were still drawing the raw count and hoping the label would do the math.

- Packet, version, and error charts are now per second of the interval on that line. On a normal hourly file, the old number divided by 3600 is the new one. A busy clock sits around 33 packets a second, not 120,000 of anything.
- The CPU title says what fraction of the interval those seconds were. Twelve seconds in an hour is not 12 percent. The line itself stays in seconds, so it does not glue itself to the floor of a percent axis.
- One clock for the whole run, so the three charts agree on when "today" ends.
- If the same hour shows up twice, ntpxyz says how many copies it dropped.

Checked on the two live clocks. The pictures matched the division.

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
