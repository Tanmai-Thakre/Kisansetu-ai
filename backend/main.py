"""
KisanSetu AI — FastAPI Application Entry Point
Phase 10: Final deployment, hardening & hackathon readiness.
"""
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

from app.api import (
    market_router, buyers_router, farmer_router, agents_router,
    quality_router, income_router, chat_router, demo_router,
)

load_dotenv()

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

# ── Application ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="KisanSetu AI API",
    description=(
        "AI-Powered Cotton & Groundnut Market Linkage Platform for Gujarat farmers.\n\n"
        "**Phase 10:** Final deployment, hardening & hackathon readiness.\n\n"
        "**Phase 8/9:** IBM Granite + Agent Orchestrator — natural-language AI chat, "
        "multi-agent orchestration, intent routing, English/Gujarati/Hindi.\n\n"
        "**Five agents:** Mandi Forecast · Buyer Matching · Storage Advisor · "
        "Quality Grading · Income Dashboard"
    ),
    version="10.0.0-final",
    contact={"name": "KisanSetu AI Team"},
    license_info={"name": "MIT"},
    # In production disable OpenAPI docs if needed
    # docs_url=None, redoc_url=None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
_cors_origins_raw = os.getenv("CORS_ORIGINS", "http://localhost:3000")
origins = [o.strip() for o in _cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept"],
)

# ── Global exception handler — never leak stack traces ────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled error on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=500,
        content={"detail": "An internal error occurred. Please try again."},
    )

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api"
app.include_router(market_router,  prefix=API_PREFIX)
app.include_router(buyers_router,  prefix=API_PREFIX)
app.include_router(farmer_router,  prefix=API_PREFIX)
app.include_router(agents_router,  prefix=API_PREFIX)
app.include_router(quality_router, prefix=API_PREFIX)
app.include_router(income_router,  prefix=API_PREFIX)
app.include_router(chat_router,    prefix=API_PREFIX)
app.include_router(demo_router,    prefix=API_PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    from app.services.market_data_provider import get_market_data_provider
    from app.ai.granite_client import get_granite_client
    provider = get_market_data_provider()
    granite  = get_granite_client()
    return {
        "status":  "ok",
        "service": "KisanSetu AI API",
        "version": "10.0.0-final",
        "phase":   "Phase 10 — Final Deployment",
        "market_data": {
            "provider":      provider.SOURCE_NAME,
            "source_status": provider.SOURCE_STATUS,
            "is_live":       provider.is_live(),
        },
        "agents": {
            "MandiForecastAgent":   "active_phase3",
            "BuyerMatchingAgent":   "active_phase4",
            "StorageAdvisorAgent":  "active_phase5",
            "QualityGradingAgent":  "active_phase6",
            "IncomeDashboardAgent": "active_phase7",
            "AgentOrchestrator":    "active_phase8",
        },
        "ibm_granite": {
            "status":    "configured" if granite.is_available() else "fallback_mode",
            "available": granite.is_available(),
        },
        "endpoints": {
            "chat":        "/api/chat",
            "orchestrate": "/api/agents/orchestrate",
            "demo":        "/api/demo/run",
            "docs":        "/docs",
        },
    }


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "message":  "KisanSetu AI — AI-Powered Agricultural Market Platform",
        "version":  "10.0.0-final",
        "health":   "/health",
        "docs":     "/docs",
        "demo":     "POST /api/demo/run",
        "chat":     "POST /api/chat",
        "key_apis": [
            "GET  /api/market/prices/latest",
            "GET  /api/market/forecast",
            "GET  /api/buyers/matches",
            "POST /api/agents/storage-advisor",
            "POST /api/agents/quality",
            "POST /api/agents/income",
            "POST /api/chat",
            "POST /api/agents/orchestrate",
            "POST /api/demo/run",
        ],
    }
