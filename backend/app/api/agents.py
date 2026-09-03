"""
Agents API router.
Phase 5:  POST /api/agents/storage-advisor
Phase 8:  POST /api/agents/orchestrate
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.schemas.advisor import AdvisorRequest, AdvisorResponse
from app.agents.storage_advisor import get_advisor_service

logger = logging.getLogger(__name__)
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


# ── Phase 8 — Orchestrate endpoint ────────────────────────────────────────────

class OrchestrateRequest(BaseModel):
    farmer_id:  int   = Field(1,  ge=1)
    message:    str   = Field(..., min_length=2, max_length=1000)
    language:   str   = Field("en", pattern="^(en|gu|hi)$")
    crop:       str   = Field("cotton")
    mandi:      str   = Field("Rajkot APMC")
    quantity:   float = Field(100.0, gt=0)
    district:   Optional[str]  = None
    quality_grade: Optional[str] = None
    storage_cost_per_quintal: float = Field(80.0, ge=0)
    cash_urgency: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH)$")


class OrchestrateResponse(BaseModel):
    agents_used:    List[str]
    agents_failed:  List[str]
    results:        Dict[str, Any]
    final_answer:   str
    intent:         Optional[str] = None
    granite_used:   bool = False
    confidence:     int = 0
    data_timestamp: str = ""
    request_id:     Optional[str] = None


@router.post(
    "/orchestrate",
    response_model=OrchestrateResponse,
    summary="Agent Orchestrator — multi-agent query",
    description=(
        "Routes a farmer query through the required agents and synthesises results.\n\n"
        "Selects agents automatically based on intent classification.\n\n"
        "Uses IBM Granite for synthesis when available; falls back to deterministic analysis.\n\n"
        "**Example complex query**: 'I have 100 quintals of cotton in Rajkot. "
        "Find the best buyer, predict prices for 15 days, and estimate my income.'\n\n"
        "⚠️ DEMO DATA — estimates only, not financial advice."
    ),
)
async def orchestrate(payload: OrchestrateRequest):
    if payload.crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")

    from app.ai.orchestrator import get_orchestrator
    orch = get_orchestrator()
    try:
        result = orch.orchestrate(
            query      = payload.message,
            language   = payload.language,
            farmer_id  = payload.farmer_id,
            crop       = payload.crop,
            mandi      = payload.mandi,
            quantity   = payload.quantity,
            district   = payload.district,
            quality_grade = payload.quality_grade,
            storage_cost_per_quintal = payload.storage_cost_per_quintal,
            cash_urgency = payload.cash_urgency,
        )
    except Exception as exc:
        logger.error("Orchestrate error: %s", exc)
        raise HTTPException(500, detail="Internal orchestration error")

    return OrchestrateResponse(
        agents_used    = result["agents_used"],
        agents_failed  = result.get("agents_failed", []),
        results        = result["results"],
        final_answer   = result["final_answer"],
        intent         = result.get("intent"),
        granite_used   = result.get("granite_used", False),
        confidence     = result["confidence"],
        data_timestamp = result["data_timestamp"],
        request_id     = result.get("request_id"),
    )
