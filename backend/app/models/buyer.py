"""
Buyer and BuyerRequirement SQLAlchemy models.
"""
from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Boolean, Float, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class Buyer(Base):
    __tablename__ = "buyers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    company_name = Column(String(255), nullable=False)
    location = Column(String(255), nullable=True)
    verified = Column(Boolean, nullable=False, default=False)

    user = relationship("User", back_populates="buyer_profile")
    requirements = relationship("BuyerRequirement", back_populates="buyer")


class BuyerRequirement(Base):
    __tablename__ = "buyer_requirements"

    id = Column(Integer, primary_key=True, index=True)
    buyer_id = Column(Integer, ForeignKey("buyers.id"), nullable=False)
    crop = Column(String(100), nullable=False, index=True)
    min_quantity = Column(Float, nullable=True)   # in quintals
    max_quantity = Column(Float, nullable=True)   # in quintals
    quality_requirement = Column(String(10), nullable=True)  # A, B, C
    offered_price = Column(Float, nullable=True)  # ₹ per quintal
    delivery_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    buyer = relationship("Buyer", back_populates="requirements")
