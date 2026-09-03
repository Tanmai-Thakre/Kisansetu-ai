"""
Database migration script — creates all tables.
Run this once to initialize the database.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database.base import Base, engine
from app.models import (
    User, FarmerProfile, Crop, MarketPrice, Buyer, BuyerRequirement,
    QualityAssessment, IncomeSale,
)


def create_tables():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")
    print("Tables:", list(Base.metadata.tables.keys()))


if __name__ == "__main__":
    create_tables()
