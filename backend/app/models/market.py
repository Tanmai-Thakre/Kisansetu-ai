"""
MarketPrice SQLAlchemy model.
"""
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, Float, DateTime
from app.database.base import Base


class MarketPrice(Base):
    __tablename__ = "market_prices"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False, index=True)
    mandi = Column(String(255), nullable=False)
    district = Column(String(255), nullable=False)
    date = Column(Date, nullable=False, index=True)
    min_price = Column(Float, nullable=False)   # ₹ per quintal
    max_price = Column(Float, nullable=False)   # ₹ per quintal
    modal_price = Column(Float, nullable=False) # ₹ per quintal
    arrival_quantity = Column(Float, nullable=True)  # in quintals
    source = Column(String(100), nullable=False, default="DEMO")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
