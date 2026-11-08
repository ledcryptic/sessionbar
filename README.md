# sessionbar

sessionbar reads a CSV of bars and reports the US equity session, a 9 EMA, a 21 EMA, and whether a squeeze is on. It is a personal study tool for those three readings.

## Session rules

Times are America/New_York. Each window includes its start and excludes its end.

| Session | Normal day | Early close |
|---|---|---|
| Premarket | 04:00–09:30 | 04:00–09:30 |
| Regular | 09:30–16:00 | 09:30–13:00 |
| After-hours | 16:00–20:00 | 13:00–17:00 |

Saturday and Sunday are closed. Full closes are New Year's Day, Martin Luther King Jr. Day, Washington's Birthday, Good Friday, Memorial Day, Juneteenth (from 2022), Independence Day, Labor Day, Thanksgiving, and Christmas. A Saturday holiday is observed Friday. A Sunday holiday is observed Monday.

Early closes are July 3, the Friday after Thanksgiving, and December 24, when that date is a weekday and is not already a full close.

## Indicators

The 9 and 21 EMAs seed from a simple average, then use the multiplier `2 / (length + 1)`.

A squeeze is on when the 20-period Bollinger Band is strictly inside the 20-period Keltner Channel. Bollinger width is 2 population standard deviations. Keltner width is 1.5 times the average true range. Momentum is the current endpoint of a linear regression of close against the bar-window midpoint. These are descriptions of the series, not trade instructions.

## CSV

```text
timestamp,open,high,low,close,volume
2026-11-04T10:00:00,10.00,10.20,9.90,10.10,1000
```

`volume` is optional. A timestamp without a timezone is read as Eastern. `datetime` is accepted in place of `timestamp`.

## Commands

From this directory, with Python 3.11 or newer:

```powershell
$env:PYTHONPATH = "src"
python -m sessionbar session 2026-11-04T10:15:00
python -m sessionbar indicators examples/sample_bars.csv
python -m sessionbar indicators examples/sample_bars.csv --all
python -m unittest discover -s tests
```

`session` prints the session name, whether the day is an early close, and why. `indicators` prints the last bar. `--all` prints every bar.

## License

MIT. You own this project.
