"""
Phase 7 — Pydantic schemas for the Income Dashboard Agent.
"""
from __future__ import annotations

from typing import Optional, List
from pydantic import BaseModel, field_validator


# ── Request ───────────────────────────────────────────────────────────────────

class IncomeRequest(BaseModel):
    crop:                           str
    quantity:                       float
    mandi:                          str            = "Rajkot APMC"
    storage_cost_per_quintal:       float          = 80.0
    # Optional farmer-entered expenses
    transport_per_quintal_override: Optional[float] = None
    labour_total:                   float          = 0.0
    packaging_total:                float          = 0.0
    other_total:                    float          = 0.0
    # Optional overrides
    mandi_price_override:           Optional[float] = None
    buyer_price_override:           Optional[float] = None
    # Quality impact from Phase 6
    quality_price_impact_pct:       Optional[float] = None

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

    @field_validator(
        "storage_cost_per_quintal",
        "labour_total",
        "packaging_total",
        "other_total",
    )
    @classmethod
    def validate_costs(cls, v: float) -> float:
        if v < 0:
            raise ValueError("cost values cannot be negative")
        return v

    @field_validator("transport_per_quintal_override", mode="before")
    @classmethod
    def validate_transport_override(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v < 0:
            raise ValueError("transport_per_quintal_override cannot be negative")
        return v


# ── Individual scenario in response ──────────────────────────────────────────

class ScenarioSchema(BaseModel):
    name:                       str
    selling_price_per_quintal:  float
    gross_revenue:              float
    transport_cost:             float
    storage_cost:               float
    labour_cost:                float
    packaging_cost:             float
    other_cost:                 float
    total_cost:                 float
    net_income:                 float
    net_income_per_quintal:     float
    notes:                      List[str]


# ── Cost breakdown in response ────────────────────────────────────────────────

class CostBreakdown(BaseModel):
    transport:  Optional[float]
    storage:    Optional[float]
    labour:     Optional[float]
    packaging:  Optional[float]
    other:      Optional[float]


# ── Response ──────────────────────────────────────────────────────────────────

class IncomeResponse(BaseModel):
    crop:                       str
    mandi:                      str
    quantity:                   float

    # Market data
    mandi_price:                float
    transport_per_quintal:      float
    buyer_price:                Optional[float]
    forecast_7d:                float
    forecast_15d:               float
    forecast_30d:               float
    forecast_confidence:        float

    # Quality (Phase 6)
    quality_price_impact_pct:   Optional[float]
    quality_adjusted_price:     Optional[float]

    # Scenarios (ranked by net income)
    scenarios:                  List[ScenarioSchema]

    # Best outcome
    best_scenario:              Optional[str]
    best_net_income:            Optional[float]
    income_difference:          float
    deterministic_summary:      str

    # Dashboard top-card shortcuts
    current_estimated_income:   float
    best_buyer_income:          Optional[float]
    partial_sell_income:        float

    # Cost breakdown
    cost_breakdown:             CostBreakdown

    source_status:              str
    disclaimer:                 str


# ── Income history item (used when transaction data exists) ───────────────────

class IncomeHistoryItem(BaseModel):
    id:             int
    date:           Optional[str]
    crop:           str
    quantity:       float
    selling_price:  float
    total_revenue:  float
    total_cost:     float
    net_income:     float


class IncomeHistoryResponse(BaseModel):
    farmer_id:  int
    count:      int
    items:      List[IncomeHistoryItem]
    note:       str
