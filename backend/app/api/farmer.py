"""
Farmer dashboard API endpoint — Phase 2 updated.
Now uses MarketDataService instead of Phase 1 demo_data.
"""
from datetime import date
from fastapi import APIRouter, Query
from app.schemas.dashboard import FarmerDashboardResponse, AIRecommendation, QuickAction
from app.schemas.market import MarketSummary, PriceTrendPoint
from app.services.market_data_service import get_market_data_service
from app.services.demo_data import get_best_buyer

router = APIRouter(prefix="/farmer", tags=["Farmer"])

QUICK_ACTIONS = [
    QuickAction(id="market", label="Check Market Prices", icon="📊", href="/farmer/market", color="green"),
    QuickAction(id="buyers", label="Find Buyers", icon="🤝", href="/farmer/buyers", color="blue"),
    QuickAction(id="advisor", label="Sell or Store?", icon="💡", href="/farmer/advisor", color="amber"),
    QuickAction(id="quality", label="Check Crop Quality", icon="🌾", href="/farmer/quality", color="purple"),
    QuickAction(id="ai", label="Ask KisanSetu AI", icon="🤖", href="/farmer/advisor", color="indigo"),
]


@router.get(
    "/dashboard",
    response_model=FarmerDashboardResponse,
    summary="Farmer dashboard data",
    description=(
        "Returns aggregated dashboard data for the farmer. "
        "Phase 2: powered by MarketDataService. AI integration in Phase 3."
    ),
)
async def farmer_dashboard(
    district: str = Query(default="Rajkot", description="Farmer's district"),
    farmer_name: str = Query(default="Rameshbhai Patel", description="Farmer name"),
):
    svc = get_market_data_service()
    summary = svc.get_dashboard_summary(district=district)
    cotton_data = summary.get("cotton")
    groundnut_data = summary.get("groundnut")

    # Convert to Phase 1 schema for backward compat
    cotton_out = None
    groundnut_out = None
    if cotton_data:
        cotton_out = MarketSummary(
            crop="cotton",
            latest_modal_price=cotton_data["latest_modal_price"],
            latest_date=date.fromisoformat(cotton_data["latest_date"]),
            district=cotton_data["district"],
            mandi=cotton_data["mandi"],
            change_percent=cotton_data.get("change_percent"),
            trend=(cotton_data.get("trend") or "stable").lower(),
            source=cotton_data["source"],
        )
    if groundnut_data:
        groundnut_out = MarketSummary(
            crop="groundnut",
            latest_modal_price=groundnut_data["latest_modal_price"],
            latest_date=date.fromisoformat(groundnut_data["latest_date"]),
            district=groundnut_data["district"],
            mandi=groundnut_data["mandi"],
            change_percent=groundnut_data.get("change_percent"),
            trend=(groundnut_data.get("trend") or "stable").lower(),
            source=groundnut_data["source"],
        )

    # 60-day price trend for chart
    cotton_hist = svc.get_price_history_for_chart("cotton", district=district, days=60)
    gn_hist = svc.get_price_history_for_chart("groundnut", district=district, days=60)

    def dedup_by_date(history, crop_name):
        seen = {}
        for h in history:
            if h["date"] not in seen:
                seen[h["date"]] = h
        return [
            PriceTrendPoint(
                date=v["date"][-5:],  # "MM-DD" for compact chart labels
                price=v["modal_price"],
                crop=crop_name,
            )
            for v in sorted(seen.values(), key=lambda x: x["date"])
        ]

    trend_points = dedup_by_date(cotton_hist, "cotton") + dedup_by_date(gn_hist, "groundnut")

    best_cotton_buyer = get_best_buyer("cotton")

    return FarmerDashboardResponse(
        farmer_name=farmer_name,
        cotton=cotton_out,
        groundnut=groundnut_out,
        price_trend=trend_points,
        best_buyer=best_cotton_buyer,
        ai_recommendation=AIRecommendation(
            title="AI Selling Advisor",
            message="AI recommendations will appear here once IBM Granite integration is complete.",
            status="pending_integration",
        ),
        quick_actions=QUICK_ACTIONS,
        note="DEMO DATA — Phase 2 Market Intelligence. Not real market data.",
    )
