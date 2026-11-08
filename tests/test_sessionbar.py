import sys
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from sessionbar.bars import load_bars  # noqa: E402
from sessionbar.calendar import session_at  # noqa: E402
from sessionbar.ema import ema  # noqa: E402
from sessionbar.squeeze import squeeze  # noqa: E402

ET = ZoneInfo("America/New_York")


def et(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=ET)


class CalendarTests(unittest.TestCase):
    def test_regular_session(self) -> None:
        info = session_at(et("2026-11-04T10:15:00"))
        self.assertEqual(info.name, "regular")
        self.assertFalse(info.early_close)

    def test_boundaries(self) -> None:
        self.assertEqual(session_at(et("2026-11-04T03:59:00")).name, "closed")
        self.assertEqual(session_at(et("2026-11-04T04:00:00")).name, "premarket")
        self.assertEqual(session_at(et("2026-11-04T09:30:00")).name, "regular")
        self.assertEqual(session_at(et("2026-11-04T16:00:00")).name, "after_hours")
        self.assertEqual(session_at(et("2026-11-04T20:00:00")).name, "closed")

    def test_weekend(self) -> None:
        info = session_at(et("2026-11-07T10:15:00"))
        self.assertEqual(info.name, "closed")
        self.assertEqual(info.reason, "weekend")

    def test_thanksgiving_and_black_friday(self) -> None:
        closed = session_at(et("2026-11-26T10:00:00"))
        self.assertEqual(closed.reason, "holiday")
        early = session_at(et("2026-11-27T12:00:00"))
        self.assertEqual(early.name, "regular")
        self.assertTrue(early.early_close)
        self.assertEqual(session_at(et("2026-11-27T13:00:00")).name, "after_hours")
        self.assertEqual(session_at(et("2026-11-27T17:00:00")).name, "closed")

    def test_independence_day_observed_and_christmas_eve(self) -> None:
        # July 4 2026 is Saturday, so Friday July 3 is a full close.
        july3 = session_at(et("2026-07-03T10:00:00"))
        self.assertEqual(july3.reason, "holiday")
        eve = session_at(et("2026-12-24T11:00:00"))
        self.assertTrue(eve.early_close)
        self.assertEqual(eve.name, "regular")


class IndicatorTests(unittest.TestCase):
    def test_ema_seed_and_step(self) -> None:
        values = ema([1, 2, 3, 4, 5], 3)
        self.assertEqual(values[:2], [None, None])
        self.assertAlmostEqual(values[2], 2.0)
        self.assertAlmostEqual(values[3], 3.0)
        self.assertAlmostEqual(values[4], 4.0)

    def test_flat_range_is_a_squeeze(self) -> None:
        highs = [11.0] * 6
        lows = [9.0] * 6
        closes = [10.0] * 6
        bars = squeeze(highs, lows, closes, length=3)
        self.assertIsNone(bars[1].squeeze_on)
        self.assertTrue(bars[2].squeeze_on)
        self.assertAlmostEqual(bars[2].momentum, 0.0)
        self.assertAlmostEqual(ema(closes, 3)[-1], 10.0)


class CsvTests(unittest.TestCase):
    def test_sample_file(self) -> None:
        bars = load_bars(ROOT / "examples" / "sample_bars.csv")
        self.assertEqual(len(bars), 25)
        self.assertEqual(bars[0].session, "regular")
        self.assertEqual(bars[0].timestamp.tzinfo, ET)


if __name__ == "__main__":
    unittest.main()
