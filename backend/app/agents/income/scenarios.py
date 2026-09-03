"""
Phase 7 — Scenario builders.

Four selling scenarios:
  A — Sell at Mandi Now
  B — Direct Buyer
  C — Store and Sell Later (7 / 15 / 30 days)
  D — Partial Sell + Partial Storage

All data is sourced from Phase 2-6 services.
No new market/forecast/buyer systems built here.
"""
from __future__ import annotations

from typing import List, Optional

from .calculations import build_scenario, ScenarioResult, quality_adjusted_price


# ── Shared cost helper ────────────────────────────────────────────────────────

def _farmer_costs(
    quantity: float,
    transport_per_quintal: float,
    labour_total: float,
    packaging_total: float,
    other_total: float,
) -> dict:
    """Return cost dict scaled correctly for a full batch sale."""
    return {
        "transport":  round(quantity * transport_per_quintal, 2),
        "labour":     labour_total,
        "packaging":  packaging_total,
        "other":      other_total,
    }


# ── Scenario A — Sell at Mandi Now ───────────────────────────────────────────

def scenario_mandi(
    quantity:             float,
    mandi_price:          float,
    transport_per_quintal: float,
    labour_total:         float = 0.0,
    packaging_total:      float = 0.0,
    other_total:          float = 0.0,
) -> ScenarioResult:
    c = _farmer_costs(quantity, transport_per_quintal, labour_total, packaging_total, other_total)
    return build_scenario(
        name="Sell Now (Mandi)",
        quantity=quantity,
        selling_price=mandi_price,
        transport=c["transport"],
        storage=0.0,
        labour=c["labour"],
        packaging=c["packaging"],
        other=c["other"],
        notes=["Current mandi price; transport to mandi included."],
    )


# ── Scenario B — Direct Buyer ─────────────────────────────────────────────────

def scenario_direct_buyer(
    quantity:              float,
    buyer_price:           float,
    transport_per_quintal: float,
    labour_total:          float = 0.0,
    packaging_total:       float = 0.0,
    other_total:           float = 0.0,
) -> ScenarioResult:
    c = _farmer_costs(quantity, transport_per_quintal, labour_total, packaging_total, other_total)
    return build_scenario(
        name="Direct Buyer",
        quantity=quantity,
        selling_price=buyer_price,
        transport=c["transport"],
        storage=0.0,
        labour=c["labour"],
        packaging=c["packaging"],
        other=c["other"],
        notes=["Best available direct-buyer offer price (estimated)."],
    )


# ── Scenario C — Store and Sell Later ─────────────────────────────────────────

def scenario_store(
    quantity:                  float,
    forecast_price:            float,
    storage_cost_per_quintal:  float,
    horizon_days:              int,
    transport_per_quintal:     float,
    labour_total:              float = 0.0,
    packaging_total:           float = 0.0,
    other_total:               float = 0.0,
) -> ScenarioResult:
    # Storage cost scales with horizon (proportional to 30-day monthly rate)
    storage_total = round(quantity * storage_cost_per_quintal * (horizon_days / 30.0), 2)
    c = _farmer_costs(quantity, transport_per_quintal, labour_total, packaging_total, other_total)
    return build_scenario(
        name=f"Store {horizon_days} Days",
        quantity=quantity,
        selling_price=forecast_price,
        transport=c["transport"],
        storage=storage_total,
        labour=c["labour"],
        packaging=c["packaging"],
        other=c["other"],
        notes=[
            f"{horizon_days}-day price forecast (estimated).",
            f"Storage cost: ₹{storage_cost_per_quintal:.0f}/qtl/month proportional.",
        ],
    )


# ── Scenario D — Partial Sell + Partial Storage ───────────────────────────────

def scenario_partial_sell(
    quantity:                  float,
    sell_price:                float,
    forecast_price:            float,
    sell_percentage:           int,         # 0–100
    storage_cost_per_quintal:  float,
    horizon_days:              int,
    transport_per_quintal:     float,
    labour_total:              float = 0.0,
    packaging_total:           float = 0.0,
    other_total:               float = 0.0,
) -> ScenarioResult:
    sell_qty  = round(quantity * sell_percentage / 100, 4)
    store_qty = round(quantity - sell_qty, 4)

    # Revenue from immediate sale
    immediate_revenue = round(sell_qty * sell_price, 2)

    # Estimated revenue from stored portion
    storage_total = round(store_qty * storage_cost_per_quintal * (horizon_days / 30.0), 2)
    future_revenue = round(store_qty * forecast_price, 2)

    # Combined gross
    total_gross = round(immediate_revenue + future_revenue, 2)
    # Blended average selling price
    blended_price = round(total_gross / quantity, 2) if quantity else 0.0

    # Costs: transport on full quantity, storage only on stored portion
    transport_total = round(quantity * transport_per_quintal, 2)
    cost = round(
        transport_total + storage_total
        + max(0.0, labour_total) + max(0.0, packaging_total) + max(0.0, other_total),
        2,
    )
    ni   = round(total_gross - cost, 2)
    ni_q = round(ni / quantity, 2) if quantity else 0.0

    return ScenarioResult(
        name=f"Partial Sell ({sell_percentage}% now, {100 - sell_percentage}% stored {horizon_days}d)",
        selling_price_per_quintal=blended_price,
        gross_revenue=total_gross,
        transport_cost=transport_total,
        storage_cost=storage_total,
        labour_cost=round(max(0.0, labour_total), 2),
        packaging_cost=round(max(0.0, packaging_total), 2),
        other_cost=round(max(0.0, other_total), 2),
        total_cost=cost,
        net_income=ni,
        net_income_per_quintal=ni_q,
        notes=[
            f"Sell {sell_percentage}% ({sell_qty:.1f} qtl) now at ₹{sell_price:,.0f}/q.",
            f"Store {100 - sell_percentage}% ({store_qty:.1f} qtl) for {horizon_days} days.",
            f"Estimated future price: ₹{forecast_price:,.0f}/q.",
        ],
    )


# ── Scenario comparison ───────────────────────────────────────────────────────

def rank_scenarios(scenarios: List[ScenarioResult]) -> List[ScenarioResult]:
    """Return scenarios sorted by net_income descending."""
    return sorted(scenarios, key=lambda s: s.net_income, reverse=True)


def best_scenario(scenarios: List[ScenarioResult]) -> Optional[ScenarioResult]:
    """Return the scenario with the highest net income."""
    if not scenarios:
        return None
    return max(scenarios, key=lambda s: s.net_income)


def income_difference(scenarios: List[ScenarioResult]) -> float:
    """Difference in net income between the best and worst scenario."""
    if len(scenarios) < 2:
        return 0.0
    values = [s.net_income for s in scenarios]
    return round(max(values) - min(values), 2)


# ── Deterministic summary sentence ───────────────────────────────────────────

def deterministic_summary(top: ScenarioResult, all_scenarios: List[ScenarioResult]) -> str:
    """
    Generate a plain-language summary based solely on calculated values.
    IBM Granite will convert this into farmer-friendly language in Phase 8.
    """
    diff = income_difference(all_scenarios)
    return (
        f"The {top.name} option currently provides the highest estimated net income "
        f"(₹{top.net_income:,.0f}) after transport and other entered costs. "
        f"This is approximately ₹{diff:,.0f} more than the lowest estimated scenario."
    )
