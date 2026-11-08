"""TTM-style squeeze from a local bar series.

A squeeze is on when the Bollinger Band sits strictly inside the Keltner
Channel. Bands use a simple average of close. Bollinger width is `bb_mult`
population standard deviations. Keltner width is `kc_mult` times the simple
average of true range. Momentum is the endpoint of a linear regression of
close minus the midpoint of the period's high/low average and the close average.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SqueezeBar:
    bb_upper: float | None
    bb_lower: float | None
    kc_upper: float | None
    kc_lower: float | None
    squeeze_on: bool | None
    momentum: float | None


def _sma(values: list[float], end: int, length: int) -> float:
    window = values[end - length + 1 : end + 1]
    return sum(window) / length


def _population_stdev(values: list[float], end: int, length: int) -> float:
    window = values[end - length + 1 : end + 1]
    mean = sum(window) / length
    var = sum((v - mean) ** 2 for v in window) / length
    return var**0.5


def _true_ranges(highs: list[float], lows: list[float], closes: list[float]) -> list[float]:
    out = [highs[0] - lows[0]]
    for i in range(1, len(closes)):
        tr = max(
            highs[i] - lows[i],
            abs(highs[i] - closes[i - 1]),
            abs(lows[i] - closes[i - 1]),
        )
        out.append(tr)
    return out


def _linreg_endpoint(values: list[float]) -> float:
    n = len(values)
    x_mean = (n - 1) / 2.0
    y_mean = sum(values) / n
    var_x = sum((i - x_mean) ** 2 for i in range(n))
    if var_x == 0:
        return y_mean
    cov = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(values))
    slope = cov / var_x
    intercept = y_mean - slope * x_mean
    return intercept + slope * (n - 1)


def squeeze(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    length: int = 20,
    bb_mult: float = 2.0,
    kc_mult: float = 1.5,
) -> list[SqueezeBar]:
    if length < 2:
        raise ValueError("length must be at least 2")
    n = len(closes)
    if not (len(highs) == n and len(lows) == n):
        raise ValueError("high, low, and close must be the same length")

    empty = SqueezeBar(None, None, None, None, None, None)
    out = [empty] * n
    if n < length:
        return out

    tr = _true_ranges(highs, lows, closes)
    for i in range(length - 1, n):
        basis = _sma(closes, i, length)
        dev = bb_mult * _population_stdev(closes, i, length)
        bb_upper = basis + dev
        bb_lower = basis - dev
        kc_range = _sma(tr, i, length)
        kc_upper = basis + kc_mult * kc_range
        kc_lower = basis - kc_mult * kc_range
        on = bb_lower > kc_lower and bb_upper < kc_upper

        highest = max(highs[i - length + 1 : i + 1])
        lowest = min(lows[i - length + 1 : i + 1])
        midline = ((highest + lowest) / 2.0 + basis) / 2.0
        deltas = [closes[j] - midline for j in range(i - length + 1, i + 1)]
        out[i] = SqueezeBar(
            bb_upper, bb_lower, kc_upper, kc_lower, on, _linreg_endpoint(deltas)
        )
    return out
