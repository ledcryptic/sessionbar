"""Command line for the session clock and the bar indicators."""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from pathlib import Path

from sessionbar.bars import load_bars
from sessionbar.calendar import session_at
from sessionbar.ema import ema
from sessionbar.squeeze import squeeze


def _cmd_session(moment: datetime) -> int:
    info = session_at(moment)
    print(
        f"{info.name} early_close={str(info.early_close).lower()} reason={info.reason}"
    )
    return 0


def _fmt(value: float | None) -> str:
    if value is None:
        return ""
    return f"{value:.4f}"


def _cmd_indicators(path: Path, show_all: bool) -> int:
    bars = load_bars(path)
    closes = [bar.close for bar in bars]
    ema9 = ema(closes, 9)
    ema21 = ema(closes, 21)
    bands = squeeze(
        [bar.high for bar in bars],
        [bar.low for bar in bars],
        closes,
    )
    rows = range(len(bars)) if show_all else range(len(bars) - 1, len(bars))
    print("timestamp,session,close,ema9,ema21,squeeze,momentum")
    for i in rows:
        bar = bars[i]
        band = bands[i]
        squeeze_text = "" if band.squeeze_on is None else str(band.squeeze_on).lower()
        print(
            ",".join(
                [
                    bar.timestamp.isoformat(),
                    bar.session,
                    f"{bar.close:.4f}",
                    _fmt(ema9[i]),
                    _fmt(ema21[i]),
                    squeeze_text,
                    _fmt(band.momentum),
                ]
            )
        )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sessionbar")
    sub = parser.add_subparsers(dest="command", required=True)

    session = sub.add_parser("session", help="name the NYSE session at a timestamp")
    session.add_argument("timestamp", help="ISO timestamp; naive values are Eastern")

    indicators = sub.add_parser(
        "indicators", help="9 EMA, 21 EMA, and squeeze from a local CSV"
    )
    indicators.add_argument("csv", type=Path)
    indicators.add_argument(
        "--all", action="store_true", help="print every bar instead of the last"
    )

    args = parser.parse_args(argv)
    try:
        if args.command == "session":
            text = args.timestamp.replace("Z", "+00:00")
            return _cmd_session(datetime.fromisoformat(text))
        return _cmd_indicators(args.csv, args.all)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
