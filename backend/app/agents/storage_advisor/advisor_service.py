"""
Phase 5 — StorageAdvisorService.

Orchestrates the SELL / STORE / PARTIAL_SELL pipeline by pulling live data
from Phase 2 (market prices), Phase 3 (forecasts), and Phase 4 (buyer offers).
All heavy arithmetic is delegated to decision_logic.py.
"""
from __future__ import annotations

from typing import Optional

from app.services.market_data_provider import get_market_data_provider
from app.services.transport_service    import get_transport_service
from app.forecasting.forecasting_service import get_forecasting_service
from app.agents.buyer_matching.matching_service import get_buyer_matching_service
from .decision_logic import make_decision, DEFAULT_STORAGE_COST_PER_QUINTAL


class StorageAdvisorService:
    """
    Phase 5 — Storage & Selling Timing Advisor.
    Pulls prices/forecasts from Phase 2/3/4 and applies deterministic rules.
    """

    def __init__(self):
        self._market  = get_market_data_provider()
        self._transport = get_transport_service()
        self._forecast  = get_forecasting_service()
        self._matching  = get_buyer_matching_service()

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_mandi_price(self, crop: str, mandi: str) -> Optional[float]:
        """Latest modal price from Phase 2 provider."""
        try:
            records = self._market.get_price_history(
                crop=crop.lower(), mandi=mandi, limit=3
            )
            if records:
                return float(records[-1].modal_price)
            latest = self._market.get_latest_prices(crop=crop.lower(), limit=10)
            if latest:
                return float(latest[0].modal_price)
        except Exception:
            pass
        return None

    def _get_forecasts(self, crop: str, mandi: str) -> dict:
        """7/15/30-day forecast from Phase 3."""
        try:
            result = self._forecast.forecast(crop, mandi)
            return {
                "forecast_7d":    result.forecast_7d,
                "forecast_15d":   result.forecast_15d,
                "forecast_30d":   result.forecast_30d,
                "confidence":     result.confidence,
                "insufficient":   result.insufficient_data,
            }
        except Exception:
            return {"forecast_7d": None, "forecast_15d": None, "forecast_30d": None,
                    "confidence": 50.0, "insufficient": True}

    def _get_best_buyer_price(self, crop: str) -> Optional[float]:
        """Highest buyer offer from Phase 4 demo data."""
        try:
            matches = self._matching.find_matches(crop=crop, top_n=3)
            if matches:
                prices = [m.offered_price for m in matches if m.offered_price]
                return max(prices) if prices else None
        except Exception:
            pass
        return None

    def _get_transport_cost(self, mandi: str, modal_price: float) -> float:
        """Net transport cost per quintal from Phase 2 transport service."""
        try:
            result = self._transport.estimate_cost(mandi, modal_price, quantity_quintals=1.0)
            return result.cost_per_quintal
        except Exception:
            return 50.0   # safe default

    # ── Public API ────────────────────────────────────────────────────────────

    def advise(
        self,
        crop:                      str,
        mandi:                     str,
        quantity:                  float,
        storage_cost_per_quintal:  Optional[float] = None,
        cash_urgency:              str = "MEDIUM",
        current_price_override:    Optional[float] = None,
        buyer_price_override:      Optional[float] = None,
    ) -> dict:
        """
        Full advisor pipeline. Returns complete structured recommendation dict.
        """
        crop_lower = crop.lower().strip()
        cash_urgency = cash_urgency.upper().strip()
        if cash_urgency not in ("LOW", "MEDIUM", "HIGH"):
            cash_urgency = "MEDIUM"

        # ── Fetch current price ───────────────────────────────────────────────
        current_price = current_price_override or self._get_mandi_price(crop_lower, mandi)
        if not current_price:
            # Hard fallback: use demo prices
            fallback = {"cotton": 7200.0, "groundnut": 6100.0}
            current_price = fallback.get(crop_lower, 6000.0)

        # ── Fetch forecasts ───────────────────────────────────────────────────
        fc = self._get_forecasts(crop_lower, mandi)
        forecast_7d  = fc["forecast_7d"]  or current_price
        forecast_15d = fc["forecast_15d"] or current_price
        forecast_30d = fc["forecast_30d"] or current_price
        confidence   = fc["confidence"]

        # ── Fetch best buyer ──────────────────────────────────────────────────
        buyer_price = buyer_price_override or self._get_best_buyer_price(crop_lower)

        # ── Transport cost (extra ₹/quintal if selling to mandi later) ────────
        transport_extra = self._get_transport_cost(mandi, current_price)

        # ── Storage cost default ──────────────────────────────────────────────
        sc = storage_cost_per_quintal if storage_cost_per_quintal is not None \
             else DEFAULT_STORAGE_COST_PER_QUINTAL

        # ── Run decision logic ────────────────────────────────────────────────
        result = make_decision(
            crop=crop_lower,
            quantity=quantity,
            current_price=current_price,
            buyer_price=buyer_price,
            forecast_7d=forecast_7d,
            forecast_15d=forecast_15d,
            forecast_30d=forecast_30d,
            storage_cost_per_quintal=sc,
            transport_extra=transport_extra,
            cash_urgency=cash_urgency,
            forecast_confidence=confidence,
        )

        # ── Augment with context ──────────────────────────────────────────────
        result["crop"]     = crop_lower
        result["mandi"]    = mandi
        result["quantity"] = quantity
        result["source_status"] = "DEMO"
        return result


# ── Singleton ─────────────────────────────────────────────────────────────────
_advisor_service = None


def get_advisor_service() -> StorageAdvisorService:
    global _advisor_service
    if _advisor_service is None:
        _advisor_service = StorageAdvisorService()
    return _advisor_service
