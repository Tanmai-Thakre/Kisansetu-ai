"""
Phase 7 — Income Dashboard Agent API endpoints.

POST /api/agents/income        — full calculation with all parameters
GET  /api/agents/income/preview — quick GET for testing
GET  /api/agents/income/history — income history (structure ready, data pending)
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException

from app.schemas.income import (
    IncomeRequest,
    IncomeResponse,
    IncomeHistoryResponse,
    CostBreakdown,
    ScenarioSchema,
)
from app.agents.income import get_income_service

router = APIRouter(prefix="/agents", tags=["AI Agents"])


def _build_response(result: dict) -> IncomeResponse:
    scenarios = [ScenarioSchema(**s) for s in result["scenarios"]]
    return IncomeResponse(
        crop=result["crop"],
        mandi=result["mandi"],
        quantity=result["quantity"],
        mandi_price=result["mandi_price"],
        transport_per_quintal=result["transport_per_quintal"],
        buyer_price=result.get("buyer_price"),
        forecast_7d=result["forecast_7d"],
        forecast_15d=result["forecast_15d"],
        forecast_30d=result["forecast_30d"],
        forecast_confidence=result["forecast_confidence"],
        quality_price_impact_pct=result.get("quality_price_impact_pct"),
        quality_adjusted_price=result.get("quality_adjusted_price"),
        scenarios=scenarios,
        best_scenario=result.get("best_scenario"),
        best_net_income=result.get("best_net_income"),
        income_difference=result["income_difference"],
        deterministic_summary=result["deterministic_summary"],
        current_estimated_income=result["current_estimated_income"],
        best_buyer_income=result.get("best_buyer_income"),
        partial_sell_income=result["partial_sell_income"],
        cost_breakdown=CostBreakdown(**result["cost_breakdown"]),
        source_status=result["source_status"],
        disclaimer=result["disclaimer"],
    )


# ── POST /api/agents/income ───────────────────────────────────────────────────

@router.post(
    "/income",
    response_model=IncomeResponse,
    summary="Income Dashboard Agent — full scenario comparison",
    description=(
        "Calculates estimated income for all four selling strategies:\n\n"
        "- **Sell Now (Mandi)** — current mandi price minus costs\n"
        "- **Direct Buyer** — best buyer offer minus costs\n"
        "- **Store 7/15/30 Days** — Phase 3 forecast price minus storage + costs\n"
        "- **Partial Sell** — Phase 5 recommended split\n\n"
        "Quality adjustment from Phase 6 is applied if `quality_price_impact_pct` is provided.\n\n"
        "⚠️ DEMO DATA — estimated values only, not financial advice."
    ),
)
async def income_calculate(payload: IncomeRequest):
    svc = get_income_service()
    result = svc.calculate(
        crop=payload.crop,
        quantity=payload.quantity,
        mandi=payload.mandi,
        storage_cost_per_quintal=payload.storage_cost_per_quintal,
        transport_per_quintal_override=payload.transport_per_quintal_override,
        labour_total=payload.labour_total,
        packaging_total=payload.packaging_total,
        other_total=payload.other_total,
        mandi_price_override=payload.mandi_price_override,
        buyer_price_override=payload.buyer_price_override,
        quality_price_impact_pct=payload.quality_price_impact_pct,
    )
    return _build_response(result)


# ── GET /api/agents/income/preview ────────────────────────────────────────────

@router.get(
    "/income/preview",
    response_model=IncomeResponse,
    summary="Income Dashboard preview — quick GET for testing",
    description=(
        "Convenience GET endpoint for testing income calculations without a request body.\n\n"
        "Example: `/api/agents/income/preview?crop=cotton&quantity=100`\n\n"
        "⚠️ DEMO DATA — estimated values only."
    ),
)
async def income_preview(
    crop:                      str   = "cotton",
    quantity:                  float = 100.0,
    mandi:                     str   = "Rajkot APMC",
    storage_cost_per_quintal:  float = 80.0,
    labour_total:              float = 0.0,
    packaging_total:           float = 0.0,
    other_total:               float = 0.0,
):
    if crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")
    if quantity <= 0:
        raise HTTPException(400, detail="quantity must be positive")

    svc = get_income_service()
    result = svc.calculate(
        crop=crop,
        quantity=quantity,
        mandi=mandi,
        storage_cost_per_quintal=storage_cost_per_quintal,
        labour_total=labour_total,
        packaging_total=packaging_total,
        other_total=other_total,
    )
    return _build_response(result)


# ── GET /api/agents/income/history ────────────────────────────────────────────

@router.get(
    "/income/history",
    response_model=IncomeHistoryResponse,
    summary="Income history (structure ready; no fabricated transactions)",
    description=(
        "Returns a farmer's completed sale history.\n\n"
        "Transaction data is not yet populated — returns an empty list.\n"
        "The schema is ready for when actual transaction records become available."
    ),
)
async def income_history(
    farmer_id: int = 1,
    limit:     int = 20,
):
    if farmer_id <= 0:
        raise HTTPException(400, detail="farmer_id must be positive")
    # Transaction data not yet available — return empty list (no fabricated sales)
    return IncomeHistoryResponse(
        farmer_id=farmer_id,
        count=0,
        items=[],
        note=(
            "Transaction history is not yet available. "
            "The API structure is ready for when completed sale records are recorded."
        ),
    )
