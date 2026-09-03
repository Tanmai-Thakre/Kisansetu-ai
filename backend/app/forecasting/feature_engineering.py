"""
Phase 3 — Feature Engineering for the Mandi Price Forecasting Agent.

Generates supervised learning features from a PreparedSeries.
All features are computed from the PAST only — no future leakage.
No external dependencies beyond stdlib and numpy.
"""
from __future__ import annotations
from typing import List, Tuple
import math

from .data_preprocessor import PreparedSeries


# ── Feature windows ───────────────────────────────────────────────────────────
MA_SHORT  =  7   # 7-day moving average
MA_MEDIUM = 14   # 14-day moving average
MA_LONG   = 21   # 21-day moving average
LAG_DAYS  = [1, 3, 7, 14]   # lagged price features


def _moving_average(prices: List[float], window: int, idx: int) -> float:
    """Mean of the last `window` prices ending at idx (inclusive)."""
    start = max(0, idx - window + 1)
    sub   = prices[start: idx + 1]
    return sum(sub) / len(sub)


def _volatility(prices: List[float], window: int, idx: int) -> float:
    """Standard deviation of the last `window` prices ending at idx."""
    start = max(0, idx - window + 1)
    sub   = prices[start: idx + 1]
    if len(sub) < 2:
        return 0.0
    mean = sum(sub) / len(sub)
    variance = sum((x - mean) ** 2 for x in sub) / len(sub)
    return math.sqrt(variance)


def _momentum(prices: List[float], idx: int, lag: int) -> float:
    """Price momentum: price[idx] - price[idx - lag]."""
    prev_idx = idx - lag
    if prev_idx < 0:
        return 0.0
    return prices[idx] - prices[prev_idx]


def build_feature_matrix(
    series: PreparedSeries,
) -> Tuple[List[List[float]], List[float]]:
    """
    Build X (feature matrix) and y (target) from a PreparedSeries.

    Features per sample (all look-back only):
      - lag_1, lag_3, lag_7, lag_14       : lagged prices
      - ma_7, ma_14, ma_21                : moving averages
      - vol_7, vol_14                     : rolling volatility
      - momentum_7, momentum_14           : price momentum
      - norm_arrival                      : arrival quantity (normalised)
      - day_of_week                       : 0-6 (cyclical pattern proxy)

    Target: next-day modal price (t+1).

    Minimum index needed = MA_LONG - 1 = 20 (0-based), so at least 21 records.
    """
    prices   = series.prices
    arrivals = series.arrivals
    dates    = series.dates
    n        = series.n

    max_arrival = max(arrivals) if arrivals else 1.0

    X: List[List[float]] = []
    y: List[float] = []

    for i in range(MA_LONG - 1, n - 1):   # need at least MA_LONG history; target is i+1
        feats: List[float] = []

        # Lagged prices
        for lag in LAG_DAYS:
            idx = i - lag
            feats.append(prices[idx] if idx >= 0 else prices[0])

        # Moving averages
        feats.append(_moving_average(prices, MA_SHORT,  i))
        feats.append(_moving_average(prices, MA_MEDIUM, i))
        feats.append(_moving_average(prices, MA_LONG,   i))

        # Volatility
        feats.append(_volatility(prices, MA_SHORT,  i))
        feats.append(_volatility(prices, MA_MEDIUM, i))

        # Momentum
        feats.append(_momentum(prices, i, MA_SHORT))
        feats.append(_momentum(prices, i, MA_MEDIUM))

        # Arrival quantity (normalised 0–1)
        feats.append(arrivals[i] / max_arrival if max_arrival > 0 else 0.0)

        # Day-of-week cyclical encoding
        dow = dates[i].weekday()   # 0=Mon, 6=Sun
        feats.append(math.sin(2 * math.pi * dow / 7))
        feats.append(math.cos(2 * math.pi * dow / 7))

        X.append(feats)
        y.append(prices[i + 1])   # predict next day

    return X, y
