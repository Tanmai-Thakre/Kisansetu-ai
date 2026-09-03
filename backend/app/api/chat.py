"""
Phase 8 — Chat API.

POST /api/chat         — Farmer natural-language query → Granite-synthesised answer.
GET  /api/chat/status  — Granite availability status.
"""
from __future__ import annotations

import logging
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.orchestrator import get_orchestrator
from app.ai.granite_client import get_granite_client

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["AI Chat — Phase 8"])


# ── Request / Response schemas ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message:    str   = Field(..., min_length=2, max_length=1000,
                               description="Farmer's question in any language.")
    language:   str   = Field("en", pattern="^(en|gu|hi)$",
                               description="Response language: en | gu | hi")
    farmer_id:  int   = Field(1,  ge=1, description="Authenticated farmer ID")
    crop:       str   = Field("cotton",  description="Crop context")
    mandi:      str   = Field("Rajkot APMC", description="Mandi context")
    quantity:   float = Field(100.0, gt=0, description="Quantity in quintals")
    district:   Optional[str]  = None
    quality_grade: Optional[str] = None
    storage_cost_per_quintal: float = Field(80.0, ge=0)
    cash_urgency: str = Field("MEDIUM", pattern="^(LOW|MEDIUM|HIGH)$")


class ChatResponse(BaseModel):
    answer:       str
    agents_used:  List[str]
    data_timestamp: str
    confidence:   int
    intent:       Optional[str] = None
    granite_used: bool = False
    agents_failed: List[str] = []
    request_id:   Optional[str] = None


class GraniteStatusResponse(BaseModel):
    available:   bool
    model:       Optional[str]
    region:      Optional[str]
    mode:        str   # "granite" | "fallback"


# ── POST /api/chat ────────────────────────────────────────────────────────────

@router.post(
    "",
    response_model=ChatResponse,
    summary="KisanSetu AI Chat",
    description=(
        "Ask any agricultural question in English, Gujarati, or Hindi.\n\n"
        "The orchestrator automatically selects the right agents (Forecast, Buyer, "
        "Storage, Income, Quality) and synthesises results using IBM Granite.\n\n"
        "Falls back to rule-based analysis if Granite is unavailable.\n\n"
        "**Never exposes internal prompts, credentials, or chain-of-thought.**\n\n"
        "⚠️ DEMO DATA — estimates only, not financial advice."
    ),
)
async def chat(payload: ChatRequest):
    if payload.crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")

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
        logger.error("Chat orchestration error: %s", exc)
        raise HTTPException(500, detail="Internal error during AI processing")

    return ChatResponse(
        answer         = result["final_answer"],
        agents_used    = result["agents_used"],
        data_timestamp = result["data_timestamp"],
        confidence     = result["confidence"],
        intent         = result.get("intent"),
        granite_used   = result.get("granite_used", False),
        agents_failed  = result.get("agents_failed", []),
        request_id     = result.get("request_id"),
    )


# ── GET /api/chat/status ──────────────────────────────────────────────────────

@router.get(
    "/status",
    response_model=GraniteStatusResponse,
    summary="IBM Granite availability status",
    description="Returns whether IBM Granite is configured and available.",
)
async def chat_status():
    import os
    client = get_granite_client()
    available = client.is_available()
    return GraniteStatusResponse(
        available = available,
        model     = os.getenv("IBM_GRANITE_MODEL") or os.getenv("WATSONX_MODEL_ID") if available else None,
        region    = os.getenv("IBM_REGION") or os.getenv("IBM_CLOUD_REGION") if available else None,
        mode      = "granite" if available else "fallback",
    )
