"""
Phase 4 — Pydantic schemas for buyer matching and connection requests.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator


# ── Match score schemas ───────────────────────────────────────────────────────

class ScoreBreakdownSchema(BaseModel):
    crop:     float
    quality:  float
    price:    float
    location: float
    quantity: float
    delivery: float


class MatchedBuyerSchema(BaseModel):
    buyer_id:            int
    buyer_name:          str
    location:            Optional[str]
    verified:            bool
    crop:                str
    offered_price:       Optional[float]
    min_quantity:        Optional[float]
    max_quantity:        Optional[float]
    quality_requirement: Optional[str]
    match_score:         float
    breakdown:           ScoreBreakdownSchema
    reasons:             List[str]
    price_vs_market:     str          # ABOVE_MARKET | AT_MARKET | BELOW_MARKET | UNKNOWN
    price_advantage:     Optional[float]
    distance_km:         Optional[float]
    market_price:        Optional[float]


class BuyerMatchResponse(BaseModel):
    crop:         str
    quantity:     Optional[float]
    district:     Optional[str]
    market_price: Optional[float]
    total_found:  int
    matches:      List[MatchedBuyerSchema]
    note:         str = "⚠️ DEMO DATA — Match scores are deterministic estimates."


# ── Connection request schemas ────────────────────────────────────────────────

class ConnectionRequestCreate(BaseModel):
    farmer_id:     int
    buyer_id:      int
    crop:          str
    quantity:      float
    offered_price: Optional[float] = None
    crop_id:       Optional[int]   = None
    message:       Optional[str]   = None
    match_score:   Optional[float] = None

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


class ConnectionRequestOut(BaseModel):
    id:            int
    farmer_id:     int
    buyer_id:      int
    crop:          str
    quantity:      float
    offered_price: Optional[float]
    message:       Optional[str]
    status:        str
    match_score:   Optional[float]
    created_at:    datetime
    updated_at:    datetime

    class Config:
        from_attributes = True


class ConnectionRequestStatusUpdate(BaseModel):
    status: str

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        allowed = {"PENDING", "ACCEPTED", "REJECTED", "COMPLETED"}
        if v.upper() not in allowed:
            raise ValueError(f"status must be one of {allowed}")
        return v.upper()
