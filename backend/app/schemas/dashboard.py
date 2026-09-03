"""
Pydantic schema for Farmer Dashboard aggregate response.
"""
from typing import Optional, List
from pydantic import BaseModel
from .market import MarketSummary, PriceTrendPoint
from .buyer import BuyerListItem


class AIRecommendation(BaseModel):
    """Placeholder for future IBM Granite AI recommendations."""
    title: str = "AI Selling Advisor"
    message: str = "AI recommendations will appear here once IBM Granite integration is complete."
    recommendation: Optional[str] = None
    confidence: Optional[float] = None
    status: str = "pending_integration"


class QuickAction(BaseModel):
    id: str
    label: str
    icon: str
    href: str
    color: str


class FarmerDashboardResponse(BaseModel):
    farmer_name: str
    cotton: Optional[MarketSummary] = None
    groundnut: Optional[MarketSummary] = None
    price_trend: List[PriceTrendPoint] = []
    best_buyer: Optional[BuyerListItem] = None
    ai_recommendation: AIRecommendation = AIRecommendation()
    quick_actions: List[QuickAction] = []
    note: str = "⚠️ DEMO DATA — Phase 1 Foundation"
