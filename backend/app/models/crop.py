"""
Crop SQLAlchemy model.
"""
import enum
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Enum, DateTime, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class CropType(str, enum.Enum):
    cotton = "cotton"
    groundnut = "groundnut"


class QualityGrade(str, enum.Enum):
    A = "A"
    B = "B"
    C = "C"
    ungraded = "ungraded"


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    farmer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    crop_type = Column(Enum(CropType), nullable=False)
    variety = Column(String(255), nullable=True)
    quantity = Column(Float, nullable=True)  # in quintals
    expected_harvest_date = Column(Date, nullable=True)
    quality_grade = Column(Enum(QualityGrade), nullable=True, default=QualityGrade.ungraded)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    farmer = relationship("User", back_populates="crops")
