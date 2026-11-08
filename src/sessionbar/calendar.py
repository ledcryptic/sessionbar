"""NYSE cash-session clock.

Full closes follow the published holiday rules, observed on Friday when the
holiday is Saturday and on Monday when it is Sunday. Early closes are 13:00 ET
on July 3, the Friday after Thanksgiving, and December 24, when that date is a
weekday and is not already a full close.

Windows are half-open, start inclusive and end exclusive, in America/New_York:

- premarket 04:00–09:30
- regular 09:30–16:00, or 09:30–13:00 on an early close
- after-hours 16:00–20:00, or 13:00–17:00 on an early close
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

PREMARKET_START = time(4, 0)
REGULAR_START = time(9, 30)
REGULAR_END = time(16, 0)
EARLY_REGULAR_END = time(13, 0)
AFTER_HOURS_END = time(20, 0)
EARLY_AFTER_HOURS_END = time(17, 0)


@dataclass(frozen=True)
class SessionInfo:
    name: str
    early_close: bool
    reason: str


def nth_weekday(year: int, month: int, weekday: int, n: int) -> date:
    """nth weekday in a month. weekday: Monday=0. n starts at 1."""
    first = date(year, month, 1)
    offset = (weekday - first.weekday()) % 7
    return first + timedelta(days=offset + 7 * (n - 1))


def last_weekday(year: int, month: int, weekday: int) -> date:
    if month == 12:
        cursor = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        cursor = date(year, month + 1, 1) - timedelta(days=1)
    while cursor.weekday() != weekday:
        cursor -= timedelta(days=1)
    return cursor


def easter(year: int) -> date:
    """Gregorian Easter Sunday (Anonymous algorithm)."""
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    month = (h + l - 7 * m + 114) // 31
    day = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, month, day)


def _observed(day: date) -> date:
    if day.weekday() == 5:
        return day - timedelta(days=1)
    if day.weekday() == 6:
        return day + timedelta(days=1)
    return day


def full_holidays(year: int) -> set[date]:
    """Observed NYSE full closes for the calendar year of each holiday."""
    fixed = [
        date(year, 1, 1),
        nth_weekday(year, 1, 0, 3),
        nth_weekday(year, 2, 0, 3),
        easter(year) - timedelta(days=2),
        last_weekday(year, 5, 0),
        date(year, 7, 4),
        nth_weekday(year, 9, 0, 1),
        nth_weekday(year, 11, 3, 4),
        date(year, 12, 25),
    ]
    if year >= 2022:
        fixed.append(date(year, 6, 19))
    return {_observed(day) for day in fixed}


def is_full_holiday(day: date) -> bool:
    if day in full_holidays(day.year):
        return True
    # New Year's Day on Saturday is observed the previous Friday.
    return day in full_holidays(day.year + 1)


def early_close_dates(year: int) -> set[date]:
    candidates = [
        date(year, 7, 3),
        nth_weekday(year, 11, 3, 4) + timedelta(days=1),
        date(year, 12, 24),
    ]
    return {
        day
        for day in candidates
        if day.weekday() < 5 and not is_full_holiday(day)
    }


def is_early_close(day: date) -> bool:
    return day in early_close_dates(day.year)


def _as_eastern(moment: datetime) -> datetime:
    if moment.tzinfo is None:
        return moment.replace(tzinfo=ET)
    return moment.astimezone(ET)


def session_at(moment: datetime) -> SessionInfo:
    local = _as_eastern(moment)
    day = local.date()
    if day.weekday() >= 5:
        return SessionInfo("closed", False, "weekend")
    if is_full_holiday(day):
        return SessionInfo("closed", False, "holiday")

    early = is_early_close(day)
    clock = local.timetz().replace(tzinfo=None)
    regular_end = EARLY_REGULAR_END if early else REGULAR_END
    after_end = EARLY_AFTER_HOURS_END if early else AFTER_HOURS_END
    reason = "early_close" if early else "open"

    if PREMARKET_START <= clock < REGULAR_START:
        return SessionInfo("premarket", early, reason)
    if REGULAR_START <= clock < regular_end:
        return SessionInfo("regular", early, reason)
    if regular_end <= clock < after_end:
        return SessionInfo("after_hours", early, reason)
    return SessionInfo("closed", early, reason)
