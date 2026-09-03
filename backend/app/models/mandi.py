"""
Mandi master data model — stores mandi metadata including geolocation.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean
from app.database.base import Base


class MandiMaster(Base):
    """
    Master table for Gujarat mandis.
    Provides geolocation, district mapping, and metadata for the comparison engine.
    """
    __tablename__ = "mandi_master"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True)     # "Rajkot APMC"
    short_name = Column(String(100), nullable=False)            # "Rajkot"
    district = Column(String(255), nullable=False, index=True)
    state = Column(String(100), nullable=False, default="Gujarat")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "short_name": self.short_name,
            "district": self.district,
            "state": self.state,
            "latitude": self.latitude,
            "longitude": self.longitude,
        }
