"""
Phase 2 — PriceAnalysisService
Deterministic numerical calculations for price trends and change indicators.
No LLM involved — pure arithmetic.
"""
from typing import List, Optional, Dict
from datetime import date, timedelta
from .market_data_provider import MarketRecord, get_market_data_provider


class TrendResult:
    def __init__(
        self,
        crop: str,
        mandi: str,
        current_price: float,
        previous_price: Optional[float],
        change: Optional[float],
        change_percent: Optional[float],
        trend: str,  # "UP", "DOWN", "STABLE"
        source: str,
        source_status: str,
        latest_date: Optional[date],
    ):
        self.crop = crop
        self.mandi = mandi
        self.current_price = current_price
        self.previous_price = previous_price
        self.change = change
        self.change_percent = change_percent
        self.trend = trend
        self.source = source
        self.source_status = source_status
        self.latest_date = latest_date

    def to_dict(self) -> Dict:
        return {
            "crop": self.crop,
            "mandi": self.mandi,
            "current_price": self.current_price,
            "previous_price": self.previous_price,
            "change": round(self.change, 2) if self.change is not None else None,
            "change_percent": round(self.change_percent, 2) if self.change_percent is not None else None,
            "trend": self.trend,
            "source": self.source,
            "source_status": self.source_status,
            "latest_date": str(self.latest_date) if self.latest_date else None,
        }


STABLE_THRESHOLD_PCT = 0.5  # within 0.5% change is "stable"


def calculate_trend(current: float, previous: Optional[float]) -> tuple:
    """
    Returns (change, change_percent, trend_direction).
    trend_direction: "UP" | "DOWN" | "STABLE"
    """
    if previous is None or previous == 0:
        return None, None, "STABLE"
    change = current - previous
    change_pct = (change / previous) * 100
    if abs(change_pct) <= STABLE_THRESHOLD_PCT:
        direction = "STABLE"
    elif change_pct > 0:
        direction = "UP"
    else:
        direction = "DOWN"
    return round(change, 2), round(change_pct, 2), direction


class PriceAnalysisService:
    """
    Calculates price trends, changes, and summaries from market records.
    All calculations are deterministic — no AI/LLM.
    """

    def __init__(self):
        self._provider = get_market_data_provider()

    def get_crop_summary(
        self,
        crop: str,
        district: Optional[str] = None,
        mandi: Optional[str] = None,
        comparison_days: int = 7,
    ) -> Optional[Dict]:
        """
        Return a price summary for the crop with trend vs N days ago.
        """
        history = self._provider.get_price_history(
            crop=crop,
            district=district,
            mandi=mandi,
            limit=comparison_days + 5,
        )
        if not history:
            return None

        # Sort by date desc to get latest
        history.sort(key=lambda r: r.date, reverse=True)
        latest = history[0]

        # Find comparison record ~N days ago
        cutoff = latest.date - timedelta(days=comparison_days)
        older = [r for r in history if r.date <= cutoff]
        previous_price = older[0].modal_price if older else None

        change, change_pct, trend = calculate_trend(latest.modal_price, previous_price)

        return {
            "crop": crop,
            "mandi": latest.mandi,
            "district": latest.district,
            "latest_modal_price": latest.modal_price,
            "latest_min_price": latest.min_price,
            "latest_max_price": latest.max_price,
            "latest_date": str(latest.date),
            "previous_price": previous_price,
            "change": change,
            "change_percent": change_pct,
            "trend": trend.lower() if trend else "stable",
            "arrival_quantity": latest.arrival_quantity,
            "unit": latest.unit,
            "source": latest.source,
            "source_status": latest.source_status,
        }

    def get_trend_for_mandi(
        self,
        crop: str,
        mandi: str,
        comparison_days: int = 7,
    ) -> TrendResult:
        """Calculate price trend for a specific mandi."""
        history = self._provider.get_price_history(crop=crop, mandi=mandi, limit=comparison_days + 5)
        history.sort(key=lambda r: r.date, reverse=True)

        if not history:
            return TrendResult(crop, mandi, 0, None, None, None, "STABLE",
                               "No data", "DEMO", None)

        latest = history[0]
        cutoff = latest.date - timedelta(days=comparison_days)
        older = [r for r in history if r.date <= cutoff]
        prev_price = older[0].modal_price if older else None
        change, change_pct, trend = calculate_trend(latest.modal_price, prev_price)

        return TrendResult(
            crop=crop,
            mandi=mandi,
            current_price=latest.modal_price,
            previous_price=prev_price,
            change=change,
            change_percent=change_pct,
            trend=trend,
            source=latest.source,
            source_status=latest.source_status,
            latest_date=latest.date,
        )

    def get_history_for_chart(
        self,
        crop: str,
        mandi: Optional[str] = None,
        district: Optional[str] = None,
        days: int = 60,
    ) -> List[Dict]:
        """Return clean chronological data for frontend charts."""
        history = self._provider.get_price_history(
            crop=crop, mandi=mandi, district=district, limit=days
        )
        history.sort(key=lambda r: r.date)
        seen = set()
        result = []
        for r in history:
            key = f"{r.mandi}::{r.date}"
            if key in seen:
                continue
            seen.add(key)
            result.append({
                "date": str(r.date),
                "modal_price": r.modal_price,
                "min_price": r.min_price,
                "max_price": r.max_price,
                "arrival_quantity": r.arrival_quantity,
                "mandi": r.mandi,
                "crop": r.crop,
            })
        return result

    def get_multi_crop_dashboard_summary(
        self, district: str = "Rajkot"
    ) -> Dict:
        """
        Return cotton + groundnut summaries for a district — used by the dashboard.
        Replaces Phase 1 hardcoded demo_data.get_market_prices().
        """
        cotton = self.get_crop_summary("cotton", district=district)
        groundnut = self.get_crop_summary("groundnut", district=district)
        return {
            "cotton": cotton,
            "groundnut": groundnut,
            "source_status": "DEMO",
            "note": "DEMO DATA — Not live market prices",
        }


# Singleton
_analysis_service: Optional[PriceAnalysisService] = None

def get_price_analysis_service() -> PriceAnalysisService:
    global _analysis_service
    if _analysis_service is None:
        _analysis_service = PriceAnalysisService()
    return _analysis_service
