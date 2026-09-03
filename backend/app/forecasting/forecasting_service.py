"""
Phase 3 — ForecastingService: the MandiForecastAgent entry point.

Pipeline:
  Historical Market Data  (Phase 2 provider)
        ↓
  DataPreprocessor
        ↓
  FeatureEngineering
        ↓
  PriceForecastModel (RandomForest / MovingAverage)
        ↓
  7 / 15 / 30-day forecast + trend + confidence + risk

No LLM. No IBM Granite. Pure numerical forecasting.
"""
from __future__ import annotations
import math
import threading
from datetime import datetime, date, timedelta
from typing import Optional, Dict, List

from app.services.market_data_provider import get_market_data_provider
from .data_preprocessor import prepare_series, MIN_HISTORY_DAYS
from .model import PriceForecastModel


# ── Constants ─────────────────────────────────────────────────────────────────
FORECAST_HORIZONS  = [7, 15, 30]
STABLE_THRESHOLD   = 0.5   # % change to call "STABLE"
CACHE_TTL_SECONDS  = 3600  # 1 hour cache per (crop, mandi) key

# Confidence penalties (subtract from 100)
CONF_PENALTY_SHORT_DATA   = 20  # < 40 records
CONF_PENALTY_HIGH_VOL     = 15  # CV > 3 %
CONF_PENALTY_HIGH_MAE     = 10  # MAE > 2% of current price
CONF_PENALTY_MA_MODEL     = 10  # using fallback model


# ── Result dataclass (plain Python — no dataclasses import needed on 3.14) ────

class ForecastResult:
    def __init__(
        self,
        crop:           str,
        mandi:          str,
        current_price:  float,
        forecast_7d:    float,
        forecast_15d:   float,
        forecast_30d:   float,
        trend:          str,
        confidence:     float,       # 0–100
        risk:           str,
        expected_change:float,
        expected_change_pct: float,
        explanation:    str,
        generated_at:   str,
        model_name:     str,
        mae:            Optional[float],
        rmse:           Optional[float],
        n_history:      int,
        source_status:  str,
        insufficient_data: bool = False,
        error_message:  Optional[str] = None,
    ):
        self.crop              = crop
        self.mandi             = mandi
        self.current_price     = current_price
        self.forecast_7d       = forecast_7d
        self.forecast_15d      = forecast_15d
        self.forecast_30d      = forecast_30d
        self.trend             = trend
        self.confidence        = round(confidence, 1)
        self.risk              = risk
        self.expected_change   = round(expected_change, 2)
        self.expected_change_pct = round(expected_change_pct, 2)
        self.explanation       = explanation
        self.generated_at      = generated_at
        self.model_name        = model_name
        self.mae               = mae
        self.rmse              = rmse
        self.n_history         = n_history
        self.source_status     = source_status
        self.insufficient_data = insufficient_data
        self.error_message     = error_message

    def to_dict(self) -> Dict:
        return {
            "crop":           self.crop,
            "mandi":          self.mandi,
            "current_price":  self.current_price,
            "forecast_7d":    self.forecast_7d,
            "forecast_15d":   self.forecast_15d,
            "forecast_30d":   self.forecast_30d,
            "trend":          self.trend,
            "confidence":     self.confidence,
            "risk":           self.risk,
            "expected_change": self.expected_change,
            "expected_change_pct": self.expected_change_pct,
            "explanation":    self.explanation,
            "disclaimer":     (
                "AI forecast is an estimate based on historical market data "
                "and is not a guaranteed future price."
            ),
            "generated_at":   self.generated_at,
            "model_name":     self.model_name,
            "mae":            self.mae,
            "rmse":           self.rmse,
            "n_history":      self.n_history,
            "source_status":  self.source_status,
            "insufficient_data": self.insufficient_data,
            "error_message":  self.error_message,
        }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _calc_trend(current: float, forecast: float) -> str:
    pct = ((forecast - current) / current) * 100 if current else 0
    if abs(pct) <= STABLE_THRESHOLD:
        return "STABLE"
    return "UP" if pct > 0 else "DOWN"


def _calc_volatility_cv(prices: List[float]) -> float:
    """Coefficient of variation (std/mean) as a percentage."""
    if len(prices) < 2:
        return 0.0
    mean = sum(prices) / len(prices)
    if mean == 0:
        return 0.0
    std = math.sqrt(sum((p - mean) ** 2 for p in prices) / len(prices))
    return (std / mean) * 100


def _calc_confidence(
    n_history:     int,
    cv_pct:        float,
    mae:           Optional[float],
    current_price: float,
    model_name:    str,
) -> float:
    """
    Confidence score 0–100.
    Starts at 90 and applies penalties for:
      - low data volume
      - high volatility
      - high model error
      - using fallback MA model
    """
    score = 90.0
    if n_history < 40:
        score -= CONF_PENALTY_SHORT_DATA
    if cv_pct > 3.0:
        score -= CONF_PENALTY_HIGH_VOL
    if mae is not None and current_price > 0:
        mae_pct = (mae / current_price) * 100
        if mae_pct > 2.0:
            score -= CONF_PENALTY_HIGH_MAE
    if "MovingAverage" in model_name:
        score -= CONF_PENALTY_MA_MODEL
    return max(20.0, min(95.0, score))


def _calc_risk(cv_pct: float, confidence: float) -> str:
    """
    Risk: LOW / MEDIUM / HIGH
    Based on price volatility (CV%) and forecast confidence.
    """
    if cv_pct <= 1.5 and confidence >= 75:
        return "LOW"
    if cv_pct > 4.0 or confidence < 50:
        return "HIGH"
    return "MEDIUM"


def _generate_explanation(
    crop:       str,
    trend:      str,
    expected_change_pct: float,
    risk:       str,
    n_history:  int,
    mae:        Optional[float],
) -> str:
    """
    Generate a plain-language explanation from structured forecast values.
    No LLM — template-based deterministic text.
    """
    crop_label = crop.capitalize()
    direction = {
        "UP":     "upward",
        "DOWN":   "downward",
        "STABLE": "stable",
    }.get(trend, "stable")
    intensity = (
        "strong" if abs(expected_change_pct) > 3 else
        "moderate" if abs(expected_change_pct) > 1 else
        "slight"
    )
    risk_text = {"LOW": "low", "MEDIUM": "moderate", "HIGH": "elevated"}.get(risk, "moderate")

    parts = [
        f"The model indicates a {intensity} {direction} trend for {crop_label} "
        f"over the next 30 days ({expected_change_pct:+.1f}%).",
        f"Market risk is {risk_text}.",
    ]
    if n_history < 40:
        parts.append("Note: forecast accuracy may be limited due to relatively short price history.")
    if mae is not None:
        parts.append(f"Model error (MAE): \u20b9{mae:.0f}/quintal.")

    return " ".join(parts)


# ── ForecastingService ────────────────────────────────────────────────────────

class ForecastingService:
    """
    Central entry point for the MandiForecastAgent.
    Trains a model per (crop, mandi) combination and caches results.
    Thread-safe cache using a simple lock.
    """

    def __init__(self):
        self._provider = get_market_data_provider()
        self._cache:  Dict[str, Dict]   = {}   # key → {"result": ForecastResult, "ts": datetime}
        self._models: Dict[str, PriceForecastModel] = {}
        self._lock    = threading.Lock()

    def _cache_key(self, crop: str, mandi: str) -> str:
        return f"{crop.lower()}::{mandi.lower()}"

    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        age = (datetime.utcnow() - self._cache[key]["ts"]).total_seconds()
        return age < CACHE_TTL_SECONDS

    def forecast(
        self,
        crop:  str,
        mandi: str,
    ) -> ForecastResult:
        """
        Generate or return cached forecast for (crop, mandi).
        """
        key = self._cache_key(crop, mandi)

        with self._lock:
            if self._is_cache_valid(key):
                return self._cache[key]["result"]

        result = self._compute_forecast(crop, mandi)

        with self._lock:
            self._cache[key] = {"result": result, "ts": datetime.utcnow()}

        return result

    def _compute_forecast(self, crop: str, mandi: str) -> ForecastResult:
        """Train model and predict for the given crop/mandi."""
        # ── 1. Fetch history ──────────────────────────────────────────────────
        records = self._provider.get_price_history(
            crop=crop.lower(), mandi=mandi, limit=120
        )

        # ── 2. Preprocess ─────────────────────────────────────────────────────
        series = prepare_series(records)

        if not series.is_sufficient:
            return ForecastResult(
                crop=crop, mandi=mandi,
                current_price=series.prices[-1] if series.prices else 0,
                forecast_7d=0, forecast_15d=0, forecast_30d=0,
                trend="STABLE", confidence=0, risk="HIGH",
                expected_change=0, expected_change_pct=0,
                explanation=(
                    "Not enough historical data to generate a reliable forecast. "
                    f"At least {MIN_HISTORY_DAYS} trading days required "
                    f"({series.n} available)."
                ),
                generated_at=datetime.utcnow().isoformat(),
                model_name="N/A",
                mae=None, rmse=None,
                n_history=series.n,
                source_status="DEMO",
                insufficient_data=True,
                error_message=f"Need {MIN_HISTORY_DAYS} records, got {series.n}",
            )

        # ── 3. Train ──────────────────────────────────────────────────────────
        model = PriceForecastModel()
        metrics = model.fit(series)
        self._models[self._cache_key(crop, mandi)] = model

        # ── 4. Predict ────────────────────────────────────────────────────────
        predictions = model.predict(FORECAST_HORIZONS)
        current_price  = series.prices[-1]
        forecast_7d    = predictions[7]
        forecast_15d   = predictions[15]
        forecast_30d   = predictions[30]

        # ── 5. Trend & change ─────────────────────────────────────────────────
        trend    = _calc_trend(current_price, forecast_30d)
        chg      = forecast_30d - current_price
        chg_pct  = (chg / current_price * 100) if current_price else 0.0

        # ── 6. Confidence & risk ──────────────────────────────────────────────
        cv_pct     = _calc_volatility_cv(series.prices[-30:] if len(series.prices) >= 30 else series.prices)
        confidence = _calc_confidence(
            n_history=series.n,
            cv_pct=cv_pct,
            mae=metrics.get("mae"),
            current_price=current_price,
            model_name=model.model_name,
        )
        risk = _calc_risk(cv_pct=cv_pct, confidence=confidence)

        # ── 7. Explanation ────────────────────────────────────────────────────
        explanation = _generate_explanation(
            crop=crop, trend=trend,
            expected_change_pct=chg_pct,
            risk=risk, n_history=series.n,
            mae=metrics.get("mae"),
        )

        return ForecastResult(
            crop=crop.lower(),
            mandi=mandi,
            current_price=current_price,
            forecast_7d=forecast_7d,
            forecast_15d=forecast_15d,
            forecast_30d=forecast_30d,
            trend=trend,
            confidence=confidence,
            risk=risk,
            expected_change=round(chg, 2),
            expected_change_pct=round(chg_pct, 2),
            explanation=explanation,
            generated_at=datetime.utcnow().isoformat(),
            model_name=model.model_name,
            mae=metrics.get("mae"),
            rmse=metrics.get("rmse"),
            n_history=series.n,
            source_status="DEMO",
            insufficient_data=False,
        )

    def get_forecast_chart_data(
        self,
        crop:  str,
        mandi: str,
        history_days: int = 30,
    ) -> Dict:
        """
        Returns historical prices + forecast points for charting.
        Historical points are clearly separated from forecast points.
        """
        result = self.forecast(crop, mandi)

        # Historical tail
        records = self._provider.get_price_history(
            crop=crop.lower(), mandi=mandi, limit=history_days
        )
        from .data_preprocessor import prepare_series as _prep
        series = _prep(records)

        history_points = [
            {"date": str(d), "price": p, "type": "historical"}
            for d, p in zip(series.dates[-history_days:], series.prices[-history_days:])
        ]

        # Forecast horizon points
        if not result.insufficient_data and series.dates:
            last_date = series.dates[-1]
            forecast_points = [
                {"date": str(last_date + timedelta(days=7)),  "price": result.forecast_7d,  "type": "forecast"},
                {"date": str(last_date + timedelta(days=15)), "price": result.forecast_15d, "type": "forecast"},
                {"date": str(last_date + timedelta(days=30)), "price": result.forecast_30d, "type": "forecast"},
            ]
        else:
            forecast_points = []

        return {
            "crop":            result.crop,
            "mandi":           result.mandi,
            "current_price":   result.current_price,
            "history":         history_points,
            "forecast_points": forecast_points,
            "trend":           result.trend,
            "source_status":   result.source_status,
        }

    def invalidate_cache(self, crop: str = None, mandi: str = None) -> None:
        """Clear cache for a specific key or all keys."""
        with self._lock:
            if crop and mandi:
                key = self._cache_key(crop, mandi)
                self._cache.pop(key, None)
            else:
                self._cache.clear()


# ── Singleton ─────────────────────────────────────────────────────────────────
_forecasting_service: Optional[ForecastingService] = None

def get_forecasting_service() -> ForecastingService:
    global _forecasting_service
    if _forecasting_service is None:
        _forecasting_service = ForecastingService()
    return _forecasting_service
