"""
Demo/seed data service — returns static DEMO DATA for Phase 1.
All data is clearly marked as DEMO DATA.
Real market data integration will happen in a future phase.
"""
from datetime import date, timedelta
from typing import List
from app.schemas.market import MarketSummary, PriceTrendPoint, MarketDashboard
from app.schemas.buyer import BuyerListItem

# ── Demo market prices (Gujarat mandis) ──────────────────────────────────────

DEMO_COTTON_PRICES = {
    "Rajkot":       {"min": 6900, "max": 7500, "modal": 7200},
    "Amreli":       {"min": 6800, "max": 7400, "modal": 7100},
    "Junagadh":     {"min": 6950, "max": 7550, "modal": 7250},
    "Bhavnagar":    {"min": 6850, "max": 7450, "modal": 7150},
    "Surendranagar":{"min": 7000, "max": 7600, "modal": 7300},
    "Jamnagar":     {"min": 6750, "max": 7350, "modal": 7050},
    "Ahmedabad":    {"min": 7100, "max": 7700, "modal": 7400},
}

DEMO_GROUNDNUT_PRICES = {
    "Rajkot":       {"min": 5800, "max": 6400, "modal": 6100},
    "Amreli":       {"min": 5700, "max": 6300, "modal": 6000},
    "Junagadh":     {"min": 5900, "max": 6500, "modal": 6200},
    "Bhavnagar":    {"min": 5750, "max": 6350, "modal": 6050},
    "Surendranagar":{"min": 5850, "max": 6450, "modal": 6150},
    "Jamnagar":     {"min": 5650, "max": 6250, "modal": 5950},
    "Ahmedabad":    {"min": 5950, "max": 6550, "modal": 6250},
}

# Demo buyers — Phase 4 expanded to 12 buyers for richer matching
DEMO_BUYERS: List[BuyerListItem] = [
    BuyerListItem(
        id=1, company_name="Gujarat Cotton Traders Pvt Ltd",
        location="Rajkot, Gujarat", verified=True, crop="cotton",
        offered_price=7350, min_quantity=50,  max_quantity=500,
        quality_requirement="A", note="DEMO DATA",
    ),
    BuyerListItem(
        id=2, company_name="Amreli Groundnut Exports",
        location="Amreli, Gujarat", verified=True, crop="groundnut",
        offered_price=6250, min_quantity=100, max_quantity=1000,
        quality_requirement="A", note="DEMO DATA",
    ),
    BuyerListItem(
        id=3, company_name="Saurashtra Agro Industries",
        location="Junagadh, Gujarat", verified=True, crop="groundnut",
        offered_price=6100, min_quantity=200, max_quantity=2000,
        quality_requirement="B", note="DEMO DATA",
    ),
    BuyerListItem(
        id=4, company_name="Bhavnagar Cotton Mills",
        location="Bhavnagar, Gujarat", verified=False, crop="cotton",
        offered_price=7150, min_quantity=100, max_quantity=800,
        quality_requirement="B", note="DEMO DATA",
    ),
    BuyerListItem(
        id=5, company_name="Ahmedabad Textile Corp",
        location="Ahmedabad, Gujarat", verified=True, crop="cotton",
        offered_price=7450, min_quantity=300, max_quantity=3000,
        quality_requirement="A", note="DEMO DATA",
    ),
    BuyerListItem(
        id=6, company_name="Surendranagar Oil Mills",
        location="Surendranagar, Gujarat", verified=True, crop="groundnut",
        offered_price=6200, min_quantity=150, max_quantity=1500,
        quality_requirement="A", note="DEMO DATA",
    ),
    # Phase 4 additional buyers
    BuyerListItem(
        id=7, company_name="Rajkot Spinning Mill Ltd",
        location="Rajkot, Gujarat", verified=True, crop="cotton",
        offered_price=7380, min_quantity=200, max_quantity=2000,
        quality_requirement="A", note="DEMO DATA",
    ),
    BuyerListItem(
        id=8, company_name="Jamnagar Agro Export",
        location="Jamnagar, Gujarat", verified=True, crop="groundnut",
        offered_price=6180, min_quantity=50,  max_quantity=600,
        quality_requirement="B", note="DEMO DATA",
    ),
    BuyerListItem(
        id=9, company_name="Ahmedabad Groundnut Processors",
        location="Ahmedabad, Gujarat", verified=True, crop="groundnut",
        offered_price=6300, min_quantity=500, max_quantity=5000,
        quality_requirement="A", note="DEMO DATA",
    ),
    BuyerListItem(
        id=10, company_name="Gondal Cotton Ginners",
        location="Gondal, Gujarat", verified=False, crop="cotton",
        offered_price=7050, min_quantity=20,  max_quantity=300,
        quality_requirement=None, note="DEMO DATA",
    ),
    BuyerListItem(
        id=11, company_name="Amreli Cottonseed Oil Corp",
        location="Amreli, Gujarat", verified=True, crop="cotton",
        offered_price=7200, min_quantity=100, max_quantity=1000,
        quality_requirement="B", note="DEMO DATA",
    ),
    BuyerListItem(
        id=12, company_name="Junagadh Peanut Products",
        location="Junagadh, Gujarat", verified=True, crop="groundnut",
        offered_price=6050, min_quantity=300, max_quantity=3000,
        quality_requirement="C", note="DEMO DATA",
    ),
]


def _build_trend(crop: str, base_price: float, days: int = 30) -> List[PriceTrendPoint]:
    """Generate a realistic-looking demo price trend."""
    import random
    random.seed(42 if crop == "cotton" else 7)
    trend = []
    price = base_price
    today = date.today()
    for i in range(days, 0, -1):
        day = today - timedelta(days=i)
        delta = random.uniform(-120, 130)
        price = max(price + delta, base_price * 0.85)
        trend.append(PriceTrendPoint(
            date=day.strftime("%b %d"),
            price=round(price, 0),
            crop=crop,
        ))
    return trend


def get_market_prices(district: str = "Rajkot") -> MarketDashboard:
    """Return demo market prices for a district."""
    cotton_data = DEMO_COTTON_PRICES.get(district, DEMO_COTTON_PRICES["Rajkot"])
    gn_data = DEMO_GROUNDNUT_PRICES.get(district, DEMO_GROUNDNUT_PRICES["Rajkot"])
    today = date.today()

    cotton = MarketSummary(
        crop="cotton",
        latest_modal_price=cotton_data["modal"],
        latest_date=today,
        district=district,
        mandi=f"{district} APMC",
        change_percent=1.4,
        trend="up",
        source="DEMO DATA",
    )
    groundnut = MarketSummary(
        crop="groundnut",
        latest_modal_price=gn_data["modal"],
        latest_date=today,
        district=district,
        mandi=f"{district} APMC",
        change_percent=-0.8,
        trend="down",
        source="DEMO DATA",
    )

    cotton_trend = _build_trend("cotton", cotton_data["modal"])
    gn_trend = _build_trend("groundnut", gn_data["modal"])

    return MarketDashboard(
        cotton=cotton,
        groundnut=groundnut,
        price_trend=cotton_trend + gn_trend,
        note="⚠️ DEMO DATA — Not live market prices. Real data integration coming in Phase 2.",
    )


def get_buyers(crop: str = None) -> List[BuyerListItem]:
    """Return demo buyers, optionally filtered by crop."""
    if crop:
        return [b for b in DEMO_BUYERS if b.crop == crop.lower()]
    return DEMO_BUYERS


def get_best_buyer(crop: str) -> BuyerListItem | None:
    """Return the best-price verified buyer for a crop."""
    filtered = [b for b in DEMO_BUYERS if b.crop == crop.lower() and b.verified]
    if not filtered:
        return None
    return max(filtered, key=lambda b: b.offered_price or 0)
