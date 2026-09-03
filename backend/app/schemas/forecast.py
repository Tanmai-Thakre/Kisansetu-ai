"""
Phase 3 — Pydantic schemas for the Forecast API.
"""
from typing import Optional, List
from pydantic import BaseModel


class ForecastResponse(BaseModel):
    crop:                str
    mandi:               str
    current_price:       float
    forecast_7d:         float
    forecast_15d:        float
    forecast_30d:        float
    trend:               str          # UP | DOWN | STABLE
    confidence:          float        # 0–100
    risk:                str          # LOW | MEDIUM | HIGH
    expected_change:     float
    expected_change_pct: float
    explanation:         str
    disclaimer:          str
    generated_at:        str
    model_name:          str
    mae:                 Optional[float]
    rmse:                Optional[float]
    n_history:           int
    source_status:       str
    insufficient_data:   bool
    error_message:       Optional[str]


class ForecastChartPoint(BaseModel):
    date:  str
    price: float
    type:  str   # "historical" | "forecast"


class ForecastChartResponse(BaseModel):
    crop:            str
    mandi:           str
    current_price:   float
    history:         List[ForecastChartPoint]
    forecast_points: List[ForecastChartPoint]
    trend:           str
    source_status:   str
