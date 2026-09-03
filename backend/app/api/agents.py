"""
Phase 5 — Agents API router.
Registers:
  POST /api/agents/storage-advisor
"""
from fastapi import APIRouter, HTTPException

from app.schemas.advisor import AdvisorRequest, AdvisorResponse
from app.agents.storage_advisor import get_advisor_service

router = APIRouter(prefix="/agents", tags=["AI Agents"])


@router.post(
    "/storage-advisor",
    response_model=AdvisorResponse,
    summary="Storage & Selling Timing Advisor",
    description=(
        "Returns a deterministic SELL_NOW / STORE / PARTIAL_SELL recommendation.\n\n"
        "Pulls current mandi prices from Phase 2, forecasts from Phase 3, "
        "and best buyer offers from Phase 4.\n\n"
        "All calculations are deterministic — no LLM involved.\n\n"
        "⚠️ DEMO DATA — estimates only, not financial advice."
    ),
)
async def storage_advisor(payload: AdvisorRequest):
    if payload.quantity <= 0:
        raise HTTPException(400, detail="quantity must be positive")

    svc = get_advisor_service()
    result = svc.advise(
        crop=payload.crop,
        mandi=payload.mandi,
        quantity=payload.quantity,
        storage_cost_per_quintal=payload.storage_cost_per_quintal,
        cash_urgency=payload.cash_urgency,
        current_price_override=payload.current_price_override,
        buyer_price_override=payload.buyer_price_override,
    )
    return result


@router.get(
    "/storage-advisor/preview",
    response_model=AdvisorResponse,
    summary="Preview advisor with GET params (for quick testing)",
    description="Convenience GET wrapper for the storage advisor. Same logic as POST.",
)
async def storage_advisor_preview(
    crop:                     str   = "cotton",
    mandi:                    str   = "Rajkot APMC",
    quantity:                 float = 100.0,
    storage_cost_per_quintal: float = 80.0,
    cash_urgency:             str   = "MEDIUM",
):
    if crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")
    if quantity <= 0:
        raise HTTPException(400, detail="quantity must be positive")

    svc = get_advisor_service()
    result = svc.advise(
        crop=crop,
        mandi=mandi,
        quantity=quantity,
        storage_cost_per_quintal=storage_cost_per_quintal,
        cash_urgency=cash_urgency,
    )
    return result
