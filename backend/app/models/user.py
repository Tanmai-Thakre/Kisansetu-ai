"""
User and FarmerProfile SQLAlchemy models.
"""
import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Enum, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database.base import Base


class UserRole(str, enum.Enum):
    farmer = "farmer"
    buyer = "buyer"
    admin = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.farmer)
    language = Column(String(10), nullable=False, default="en")
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    farmer_profile = relationship("FarmerProfile", back_populates="user", uselist=False)
    buyer_profile = relationship("Buyer", back_populates="user", uselist=False)
    crops = relationship("Crop", back_populates="farmer")


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    village = Column(String(255), nullable=True)
    district = Column(String(255), nullable=True)
    state = Column(String(255), nullable=False, default="Gujarat")
    land_area = Column(Float, nullable=True)  # in acres

    user = relationship("User", back_populates="farmer_profile")
