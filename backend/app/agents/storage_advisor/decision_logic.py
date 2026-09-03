"""
Phase 5 — Storage & Selling Advisor: Decision Logic.

Fully deterministic rule-based engine.
No LLM. No randomness.

Inputs: current_price, forecast prices, buyer price, storage cost,
        transport cost, quantity, cash_urgency, risk.

Outputs: SELL_NOW | STORE | PARTIAL_SELL + percentages + horizon + reasons.
"""
from __future__ import annotations

from typing import Optional, List, Tuple

# ── Constants ─────────────────────────────────────────────────────────────────
DEFAULT_STORAGE_COST_PER_QUINTAL = 80.0     # ₹/quintal/month  (if not supplied)
DEFAULT_TRANSPORT_COST           = 100.0    # ₹/quintal extra if selling later
MIN_WORTHWHILE_GAIN_PCT          = 1.5      # % gain needed to justify storage
RISK_WEIGHT_HIGH                 = 0.60     # High-risk: sell 60%+ immediately
RISK_WEIGHT_MEDIUM               = 0.40
RISK_WEIGHT_LOW                  = 0.20

# Partial-sell bounds
MIN_SELL_PCT  = 20
MAX_SELL_PCT  = 95


class HorizonResult:
    """Calculated economics for one storage horizon."""

    def __init__(
        self,
        horizon_days:     int,
        forecast_price:   float,
        current_best:     float,
        quantity:         float,
        storage_cost:     float,          # total ₹ for this horizon
        extra_transport:  float,          # additional ₹/quintal if selling later
    ):
        self.horizon_days    = horizon_days
        self.forecast_price  = forecast_price
        self.current_best    = current_best
        self.quantity        = quantity

        gross_future         = quantity * forecast_price
        sell_now_value       = quantity * current_best
        self.sell_now_value  = round(sell_now_value, 2)
        self.gross_future    = round(gross_future, 2)
        self.storage_cost    = round(storage_cost, 2)
        self.extra_transport = round(extra_transport * quantity, 2)
        self.net_future      = round(
            gross_future - storage_cost - self.extra_transport, 2
        )
        self.potential_gain       = round(self.net_future - sell_now_value, 2)
        self.gain_per_quintal     = round(self.potential_gain / quantity, 2) if quantity else 0.0
        self.gain_percent         = round(
            (self.potential_gain / sell_now_value * 100) if sell_now_value else 0.0, 2
        )

    def to_dict(self) -> dict:
        return {
            "horizon_days":      self.horizon_days,
            "forecast_price":    self.forecast_price,
            "gross_future":      self.gross_future,
            "storage_cost":      self.storage_cost,
            "net_future":        self.net_future,
            "sell_now_value":    self.sell_now_value,
            "potential_gain":    self.potential_gain,
            "gain_per_quintal":  self.gain_per_quintal,
            "gain_percent":      self.gain_percent,
        }


# ── Risk calculation ──────────────────────────────────────────────────────────

def calculate_risk(
    forecast_confidence: float,     # 0–100 from Phase 3
    price_change_pct:    float,     # % change from current to forecast (signed)
    storage_days:        int,
    volatility_pct:      float = 2.0,  # CV% from Phase 3 (default moderate)
) -> Tuple[str, float]:
    """
    Returns (label, numeric_score 0–100).
    Deterministic: higher score = higher risk.
    """
    score = 0.0

    # Low confidence → higher risk
    confidence_risk = (100 - forecast_confidence) * 0.40
    score += confidence_risk

    # High volatility → higher risk
    vol_risk = min(volatility_pct * 5.0, 30.0)
    score += vol_risk

    # Longer storage → higher risk
    duration_risk = min(storage_days / 90.0 * 20.0, 20.0)
    score += duration_risk

    # Larger expected price swing → higher risk (both ways)
    swing_risk = min(abs(price_change_pct) * 1.5, 20.0)
    score += swing_risk

    score = round(min(max(score, 0.0), 100.0), 1)

    if score <= 35:
        label = "LOW"
    elif score <= 65:
        label = "MEDIUM"
    else:
        label = "HIGH"

    return label, score


# ── Partial-sell percentage ───────────────────────────────────────────────────

def calc_sell_percentage(
    risk:         str,
    cash_urgency: str,
    gain_pct:     float,   # expected net gain %
) -> int:
    """
    Deterministic sell-now percentage (0–100) for PARTIAL_SELL recommendation.

    Higher risk → sell more now.
    High cash urgency → sell more now.
    High gain potential → keep more for later.
    """
    base = 50  # default: split evenly

    # Risk adjustment
    if risk == "HIGH":
        base += 20
    elif risk == "LOW":
        base -= 10

    # Cash urgency adjustment
    if cash_urgency == "HIGH":
        base += 20
    elif cash_urgency == "LOW":
        base -= 10

    # Gain potential adjustment: bigger upside → sell less now
    if gain_pct >= 5.0:
        base -= 15
    elif gain_pct >= 2.5:
        base -= 8
    elif gain_pct < 1.0:
        base += 10

    return int(max(MIN_SELL_PCT, min(MAX_SELL_PCT, base)))


# ── Best horizon selector ─────────────────────────────────────────────────────

def select_best_horizon(
    horizons: List[HorizonResult],
    risk:     str,
) -> HorizonResult:
    """
    Select the horizon with the best risk-adjusted net gain.
    Penalise longer horizons proportionally to risk.
    """
    def risk_adj_gain(h: HorizonResult) -> float:
        penalty = {7: 0.95, 15: 0.85, 30: 0.72}.get(h.horizon_days, 0.70)
        if risk == "HIGH":
            penalty *= 0.80
        elif risk == "LOW":
            penalty = 1.0
        return h.potential_gain * penalty

    return max(horizons, key=risk_adj_gain)


# ── Main decision function ────────────────────────────────────────────────────

def make_decision(
    crop:             str,
    quantity:         float,
    current_price:    float,
    buyer_price:      Optional[float],
    forecast_7d:      float,
    forecast_15d:     float,
    forecast_30d:     float,
    storage_cost_per_quintal: float,
    transport_extra:  float,
    cash_urgency:     str,                      # LOW | MEDIUM | HIGH
    forecast_confidence: float = 70.0,
    volatility_pct:   float = 2.0,
) -> dict:
    """
    Core decision engine. Returns a complete structured recommendation.
    All arithmetic is done here — no duplication in the API layer.
    """
    cash_urgency = cash_urgency.upper().strip()

    # ── 1. Current best price ─────────────────────────────────────────────────
    current_best = current_price
    buyer_is_best = False
    if buyer_price and buyer_price > current_best:
        current_best = buyer_price
        buyer_is_best = True

    sell_now_value = round(quantity * current_best, 2)

    # ── 2. Horizon economics ──────────────────────────────────────────────────
    # Storage cost scales with horizon (proportional to 30-day rate)
    def storage_for_days(days: int) -> float:
        monthly_rate = storage_cost_per_quintal   # ₹/quintal for ~30 days
        return quantity * monthly_rate * (days / 30.0)

    horizons = [
        HorizonResult(7,  forecast_7d,  current_best, quantity, storage_for_days(7),  transport_extra),
        HorizonResult(15, forecast_15d, current_best, quantity, storage_for_days(15), transport_extra),
        HorizonResult(30, forecast_30d, current_best, quantity, storage_for_days(30), transport_extra),
    ]

    # ── 3. Best horizon ───────────────────────────────────────────────────────
    # Determine risk from best 30d forecast for risk calculation
    price_chg_pct_30 = ((forecast_30d - current_best) / current_best * 100) if current_best else 0
    risk_label, risk_score = calculate_risk(
        forecast_confidence=forecast_confidence,
        price_change_pct=price_chg_pct_30,
        storage_days=30,
        volatility_pct=volatility_pct,
    )

    best_h = select_best_horizon(horizons, risk_label)

    # ── 4. Decision rule ──────────────────────────────────────────────────────
    gain_pct = best_h.gain_percent

    # SELL NOW conditions:
    #   a) best horizon has negligible net gain
    #   b) cash urgency HIGH
    #   c) risk HIGH + gain small
    sell_now_conditions = [
        gain_pct < MIN_WORTHWHILE_GAIN_PCT,
        cash_urgency == "HIGH" and gain_pct < 3.0,
        risk_label == "HIGH" and gain_pct < 4.0,
    ]

    # STORE conditions:
    #   a) gain is meaningful AND risk is LOW
    #   b) cash urgency LOW AND gain >= threshold
    store_conditions = [
        gain_pct >= 4.0 and risk_label == "LOW",
        gain_pct >= 6.0 and risk_label == "MEDIUM" and cash_urgency == "LOW",
    ]

    if any(sell_now_conditions):
        recommendation = "SELL_NOW"
        sell_pct = 100
        store_pct = 0
    elif any(store_conditions):
        recommendation = "STORE"
        sell_pct = 0
        store_pct = 100
    else:
        recommendation = "PARTIAL_SELL"
        sell_pct = calc_sell_percentage(risk_label, cash_urgency, gain_pct)
        store_pct = 100 - sell_pct

    # ── 5. Reasons ────────────────────────────────────────────────────────────
    reasons: List[str] = []

    if buyer_is_best and buyer_price:
        reasons.append(
            f"Direct buyer offer (₹{buyer_price:,.0f}/q) is above the mandi price "
            f"(₹{current_price:,.0f}/q)"
        )
    else:
        reasons.append(f"Best current option: mandi at ₹{current_best:,.0f}/q")

    if gain_pct >= MIN_WORTHWHILE_GAIN_PCT:
        reasons.append(
            f"Forecast suggests {gain_pct:+.1f}% net gain over "
            f"{best_h.horizon_days} days (₹{best_h.potential_gain:,.0f} total)"
        )
    else:
        reasons.append(
            f"Expected storage gain is small ({gain_pct:+.1f}%) — "
            "storage costs reduce the benefit"
        )

    storage_total = round(quantity * storage_cost_per_quintal, 0)
    reasons.append(
        f"Estimated storage cost: ₹{storage_total:,.0f} "
        f"(₹{storage_cost_per_quintal:.0f}/quintal)"
    )

    if risk_label == "HIGH":
        reasons.append("Price volatility is high — selling part now reduces risk")
    elif risk_label == "LOW":
        reasons.append("Price volatility is low — storage risk is manageable")

    if cash_urgency == "HIGH":
        reasons.append("High cash urgency — prioritise immediate income")
    elif cash_urgency == "LOW":
        reasons.append("Low cash urgency — you can wait for a better price")

    if recommendation == "PARTIAL_SELL":
        reasons.append(
            f"Recommended split: sell {sell_pct}% now (₹{sell_now_value * sell_pct / 100:,.0f}), "
            f"store {store_pct}% for {best_h.horizon_days} days"
        )

    # ── 6. Explanation paragraph ──────────────────────────────────────────────
    crop_label = crop.capitalize()
    option_str = (
        "a direct buyer" if buyer_is_best else "the nearby mandi"
    )
    upside_str = (
        f"moderate upside of {gain_pct:.1f}% over {best_h.horizon_days} days"
        if gain_pct >= MIN_WORTHWHILE_GAIN_PCT
        else "limited upside when storage costs are factored in"
    )
    risk_str = {"LOW": "low", "MEDIUM": "moderate", "HIGH": "elevated"}.get(risk_label, "moderate")
    urgency_str = {"LOW": "low", "MEDIUM": "moderate", "HIGH": "high"}.get(cash_urgency, "moderate")

    if recommendation == "SELL_NOW":
        explanation = (
            f"The best available price for {crop_label} is currently through "
            f"{option_str} at ₹{current_best:,.0f}/q. "
            f"After accounting for storage costs, the forecast shows {upside_str}. "
            f"With {risk_str} market risk and {urgency_str} cash urgency, "
            f"selling now is the most efficient option."
        )
    elif recommendation == "STORE":
        explanation = (
            f"The forecast shows {upside_str} for {crop_label}. "
            f"At ₹{storage_cost_per_quintal:.0f}/quintal, storage costs are manageable. "
            f"Market risk is {risk_str} and cash urgency is {urgency_str} — "
            f"storing for {best_h.horizon_days} days maximises expected income."
        )
    else:
        explanation = (
            f"{'A direct buyer' if buyer_is_best else 'The mandi'} currently offers "
            f"a good price (₹{current_best:,.0f}/q) for {crop_label}. "
            f"The forecast suggests {upside_str}. "
            f"Storage costs and {risk_str} price risk make a partial sale the balanced approach: "
            f"sell {sell_pct}% now to secure income and store {store_pct}% "
            f"to benefit from the expected price improvement."
        )

    return {
        "recommendation":          recommendation,
        "sell_percentage":         sell_pct,
        "store_percentage":        store_pct,
        "recommended_horizon_days": best_h.horizon_days,
        "current_best_price":      current_best,
        "current_mandi_price":     current_price,
        "buyer_price":             buyer_price,
        "buyer_is_best":           buyer_is_best,
        "forecast_price":          best_h.forecast_price,
        "sell_now_value":          sell_now_value,
        "estimated_storage_cost":  round(storage_for_days(best_h.horizon_days), 2),
        "potential_net_gain":      best_h.potential_gain,
        "gain_per_quintal":        best_h.gain_per_quintal,
        "gain_percent":            gain_pct,
        "risk":                    risk_label,
        "risk_score":              risk_score,
        "confidence":              round(forecast_confidence, 1),
        "cash_urgency":            cash_urgency,
        "horizons":                [h.to_dict() for h in horizons],
        "reasons":                 reasons,
        "explanation":             explanation,
        "disclaimer": (
            "AI-assisted recommendation: Forecasts and recommendations are estimates "
            "based on available market data. Prices can change and no profit is guaranteed."
        ),
    }
