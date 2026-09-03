"""
Phase 4 — BuyerConnectionRequest model.
Tracks farmer → buyer purchase/connection requests.
"""
import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database.base import Base


class RequestStatus(str, enum.Enum):
    PENDING   = "PENDING"
    ACCEPTED  = "ACCEPTED"
    REJECTED  = "REJECTED"
    COMPLETED = "COMPLETED"


class BuyerConnectionRequest(Base):
    __tablename__ = "buyer_connection_requests"

    id            = Column(Integer, primary_key=True, index=True)
    farmer_id     = Column(Integer, ForeignKey("users.id"),            nullable=False, index=True)
    buyer_id      = Column(Integer, ForeignKey("buyers.id"),           nullable=False, index=True)
    crop_id       = Column(Integer, ForeignKey("crops.id"),            nullable=True,  index=True)
    crop          = Column(String(50),  nullable=False)          # cotton | groundnut
    quantity      = Column(Float,       nullable=False)          # quintals
    offered_price = Column(Float,       nullable=True)           # buyer offered price at time of request
    message       = Column(Text,        nullable=True)
    status        = Column(Enum(RequestStatus), nullable=False, default=RequestStatus.PENDING, index=True)
    match_score   = Column(Float,       nullable=True)           # snapshot of match score at request time
    created_at    = Column(DateTime,    nullable=False, default=datetime.utcnow)
    updated_at    = Column(DateTime,    nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Prevent duplicate PENDING requests for the same (farmer, buyer, crop)
    __table_args__ = (
        UniqueConstraint("farmer_id", "buyer_id", "crop", name="uq_farmer_buyer_crop_active"),
    )

    # Relationships (back-populate lazily — avoids circular imports)
    farmer = relationship("User",  foreign_keys=[farmer_id],  lazy="select")
    buyer  = relationship("Buyer", foreign_keys=[buyer_id],   lazy="select")
    crop_listing = relationship("Crop", foreign_keys=[crop_id], lazy="select")
