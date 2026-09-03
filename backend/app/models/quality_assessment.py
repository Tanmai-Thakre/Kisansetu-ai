"""
Phase 6 — QualityAssessment SQLAlchemy model.
Stores results of AI-assisted quality grading assessments.
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, ForeignKey
)
from app.database.base import Base


class QualityAssessment(Base):
    __tablename__ = "quality_assessments"

    id                    = Column(Integer, primary_key=True, index=True)
    farmer_id             = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    crop_id               = Column(Integer, ForeignKey("crops.id"), nullable=True)
    crop                  = Column(String(50), nullable=False)          # "cotton" | "groundnut"
    image_reference       = Column(String(255), nullable=True)          # opaque hash ref
    grade                 = Column(String(20), nullable=False)          # EXCELLENT/GOOD/AVERAGE/POOR
    quality_score         = Column(Float, nullable=False)               # 0–100
    confidence            = Column(Float, nullable=False)               # 0–100
    parameters_json       = Column(Text, nullable=True)                 # JSON blob
    observations_json     = Column(Text, nullable=True)                 # JSON blob
    price_impact_percent  = Column(Float, nullable=True)
    reference_price       = Column(Float, nullable=True)
    estimated_quality_price = Column(Float, nullable=True)
    created_at            = Column(DateTime, nullable=False, default=datetime.utcnow)
