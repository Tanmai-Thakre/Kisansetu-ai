"""
Phase 2 — MandiComparisonService + BestMandiService
Compares multiple mandis by net effective price (modal - transport cost).
All logic is deterministic — no LLM.
"""
from typing import List, Optional, Dict
from .market_data_provider import get_market_data_provider
from .transport_service import get_transport_service, TransportCostResult
from .price_analysis_service import calculate_trend, get_price_analysis_service


class MandiComparisonEntry:
    def __init__(
        self,
        mandi: str,
        district: str,
        modal_price: float,
        min_price: float,
        max_price: float,
        net_price: float,
        transport_cost: float,
        distance_km: float,
        trend: str,
        change_percent: Optional[float],
        arrival_quantity: Optional[float],
        source_status: str,
        latest_date: Optional[str],
    ):
        self.mandi = mandi
        self.district = district
        self.modal_price = modal_price
        self.min_price = min_price
        self.max_price = max_price
        self.net_price = round(net_price, 2)
        self.transport_cost = round(transport_cost, 2)
        self.distance_km = distance_km
        self.trend = trend
        self.change_percent = change_percent
        self.arrival_quantity = arrival_quantity
        self.source_status = source_status
        self.latest_date = latest_date

    def to_dict(self) -> Dict:
        return {
            "mandi": self.mandi,
            "district": self.district,
            "modal_price": self.modal_price,
            "min_price": self.min_price,
            "max_price": self.max_price,
            "net_price": self.net_price,
            "transport_cost_per_quintal": self.transport_cost,
            "estimated_distance_km": self.distance_km,
            "trend": self.trend,
            "change_percent": self.change_percent,
            "arrival_quantity": self.arrival_quantity,
            "source_status": self.source_status,
            "latest_date": self.latest_date,
            "transport_note": "Estimated transport — not official rates",
        }


class MandiComparisonService:
    """
    Compares mandis for a given crop and quantity, ranked by net effective price.
    """

    def __init__(self):
        self._provider = get_market_data_provider()
        self._transport = get_transport_service()
        self._analysis = get_price_analysis_service()

    def compare(
        self,
        crop: str,
        quantity_quintals: float = 100.0,
        mandi_list: Optional[List[str]] = None,
        district: Optional[str] = None,
    ) -> List[MandiComparisonEntry]:
        """
        Compare mandis for a crop, ranked by net effective price.
        If mandi_list is None, compare all available mandis (or those in the district).
        """
        latest_records = self._provider.get_latest_prices(
            crop=crop, district=district
        )
        if not latest_records:
            return []

        # Filter to requested mandis if specified
        if mandi_list:
            ml_lower = [m.lower() for m in mandi_list]
            latest_records = [r for r in latest_records if r.mandi.lower() in ml_lower]

        entries: List[MandiComparisonEntry] = []
        for record in latest_records:
            # Transport cost calculation
            tc = self._transport.estimate_cost(
                mandi_name=record.mandi,
                modal_price=record.modal_price,
                quantity_quintals=quantity_quintals,
            )
            # Trend calculation for this mandi
            trend_result = self._analysis.get_trend_for_mandi(crop=crop, mandi=record.mandi)

            entries.append(MandiComparisonEntry(
                mandi=record.mandi,
                district=record.district,
                modal_price=record.modal_price,
                min_price=record.min_price,
                max_price=record.max_price,
                net_price=tc.net_price_per_quintal,
                transport_cost=tc.cost_per_quintal,
                distance_km=tc.distance_km,
                trend=trend_result.trend,
                change_percent=trend_result.change_percent,
                arrival_quantity=record.arrival_quantity,
                source_status=record.source_status,
                latest_date=str(record.date),
            ))

        # Sort by net price descending (best value first)
        entries.sort(key=lambda e: e.net_price, reverse=True)
        return entries


class BestMandiService:
    """
    Identifies the best mandi by net effective price (not just highest modal price).
    Returns a structured recommendation with an explanation.
    """

    def __init__(self):
        self._comparison = MandiComparisonService()

    def get_best_mandi(
        self,
        crop: str,
        quantity_quintals: float = 100.0,
        district: Optional[str] = None,
    ) -> Dict:
        """
        Return the best mandi and a deterministic explanation.
        """
        ranked = self._comparison.compare(
            crop=crop, quantity_quintals=quantity_quintals, district=district
        )
        if not ranked:
            return {"error": "No market data available", "best_mandi": None}

        best = ranked[0]
        highest_modal = max(ranked, key=lambda e: e.modal_price)

        # Build explanation
        if best.mandi == highest_modal.mandi:
            explanation = (
                f"{best.mandi} offers both the highest modal price "
                f"(₹{best.modal_price:,.0f}/q) and the best net return "
                f"(₹{best.net_price:,.0f}/q) after estimated transport."
            )
        else:
            explanation = (
                f"{best.mandi} has a lower modal price (₹{best.modal_price:,.0f}/q) "
                f"than {highest_modal.mandi} (₹{highest_modal.modal_price:,.0f}/q), "
                f"but lower estimated transport cost "
                f"(₹{best.transport_cost:,.0f}/q vs ₹{highest_modal.transport_cost:,.0f}/q) "
                f"results in a better net return of ₹{best.net_price:,.0f}/q."
            )

        return {
            "crop": crop,
            "quantity_quintals": quantity_quintals,
            "best_mandi": best.to_dict(),
            "explanation": explanation,
            "all_mandis": [e.to_dict() for e in ranked],
            "source_status": "DEMO",
            "note": "DEMO DATA — Estimated transport costs",
        }


# Singletons
_comparison_service: Optional[MandiComparisonService] = None
_best_mandi_service: Optional[BestMandiService] = None

def get_mandi_comparison_service() -> MandiComparisonService:
    global _comparison_service
    if _comparison_service is None:
        _comparison_service = MandiComparisonService()
    return _comparison_service

def get_best_mandi_service() -> BestMandiService:
    global _best_mandi_service
    if _best_mandi_service is None:
        _best_mandi_service = BestMandiService()
    return _best_mandi_service
