"""
Phase 5 — Pydantic schemas for the Storage & Selling Advisor.
"""
from __future__ import annotations
from typing import Optional, List
from pydantic import BaseModel, field_validator


class AdvisorRequest(BaseModel):
    crop:                     str
    mandi:                    str = "Rajkot APMC"
    quantity:                 float
    storage_cost_per_quintal: Optional[float] = None
    cash_urgency:             str = "MEDIUM"
    current_price_override:   Optional[float] = None
    buyer_price_override:     Optional[float] = None

    @field_validator("crop")
    @classmethod
    def validate_crop(cls, v: str) -> str:
        if v.lower() not in ("cotton", "groundnut"):
            raise ValueError("crop must be 'cotton' or 'groundnut'")
        return v.lower()

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("quantity must be positive")
        return v

    @field_validator("storage_cost_per_quintal")
    @classmethod
    def validate_storage_cost(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("storage_cost_per_quintal cannot be negative")
        return v

    @field_validator("cash_urgency")
    @classmethod
    def validate_urgency(cls, v: str) -> str:
        v = v.upper().strip()
        if v not in ("LOW", "MEDIUM", "HIGH"):
            raise ValueError("cash_urgency must be LOW, MEDIUM, or HIGH")
        return v


class HorizonResultSchema(BaseModel):
    horizon_days:     int
    forecast_price:   float
    gross_future:     float
    storage_cost:     float
    net_future:       float
    sell_now_value:   float
    potential_gain:   float
    gain_per_quintal: float
    gain_percent:     float


class AdvisorResponse(BaseModel):
    recommendation:           str           # SELL_NOW | STORE | PARTIAL_SELL
    sell_percentage:          int
    store_percentage:         int
    recommended_horizon_days: int
    current_best_price:       float
    current_mandi_price:      float
    buyer_price:              Optional[float]
    buyer_is_best:            bool
    forecast_price:           float
    sell_now_value:           float
    estimated_storage_cost:   float
    potential_net_gain:       float
    gain_per_quintal:         float
    gain_percent:             float
    risk:                     str
    risk_score:               float
    confidence:               float
    cash_urgency:             str
    crop:                     str
    mandi:                    str
    quantity:                 float
    source_status:            str
    horizons:                 List[HorizonResultSchema]
    reasons:                  List[str]
    explanation:              str
    disclaimer:               str
