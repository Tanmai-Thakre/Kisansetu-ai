"""
Phase 9 — Demo API endpoints.

GET  /api/demo/farmer      — demo farmer profile for hackathon demo mode
POST /api/demo/run         — run full AI analysis with the canonical demo scenario
"""
from __future__ import annotations

import logging
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.ai.orchestrator import get_orchestrator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/demo", tags=["Demo Mode — Phase 9"])

# ── Demo farmer profile ────────────────────────────────────────────────────────

DEMO_FARMER = {
    "id":           1,
    "name":         "Rameshbhai Patel",
    "village":      "Gondal",
    "district":     "Rajkot",
    "state":        "Gujarat",
    "crop":         "cotton",
    "quantity":     100.0,
    "mandi":        "Rajkot APMC",
    "land_area":    5.0,
    "phone":        "Demo account",
    "note":         "This is synthetic demo data for demonstration purposes.",
}

DEMO_QUERIES = {
    "en": (
        "I have 100 quintals of cotton in Rajkot. "
        "Find the best buyer, predict the price for the next 15 days, "
        "tell me whether I should sell or store, and estimate my income."
    ),
    "gu": (
        "100 ક્વિન્ટલ કપાસ રાજકોટમાં છે. "
        "શ્રેષ્ઠ ખરીદદાર, 15 દિવસ ભાવ, વેચો/સ્ટોર સલાહ અને આવક ગણો."
    ),
    "hi": (
        "100 क्विंटल कपास राजकोट में है। "
        "सबसे अच्छा खरीदार, 15 दिन भाव, बेचें/रखें सलाह और आय की गणना करें।"
    ),
}


# ── Schemas ───────────────────────────────────────────────────────────────────

class DemoRunRequest(BaseModel):
    language: str = Field("en", pattern="^(en|gu|hi)$")


class DemoRunResponse(BaseModel):
    farmer:        Dict[str, Any]
    query:         str
    agents_used:   list
    agents_failed: list
    final_answer:  str
    granite_used:  bool
    confidence:    int
    data_timestamp: str
    intent:        str | None = None


# ── GET /api/demo/farmer ──────────────────────────────────────────────────────

@router.get(
    "/farmer",
    summary="Demo farmer profile",
    description="Returns the canonical demo farmer data for hackathon demo mode.",
)
async def demo_farmer():
    return DEMO_FARMER


# ── POST /api/demo/run ────────────────────────────────────────────────────────

@router.post(
    "/run",
    response_model=DemoRunResponse,
    summary="Run Full AI Analysis (demo scenario)",
    description=(
        "Runs the canonical demo scenario through the Agent Orchestrator + IBM Granite.\n\n"
        "**Demo scenario**: Rameshbhai Patel, 100 quintals cotton, Rajkot APMC.\n\n"
        "Invokes Forecast + Buyer + Storage + Income agents, then synthesises with Granite.\n\n"
        "⚠️ DEMO DATA — synthetic data, not live market prices."
    ),
)
async def demo_run(payload: DemoRunRequest):
    query = DEMO_QUERIES.get(payload.language, DEMO_QUERIES["en"])
    orch  = get_orchestrator()
    try:
        result = orch.orchestrate(
            query      = query,
            language   = payload.language,
            farmer_id  = 1,
            crop       = "cotton",
            mandi      = "Rajkot APMC",
            quantity   = 100.0,
            district   = "Rajkot",
        )
    except Exception as exc:
        logger.error("Demo run error: %s", exc)
        raise HTTPException(500, detail="Demo analysis failed")

    return DemoRunResponse(
        farmer         = DEMO_FARMER,
        query          = query,
        agents_used    = result["agents_used"],
        agents_failed  = result.get("agents_failed", []),
        final_answer   = result["final_answer"],
        granite_used   = result.get("granite_used", False),
        confidence     = result["confidence"],
        data_timestamp = result["data_timestamp"],
        intent         = result.get("intent"),
    )
