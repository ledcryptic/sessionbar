"""Exponential moving average.

The first value is the simple average of the first `length` prices. After that
the multiplier is 2 / (length + 1).
"""

from __future__ import annotations


def ema(values: list[float], length: int) -> list[float | None]:
    if length < 1:
        raise ValueError("length must be at least 1")
    out: list[float | None] = [None] * len(values)
    if len(values) < length:
        return out

    seed = sum(values[:length]) / length
    out[length - 1] = seed
    k = 2.0 / (length + 1)
    prev = seed
    for i in range(length, len(values)):
        prev = values[i] * k + prev * (1.0 - k)
        out[i] = prev
    return out
