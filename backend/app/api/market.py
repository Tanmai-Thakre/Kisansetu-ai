"""
Phase 3 — Market Intelligence API (Phase 2 preserved + Phase 3 forecast endpoints)
"""
from typing import Optional, List
from datetime import date
from fastapi import APIRouter, Query, HTTPException

from app.schemas.market import MarketDashboard  # Phase 1 schema preserved
from app.schemas.market_v2 import (
    PaginatedMarketResponse, PriceHistoryResponse, MandiComparisonResponse,
    BestMandiResponse, MandiOut, CropOut, ForecastInputResponse,
    TrendOut, DataSourceInfo
)
from app.schemas.forecast import ForecastResponse, ForecastChartResponse
from app.services.market_data_service import get_market_data_service
from app.services.demo_data import get_market_prices  # Phase 1 fallback
from app.forecasting import get_forecasting_service

router = APIRouter(prefix="/market", tags=["Market Intelligence"])


# ── Helper ────────────────────────────────────────────────────────────────────

def _svc():
    return get_market_data_service()


# ── Phase 1 backward-compat endpoint ─────────────────────────────────────────

@router.get(
    "/prices",
    summary="[v1] Market dashboard prices",
    description=(
        "**Phase 1 compatible endpoint** — returns cotton & groundnut summary for a district.\n\n"
        "For full market intelligence use `/api/market/prices/latest`.\n\n"
        "⚠️ DEMO DATA — Not live market prices."
    ),
    tags=["Market Intelligence"],
)
async def get_prices_v1(
    district: str = Query(default="Rajkot", description="Gujarat district name"),
):
    """Backward-compatible Phase 1 endpoint. Returns MarketDashboard schema."""
    svc = _svc()
    summary = svc.get_dashboard_summary(district=district)

    # Convert Phase 2 summary to Phase 1 MarketDashboard schema
    cotton = summary.get("cotton")
    groundnut = summary.get("groundnut")

    from app.schemas.market import MarketSummary, PriceTrendPoint
    cotton_out = None
    groundnut_out = None

    if cotton:
        cotton_out = MarketSummary(
            crop="cotton",
            latest_modal_price=cotton["latest_modal_price"],
            latest_date=date.fromisoformat(cotton["latest_date"]),
            district=cotton["district"],
            mandi=cotton["mandi"],
            change_percent=cotton.get("change_percent"),
            trend=(cotton.get("trend") or "stable").lower(),
            source=cotton["source"],
        )
    if groundnut:
        groundnut_out = MarketSummary(
            crop="groundnut",
            latest_modal_price=groundnut["latest_modal_price"],
            latest_date=date.fromisoformat(groundnut["latest_date"]),
            district=groundnut["district"],
            mandi=groundnut["mandi"],
            change_percent=groundnut.get("change_percent"),
            trend=(groundnut.get("trend") or "stable").lower(),
            source=groundnut["source"],
        )

    # Build 60-day trend for both crops for the dashboard chart
    cotton_history = svc.get_price_history_for_chart("cotton", district=district, days=60)
    gn_history = svc.get_price_history_for_chart("groundnut", district=district, days=60)

    # Deduplicate by date (take first mandi for each date to represent the district)
    def dedup_by_date(history, crop_name):
        seen = {}
        for h in history:
            if h["date"] not in seen:
                seen[h["date"]] = h
        return [PriceTrendPoint(date=v["date"], price=v["modal_price"], crop=crop_name)
                for v in sorted(seen.values(), key=lambda x: x["date"])]

    trend_points = dedup_by_date(cotton_history, "cotton") + dedup_by_date(gn_history, "groundnut")

    return MarketDashboard(
        cotton=cotton_out,
        groundnut=groundnut_out,
        price_trend=trend_points,
        note="DEMO DATA — Not live market prices. Phase 2 Market Intelligence.",
    )


# ── Phase 2 endpoints ─────────────────────────────────────────────────────────

@router.get(
    "/prices/latest",
    summary="Latest prices for all mandis",
    description=(
        "Returns the latest available price for each mandi/crop combination.\n\n"
        "Supports filtering by crop, district, and mandi.\n\n"
        "⚠️ DEMO DATA"
    ),
)
async def get_latest_prices(
    crop: Optional[str] = Query(None, description="Filter by crop: cotton or groundnut"),
    district: Optional[str] = Query(None, description="Filter by Gujarat district"),
    mandi: Optional[str] = Query(None, description="Filter by specific mandi name"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(50, ge=1, le=200, description="Records per page"),
):
    if crop and crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")
    result = _svc().get_latest_prices(
        crop=crop, district=district, mandi=mandi, page=page, limit=limit
    )
    return result


@router.get(
    "/prices/history",
    summary="Historical price data for charts",
    description=(
        "Returns chronological price history for a crop.\n\n"
        "Use for rendering price trend charts.\n\n"
        "Example: `GET /api/market/prices/history?crop=cotton&mandi=Rajkot APMC`\n\n"
        "⚠️ DEMO DATA"
    ),
)
async def get_price_history(
    crop: str = Query(..., description="Crop name: cotton or groundnut"),
    mandi: Optional[str] = Query(None, description="Filter by mandi name"),
    district: Optional[str] = Query(None, description="Filter by district"),
    start_date: Optional[date] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[date] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(90, ge=1, le=365, description="Maximum records"),
):
    if crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")
    if start_date and end_date and start_date > end_date:
        raise HTTPException(400, detail="start_date must be before end_date")
    result = _svc().get_price_history(
        crop=crop, mandi=mandi, district=district,
        start_date=start_date, end_date=end_date, limit=limit,
    )
    return result


@router.get(
    "/prices/compare",
    summary="Compare mandis by net effective price",
    description=(
        "Compare multiple mandis ranked by **net effective price** after estimated transport.\n\n"
        "Pass comma-separated mandi names or leave blank to compare all available mandis.\n\n"
        "Example: `GET /api/market/prices/compare?crop=cotton&quantity=100`\n\n"
        "⚠️ DEMO DATA — Transport costs are estimates"
    ),
)
async def compare_prices(
    crop: str = Query(..., description="Crop: cotton or groundnut"),
    quantity: float = Query(100.0, gt=0, description="Quantity in quintals"),
    mandis: Optional[str] = Query(None, description="Comma-separated mandi names"),
    district: Optional[str] = Query(None, description="Filter by district"),
):
    if crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")
    mandi_list = [m.strip() for m in mandis.split(",")] if mandis else None
    return _svc().compare_mandis(crop=crop, quantity=quantity, mandi_list=mandi_list, district=district)


@router.get(
    "/mandis",
    summary="List all Gujarat mandis",
    description="Returns master data for all supported mandis with geolocation.",
)
async def list_mandis(
    district: Optional[str] = Query(None, description="Filter by district"),
):
    return _svc().get_mandis(district=district)


@router.get(
    "/crops",
    summary="List supported crops",
    description="Returns master data for all supported crops.",
)
async def list_crops():
    return _svc().get_crops()


@router.get(
    "/districts",
    summary="List supported Gujarat districts",
)
async def list_districts():
    return _svc().get_districts()


@router.get(
    "/trends",
    summary="Price trend indicators",
    description=(
        "Returns trend direction (UP/DOWN/STABLE), change, and change% for each mandi.\n\n"
        "Comparison window is configurable (default: 7 days).\n\n"
        "⚠️ DEMO DATA"
    ),
)
async def get_trends(
    crop: Optional[str] = Query(None, description="Filter by crop"),
    district: Optional[str] = Query(None, description="Filter by district"),
    comparison_days: int = Query(7, ge=1, le=30, description="Comparison window in days"),
):
    return _svc().get_trends(crop=crop, district=district, comparison_days=comparison_days)


@router.get(
    "/best-mandi",
    summary="Best mandi recommendation",
    description=(
        "Returns the best mandi for a crop based on **net effective price** "
        "(modal price minus estimated transport cost).\n\n"
        "Includes a deterministic explanation of why this mandi is recommended.\n\n"
        "⚠️ DEMO DATA — Transport estimates only"
    ),
)
async def get_best_mandi(
    crop: str = Query(..., description="Crop: cotton or groundnut"),
    quantity: float = Query(100.0, gt=0, description="Quantity in quintals"),
    district: Optional[str] = Query(None, description="Optional district filter"),
):
    if crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")
    return _svc().get_best_mandi(crop=crop, quantity=quantity, district=district)


@router.get(
    "/forecast-input",
    summary="Structured data for future AI forecasting",
    description=(
        "Returns clean time-series data ready for Phase 3 MandiForecastAgent.\n\n"
        "Do NOT perform forecasting here — this is raw data only.\n\n"
        "⚠️ DEMO DATA"
    ),
)
async def get_forecast_input(
    crop: str = Query(..., description="Crop: cotton or groundnut"),
    mandi: str = Query(..., description="Mandi name"),
    days: int = Query(90, ge=7, le=365, description="Days of history"),
):
    if crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")
    return _svc().get_forecast_input(crop=crop, mandi=mandi, days=days)


@router.get(
    "/source-info",
    summary="Data source and freshness information",
    description="Returns current data source status for display in the UI.",
)
async def get_source_info():
    info = _svc()._provider.get_source_info()
    return {
        **info,
        "tooltip": (
            "This prototype is currently using synthetic demonstration data. "
            "Live market integration can be connected through the MarketDataProvider."
        ),
    }


# ── Phase 3: Forecast endpoints ───────────────────────────────────────────────

@router.get(
    "/forecast",
    response_model=ForecastResponse,
    summary="7 / 15 / 30-day price forecast",
    description=(
        "Returns a price forecast for a specific crop and mandi.\n\n"
        "Uses a RandomForest model trained on Phase 2 historical data.\n\n"
        "Returns trend (UP/DOWN/STABLE), confidence (0–100%), and risk (LOW/MEDIUM/HIGH).\n\n"
        "Results are cached for 1 hour.\n\n"
        "⚠️ DEMO DATA — Forecast based on synthetic market history. "
        "Not a guaranteed future price."
    ),
    tags=["Market Intelligence"],
)
async def get_forecast(
    crop:  str = Query(..., description="Crop: cotton or groundnut"),
    mandi: str = Query(..., description="Mandi name, e.g. 'Rajkot APMC'"),
):
    if crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")
    svc = get_forecasting_service()
    result = svc.forecast(crop=crop, mandi=mandi)
    return result.to_dict()


@router.get(
    "/forecast/chart",
    response_model=ForecastChartResponse,
    summary="Historical + forecast chart data",
    description=(
        "Returns historical prices AND forecast points for a combined chart.\n\n"
        "Historical type='historical', forecast type='forecast'.\n\n"
        "Use `history_days` to control how many past days to include.\n\n"
        "⚠️ DEMO DATA"
    ),
    tags=["Market Intelligence"],
)
async def get_forecast_chart(
    crop:         str = Query(..., description="Crop: cotton or groundnut"),
    mandi:        str = Query(..., description="Mandi name"),
    history_days: int = Query(30, ge=7, le=90, description="Days of history to include"),
):
    if crop.lower() not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")
    svc = get_forecasting_service()
    return svc.get_forecast_chart_data(crop=crop, mandi=mandi, history_days=history_days)
