"""
Phase 6 — Quality Grading Assistance API endpoints.

POST /api/agents/quality          — assess crop quality (JSON params + optional image)
POST /api/agents/quality/upload   — assess with file upload (multipart form)
GET  /api/agents/quality/history  — assessment history for a farmer
GET  /api/agents/quality/preview  — quick GET endpoint for testing
"""
from __future__ import annotations

import json
from typing import Optional

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database.base import get_db
from app.schemas.quality import (
    QualityAssessmentRequest,
    QualityAssessmentResponse,
    QualityHistoryResponse,
    QualityHistoryItem,
    CottonParams,
    GroundnutParams,
)
from app.agents.quality import get_quality_service

router = APIRouter(prefix="/agents", tags=["AI Agents"])

# ── Shared constants ───────────────────────────────────────────────────────────
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def _validate_image(upload: UploadFile) -> bytes:
    """Validate and read an uploaded image file."""
    import os
    # Check extension
    if upload.filename:
        ext = os.path.splitext(upload.filename.lower())[1]
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                400,
                detail=f"Invalid file extension '{ext}'. Allowed: JPG, PNG, WebP.",
            )
    # Check content type
    if upload.content_type and upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            400,
            detail=f"Invalid content type '{upload.content_type}'. Allowed: JPEG, PNG, WebP.",
        )
    return None  # read async below


# ── POST /api/agents/quality  (JSON body, no image) ───────────────────────────

@router.post(
    "/quality",
    response_model=QualityAssessmentResponse,
    summary="Quality Grading Assistance — JSON parameters",
    description=(
        "Assess crop quality using manual quality parameters.\n\n"
        "Supports **Cotton** and **Groundnut**.\n\n"
        "Returns grade, score, confidence, price impact, and improvement suggestions.\n\n"
        "For image upload, use `POST /api/agents/quality/upload` (multipart form).\n\n"
        "⚠️ Preliminary AI-assisted assessment — not a substitute for laboratory testing."
    ),
)
async def quality_assess_json(
    payload: QualityAssessmentRequest,
    db: Session = Depends(get_db),
):
    manual_params = payload.get_manual_params()
    svc = get_quality_service()
    result = svc.assess(
        db=db,
        farmer_id=payload.farmer_id,
        crop=payload.crop,
        manual_params=manual_params,
        image_bytes=None,
        crop_id=payload.crop_id,
    )
    return _build_response(result)


# ── POST /api/agents/quality/upload  (multipart, with optional image) ─────────

@router.post(
    "/quality/upload",
    response_model=QualityAssessmentResponse,
    summary="Quality Grading Assistance — image upload + parameters",
    description=(
        "Assess crop quality with an **optional image upload** plus manual parameters.\n\n"
        "Pass `params_json` as a JSON string of the quality parameters (same as the "
        "`cotton_params` / `groundnut_params` fields in the JSON endpoint).\n\n"
        "Image analysis provides visual observations only; lab parameters cannot be "
        "determined from images.\n\n"
        "⚠️ Preliminary AI-assisted assessment — not a substitute for laboratory testing."
    ),
)
async def quality_assess_upload(
    farmer_id: int          = Form(...),
    crop:      str          = Form(...),
    crop_id:   Optional[int]= Form(None),
    params_json: Optional[str] = Form(None, description="JSON string of crop quality parameters"),
    image:     Optional[UploadFile] = File(None),
    db:        Session      = Depends(get_db),
):
    # Validate crop
    crop = crop.lower().strip()
    if crop not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")

    if farmer_id <= 0:
        raise HTTPException(400, detail="farmer_id must be positive")

    # Parse manual params
    manual_params: dict = {}
    if params_json:
        try:
            raw = json.loads(params_json)
        except json.JSONDecodeError:
            raise HTTPException(400, detail="params_json must be valid JSON")

        try:
            if crop == "cotton":
                p = CottonParams(**raw)
                manual_params = p.to_params_dict()
            else:
                p = GroundnutParams(**raw)
                manual_params = p.to_params_dict()
        except Exception as exc:
            raise HTTPException(422, detail=f"Invalid parameters: {exc}")

    # Read and validate image
    image_bytes: Optional[bytes] = None
    if image and image.filename:
        import os
        ext = os.path.splitext(image.filename.lower())[1]
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                400,
                detail=f"Invalid file extension '{ext}'. Allowed: .jpg, .jpeg, .png, .webp",
            )
        if image.content_type and image.content_type not in ALLOWED_CONTENT_TYPES:
            raise HTTPException(
                400,
                detail=f"Invalid content type '{image.content_type}'.",
            )
        raw_bytes = await image.read()
        if len(raw_bytes) > MAX_IMAGE_SIZE:
            raise HTTPException(413, detail="Image too large. Maximum 10 MB.")
        if len(raw_bytes) == 0:
            raise HTTPException(400, detail="Uploaded file is empty.")
        image_bytes = raw_bytes

    svc = get_quality_service()
    result = svc.assess(
        db=db,
        farmer_id=farmer_id,
        crop=crop,
        manual_params=manual_params,
        image_bytes=image_bytes,
        crop_id=crop_id,
    )
    return _build_response(result)


# ── GET /api/agents/quality/history ───────────────────────────────────────────

@router.get(
    "/quality/history",
    response_model=QualityHistoryResponse,
    summary="Quality assessment history for a farmer",
)
async def quality_history(
    farmer_id: int,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    if farmer_id <= 0:
        raise HTTPException(400, detail="farmer_id must be positive")
    if limit < 1 or limit > 100:
        limit = 20

    svc = get_quality_service()
    items = svc.get_history(db=db, farmer_id=farmer_id, limit=limit)
    return QualityHistoryResponse(
        farmer_id=farmer_id,
        count=len(items),
        items=[QualityHistoryItem(**i) for i in items],
    )


# ── GET /api/agents/quality/preview  (quick test, no DB) ──────────────────────

@router.get(
    "/quality/preview",
    summary="Quick preview — quality grading without DB persistence",
    description=(
        "Convenience GET endpoint for testing grading logic without a DB connection.\n"
        "Does not save any data.\n\n"
        "Example: `/api/agents/quality/preview?crop=cotton&moisture=9.5&foreign_matter=1.2`"
    ),
)
async def quality_preview(
    crop:              str   = "cotton",
    # Cotton
    moisture:          Optional[float] = None,
    staple_length:     Optional[float] = None,
    micronaire:        Optional[float] = None,
    foreign_matter:    Optional[float] = None,
    color:             Optional[float] = None,
    uniformity:        Optional[float] = None,
    # Groundnut
    kernel_appearance: Optional[float] = None,
    damaged_kernels:   Optional[float] = None,
    kernel_size:       Optional[float] = None,
):
    from app.agents.quality.grading_rules import grade_crop, GRADE_PRICE_IMPACT
    from app.services.market_data_provider import get_market_data_provider

    crop = crop.lower().strip()
    if crop not in ("cotton", "groundnut"):
        raise HTTPException(400, detail="crop must be 'cotton' or 'groundnut'")

    if crop == "cotton":
        params = {
            "moisture":       moisture,
            "staple_length":  staple_length,
            "micronaire":     micronaire,
            "foreign_matter": foreign_matter,
            "color":          color,
            "uniformity":     uniformity,
        }
    else:
        params = {
            "moisture":          moisture,
            "kernel_appearance": kernel_appearance,
            "damaged_kernels":   damaged_kernels,
            "foreign_matter":    foreign_matter,
            "kernel_size":       kernel_size,
            "color":             color,
        }

    result = grade_crop(crop, params)

    # Get reference price
    ref_price = None
    try:
        provider = get_market_data_provider()
        records = provider.get_latest_prices(crop=crop, limit=1)
        if records:
            ref_price = float(records[0].modal_price)
    except Exception:
        pass
    if ref_price is None:
        ref_price = 7200.0 if crop == "cotton" else 6100.0

    estimated = round(ref_price * (1 + result.price_impact_percent / 100), 2)

    return {
        "crop":                  result.crop,
        "grade":                 result.grade,
        "quality_score":         result.quality_score,
        "confidence":            result.confidence,
        "factors":               {k: v.rating for k, v in result.parameters.items()},
        "price_impact_percent":  result.price_impact_percent,
        "reference_price":       ref_price,
        "estimated_quality_price": estimated,
        "observations":          result.observations,
        "suggestions":           result.suggestions,
        "limitations":           result.limitations,
        "disclaimer": (
            "Preliminary AI-assisted assessment: This result is an estimate and "
            "is not a substitute for laboratory or authorized quality testing."
        ),
        "note": "Preview mode — not saved to database.",
    }


# ── Response builder ───────────────────────────────────────────────────────────

def _build_response(result: dict) -> QualityAssessmentResponse:
    from app.schemas.quality import ParameterDetail
    return QualityAssessmentResponse(
        id=result["id"],
        crop=result["crop"],
        grade=result["grade"],
        quality_score=result["quality_score"],
        confidence=result["confidence"],
        factors=result["factors"],
        parameter_details={
            k: ParameterDetail(**v)
            for k, v in result["parameter_details"].items()
        },
        price_impact_percent=result["price_impact_percent"],
        reference_price=result.get("reference_price"),
        estimated_quality_price=result.get("estimated_quality_price"),
        price_impact_range=result.get("price_impact_range"),
        price_note=result.get("price_note"),
        observations=result["observations"],
        suggestions=result["suggestions"],
        limitations=result["limitations"],
        image_used=result["image_used"],
        disclaimer=result["disclaimer"],
        source_status=result["source_status"],
        created_at=result["created_at"],
    )
