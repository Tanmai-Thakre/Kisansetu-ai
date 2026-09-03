"""
Pydantic schemas for MarketPrice.
"""
from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict


class MarketPriceBase(BaseModel):
    crop: str
    mandi: str
    district: str
    date: date
    min_price: float
    max_price: float
    modal_price: float
    arrival_quantity: Optional[float] = None
    source: str = "DEMO"


class MarketPriceCreate(MarketPriceBase):
    pass


class MarketPriceOut(MarketPriceBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class MarketSummary(BaseModel):
    crop: str
    latest_modal_price: float
    latest_date: date
    district: str
    mandi: str
    change_percent: Optional[float] = None
    trend: Optional[str] = None  # "up", "down", "stable"
    source: str = "DEMO DATA"


class PriceTrendPoint(BaseModel):
    date: str
    price: float
    crop: str


class MarketDashboard(BaseModel):
    cotton: Optional[MarketSummary] = None
    groundnut: Optional[MarketSummary] = None
    price_trend: List[PriceTrendPoint] = []
    note: str = "⚠️ DEMO DATA — Not live market prices"
