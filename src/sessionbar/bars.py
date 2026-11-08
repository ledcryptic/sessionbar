"""Load OHLC bars from a local CSV. No network access."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from sessionbar.calendar import ET, session_at


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None

    @property
    def session(self) -> str:
        return session_at(self.timestamp).name


def _parse_timestamp(raw: str) -> datetime:
    text = raw.strip().replace("Z", "+00:00")
    moment = datetime.fromisoformat(text)
    if moment.tzinfo is None:
        return moment.replace(tzinfo=ET)
    return moment.astimezone(ET)


def load_bars(path: Path) -> list[Bar]:
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no header row")
        fields = {name.strip().lower(): name for name in reader.fieldnames}
        time_key = fields.get("timestamp") or fields.get("datetime")
        required = ("open", "high", "low", "close")
        missing = [name for name in required if name not in fields]
        if time_key is None:
            missing.insert(0, "timestamp")
        if missing:
            raise ValueError(f"{path} is missing columns: {', '.join(missing)}")

        volume_key = fields.get("volume")
        bars: list[Bar] = []
        for row in reader:
            if not (row.get(time_key) or "").strip():
                continue
            volume = None
            if volume_key and (row.get(volume_key) or "").strip():
                volume = float(row[volume_key])
            bars.append(
                Bar(
                    timestamp=_parse_timestamp(row[time_key]),
                    open=float(row[fields["open"]]),
                    high=float(row[fields["high"]]),
                    low=float(row[fields["low"]]),
                    close=float(row[fields["close"]]),
                    volume=volume,
                )
            )
    if not bars:
        raise ValueError(f"{path} has no bars")
    return bars
