"""
Phase 3 — Data Preprocessor for the Mandi Price Forecasting Agent.

Transforms raw MarketRecord objects into a clean pandas-free numpy array
suitable for training. No LLM involved — pure data engineering.
"""
from __future__ import annotations
from typing import List, Optional, Tuple, Dict
from datetime import date, timedelta
import math

MIN_HISTORY_DAYS = 21   # minimum records needed for a reliable model
TRAIN_RATIO      = 0.80  # 80% train, 20% test (chronological)


class PreparedSeries:
    """
    A chronologically sorted, gap-filled time series ready for modelling.
    Prices and quantities are stored as plain lists (no external deps).
    """
    def __init__(
        self,
        dates:    List[date],
        prices:   List[float],
        arrivals: List[float],
        crop:     str,
        mandi:    str,
    ):
        self.dates    = dates
        self.prices   = prices
        self.arrivals = arrivals
        self.crop     = crop
        self.mandi    = mandi
        self.n        = len(dates)

    @property
    def is_sufficient(self) -> bool:
        return self.n >= MIN_HISTORY_DAYS

    def train_test_split(self) -> Tuple["PreparedSeries", "PreparedSeries"]:
        """Chronological split — never leak future data into training."""
        split = max(1, int(self.n * TRAIN_RATIO))
        train = PreparedSeries(
            self.dates[:split], self.prices[:split], self.arrivals[:split],
            self.crop, self.mandi,
        )
        test = PreparedSeries(
            self.dates[split:], self.prices[split:], self.arrivals[split:],
            self.crop, self.mandi,
        )
        return train, test


def _fill_missing_arrivals(arrivals: List[Optional[float]]) -> List[float]:
    """Forward-fill then backward-fill missing arrival quantities."""
    result: List[float] = []
    last_valid: float = 1000.0  # sensible default
    for v in arrivals:
        if v is not None and v > 0:
            last_valid = v
        result.append(last_valid)
    # backward fill from the start if needed
    if arrivals and arrivals[0] is None:
        first_valid = next((v for v in result if v > 0), 1000.0)
        result = [first_valid if v == 1000.0 else v for v in result]
    return result


def prepare_series(records) -> PreparedSeries:
    """
    Convert a list of MarketRecord objects into a clean PreparedSeries.

    Steps:
    1. Sort chronologically.
    2. Deduplicate — keep one record per date (highest arrival wins).
    3. Fill missing arrival_quantity values.
    4. Validate minimum length.
    """
    if not records:
        return PreparedSeries([], [], [], "unknown", "unknown")

    # Deduplicate by date
    by_date: Dict[date, object] = {}
    for r in records:
        d = r.date if isinstance(r.date, date) else date.fromisoformat(str(r.date))
        if d not in by_date:
            by_date[d] = r
        else:
            # prefer record with higher arrival quantity
            existing = by_date[d]
            existing_qty = existing.arrival_quantity or 0
            new_qty = r.arrival_quantity or 0
            if new_qty > existing_qty:
                by_date[d] = r

    sorted_records = sorted(by_date.values(), key=lambda r: r.date)

    dates    = [r.date for r in sorted_records]
    prices   = [float(r.modal_price) for r in sorted_records]
    raw_arr  = [r.arrival_quantity for r in sorted_records]
    arrivals = _fill_missing_arrivals(raw_arr)

    crop  = sorted_records[0].crop  if sorted_records else "unknown"
    mandi = sorted_records[0].mandi if sorted_records else "unknown"

    return PreparedSeries(dates, prices, arrivals, crop, mandi)
