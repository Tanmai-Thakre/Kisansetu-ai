"""
Phase 6 — Quality Grading Rules (deterministic, crop-specific).

Grades: EXCELLENT / GOOD / AVERAGE / POOR
Score: 0–100  (weighted parameter sum)
Confidence: 0–100 (based on how many parameters were supplied)

Rules are pure functions — no side effects, no LLM.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple

# ── Grade constants ────────────────────────────────────────────────────────────

GRADE_EXCELLENT = "EXCELLENT"
GRADE_GOOD      = "GOOD"
GRADE_AVERAGE   = "AVERAGE"
GRADE_POOR      = "POOR"

# Price-impact multipliers per grade (percentage change relative to baseline)
GRADE_PRICE_IMPACT: Dict[str, Tuple[float, float]] = {
    GRADE_EXCELLENT: ( 3.0,  5.0),   # +3% to +5%
    GRADE_GOOD:      ( 0.5,  2.5),   # +0.5% to +2.5%
    GRADE_AVERAGE:   ( 0.0,  0.0),   # baseline
    GRADE_POOR:      (-5.0, -2.0),   # −5% to −2%
}

# ── Parameter-level rating ─────────────────────────────────────────────────────

RATING_GOOD     = "good"
RATING_MODERATE = "moderate"
RATING_POOR     = "poor"
RATING_NA       = "not_available"


@dataclass
class ParameterResult:
    name: str
    value: Optional[float]
    rating: str          # good / moderate / poor / not_available
    score: float         # 0–100 contribution
    weight: float        # relative weight
    source: str          # "measured" | "estimated" | "unavailable"
    note: str = ""


@dataclass
class GradingResult:
    crop: str
    grade: str
    quality_score: float
    confidence: float
    parameters: Dict[str, ParameterResult] = field(default_factory=dict)
    observations: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    price_impact_percent: float = 0.0
    image_used: bool = False


# ── Score helpers ──────────────────────────────────────────────────────────────

def _score_in_range(value: float, excellent: tuple, good: tuple, average: tuple) -> Tuple[float, str]:
    """
    Returns (score 0-100, rating) given inclusive thresholds for excellent/good/average.
    Values outside average → poor.
    """
    lo_ex, hi_ex = excellent
    lo_go, hi_go = good
    lo_av, hi_av = average

    if lo_ex <= value <= hi_ex:
        return 90.0, RATING_GOOD
    if lo_go <= value <= hi_go:
        return 70.0, RATING_GOOD
    if lo_av <= value <= hi_av:
        return 50.0, RATING_MODERATE
    return 20.0, RATING_POOR


def _score_below(value: float, excellent: float, good: float, average: float) -> Tuple[float, str]:
    """
    Lower is better (e.g. moisture, foreign matter, damaged kernels).
    """
    if value <= excellent:
        return 90.0, RATING_GOOD
    if value <= good:
        return 70.0, RATING_GOOD
    if value <= average:
        return 50.0, RATING_MODERATE
    return 20.0, RATING_POOR


def _score_above(value: float, excellent: float, good: float, average: float) -> Tuple[float, str]:
    """
    Higher is better (e.g. staple length, kernel size score).
    """
    if value >= excellent:
        return 90.0, RATING_GOOD
    if value >= good:
        return 70.0, RATING_GOOD
    if value >= average:
        return 50.0, RATING_MODERATE
    return 20.0, RATING_POOR


# ── COTTON grading ─────────────────────────────────────────────────────────────

# Cotton parameter weights (must sum to 1.0)
_COTTON_WEIGHTS = {
    "moisture":      0.25,
    "staple_length": 0.20,
    "micronaire":    0.15,
    "foreign_matter":0.20,
    "color":         0.12,
    "uniformity":    0.08,
}


def _grade_cotton_moisture(v: float) -> Tuple[float, str]:
    # Moisture (%): ≤8 excellent, ≤10 good, ≤12 average, >12 poor
    return _score_below(v, excellent=8.0, good=10.0, average=12.0)


def _grade_cotton_staple(v: float) -> Tuple[float, str]:
    # Staple length (mm): ≥30 excellent, ≥27 good, ≥24 average
    return _score_above(v, excellent=30.0, good=27.0, average=24.0)


def _grade_cotton_micronaire(v: float) -> Tuple[float, str]:
    # Micronaire (µg/inch): 3.5–4.9 excellent, 3.0–5.4 good, 2.5–5.9 average
    return _score_in_range(v,
        excellent=(3.5, 4.9),
        good=(3.0, 5.4),
        average=(2.5, 5.9),
    )


def _grade_cotton_foreign(v: float) -> Tuple[float, str]:
    # Foreign matter (%): ≤1 excellent, ≤2 good, ≤4 average
    return _score_below(v, excellent=1.0, good=2.0, average=4.0)


def _grade_cotton_color(v: float) -> Tuple[float, str]:
    # Color score (1–5, user-entered, 5=best): ≥4.5 excellent, ≥3.5 good, ≥2.5 average
    return _score_above(v, excellent=4.5, good=3.5, average=2.5)


def _grade_cotton_uniformity(v: float) -> Tuple[float, str]:
    # Uniformity index (%): ≥84 excellent, ≥80 good, ≥76 average
    return _score_above(v, excellent=84.0, good=80.0, average=76.0)


def grade_cotton(params: Dict[str, Optional[float]]) -> GradingResult:
    """
    Deterministic cotton quality grading.
    params keys: moisture, staple_length, micronaire, foreign_matter, color, uniformity
    All are optional floats. Unknown = None.
    """
    _graders = {
        "moisture":      _grade_cotton_moisture,
        "staple_length": _grade_cotton_staple,
        "micronaire":    _grade_cotton_micronaire,
        "foreign_matter":_grade_cotton_foreign,
        "color":         _grade_cotton_color,
        "uniformity":    _grade_cotton_uniformity,
    }

    param_results: Dict[str, ParameterResult] = {}
    weighted_score = 0.0
    total_weight_used = 0.0
    suggestions: List[str] = []
    observations: List[str] = []

    for key, grader in _graders.items():
        val = params.get(key)
        weight = _COTTON_WEIGHTS[key]
        if val is None:
            param_results[key] = ParameterResult(
                name=key, value=None, rating=RATING_NA,
                score=0.0, weight=weight,
                source="unavailable",
                note="Not provided",
            )
        else:
            score, rating = grader(val)
            weighted_score += score * weight
            total_weight_used += weight
            param_results[key] = ParameterResult(
                name=key, value=val, rating=rating,
                score=score, weight=weight,
                source="measured",
            )
            if rating == RATING_POOR:
                suggestions.append(_cotton_suggestion(key, val))
            elif rating == RATING_GOOD and score >= 80:
                observations.append(_cotton_observation(key, val))

    # Normalise if not all params supplied
    if total_weight_used > 0:
        quality_score = round(weighted_score / total_weight_used, 1)
    else:
        quality_score = 50.0  # unknown → neutral

    # Confidence = fraction of max possible weight supplied
    confidence = round((total_weight_used / 1.0) * 100, 1)

    grade = _score_to_grade(quality_score)
    price_impact = _midpoint_impact(grade)

    if not observations:
        observations.append("Assessment based on provided parameters.")

    return GradingResult(
        crop="Cotton",
        grade=grade,
        quality_score=quality_score,
        confidence=confidence,
        parameters=param_results,
        observations=observations,
        suggestions=suggestions,
        limitations=[],
        price_impact_percent=price_impact,
    )


def _cotton_suggestion(key: str, val: float) -> str:
    msgs = {
        "moisture":       f"Moisture is {val}% — dry the cotton below 12% before sale.",
        "staple_length":  f"Staple length is {val} mm — consider premium varieties (≥30 mm) for next season.",
        "micronaire":     f"Micronaire value {val} is outside optimal range (3.5–4.9).",
        "foreign_matter": f"Foreign matter {val}% is high — clean the cotton before sale.",
        "color":          f"Color score {val}/5 is low — avoid contamination and over-exposure.",
        "uniformity":     f"Uniformity index {val}% is below ideal — ginning quality may be affecting uniformity.",
    }
    return msgs.get(key, f"{key} is below recommended range.")


def _cotton_observation(key: str, val: float) -> str:
    msgs = {
        "moisture":       f"Good moisture level ({val}%).",
        "staple_length":  f"Excellent staple length ({val} mm).",
        "micronaire":     f"Micronaire within optimal range ({val}).",
        "foreign_matter": f"Low foreign matter ({val}%).",
        "color":          f"Good color appearance (score {val}/5).",
        "uniformity":     f"Good fiber uniformity ({val}%).",
    }
    return msgs.get(key, f"{key} looks good.")


# ── GROUNDNUT grading ──────────────────────────────────────────────────────────

_GROUNDNUT_WEIGHTS = {
    "moisture":         0.25,
    "kernel_appearance":0.15,
    "damaged_kernels":  0.20,
    "foreign_matter":   0.20,
    "kernel_size":      0.12,
    "color":            0.08,
}


def _grade_gn_moisture(v: float) -> Tuple[float, str]:
    # Moisture (%): ≤7 excellent, ≤9 good, ≤11 average
    return _score_below(v, excellent=7.0, good=9.0, average=11.0)


def _grade_gn_appearance(v: float) -> Tuple[float, str]:
    # Kernel appearance score (1–5): ≥4.5 excellent, ≥3.5 good, ≥2.5 average
    return _score_above(v, excellent=4.5, good=3.5, average=2.5)


def _grade_gn_damaged(v: float) -> Tuple[float, str]:
    # Damaged kernels (%): ≤2 excellent, ≤5 good, ≤10 average
    return _score_below(v, excellent=2.0, good=5.0, average=10.0)


def _grade_gn_foreign(v: float) -> Tuple[float, str]:
    # Foreign matter (%): ≤1 excellent, ≤2 good, ≤4 average
    return _score_below(v, excellent=1.0, good=2.0, average=4.0)


def _grade_gn_size(v: float) -> Tuple[float, str]:
    # Kernel size score (1–5): ≥4 excellent, ≥3 good, ≥2 average
    return _score_above(v, excellent=4.0, good=3.0, average=2.0)


def _grade_gn_color(v: float) -> Tuple[float, str]:
    # Color score (1–5): ≥4.5 excellent, ≥3.5 good, ≥2.5 average
    return _score_above(v, excellent=4.5, good=3.5, average=2.5)


def grade_groundnut(params: Dict[str, Optional[float]]) -> GradingResult:
    """
    Deterministic groundnut quality grading.
    params keys: moisture, kernel_appearance, damaged_kernels, foreign_matter, kernel_size, color
    """
    _graders = {
        "moisture":         _grade_gn_moisture,
        "kernel_appearance":_grade_gn_appearance,
        "damaged_kernels":  _grade_gn_damaged,
        "foreign_matter":   _grade_gn_foreign,
        "kernel_size":      _grade_gn_size,
        "color":            _grade_gn_color,
    }

    param_results: Dict[str, ParameterResult] = {}
    weighted_score = 0.0
    total_weight_used = 0.0
    suggestions: List[str] = []
    observations: List[str] = []

    for key, grader in _graders.items():
        val = params.get(key)
        weight = _GROUNDNUT_WEIGHTS[key]
        if val is None:
            param_results[key] = ParameterResult(
                name=key, value=None, rating=RATING_NA,
                score=0.0, weight=weight,
                source="unavailable",
                note="Not provided",
            )
        else:
            score, rating = grader(val)
            weighted_score += score * weight
            total_weight_used += weight
            param_results[key] = ParameterResult(
                name=key, value=val, rating=rating,
                score=score, weight=weight,
                source="measured",
            )
            if rating == RATING_POOR:
                suggestions.append(_groundnut_suggestion(key, val))
            elif rating == RATING_GOOD and score >= 80:
                observations.append(_groundnut_observation(key, val))

    if total_weight_used > 0:
        quality_score = round(weighted_score / total_weight_used, 1)
    else:
        quality_score = 50.0

    confidence = round((total_weight_used / 1.0) * 100, 1)

    grade = _score_to_grade(quality_score)
    price_impact = _midpoint_impact(grade)

    if not observations:
        observations.append("Assessment based on provided parameters.")

    return GradingResult(
        crop="Groundnut",
        grade=grade,
        quality_score=quality_score,
        confidence=confidence,
        parameters=param_results,
        observations=observations,
        suggestions=suggestions,
        limitations=[],
        price_impact_percent=price_impact,
    )


def _groundnut_suggestion(key: str, val: float) -> str:
    msgs = {
        "moisture":         f"Moisture is {val}% — sun-dry or mechanically dry below 9% before storage/sale.",
        "kernel_appearance":f"Kernel appearance score {val}/5 is low — check for fungal growth or discolouration.",
        "damaged_kernels":  f"Damaged kernels at {val}% — sort and remove damaged pods before sale.",
        "foreign_matter":   f"Foreign matter {val}% exceeds recommended limit — clean before sale.",
        "kernel_size":      f"Kernel size score {val}/5 is below market preference.",
        "color":            f"Color score {val}/5 — poor color may indicate improper drying or storage.",
    }
    return msgs.get(key, f"{key} is below recommended range.")


def _groundnut_observation(key: str, val: float) -> str:
    msgs = {
        "moisture":         f"Good moisture level ({val}%).",
        "kernel_appearance":f"Good kernel appearance (score {val}/5).",
        "damaged_kernels":  f"Low damaged kernel percentage ({val}%).",
        "foreign_matter":   f"Low foreign matter ({val}%).",
        "kernel_size":      f"Good kernel size (score {val}/5).",
        "color":            f"Good color (score {val}/5).",
    }
    return msgs.get(key, f"{key} looks good.")


# ── Shared helpers ─────────────────────────────────────────────────────────────

def _score_to_grade(score: float) -> str:
    if score >= 80:
        return GRADE_EXCELLENT
    if score >= 62:
        return GRADE_GOOD
    if score >= 44:
        return GRADE_AVERAGE
    return GRADE_POOR


def _midpoint_impact(grade: str) -> float:
    lo, hi = GRADE_PRICE_IMPACT.get(grade, (0.0, 0.0))
    return round((lo + hi) / 2, 2)


# ── Dispatcher ─────────────────────────────────────────────────────────────────

def grade_crop(crop: str, params: Dict[str, Optional[float]]) -> GradingResult:
    """Entry point — routes to per-crop grader."""
    c = crop.lower().strip()
    if c == "cotton":
        return grade_cotton(params)
    if c in ("groundnut", "peanut"):
        return grade_groundnut(params)
    raise ValueError(f"Unsupported crop: '{crop}'. Supported: cotton, groundnut.")
