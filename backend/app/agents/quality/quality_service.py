"""
Phase 6 — QualityService: orchestrates grading pipeline.

Pipeline:
  1. Validate crop & parameters
  2. Optionally analyse image
  3. Merge image observations with manual params
  4. Grade using deterministic rules
  5. Fetch reference market price (Phase 2)
  6. Calculate price-impact estimate
  7. Persist assessment to DB
  8. Return structured response
"""
from __future__ import annotations

import hashlib
import os
import pathlib
import uuid
from datetime import datetime, timezone

_UTC = timezone.utc
from typing import Optional, Dict, List, Any

from sqlalchemy.orm import Session

from app.agents.quality.grading_rules import grade_crop, GRADE_PRICE_IMPACT, GradingResult
from app.agents.quality.image_analysis import analyze_image, merge_image_params, ImageObservation
from app.models.quality_assessment import QualityAssessment
from app.services.market_data_provider import get_market_data_provider

# ── Upload directory ───────────────────────────────────────────────────────────

UPLOAD_DIR = pathlib.Path(
    os.getenv("QUALITY_UPLOAD_DIR", "./uploads/quality")
)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

MAX_FILE_BYTES = 10 * 1024 * 1024   # 10 MB
ALLOWED_TYPES  = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTS   = {".jpg", ".jpeg", ".png", ".webp"}

# ── Default reference prices (fallback if market service unavailable) ──────────

_FALLBACK_PRICES = {
    "cotton":    7200.0,
    "groundnut": 6100.0,
}

DISCLAIMER = (
    "Preliminary AI-assisted assessment: This result is an estimate and is not a "
    "substitute for laboratory or authorized quality testing."
)


# ── QualityService ─────────────────────────────────────────────────────────────

class QualityService:
    """
    Phase 6 Quality Grading Assistance Service.
    All calculations are deterministic — no LLM.
    """

    def __init__(self):
        self._market = get_market_data_provider()

    # ── Market price helper ────────────────────────────────────────────────────

    def _get_reference_price(self, crop: str) -> Optional[float]:
        try:
            records = self._market.get_latest_prices(crop=crop.lower(), limit=5)
            if records:
                return float(records[0].modal_price)
        except Exception:
            pass
        return _FALLBACK_PRICES.get(crop.lower())

    # ── Price-impact calculation ───────────────────────────────────────────────

    @staticmethod
    def _calculate_price_impact(
        grade: str, price_impact_pct: float, reference_price: Optional[float]
    ) -> Dict[str, Any]:
        if reference_price is None:
            return {
                "reference_price": None,
                "price_impact_percent": price_impact_pct,
                "estimated_quality_price": None,
                "price_note": "Reference market price unavailable. Quality assessment completed without price estimation.",
            }
        estimated = round(reference_price * (1 + price_impact_pct / 100), 2)
        lo, hi = GRADE_PRICE_IMPACT.get(grade, (0.0, 0.0))
        sign = "+" if price_impact_pct >= 0 else ""
        return {
            "reference_price": reference_price,
            "price_impact_percent": price_impact_pct,
            "estimated_quality_price": estimated,
            "price_impact_range": f"{'+' if lo >= 0 else ''}{lo:.1f}% to {'+' if hi >= 0 else ''}{hi:.1f}%",
            "price_note": (
                f"Estimated quality impact: {sign}{price_impact_pct:.1f}%. "
                "This is an estimate, not a guaranteed buyer price."
            ),
        }

    # ── Image handling ─────────────────────────────────────────────────────────

    @staticmethod
    def _save_image(image_bytes: bytes, crop: str, farmer_id: int) -> str:
        """Save image safely; return opaque reference (not the real path)."""
        ext = ".jpg"  # default; caller should detect MIME
        safe_name = f"{farmer_id}_{crop}_{uuid.uuid4().hex[:12]}{ext}"
        dest = UPLOAD_DIR / safe_name
        dest.write_bytes(image_bytes)
        # Return a content-hash reference — don't expose filesystem path
        sha = hashlib.sha256(image_bytes).hexdigest()[:16]
        return f"img_{sha}"

    # ── DB persistence ─────────────────────────────────────────────────────────

    @staticmethod
    def _save_assessment(
        db: Session,
        farmer_id: int,
        crop_id: Optional[int],
        crop: str,
        image_ref: Optional[str],
        result: GradingResult,
        price_info: Dict,
    ) -> QualityAssessment:
        import json

        factors = {
            k: v.rating
            for k, v in result.parameters.items()
        }
        parameters_json = json.dumps(
            {
                k: {
                    "value": v.value,
                    "rating": v.rating,
                    "score": v.score,
                    "source": v.source,
                }
                for k, v in result.parameters.items()
            }
        )
        observations_json = json.dumps({
            "observations": result.observations,
            "suggestions":  result.suggestions,
            "limitations":  result.limitations,
        })

        qa = QualityAssessment(
            farmer_id=farmer_id,
            crop_id=crop_id,
            crop=crop.lower(),
            image_reference=image_ref,
            grade=result.grade,
            quality_score=result.quality_score,
            confidence=result.confidence,
            parameters_json=parameters_json,
            observations_json=observations_json,
            price_impact_percent=result.price_impact_percent,
            reference_price=price_info.get("reference_price"),
            estimated_quality_price=price_info.get("estimated_quality_price"),
            created_at=datetime.now(_UTC),
        )
        db.add(qa)
        db.commit()
        db.refresh(qa)
        return qa

    # ── Main assessment entry point ────────────────────────────────────────────

    def assess(
        self,
        db: Session,
        farmer_id: int,
        crop: str,
        manual_params: Dict[str, Optional[float]],
        image_bytes: Optional[bytes] = None,
        crop_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Full quality grading pipeline.
        Returns a structured dict matching the API response schema.
        """
        crop_lower = crop.lower().strip()

        # ── Image analysis ─────────────────────────────────────────────────────
        image_ref: Optional[str] = None
        img_obs: Optional[ImageObservation] = None
        image_limitations: List[str] = []
        image_observations: List[str] = []

        if image_bytes:
            try:
                img_obs = analyze_image(image_bytes, crop_lower)
                if img_obs.available:
                    image_observations = img_obs.observations or []
                    image_limitations  = img_obs.limitations  or []
                    image_ref = self._save_image(image_bytes, crop_lower, farmer_id)
                else:
                    image_limitations = [
                        img_obs.error or "Image analysis was unavailable. "
                        "You can continue using manual quality parameters."
                    ]
            except Exception as e:
                image_limitations = [
                    f"Image analysis failed ({e}). "
                    "Continuing with manual parameters only."
                ]

        # ── Merge image-estimated params with manual params ────────────────────
        merged_params = dict(manual_params)
        image_param_annotations: List[str] = []
        if img_obs and img_obs.available:
            merged_params, image_param_annotations = merge_image_params(
                manual_params, img_obs, crop_lower
            )
            # Mark image-sourced params
            for p_name in merged_params:
                if (
                    manual_params.get(p_name) is None
                    and merged_params[p_name] is not None
                ):
                    pass  # will be labelled "estimated" by grading_rules

        # ── Grading ───────────────────────────────────────────────────────────
        result = grade_crop(crop_lower, merged_params)

        # Update source tags for image-derived params
        if img_obs and img_obs.available:
            for note in image_param_annotations:
                param_name = note.split(":")[0].strip()
                if param_name in result.parameters:
                    result.parameters[param_name].source = "estimated"
                    result.parameters[param_name].note = "Estimated from image"

        # ── Reference price & impact ───────────────────────────────────────────
        reference_price = self._get_reference_price(crop_lower)
        price_info = self._calculate_price_impact(
            result.grade, result.price_impact_percent, reference_price
        )

        # ── Persist ────────────────────────────────────────────────────────────
        qa = self._save_assessment(
            db=db,
            farmer_id=farmer_id,
            crop_id=crop_id,
            crop=crop_lower,
            image_ref=image_ref,
            result=result,
            price_info=price_info,
        )

        # ── Build response ─────────────────────────────────────────────────────
        all_observations = list(result.observations) + image_observations
        all_limitations  = list(result.limitations)  + image_limitations
        if img_obs and img_obs.NOT_DETECTABLE:
            all_limitations.extend(img_obs.NOT_DETECTABLE)
        if image_param_annotations:
            all_observations.extend([f"[Image] {a}" for a in image_param_annotations])

        return {
            "id":                    qa.id,
            "crop":                  result.crop,
            "grade":                 result.grade,
            "quality_score":         result.quality_score,
            "confidence":            result.confidence,
            "factors": {
                k: v.rating
                for k, v in result.parameters.items()
            },
            "parameter_details": {
                k: {
                    "value":  v.value,
                    "rating": v.rating,
                    "source": v.source,
                    "note":   v.note,
                }
                for k, v in result.parameters.items()
            },
            "price_impact_percent":    price_info["price_impact_percent"],
            "reference_price":         price_info.get("reference_price"),
            "estimated_quality_price": price_info.get("estimated_quality_price"),
            "price_impact_range":      price_info.get("price_impact_range"),
            "price_note":              price_info.get("price_note"),
            "observations":            all_observations,
            "suggestions":             result.suggestions,
            "limitations":             all_limitations,
            "image_used":              image_ref is not None,
            "disclaimer":              DISCLAIMER,
            "source_status":           "DEMO",
            "created_at":              qa.created_at.isoformat(),
        }

    # ── History ────────────────────────────────────────────────────────────────

    @staticmethod
    def get_history(db: Session, farmer_id: int, limit: int = 20) -> List[Dict]:
        import json
        assessments = (
            db.query(QualityAssessment)
            .filter(QualityAssessment.farmer_id == farmer_id)
            .order_by(QualityAssessment.created_at.desc())
            .limit(limit)
            .all()
        )
        results = []
        for a in assessments:
            obs = {}
            try:
                obs = json.loads(a.observations_json or "{}")
            except Exception:
                pass
            results.append({
                "id":                    a.id,
                "crop":                  a.crop,
                "grade":                 a.grade,
                "quality_score":         a.quality_score,
                "confidence":            a.confidence,
                "price_impact_percent":  a.price_impact_percent,
                "reference_price":       a.reference_price,
                "estimated_quality_price": a.estimated_quality_price,
                "image_used":            a.image_reference is not None,
                "suggestions":           obs.get("suggestions", []),
                "created_at":            a.created_at.isoformat() if a.created_at else None,
            })
        return results


# ── Singleton ─────────────────────────────────────────────────────────────────

_quality_service: Optional[QualityService] = None


def get_quality_service() -> QualityService:
    global _quality_service
    if _quality_service is None:
        _quality_service = QualityService()
    return _quality_service
