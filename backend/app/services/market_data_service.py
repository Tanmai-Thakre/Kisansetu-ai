"""
Phase 2 — MarketDataService
Orchestrates all market intelligence operations.
This is the single entry point for all API routes.
"""
from typing import List, Optional, Dict
from datetime import date
from .market_data_provider import get_market_data_provider
from .price_analysis_service import get_price_analysis_service
from .mandi_comparison_service import get_mandi_comparison_service, get_best_mandi_service
from .master_data import MANDI_MASTER_DATA, CROP_MASTER_DATA


class MarketDataService:
    """Central service for all market intelligence queries."""

    def __init__(self):
        self._provider = get_market_data_provider()
        self._analysis = get_price_analysis_service()
        self._comparison = get_mandi_comparison_service()
        self._best_mandi = get_best_mandi_service()

    # ── Prices ──────────────────────────────────────────────────────────────

    def get_latest_prices(
        self,
        crop: Optional[str] = None,
        district: Optional[str] = None,
        mandi: Optional[str] = None,
        page: int = 1,
        limit: int = 50,
    ) -> Dict:
        records = self._provider.get_latest_prices(crop=crop, district=district, mandi=mandi)
        total = len(records)
        start = (page - 1) * limit
        paged = records[start: start + limit]
        source_info = self._provider.get_source_info()
        return {
            "total": total,
            "page": page,
            "limit": limit,
            "data": [r.to_dict() for r in paged],
            **source_info,
        }

    def get_price_history(
        self,
        crop: str,
        mandi: Optional[str] = None,
        district: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 90,
    ) -> Dict:
        records = self._provider.get_price_history(
            crop=crop, mandi=mandi, district=district,
            start_date=start_date, end_date=end_date, limit=limit,
        )
        records.sort(key=lambda r: r.date)
        source_info = self._provider.get_source_info()
        return {
            "crop": crop,
            "mandi": mandi,
            "district": district,
            "count": len(records),
            "data": [r.to_dict() for r in records],
            **source_info,
        }

    def get_price_history_for_chart(
        self,
        crop: str,
        mandi: Optional[str] = None,
        district: Optional[str] = None,
        days: int = 60,
    ) -> List[Dict]:
        return self._analysis.get_history_for_chart(
            crop=crop, mandi=mandi, district=district, days=days
        )

    # ── Trends ──────────────────────────────────────────────────────────────

    def get_trends(
        self,
        crop: Optional[str] = None,
        district: Optional[str] = None,
        comparison_days: int = 7,
    ) -> List[Dict]:
        """Return trend summary for all mandis of a given crop."""
        crops = [crop] if crop else ["cotton", "groundnut"]
        results = []
        for c in crops:
            latest = self._provider.get_latest_prices(crop=c, district=district)
            seen_mandis = set()
            for record in latest:
                if record.mandi in seen_mandis:
                    continue
                seen_mandis.add(record.mandi)
                tr = self._analysis.get_trend_for_mandi(c, record.mandi, comparison_days)
                results.append(tr.to_dict())
        return results

    # ── Comparison ───────────────────────────────────────────────────────────

    def compare_mandis(
        self,
        crop: str,
        quantity: float = 100.0,
        mandi_list: Optional[List[str]] = None,
        district: Optional[str] = None,
    ) -> Dict:
        entries = self._comparison.compare(crop=crop, quantity_quintals=quantity,
                                            mandi_list=mandi_list, district=district)
        source_info = self._provider.get_source_info()
        return {
            "crop": crop,
            "quantity_quintals": quantity,
            "mandis": [e.to_dict() for e in entries],
            "count": len(entries),
            **source_info,
            "note": "DEMO DATA — Estimated transport costs. Not official rates.",
        }

    def get_best_mandi(
        self, crop: str, quantity: float = 100.0, district: Optional[str] = None
    ) -> Dict:
        return self._best_mandi.get_best_mandi(crop=crop, quantity_quintals=quantity, district=district)

    # ── Master data ──────────────────────────────────────────────────────────

    def get_mandis(self, district: Optional[str] = None) -> List[Dict]:
        mandis = MANDI_MASTER_DATA
        if district:
            mandis = [m for m in mandis if m["district"].lower() == district.lower()]
        return [{"name": m["name"], "short_name": m["short_name"],
                 "district": m["district"], "state": "Gujarat",
                 "latitude": m["lat"], "longitude": m["lon"]} for m in mandis]

    def get_crops(self) -> List[Dict]:
        return [{"name": c["name"], "display_name": c["display_name"],
                 "unit": c["unit"], "description": c["description"]}
                for c in CROP_MASTER_DATA]

    def get_districts(self) -> List[str]:
        return sorted(set(m["district"] for m in MANDI_MASTER_DATA))

    # ── Forecast input ───────────────────────────────────────────────────────

    def get_forecast_input(
        self,
        crop: str,
        mandi: str,
        days: int = 90,
    ) -> Dict:
        """
        Return clean time-series data suitable for future ML forecasting models.
        Phase 3 MandiForecastAgent will consume this endpoint.
        """
        records = self._provider.get_price_history(crop=crop, mandi=mandi, limit=days)
        records.sort(key=lambda r: r.date)
        source_info = self._provider.get_source_info()
        return {
            "crop": crop,
            "mandi": mandi,
            "days_requested": days,
            "records_available": len(records),
            "data": [
                {
                    "date": str(r.date),
                    "modal_price": r.modal_price,
                    "min_price": r.min_price,
                    "max_price": r.max_price,
                    "arrival_quantity": r.arrival_quantity,
                }
                for r in records
            ],
            **source_info,
            "note": (
                "Structured for Phase 3 MandiForecastAgent. "
                "DEMO DATA — not official market prices."
            ),
        }

    # ── Dashboard aggregate ──────────────────────────────────────────────────

    def get_dashboard_summary(self, district: str = "Rajkot") -> Dict:
        return self._analysis.get_multi_crop_dashboard_summary(district=district)


# Singleton
_market_service: Optional[MarketDataService] = None

def get_market_data_service() -> MarketDataService:
    global _market_service
    if _market_service is None:
        _market_service = MarketDataService()
    return _market_service
