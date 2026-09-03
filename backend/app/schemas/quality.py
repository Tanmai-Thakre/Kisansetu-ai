"""
Phase 6 — Pydantic schemas for Quality Grading Assistance API.
"""
from __future__ import annotations
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, field_validator, model_validator


# ── Cotton parameter schema ────────────────────────────────────────────────────

class CottonParams(BaseModel):
    """Optional quality parameters for cotton."""
    moisture:       Optional[float] = None   # % (0–30)
    staple_length:  Optional[float] = None   # mm (20–45)
    micronaire:     Optional[float] = None   # µg/inch (1–8)
    foreign_matter: Optional[float] = None   # % (0–20)
    color:          Optional[float] = None   # score 1–5
    uniformity:     Optional[float] = None   # % (70–100)

    @field_validator("moisture")
    @classmethod
    def v_moisture(cls, v):
        if v is not None and not (0 <= v <= 30):
            raise ValueError("moisture must be between 0 and 30 %")
        return v

    @field_validator("staple_length")
    @classmethod
    def v_staple(cls, v):
        if v is not None and not (10 <= v <= 50):
            raise ValueError("staple_length must be between 10 and 50 mm")
        return v

    @field_validator("micronaire")
    @classmethod
    def v_mic(cls, v):
        if v is not None and not (1.0 <= v <= 8.0):
            raise ValueError("micronaire must be between 1.0 and 8.0")
        return v

    @field_validator("foreign_matter")
    @classmethod
    def v_foreign(cls, v):
        if v is not None and not (0 <= v <= 20):
            raise ValueError("foreign_matter must be between 0 and 20 %")
        return v

    @field_validator("color")
    @classmethod
    def v_color(cls, v):
        if v is not None and not (1.0 <= v <= 5.0):
            raise ValueError("color score must be between 1 and 5")
        return v

    @field_validator("uniformity")
    @classmethod
    def v_uniformity(cls, v):
        if v is not None and not (60 <= v <= 100):
            raise ValueError("uniformity must be between 60 and 100 %")
        return v

    def to_params_dict(self) -> Dict[str, Optional[float]]:
        return {
            "moisture":       self.moisture,
            "staple_length":  self.staple_length,
            "micronaire":     self.micronaire,
            "foreign_matter": self.foreign_matter,
            "color":          self.color,
            "uniformity":     self.uniformity,
        }


# ── Groundnut parameter schema ─────────────────────────────────────────────────

class GroundnutParams(BaseModel):
    """Optional quality parameters for groundnut."""
    moisture:          Optional[float] = None   # % (0–20)
    kernel_appearance: Optional[float] = None   # score 1–5
    damaged_kernels:   Optional[float] = None   # % (0–50)
    foreign_matter:    Optional[float] = None   # % (0–20)
    kernel_size:       Optional[float] = None   # score 1–5
    color:             Optional[float] = None   # score 1–5

    @field_validator("moisture")
    @classmethod
    def v_moisture(cls, v):
        if v is not None and not (0 <= v <= 20):
            raise ValueError("moisture must be between 0 and 20 %")
        return v

    @field_validator("kernel_appearance")
    @classmethod
    def v_appearance(cls, v):
        if v is not None and not (1.0 <= v <= 5.0):
            raise ValueError("kernel_appearance score must be between 1 and 5")
        return v

    @field_validator("damaged_kernels")
    @classmethod
    def v_damaged(cls, v):
        if v is not None and not (0 <= v <= 50):
            raise ValueError("damaged_kernels must be between 0 and 50 %")
        return v

    @field_validator("foreign_matter")
    @classmethod
    def v_foreign(cls, v):
        if v is not None and not (0 <= v <= 20):
            raise ValueError("foreign_matter must be between 0 and 20 %")
        return v

    @field_validator("kernel_size")
    @classmethod
    def v_size(cls, v):
        if v is not None and not (1.0 <= v <= 5.0):
            raise ValueError("kernel_size score must be between 1 and 5")
        return v

    @field_validator("color")
    @classmethod
    def v_color(cls, v):
        if v is not None and not (1.0 <= v <= 5.0):
            raise ValueError("color score must be between 1 and 5")
        return v

    def to_params_dict(self) -> Dict[str, Optional[float]]:
        return {
            "moisture":          self.moisture,
            "kernel_appearance": self.kernel_appearance,
            "damaged_kernels":   self.damaged_kernels,
            "foreign_matter":    self.foreign_matter,
            "kernel_size":       self.kernel_size,
            "color":             self.color,
        }


# ── Request schema ─────────────────────────────────────────────────────────────

class QualityAssessmentRequest(BaseModel):
    farmer_id:        int
    crop:             str
    crop_id:          Optional[int] = None
    cotton_params:    Optional[CottonParams]    = None
    groundnut_params: Optional[GroundnutParams] = None

    @field_validator("crop")
    @classmethod
    def v_crop(cls, v: str) -> str:
        if v.lower().strip() not in ("cotton", "groundnut"):
            raise ValueError("crop must be 'cotton' or 'groundnut'")
        return v.lower().strip()

    @field_validator("farmer_id")
    @classmethod
    def v_farmer(cls, v: int) -> int:
        if v <= 0:
            raise ValueError("farmer_id must be positive")
        return v

    @model_validator(mode="after")
    def check_params_match_crop(self) -> "QualityAssessmentRequest":
        if self.crop == "cotton" and self.groundnut_params is not None:
            raise ValueError("Do not supply groundnut_params for crop='cotton'")
        if self.crop == "groundnut" and self.cotton_params is not None:
            raise ValueError("Do not supply cotton_params for crop='groundnut'")
        return self

    def get_manual_params(self) -> Dict[str, Optional[float]]:
        if self.crop == "cotton" and self.cotton_params:
            return self.cotton_params.to_params_dict()
        if self.crop == "groundnut" and self.groundnut_params:
            return self.groundnut_params.to_params_dict()
        return {}


# ── Response schemas ───────────────────────────────────────────────────────────

class ParameterDetail(BaseModel):
    value:  Optional[float]
    rating: str
    source: str
    note:   str = ""


class QualityAssessmentResponse(BaseModel):
    id:                      int
    crop:                    str
    grade:                   str
    quality_score:           float
    confidence:              float
    factors:                 Dict[str, str]
    parameter_details:       Dict[str, ParameterDetail]
    price_impact_percent:    float
    reference_price:         Optional[float]
    estimated_quality_price: Optional[float]
    price_impact_range:      Optional[str] = None
    price_note:              Optional[str] = None
    observations:            List[str]
    suggestions:             List[str]
    limitations:             List[str]
    image_used:              bool
    disclaimer:              str
    source_status:           str
    created_at:              str


class QualityHistoryItem(BaseModel):
    id:                      int
    crop:                    str
    grade:                   str
    quality_score:           float
    confidence:              float
    price_impact_percent:    Optional[float]
    reference_price:         Optional[float]
    estimated_quality_price: Optional[float]
    image_used:              bool
    suggestions:             List[str] = []
    created_at:              Optional[str]


class QualityHistoryResponse(BaseModel):
    farmer_id: int
    count:     int
    items:     List[QualityHistoryItem]
