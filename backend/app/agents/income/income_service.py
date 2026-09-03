"""
Phase 7 — IncomeDashboardService.

Orchestrates the income calculation pipeline by pulling data from:
  Phase 2 → market/net price + transport cost
  Phase 3 → 7/15/30-day forecasts
  Phase 4 → best buyer offer
  Phase 5 → sell/store split recommendation
  Phase 6 → quality adjustment (price impact %)

No new market/forecast/buyer systems built here.
All heavy arithmetic is in calculations.py and scenarios.py.
"""
from __future__ import annotations

from typing import Optional

from app.services.market_data_provider import get_market_data_provider
from app.services.transport_service    import get_transport_service
from app.forecasting.forecasting_service import get_forecasting_service
from app.agents.buyer_matching.matching_service import get_buyer_matching_service
from app.agents.storage_advisor import get_advisor_service
from app.agents.quality.grading_rules import GRADE_PRICE_IMPACT

from .calculations import quality_adjusted_price
from .scenarios import (
    scenario_mandi,
    scenario_direct_buyer,
    scenario_store,
    scenario_partial_sell,
    rank_scenarios,
    best_scenario,
    income_difference,
    deterministic_summary,
    ScenarioResult,
)

# ── Default crop prices when no live data ─────────────────────────────────────
_CROP_DEFAULTS = {"cotton": 7200.0, "groundnut": 6100.0}


class IncomeService:
    """
    Phase 7 — Farmer Income Dashboard Agent.
    Builds all selling scenarios and returns a comprehensive income breakdown.
    """

    def __init__(self):
        self._market    = get_market_data_provider()
        self._transport = get_transport_service()
        self._forecast  = get_forecasting_service()
        self._matching  = get_buyer_matching_service()
        self._advisor   = get_advisor_service()

    # ── Private data helpers ──────────────────────────────────────────────────

    def _mandi_price(self, crop: str, mandi: str) -> float:
        try:
            records = self._market.get_price_history(crop=crop, mandi=mandi, limit=3)
            if records:
                return float(records[-1].modal_price)
            latest = self._market.get_latest_prices(crop=crop, limit=5)
            if latest:
                return float(latest[0].modal_price)
        except Exception:
            pass
        return _CROP_DEFAULTS.get(crop, 6000.0)

    def _transport_per_quintal(self, mandi: str, price: float) -> float:
        try:
            r = self._transport.estimate_cost(mandi, price, quantity_quintals=1.0)
            return float(r.cost_per_quintal)
        except Exception:
            return 50.0

    def _forecasts(self, crop: str, mandi: str) -> dict:
        try:
            r = self._forecast.forecast(crop, mandi)
            return {
                "7d":   float(r.forecast_7d),
                "15d":  float(r.forecast_15d),
                "30d":  float(r.forecast_30d),
                "confidence": float(r.confidence),
            }
        except Exception:
            base = _CROP_DEFAULTS.get(crop, 6000.0)
            return {"7d": base, "15d": base, "30d": base, "confidence": 50.0}

    def _best_buyer_price(self, crop: str) -> Optional[float]:
        try:
            matches = self._matching.find_matches(crop=crop, top_n=5)
            prices = [m.offered_price for m in matches if m.offered_price]
            return max(prices) if prices else None
        except Exception:
            return None

    def _advisor_split(self, crop: str, mandi: str, quantity: float,
                       storage_cost_per_quintal: float) -> dict:
        """Phase 5 — get sell/store percentage and best horizon."""
        try:
            result = self._advisor.advise(
                crop=crop,
                mandi=mandi,
                quantity=quantity,
                storage_cost_per_quintal=storage_cost_per_quintal,
                cash_urgency="MEDIUM",
            )
            return {
                "sell_pct":    result.get("sell_percentage", 50),
                "store_pct":   result.get("store_percentage", 50),
                "horizon_days": result.get("recommended_horizon_days", 15),
            }
        except Exception:
            return {"sell_pct": 50, "store_pct": 50, "horizon_days": 15}

    # ── Public API ────────────────────────────────────────────────────────────

    def calculate(
        self,
        crop:                      str,
        quantity:                  float,
        mandi:                     str            = "Rajkot APMC",
        storage_cost_per_quintal:  float          = 80.0,
        # Optional farmer-entered expenses
        transport_per_quintal_override: Optional[float] = None,
        labour_total:              float          = 0.0,
        packaging_total:           float          = 0.0,
        other_total:               float          = 0.0,
        # Optional price overrides (for testing / manual entry)
        mandi_price_override:      Optional[float] = None,
        buyer_price_override:      Optional[float] = None,
        # Optional quality data from Phase 6
        quality_price_impact_pct:  Optional[float] = None,
    ) -> dict:
        """
        Main calculation pipeline.
        Returns a complete structured income dashboard dict.
        """
        crop = crop.lower().strip()

        # ── 1. Prices from Phase 2 ────────────────────────────────────────────
        mandi_price = (mandi_price_override if mandi_price_override is not None
                       else self._mandi_price(crop, mandi))
        transport_pq = (
            transport_per_quintal_override
            if transport_per_quintal_override is not None
            else self._transport_per_quintal(mandi, mandi_price)
        )

        # ── 2. Forecasts from Phase 3 ─────────────────────────────────────────
        fc = self._forecasts(crop, mandi)

        # ── 3. Best buyer from Phase 4 ────────────────────────────────────────
        # None → fetch from Phase 4; 0 or explicit value → use as-is (0 disables buyer)
        if buyer_price_override is None:
            buyer_price = self._best_buyer_price(crop)
        else:
            buyer_price = buyer_price_override if buyer_price_override > 0 else None

        # ── 4. Phase 5 — sell/store split ─────────────────────────────────────
        split = self._advisor_split(crop, mandi, quantity, storage_cost_per_quintal)

        # ── 5. Quality-adjusted price from Phase 6 ────────────────────────────
        quality_price: Optional[float] = None
        if quality_price_impact_pct is not None:
            quality_price = quality_adjusted_price(mandi_price, quality_price_impact_pct)

        # ── 6. Build scenarios ────────────────────────────────────────────────

        # A — Sell at Mandi Now
        s_mandi = scenario_mandi(
            quantity=quantity,
            mandi_price=mandi_price,
            transport_per_quintal=transport_pq,
            labour_total=labour_total,
            packaging_total=packaging_total,
            other_total=other_total,
        )

        # B — Direct Buyer (only if a buyer price is available)
        s_buyer: Optional[ScenarioResult] = None
        if buyer_price and buyer_price > 0:
            s_buyer = scenario_direct_buyer(
                quantity=quantity,
                buyer_price=buyer_price,
                transport_per_quintal=transport_pq,
                labour_total=labour_total,
                packaging_total=packaging_total,
                other_total=other_total,
            )

        # C — Store scenarios (7 / 15 / 30 days)
        s_store_7  = scenario_store(
            quantity=quantity,
            forecast_price=fc["7d"],
            storage_cost_per_quintal=storage_cost_per_quintal,
            horizon_days=7,
            transport_per_quintal=transport_pq,
            labour_total=labour_total,
            packaging_total=packaging_total,
            other_total=other_total,
        )
        s_store_15 = scenario_store(
            quantity=quantity,
            forecast_price=fc["15d"],
            storage_cost_per_quintal=storage_cost_per_quintal,
            horizon_days=15,
            transport_per_quintal=transport_pq,
            labour_total=labour_total,
            packaging_total=packaging_total,
            other_total=other_total,
        )
        s_store_30 = scenario_store(
            quantity=quantity,
            forecast_price=fc["30d"],
            storage_cost_per_quintal=storage_cost_per_quintal,
            horizon_days=30,
            transport_per_quintal=transport_pq,
            labour_total=labour_total,
            packaging_total=packaging_total,
            other_total=other_total,
        )

        # D — Partial Sell (use Phase 5 split on best forecast horizon)
        s_partial = scenario_partial_sell(
            quantity=quantity,
            sell_price=mandi_price,
            forecast_price=fc[f"{split['horizon_days']}d"],
            sell_percentage=split["sell_pct"],
            storage_cost_per_quintal=storage_cost_per_quintal,
            horizon_days=split["horizon_days"],
            transport_per_quintal=transport_pq,
            labour_total=labour_total,
            packaging_total=packaging_total,
            other_total=other_total,
        )

        # ── 7. Collect all scenarios ──────────────────────────────────────────
        all_scenarios: list[ScenarioResult] = [
            s_mandi, s_store_7, s_store_15, s_store_30, s_partial,
        ]
        if s_buyer:
            all_scenarios.append(s_buyer)

        ranked     = rank_scenarios(all_scenarios)
        top        = best_scenario(all_scenarios)
        diff       = income_difference(all_scenarios)
        summary    = deterministic_summary(top, all_scenarios) if top else ""

        # ── 8. Cost breakdown ─────────────────────────────────────────────────
        cost_breakdown = {
            "transport":  s_mandi.transport_cost,
            "storage":    None,          # varies by scenario
            "labour":     labour_total if labour_total > 0 else None,
            "packaging":  packaging_total if packaging_total > 0 else None,
            "other":      other_total if other_total > 0 else None,
        }

        return {
            "crop":     crop,
            "mandi":    mandi,
            "quantity": quantity,

            # Current price references
            "mandi_price":        mandi_price,
            "transport_per_quintal": transport_pq,
            "buyer_price":        buyer_price,
            "forecast_7d":        fc["7d"],
            "forecast_15d":       fc["15d"],
            "forecast_30d":       fc["30d"],
            "forecast_confidence": fc["confidence"],

            # Quality adjustment (Phase 6)
            "quality_price_impact_pct": quality_price_impact_pct,
            "quality_adjusted_price":   quality_price,

            # Scenarios
            "scenarios": [s.to_dict() for s in ranked],

            # Summary
            "best_scenario":            top.name if top else None,
            "best_net_income":          top.net_income if top else None,
            "income_difference":        diff,
            "deterministic_summary":    summary,

            # Sell-now shortcut values (for dashboard top cards)
            "current_estimated_income": s_mandi.net_income,
            "best_buyer_income":        s_buyer.net_income if s_buyer else None,
            "partial_sell_income":      s_partial.net_income,

            # Cost breakdown
            "cost_breakdown": cost_breakdown,

            # Input echo
            "inputs": {
                "storage_cost_per_quintal": storage_cost_per_quintal,
                "labour_total":    labour_total,
                "packaging_total": packaging_total,
                "other_total":     other_total,
            },

            "source_status": "DEMO",
            "disclaimer": (
                "All income figures are estimates based on available market data. "
                "Actual income may differ. This is not financial advice."
            ),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────
_income_service: Optional[IncomeService] = None


def get_income_service() -> IncomeService:
    global _income_service
    if _income_service is None:
        _income_service = IncomeService()
    return _income_service
