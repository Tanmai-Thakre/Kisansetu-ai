"""
Phase 6 — Image Analysis module.

Provides heuristic computer-vision analysis for crop images.
Uses only Pillow (already available as a transitive dependency) — no heavy ML libs.

Important constraints:
  - Does NOT claim laboratory-level accuracy.
  - Clearly states which attributes cannot be determined from image.
  - Returns "not_reliably_detectable" for all sub-millimetre properties
    (moisture content, micronaire, staple length, exact percentages).
  - Falls back gracefully if Pillow is not installed.
"""
from __future__ import annotations

import io
import math
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple

# ── Image observation result ───────────────────────────────────────────────────

@dataclass
class ImageObservation:
    """Visual observations extracted from a crop image."""
    available: bool = False
    error: Optional[str] = None

    # Shared observations (crop-agnostic)
    color_score: Optional[float] = None          # 1–5 visual estimate
    visible_foreign_matter_low: Optional[bool] = None  # True = looks clean
    discolouration_detected: Optional[bool] = None

    # Cotton-specific
    cotton_whiteness_good: Optional[bool] = None

    # Groundnut-specific
    kernel_uniformity_good: Optional[bool] = None
    visible_damage_low: Optional[bool] = None

    observations: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    # Parameters that cannot be determined from image
    NOT_DETECTABLE: List[str] = field(default_factory=list)


# Attributes never determinable from a photo
_COTTON_NOT_DETECTABLE = [
    "Exact moisture content — requires moisture meter.",
    "Micronaire (fiber fineness) — requires HVI instrument.",
    "Staple length — requires HVI or AFIS instrument.",
    "Uniformity index — requires HVI instrument.",
]

_GROUNDNUT_NOT_DETECTABLE = [
    "Exact moisture content — requires moisture meter.",
    "Aflatoxin contamination — requires laboratory testing.",
    "Exact damaged kernel percentage — requires sample sorting.",
]


def _try_import_pillow():
    try:
        from PIL import Image, ImageStat
        return Image, ImageStat
    except ImportError:
        return None, None


def _analyze_color_stats(img) -> Tuple[Optional[float], Optional[bool], Optional[bool]]:
    """
    Analyse image color statistics.
    Returns (color_score 1-5, is_bright, has_discolouration).
    """
    try:
        from PIL import ImageStat
        # Convert to RGB if needed
        img_rgb = img.convert("RGB")
        stat = ImageStat.Stat(img_rgb)
        r_mean, g_mean, b_mean = stat.mean[:3]
        r_std, g_std, b_std = stat.stddev[:3]

        brightness = (r_mean + g_mean + b_mean) / 3.0
        # Simple whiteness index for cotton
        # White cotton: high brightness, low colour deviation
        color_balance = abs(r_mean - b_mean) + abs(r_mean - g_mean)

        # Score brightness (0–255 → 1–5)
        brightness_score = 1.0 + (brightness / 255.0) * 4.0

        # Penalise strong colour casts (yellowing, browning)
        cast_penalty = min(2.0, color_balance / 40.0)
        color_score = max(1.0, min(5.0, round(brightness_score - cast_penalty, 1)))

        is_bright = brightness > 140
        has_discolouration = color_balance > 40

        return color_score, is_bright, has_discolouration
    except Exception:
        return None, None, None


def analyze_image(image_bytes: bytes, crop: str) -> ImageObservation:
    """
    Perform heuristic visual analysis on a crop image.
    Returns observations; never fabricates lab parameters.
    """
    Image, _ = _try_import_pillow()
    obs = ImageObservation()
    c = crop.lower().strip()

    if Image is None:
        obs.available = False
        obs.error = "Image analysis library (Pillow) not installed."
        obs.observations = ["Image processing unavailable on this server."]
        obs.limitations = ["Install Pillow to enable image analysis."]
        return obs

    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Limit image to 1024px to avoid memory issues
        img.thumbnail((1024, 1024))
    except Exception as e:
        obs.available = False
        obs.error = f"Could not open image: {e}"
        obs.observations = ["Image could not be processed."]
        obs.limitations = ["Please upload a valid JPG, PNG, or WebP image."]
        return obs

    color_score, is_bright, has_discolouration = _analyze_color_stats(img)
    obs.available = True
    obs.color_score = color_score
    obs.discolouration_detected = has_discolouration

    if c == "cotton":
        return _analyze_cotton_image(obs, is_bright, has_discolouration, color_score)
    elif c in ("groundnut", "peanut"):
        return _analyze_groundnut_image(obs, is_bright, has_discolouration, color_score)
    else:
        obs.observations.append("Crop type not recognized for image analysis.")
        return obs


def _analyze_cotton_image(
    obs: ImageObservation,
    is_bright: Optional[bool],
    has_discolouration: Optional[bool],
    color_score: Optional[float],
) -> ImageObservation:
    """Heuristic cotton-specific observations."""
    obs.NOT_DETECTABLE = _COTTON_NOT_DETECTABLE

    if is_bright is not None:
        obs.cotton_whiteness_good = is_bright
        if is_bright:
            obs.observations.append("Cotton appears light-coloured — visually consistent with good color grade.")
        else:
            obs.observations.append("Cotton appears darker — may indicate yellowing or staining.")

    if has_discolouration is not None:
        if has_discolouration:
            obs.discolouration_detected = True
            obs.observations.append("Possible colour variation detected — verify color grade manually.")
        else:
            obs.observations.append("No significant discolouration visible in image.")

    obs.visible_foreign_matter_low = None  # cannot reliably determine from image alone
    obs.observations.append("Foreign matter visibility is low-resolution — visual estimate only.")

    obs.limitations = [
        "Exact moisture cannot be confirmed from image — use a moisture meter.",
        "Staple length and micronaire cannot be estimated from image.",
        "Uniformity index cannot be estimated from image.",
    ]

    return obs


def _analyze_groundnut_image(
    obs: ImageObservation,
    is_bright: Optional[bool],
    has_discolouration: Optional[bool],
    color_score: Optional[float],
) -> ImageObservation:
    """Heuristic groundnut-specific observations."""
    obs.NOT_DETECTABLE = _GROUNDNUT_NOT_DETECTABLE

    if color_score is not None:
        obs.observations.append(
            f"Estimated visual color score: {color_score}/5 — "
            "confirm with physical inspection."
        )

    if has_discolouration is not None:
        if has_discolouration:
            obs.observations.append(
                "Possible discolouration detected — check for mould or aflatoxin risk."
            )
        else:
            obs.observations.append("Colour appears reasonably uniform in image.")

    if is_bright is not None:
        obs.kernel_uniformity_good = is_bright  # very rough heuristic
        obs.visible_damage_low = is_bright

    obs.limitations = [
        "Exact moisture content cannot be determined from image.",
        "Aflatoxin contamination cannot be detected visually — laboratory testing required.",
        "Exact damaged kernel percentage cannot be determined from image alone.",
    ]

    return obs


def merge_image_params(
    manual_params: Dict[str, Optional[float]],
    image_obs: ImageObservation,
    crop: str,
) -> Tuple[Dict[str, Optional[float]], List[str]]:
    """
    Merge manual parameters with image-derived estimates.
    Manual values always take precedence over image estimates.

    Returns (merged_params, source_annotations)
    """
    merged = dict(manual_params)
    annotations: List[str] = []
    c = crop.lower().strip()

    if not image_obs.available:
        return merged, annotations

    if c == "cotton":
        # Color: use image estimate only if not manually provided
        if merged.get("color") is None and image_obs.color_score is not None:
            merged["color"] = image_obs.color_score
            annotations.append(f"color: estimated from image ({image_obs.color_score}/5)")

    elif c in ("groundnut", "peanut"):
        if merged.get("color") is None and image_obs.color_score is not None:
            merged["color"] = image_obs.color_score
            annotations.append(f"color: estimated from image ({image_obs.color_score}/5)")

    return merged, annotations
