"""
Phase 2 — Extended Pydantic schemas for Market Intelligence.
Extends Phase 1 schemas without breaking them.
"""
from datetime import date, datetime
from typing import Optional, List, Any
from pydantic import BaseModel, ConfigDict, field_validator, model_validator
from enum import Enum


class SourceStatus(str, Enum):
    LIVE = "LIVE"
    LATEST_AVAILABLE = "LATEST_AVAILABLE"
    DEMO = "DEMO"


# ── Validation ────────────────────────────────────────────────────────────────

class MarketPriceV2Create(BaseModel):
    """Schema with validation for creating a new market price record."""
    crop: str
    variety: Optional[str] = None
    mandi: str
    district: str
    state: str = "Gujarat"
    date: date
    min_price: float
    max_price: float
    modal_price: float
    arrival_quantity: Optional[float] = None
    unit: str = "quintal"
    source: str = "DEMO"
    source_status: SourceStatus = SourceStatus.DEMO

    @field_validator("crop")
    @classmethod
    def validate_crop(cls, v: str) -> str:
        allowed = {"cotton", "groundnut"}
        if v.lower() not in allowed:
            raise ValueError(f"crop must be one of {allowed}")
        return v.lower()

    @field_validator("min_price", "max_price", "modal_price")
    @classmethod
    def validate_prices(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Prices must be positive")
        return round(v, 2)

    @field_validator("arrival_quantity")
    @classmethod
    def validate_quantity(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("arrival_quantity must be >= 0")
        return v

    @model_validator(mode="after")
    def validate_price_ordering(self) -> "MarketPriceV2Create":
        if self.min_price > self.modal_price:
            raise ValueError("min_price must be <= modal_price")
        if self.modal_price > self.max_price:
            raise ValueError("modal_price must be <= max_price")
        return self


# ── Response schemas ──────────────────────────────────────────────────────────

class MarketRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    crop: str
    variety: Optional[str] = None
    mandi: str
    district: str
    state: str
    date: str
    min_price: float
    max_price: float
    modal_price: float
    arrival_quantity: Optional[float] = None
    unit: str
    source: str
    source_status: str


class PaginatedMarketResponse(BaseModel):
    total: int
    page: int
    limit: int
    source: str
    source_status: str
    is_live: bool
    data: List[MarketRecordOut]


class TrendOut(BaseModel):
    crop: str
    mandi: str
    current_price: Optional[float]
    previous_price: Optional[float]
    change: Optional[float]
    change_percent: Optional[float]
    trend: str   # "UP", "DOWN", "STABLE"
    source: str
    source_status: str
    latest_date: Optional[str]


class MandiComparisonEntryOut(BaseModel):
    mandi: str
    district: str
    modal_price: float
    min_price: float
    max_price: float
    net_price: float
    transport_cost_per_quintal: float
    estimated_distance_km: float
    trend: str
    change_percent: Optional[float]
    arrival_quantity: Optional[float]
    source_status: str
    latest_date: Optional[str]
    transport_note: str


class MandiComparisonResponse(BaseModel):
    crop: str
    quantity_quintals: float
    mandis: List[MandiComparisonEntryOut]
    count: int
    source: str
    source_status: str
    is_live: bool
    note: str


class BestMandiResponse(BaseModel):
    crop: str
    quantity_quintals: float
    best_mandi: Optional[MandiComparisonEntryOut]
    explanation: str
    all_mandis: List[MandiComparisonEntryOut]
    source_status: str
    note: str


class HistoryPoint(BaseModel):
    date: str
    modal_price: float
    min_price: float
    max_price: float
    arrival_quantity: Optional[float]
    mandi: str
    crop: str


class PriceHistoryResponse(BaseModel):
    crop: str
    mandi: Optional[str]
    district: Optional[str]
    count: int
    source: str
    source_status: str
    is_live: bool
    data: List[HistoryPoint]


class MandiOut(BaseModel):
    name: str
    short_name: str
    district: str
    state: str
    latitude: Optional[float]
    longitude: Optional[float]


class CropOut(BaseModel):
    name: str
    display_name: str
    unit: str
    description: Optional[str]


class ForecastInputPoint(BaseModel):
    date: str
    modal_price: float
    min_price: float
    max_price: float
    arrival_quantity: Optional[float]


class ForecastInputResponse(BaseModel):
    crop: str
    mandi: str
    days_requested: int
    records_available: int
    source: str
    source_status: str
    is_live: bool
    note: str
    data: List[ForecastInputPoint]


class DataSourceInfo(BaseModel):
    """Displayed on every market page to show data freshness."""
    source: str
    source_status: str
    is_live: bool
    tooltip: str = (
        "This prototype is currently using synthetic demonstration data. "
        "Live market integration can be connected through the MarketDataProvider."
    )
