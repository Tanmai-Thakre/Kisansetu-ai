"""
Phase 7 — IncomeSale model.

Stores completed crop sale records for a farmer.
This is a structural placeholder — no fabricated transactions.
Data will populate when farmers actually record sales.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.database.base import Base


class IncomeSale(Base):
    """
    A completed (or estimated) crop sale transaction recorded by a farmer.
    """
    __tablename__ = "income_sales"

    id            = Column(Integer, primary_key=True, index=True)
    farmer_id     = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    crop          = Column(String(50), nullable=False)
    quantity      = Column(Float, nullable=False)           # quintals
    selling_price = Column(Float, nullable=False)           # ₹/qtl
    total_revenue = Column(Float, nullable=False)           # gross ₹
    transport_cost= Column(Float, default=0.0)
    storage_cost  = Column(Float, default=0.0)
    labour_cost   = Column(Float, default=0.0)
    packaging_cost= Column(Float, default=0.0)
    other_cost    = Column(Float, default=0.0)
    total_cost    = Column(Float, default=0.0)
    net_income    = Column(Float, nullable=False)           # total_revenue - total_cost
    mandi         = Column(String(100), nullable=True)
    buyer_name    = Column(String(200), nullable=True)
    notes         = Column(String(500), nullable=True)
    sale_date     = Column(DateTime, default=datetime.utcnow)
    created_at    = Column(DateTime, default=datetime.utcnow)

    def to_dict(self) -> dict:
        return {
            "id":             self.id,
            "farmer_id":      self.farmer_id,
            "crop":           self.crop,
            "quantity":       self.quantity,
            "selling_price":  self.selling_price,
            "total_revenue":  self.total_revenue,
            "transport_cost": self.transport_cost,
            "storage_cost":   self.storage_cost,
            "labour_cost":    self.labour_cost,
            "packaging_cost": self.packaging_cost,
            "other_cost":     self.other_cost,
            "total_cost":     self.total_cost,
            "net_income":     self.net_income,
            "mandi":          self.mandi,
            "buyer_name":     self.buyer_name,
            "notes":          self.notes,
            "sale_date":      str(self.sale_date) if self.sale_date else None,
            "created_at":     str(self.created_at) if self.created_at else None,
        }
