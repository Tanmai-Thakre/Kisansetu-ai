"""
Phase 4 — Buyer Matching Scoring Engine.

100-point transparent scoring system — fully deterministic, no LLM.

Score breakdown:
    Crop compatibility       30 pts  (binary: buyer must want this crop)
    Quality compatibility    20 pts  (grade match)
    Price compatibility      20 pts  (vs current market price)
    Location proximity       15 pts  (estimated distance)
    Quantity compatibility   10 pts  (farmer qty fits buyer range)
    Delivery timing           5 pts  (harvest date vs buyer delivery date)
                           --------
                   Total   100 pts
"""
from __future__ import annotations

import math
from datetime import date
from typing import Optional, List


# ── Weight constants ──────────────────────────────────────────────────────────
W_CROP     = 30
W_QUALITY  = 20
W_PRICE    = 20
W_LOCATION = 15
W_QUANTITY = 10
W_DELIVERY =  5
TOTAL_WEIGHT = W_CROP + W_QUALITY + W_PRICE + W_LOCATION + W_QUANTITY + W_DELIVERY  # 100

# ── Distance thresholds (km) ──────────────────────────────────────────────────
DIST_EXCELLENT =  50   # full location score
DIST_GOOD      = 150   # 75% location score
DIST_OK        = 300   # 50% location score
DIST_FAR       = 500   # 25% location score
# > 500 km → 0 location score

# ── Quality grade ordering ────────────────────────────────────────────────────
GRADE_ORDER = {"A": 3, "B": 2, "C": 1, "ungraded": 0}

# ── Price thresholds (% above market) ────────────────────────────────────────
PRICE_ABOVE_EXCELLENT = 3.0   # ≥3% above market → full price score
PRICE_ABOVE_GOOD      = 1.0   # 1–3% above       → 75%
PRICE_AT_MARKET       = -1.0  # within ±1%       → 50%
PRICE_BELOW_OK        = -3.0  # 1–3% below       → 25%
# <-3% below market → 0 price score


class ScoreBreakdown:
    """Individual component scores (each 0..max_weight)."""
    def __init__(
        self,
        crop:     float,
        quality:  float,
        price:    float,
        location: float,
        quantity: float,
        delivery: float,
    ):
        self.crop     = round(crop,     2)
        self.quality  = round(quality,  2)
        self.price    = round(price,    2)
        self.location = round(location, 2)
        self.quantity = round(quantity, 2)
        self.delivery = round(delivery, 2)

    @property
    def total(self) -> float:
        return round(
            self.crop + self.quality + self.price +
            self.location + self.quantity + self.delivery, 2
        )

    def to_dict(self) -> dict:
        return {
            "crop":     self.crop,
            "quality":  self.quality,
            "price":    self.price,
            "location": self.location,
            "quantity": self.quantity,
            "delivery": self.delivery,
        }


class MatchScore:
    """Full match result for one (farmer_crop, buyer) pair."""

    def __init__(
        self,
        breakdown: ScoreBreakdown,
        reasons:   List[str],
        price_vs_market: str,        # "ABOVE_MARKET" | "AT_MARKET" | "BELOW_MARKET" | "UNKNOWN"
        price_advantage: Optional[float],  # ₹/q above (+) or below (-) market price
        distance_km: Optional[float],
        market_price: Optional[float],
    ):
        self.breakdown       = breakdown
        self.match_score     = breakdown.total
        self.reasons         = reasons
        self.price_vs_market = price_vs_market
        self.price_advantage = price_advantage
        self.distance_km     = distance_km
        self.market_price    = market_price

    def to_dict(self) -> dict:
        return {
            "match_score":     self.match_score,
            "breakdown":       self.breakdown.to_dict(),
            "reasons":         self.reasons,
            "price_vs_market": self.price_vs_market,
            "price_advantage": self.price_advantage,
            "distance_km":     self.distance_km,
            "market_price":    self.market_price,
        }


# ── Individual scoring functions ──────────────────────────────────────────────

def score_crop(farmer_crop: str, buyer_crop: str) -> float:
    """Binary: buyer must want this crop. 30 or 0."""
    if farmer_crop.lower().strip() == buyer_crop.lower().strip():
        return float(W_CROP)
    return 0.0


def score_quality(
    farmer_grade: Optional[str],
    buyer_grade:  Optional[str],
) -> float:
    """
    Grade A > B > C > ungraded.
    If farmer grade is missing → 0.5 × W_QUALITY (cannot confirm).
    If buyer grade is missing → full W_QUALITY (buyer accepts all).
    """
    if buyer_grade is None or buyer_grade.upper() in ("", "ANY", "ALL"):
        return float(W_QUALITY)     # buyer accepts any quality

    if farmer_grade is None or farmer_grade.lower() == "ungraded":
        return W_QUALITY * 0.5      # uncertain — partial credit

    fg = GRADE_ORDER.get(farmer_grade.upper(), 0)
    bq = GRADE_ORDER.get(buyer_grade.upper(), 0)

    if fg >= bq:
        return float(W_QUALITY)     # farmer grade meets or exceeds requirement
    diff = bq - fg
    if diff == 1:
        return W_QUALITY * 0.4      # one grade short
    return 0.0                      # two grades short (C vs A)


def score_price(
    offered_price: Optional[float],
    market_price:  Optional[float],
) -> tuple[float, str, Optional[float]]:
    """
    Returns (score, price_vs_market_label, price_advantage_₹).
    Compared against current market modal price from Phase 2.
    """
    if offered_price is None:
        return (W_PRICE * 0.3, "UNKNOWN", None)

    if market_price is None or market_price == 0:
        # No market reference — give neutral score
        return (W_PRICE * 0.5, "UNKNOWN", None)

    advantage = offered_price - market_price
    pct = (advantage / market_price) * 100

    if pct >= PRICE_ABOVE_EXCELLENT:
        label = "ABOVE_MARKET"
        score = float(W_PRICE)
    elif pct >= PRICE_ABOVE_GOOD:
        label = "ABOVE_MARKET"
        score = W_PRICE * 0.75
    elif pct >= PRICE_AT_MARKET:
        label = "AT_MARKET"
        score = W_PRICE * 0.50
    elif pct >= PRICE_BELOW_OK:
        label = "BELOW_MARKET"
        score = W_PRICE * 0.25
    else:
        label = "BELOW_MARKET"
        score = 0.0

    return (round(score, 2), label, round(advantage, 2))


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two (lat, lon) points."""
    R = 6371.0
    φ1, φ2 = math.radians(lat1), math.radians(lat2)
    Δφ = math.radians(lat2 - lat1)
    Δλ = math.radians(lon2 - lon1)
    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# Gujarat district approximate centroids (lat, lon)
DISTRICT_COORDS = {
    "rajkot":         (22.3039, 70.8022),
    "amreli":         (21.6009, 71.2188),
    "junagadh":       (21.5222, 70.4579),
    "bhavnagar":      (21.7645, 72.1519),
    "ahmedabad":      (23.0225, 72.5714),
    "surendranagar":  (22.7273, 71.6490),
    "jamnagar":       (22.4707, 70.0577),
    "mehsana":        (23.5880, 72.3693),
    "banaskantha":    (24.1745, 72.4440),
    "anand":          (22.5645, 72.9289),
    "surat":          (21.1702, 72.8311),
    "vadodara":       (22.3072, 73.1812),
    "kutch":          (23.7337, 69.8597),
    "morbi":          (22.8173, 70.8378),
    "botad":          (22.1698, 71.6669),
    "gondal":         (21.9617, 70.5258),
}


def _parse_district(location_str: Optional[str]) -> Optional[str]:
    """Extract the first token before comma as the district name."""
    if not location_str:
        return None
    city = location_str.split(",")[0].strip().lower()
    return city


def score_location(
    farmer_district: Optional[str],
    buyer_location:  Optional[str],
) -> tuple[float, Optional[float]]:
    """
    Returns (score, distance_km).
    Uses haversine from district centroids.
    If location unknown → neutral score with None distance.
    """
    farmer_key = farmer_district.lower().strip() if farmer_district else None
    buyer_key  = _parse_district(buyer_location)

    farmer_coords = DISTRICT_COORDS.get(farmer_key) if farmer_key else None
    buyer_coords  = DISTRICT_COORDS.get(buyer_key)  if buyer_key  else None

    if not farmer_coords or not buyer_coords:
        return (W_LOCATION * 0.4, None)   # unknown → partial score

    dist = _haversine_km(farmer_coords[0], farmer_coords[1],
                         buyer_coords[0],  buyer_coords[1])
    dist = round(dist, 1)

    if dist <= DIST_EXCELLENT:
        score = float(W_LOCATION)
    elif dist <= DIST_GOOD:
        score = W_LOCATION * 0.75
    elif dist <= DIST_OK:
        score = W_LOCATION * 0.50
    elif dist <= DIST_FAR:
        score = W_LOCATION * 0.25
    else:
        score = 0.0

    return (round(score, 2), dist)


def score_quantity(
    farmer_quantity: Optional[float],
    buyer_min:       Optional[float],
    buyer_max:       Optional[float],
) -> float:
    """
    Full score if farmer qty is within buyer range.
    Partial if close to range.
    Zero if farmer qty is far outside buyer range.
    """
    if farmer_quantity is None:
        return W_QUANTITY * 0.3    # unknown quantity → minimal credit

    if buyer_min is None and buyer_max is None:
        return float(W_QUANTITY)   # buyer has no quantity restriction

    lo = buyer_min or 0.0
    hi = buyer_max or float("inf")

    if lo <= farmer_quantity <= hi:
        return float(W_QUANTITY)   # perfect fit

    # Below minimum
    if farmer_quantity < lo:
        ratio = farmer_quantity / lo if lo > 0 else 0
        return round(W_QUANTITY * max(0, ratio), 2)

    # Above maximum
    if farmer_quantity > hi and hi < float("inf"):
        ratio = hi / farmer_quantity if farmer_quantity > 0 else 0
        return round(W_QUANTITY * max(0, ratio), 2)

    return float(W_QUANTITY)


def score_delivery(
    harvest_date:   Optional[date],
    delivery_date:  Optional[date],
) -> float:
    """
    Compares farmer expected harvest date with buyer delivery deadline.
    Full score if harvest is before deadline with plenty of time.
    """
    if harvest_date is None or delivery_date is None:
        return W_DELIVERY * 0.5    # unknown — neutral

    if harvest_date <= delivery_date:
        days_margin = (delivery_date - harvest_date).days
        if days_margin >= 14:
            return float(W_DELIVERY)
        if days_margin >= 7:
            return W_DELIVERY * 0.75
        return W_DELIVERY * 0.5
    else:
        # Harvest is AFTER the delivery date — risky
        overdue = (harvest_date - delivery_date).days
        if overdue <= 7:
            return W_DELIVERY * 0.25
        return 0.0


# ── Reason generator ──────────────────────────────────────────────────────────

def generate_reasons(
    breakdown:       ScoreBreakdown,
    offered_price:   Optional[float],
    market_price:    Optional[float],
    price_advantage: Optional[float],
    distance_km:     Optional[float],
    farmer_grade:    Optional[str],
    buyer_grade:     Optional[str],
    farmer_qty:      Optional[float],
    buyer_min:       Optional[float],
    buyer_max:       Optional[float],
    price_vs_market: str,
) -> List[str]:
    """
    Build a plain-English list of match reasons from structured scoring data.
    No LLM — deterministic template-based text only.
    """
    reasons: List[str] = []

    # Crop
    if breakdown.crop >= W_CROP:
        reasons.append("Buyer requires your crop")

    # Quality
    if breakdown.quality >= W_QUALITY:
        reasons.append(f"Your quality grade meets buyer requirement (Grade {buyer_grade or 'Any'})")
    elif breakdown.quality >= W_QUALITY * 0.4:
        reasons.append("Partial quality match — buyer may negotiate grade")
    elif breakdown.quality > 0:
        reasons.append("Grade not confirmed — buyer will verify at delivery")

    # Price
    if offered_price and market_price:
        if price_vs_market == "ABOVE_MARKET":
            reasons.append(
                f"Buyer offer ₹{offered_price:,.0f}/q is"
                f" ₹{abs(price_advantage or 0):,.0f} above market price (₹{market_price:,.0f}/q)"
            )
        elif price_vs_market == "AT_MARKET":
            reasons.append(
                f"Buyer offer ₹{offered_price:,.0f}/q is near current market price (₹{market_price:,.0f}/q)"
            )
        else:
            reasons.append(
                f"Buyer offer ₹{offered_price:,.0f}/q is"
                f" ₹{abs(price_advantage or 0):,.0f} below market (₹{market_price:,.0f}/q)"
            )
    elif offered_price:
        reasons.append(f"Buyer offering ₹{offered_price:,.0f}/q (market price unavailable)")

    # Location
    if distance_km is not None:
        if distance_km <= DIST_EXCELLENT:
            reasons.append(f"Buyer is very close — approx {distance_km:.0f} km away")
        elif distance_km <= DIST_GOOD:
            reasons.append(f"Buyer is within comfortable distance — approx {distance_km:.0f} km")
        elif distance_km <= DIST_OK:
            reasons.append(f"Buyer is at moderate distance — approx {distance_km:.0f} km")
        else:
            reasons.append(f"Buyer is far — approx {distance_km:.0f} km away (transport costs apply)")
    else:
        reasons.append("Buyer location estimated from district data")

    # Quantity
    if farmer_qty is not None and (buyer_min or buyer_max):
        if breakdown.quantity >= W_QUANTITY:
            reasons.append(
                f"Your quantity ({farmer_qty:.0f} qtl) fits buyer requirement"
                f" ({buyer_min or 0:.0f}–{buyer_max or '∞'} qtl)"
            )
        else:
            reasons.append(
                f"Quantity partial match — you have {farmer_qty:.0f} qtl,"
                f" buyer wants {buyer_min or 0:.0f}–{buyer_max or '∞'} qtl"
            )

    return reasons


# ── Master scoring function ───────────────────────────────────────────────────

def compute_match_score(
    farmer_crop:     str,
    farmer_grade:    Optional[str],
    farmer_quantity: Optional[float],
    farmer_district: Optional[str],
    harvest_date:    Optional[date],
    buyer_crop:      str,
    buyer_grade:     Optional[str],
    buyer_min_qty:   Optional[float],
    buyer_max_qty:   Optional[float],
    offered_price:   Optional[float],
    buyer_location:  Optional[str],
    delivery_date:   Optional[date],
    market_price:    Optional[float],
) -> MatchScore:
    """
    Compute the full 100-point match score for a (farmer_crop, buyer) pair.
    Returns a MatchScore with breakdown, reasons, and market price context.
    """
    # Individual scores
    crop_score     = score_crop(farmer_crop, buyer_crop)
    quality_score  = score_quality(farmer_grade, buyer_grade)
    price_score, price_label, price_adv = score_price(offered_price, market_price)
    location_score, dist_km             = score_location(farmer_district, buyer_location)
    quantity_score = score_quantity(farmer_quantity, buyer_min_qty, buyer_max_qty)
    delivery_score = score_delivery(harvest_date, delivery_date)

    breakdown = ScoreBreakdown(
        crop=crop_score,
        quality=quality_score,
        price=price_score,
        location=location_score,
        quantity=quantity_score,
        delivery=delivery_score,
    )

    reasons = generate_reasons(
        breakdown=breakdown,
        offered_price=offered_price,
        market_price=market_price,
        price_advantage=price_adv,
        distance_km=dist_km,
        farmer_grade=farmer_grade,
        buyer_grade=buyer_grade,
        farmer_qty=farmer_quantity,
        buyer_min=buyer_min_qty,
        buyer_max=buyer_max_qty,
        price_vs_market=price_label,
    )

    return MatchScore(
        breakdown=breakdown,
        reasons=reasons,
        price_vs_market=price_label,
        price_advantage=price_adv,
        distance_km=dist_km,
        market_price=market_price,
    )
