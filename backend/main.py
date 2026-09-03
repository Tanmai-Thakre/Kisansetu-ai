"""
KisanSetu AI — FastAPI Application Entry Point

Challenge 13: AI-Powered Cotton & Groundnut Market Linkage Platform
Phase 3: Mandi Price Forecasting Agent.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.api import market_router, buyers_router, farmer_router, agents_router, quality_router, income_router

load_dotenv()

app = FastAPI(
    title="KisanSetu AI API",
    description=(
        "AI-Powered Cotton & Groundnut Market Linkage Platform for Gujarat farmers.\n\n"
        "**Phase 7:** Farmer Income Dashboard Agent — scenario comparison & estimated net income.\n\n"
        "**Phase 6:** Quality Grading Assistance Agent — deterministic Cotton & Groundnut grading.\n\n"
        "**Phase 5:** Storage & Selling Timing Advisor — deterministic SELL/STORE/PARTIAL_SELL.\n\n"
        "**Phase 4:** Direct Buyer–Farmer Matching Agent — 100-point deterministic match score.\n\n"
        "**Phase 3:** Mandi Price Forecasting Agent — 7/15/30-day RandomForest forecasts.\n\n"
        "IBM Granite LLM integration coming in a future phase."
    ),
    version="7.0.0-phase7",
    contact={
        "name": "KisanSetu AI Team",
    },
    license_info={
        "name": "MIT",
    },
)

# ── CORS ──────────────────────────────────────────────────────────────────────
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
API_PREFIX = "/api"
app.include_router(market_router,  prefix=API_PREFIX)
app.include_router(buyers_router,  prefix=API_PREFIX)
app.include_router(farmer_router,  prefix=API_PREFIX)
app.include_router(agents_router,  prefix=API_PREFIX)
app.include_router(quality_router, prefix=API_PREFIX)
app.include_router(income_router,  prefix=API_PREFIX)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    from app.services.market_data_provider import get_market_data_provider
    provider = get_market_data_provider()
    return {
        "status": "ok",
        "service": "KisanSetu AI API",
        "version": "7.0.0-phase7",
        "phase": "Phase 7 — Farmer Income Dashboard Agent",
        "market_data": {
            "provider": provider.SOURCE_NAME,
            "source_status": provider.SOURCE_STATUS,
            "is_live": provider.is_live(),
        },
        "agents": {
            "MandiForecastAgent":   "active_phase3",
            "BuyerMatchingAgent":   "active_phase4",
            "StorageAdvisorAgent":  "active_phase5",
            "QualityGradingAgent":  "active_phase6",
            "IncomeDashboardAgent": "active_phase7",
        },
        "ibm_granite": "pending_future",
    }


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Welcome to KisanSetu AI API — Phase 4 Buyer Matching",
        "docs": "/docs",
        "health": "/health",
        "phase4_endpoints": [
            "/api/buyers/matches?crop=cotton&quantity=150&quality=A&district=Rajkot",
            "/api/buyers/request  [POST]",
            "/api/buyers/requests [GET]",
            "/api/buyers/requests/{id} [PATCH]",
        ],
        "forecast_endpoints": [
            "/api/market/forecast?crop=cotton&mandi=Rajkot APMC",
            "/api/market/forecast/chart?crop=cotton&mandi=Rajkot APMC",
        ],
        "market_endpoints": [
            "/api/market/prices", "/api/market/prices/latest",
            "/api/market/prices/history", "/api/market/prices/compare",
            "/api/market/mandis", "/api/market/crops",
            "/api/market/trends", "/api/market/best-mandi",
        ],
        "note": "Phase 4 Buyer Matching active. IBM Granite LLM in Phase 5.",
    }
