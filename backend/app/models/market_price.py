"""
Phase 2 — Enhanced MarketPrice model with full market intelligence fields.
Backward-compatible with Phase 1 market_prices table via Alembic migration.
"""
import enum
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Date, Float, DateTime, Index, Numeric
from app.database.base import Base


class SourceStatus(str, enum.Enum):
    LIVE = "LIVE"
    LATEST_AVAILABLE = "LATEST_AVAILABLE"
    DEMO = "DEMO"


class MarketPriceV2(Base):
    """
    Enhanced market price model for Phase 2.
    Uses a new table market_prices_v2 to avoid breaking Phase 1 data.
    Phase 1 MarketPrice model continues to work unchanged.
    """
    __tablename__ = "market_prices_v2"

    id = Column(Integer, primary_key=True, index=True)
    crop = Column(String(100), nullable=False)          # e.g. "cotton", "groundnut"
    variety = Column(String(100), nullable=True)        # e.g. "Bt Cotton", "Bold"
    mandi = Column(String(255), nullable=False)         # e.g. "Rajkot APMC"
    district = Column(String(255), nullable=False)      # e.g. "Rajkot"
    state = Column(String(100), nullable=False, default="Gujarat")
    date = Column(Date, nullable=False)

    # Prices — stored as Numeric for precision
    min_price = Column(Numeric(10, 2), nullable=False)
    max_price = Column(Numeric(10, 2), nullable=False)
    modal_price = Column(Numeric(10, 2), nullable=False)
    arrival_quantity = Column(Numeric(12, 2), nullable=True)   # quintals
    unit = Column(String(50), nullable=False, default="quintal")

    # Data provenance
    source = Column(String(100), nullable=False, default="DEMO")
    source_status = Column(String(30), nullable=False, default=SourceStatus.DEMO)
    recorded_at = Column(DateTime, nullable=True)              # when provider recorded it
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_mpv2_crop",       "crop"),
        Index("ix_mpv2_district",   "district"),
        Index("ix_mpv2_mandi",      "mandi"),
        Index("ix_mpv2_date",       "date"),
        Index("ix_mpv2_crop_date",  "crop", "date"),
        Index("ix_mpv2_crop_mandi", "crop", "mandi"),
    )

    def to_dict(self):
        return {
            "id": self.id,
            "crop": self.crop,
            "variety": self.variety,
            "mandi": self.mandi,
            "district": self.district,
            "state": self.state,
            "date": str(self.date),
            "min_price": float(self.min_price),
            "max_price": float(self.max_price),
            "modal_price": float(self.modal_price),
            "arrival_quantity": float(self.arrival_quantity) if self.arrival_quantity else None,
            "unit": self.unit,
            "source": self.source,
            "source_status": self.source_status,
        }
