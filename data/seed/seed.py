"""
Seed script — populates the database with DEMO DATA for Phase 1.
All inserted records are clearly labeled as DEMO DATA.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import date, timedelta
from app.database.base import SessionLocal, engine, Base
from app.models import User, FarmerProfile, Crop, MarketPrice, Buyer, BuyerRequirement
from app.models.user import UserRole
from app.models.crop import CropType, QualityGrade
import hashlib

Base.metadata.create_all(bind=engine)


def fake_hash(password: str) -> str:
    """Simple placeholder hash — replace with bcrypt in production."""
    return hashlib.sha256(password.encode()).hexdigest()


DEMO_FARMERS = [
    {"name": "Rameshbhai Patel", "phone": "9876543210", "village": "Gondal", "district": "Rajkot", "land_area": 12.5},
    {"name": "Kantibhai Solanki", "phone": "9876543211", "village": "Amreli", "district": "Amreli", "land_area": 8.0},
    {"name": "Bhavnaben Mer", "phone": "9876543212", "village": "Visavadar", "district": "Junagadh", "land_area": 15.0},
    {"name": "Jitubhai Jadeja", "phone": "9876543213", "village": "Palitana", "district": "Bhavnagar", "land_area": 6.5},
    {"name": "Savitaben Rana", "phone": "9876543214", "village": "Wadhwan", "district": "Surendranagar", "land_area": 20.0},
]

DEMO_BUYER_USERS = [
    {"name": "Gujarat Cotton Traders Pvt Ltd", "phone": "9876540001", "company": "Gujarat Cotton Traders Pvt Ltd", "location": "Rajkot, Gujarat", "verified": True},
    {"name": "Amreli Groundnut Exports", "phone": "9876540002", "company": "Amreli Groundnut Exports", "location": "Amreli, Gujarat", "verified": True},
    {"name": "Saurashtra Agro Industries", "phone": "9876540003", "company": "Saurashtra Agro Industries", "location": "Junagadh, Gujarat", "verified": True},
]

COTTON_MANDI_DATA = [
    ("Rajkot APMC",       "Rajkot",        6900, 7500, 7200),
    ("Amreli APMC",       "Amreli",        6800, 7400, 7100),
    ("Junagadh APMC",     "Junagadh",      6950, 7550, 7250),
    ("Bhavnagar APMC",    "Bhavnagar",     6850, 7450, 7150),
    ("Surendranagar APMC","Surendranagar", 7000, 7600, 7300),
    ("Jamnagar APMC",     "Jamnagar",      6750, 7350, 7050),
    ("Ahmedabad APMC",    "Ahmedabad",     7100, 7700, 7400),
]

GROUNDNUT_MANDI_DATA = [
    ("Rajkot APMC",       "Rajkot",        5800, 6400, 6100),
    ("Amreli APMC",       "Amreli",        5700, 6300, 6000),
    ("Junagadh APMC",     "Junagadh",      5900, 6500, 6200),
    ("Bhavnagar APMC",    "Bhavnagar",     5750, 6350, 6050),
    ("Surendranagar APMC","Surendranagar", 5850, 6450, 6150),
    ("Jamnagar APMC",     "Jamnagar",      5650, 6250, 5950),
    ("Ahmedabad APMC",    "Ahmedabad",     5950, 6550, 6250),
]


def seed():
    db = SessionLocal()
    try:
        # Check already seeded
        if db.query(User).count() > 0:
            print("Database already seeded. Skipping.")
            return

        print("Seeding DEMO DATA...")

        # ── Farmers ───────────────────────────────────────────────────────────
        farmer_users = []
        for f in DEMO_FARMERS:
            user = User(
                name=f["name"],
                phone=f["phone"],
                email=None,
                password_hash=fake_hash("demo1234"),
                role=UserRole.farmer,
                language="gu",
            )
            db.add(user)
            db.flush()

            profile = FarmerProfile(
                user_id=user.id,
                village=f["village"],
                district=f["district"],
                state="Gujarat",
                land_area=f["land_area"],
            )
            db.add(profile)
            farmer_users.append(user)

        db.flush()

        # ── Crops ─────────────────────────────────────────────────────────────
        crop_assignments = [
            (farmer_users[0], CropType.cotton,    "Bt Cotton",  150.0, QualityGrade.A),
            (farmer_users[1], CropType.groundnut, "Bold",       200.0, QualityGrade.A),
            (farmer_users[2], CropType.cotton,    "Bt Cotton",   80.0, QualityGrade.B),
            (farmer_users[3], CropType.groundnut, "Java",       120.0, QualityGrade.B),
            (farmer_users[4], CropType.cotton,    "Desi Cotton", 50.0, QualityGrade.C),
        ]
        harvest = date.today() + timedelta(days=30)
        for user, crop_type, variety, qty, grade in crop_assignments:
            crop = Crop(
                farmer_id=user.id,
                crop_type=crop_type,
                variety=variety,
                quantity=qty,
                expected_harvest_date=harvest,
                quality_grade=grade,
            )
            db.add(crop)

        # ── Market Prices (last 7 days) ───────────────────────────────────────
        today = date.today()
        import random
        random.seed(42)
        for days_ago in range(6, -1, -1):
            price_date = today - timedelta(days=days_ago)
            factor = 1 + random.uniform(-0.01, 0.012)
            for mandi, district, mn, mx, modal in COTTON_MANDI_DATA:
                db.add(MarketPrice(
                    crop="cotton", mandi=mandi, district=district,
                    date=price_date,
                    min_price=round(mn * factor, 0),
                    max_price=round(mx * factor, 0),
                    modal_price=round(modal * factor, 0),
                    arrival_quantity=random.uniform(200, 1500),
                    source="DEMO DATA",
                ))
            for mandi, district, mn, mx, modal in GROUNDNUT_MANDI_DATA:
                db.add(MarketPrice(
                    crop="groundnut", mandi=mandi, district=district,
                    date=price_date,
                    min_price=round(mn * factor, 0),
                    max_price=round(mx * factor, 0),
                    modal_price=round(modal * factor, 0),
                    arrival_quantity=random.uniform(300, 2000),
                    source="DEMO DATA",
                ))

        # ── Buyer Users ───────────────────────────────────────────────────────
        for bd in DEMO_BUYER_USERS:
            user = User(
                name=bd["name"],
                phone=bd["phone"],
                email=None,
                password_hash=fake_hash("buyer1234"),
                role=UserRole.buyer,
                language="en",
            )
            db.add(user)
            db.flush()
            buyer = Buyer(
                user_id=user.id,
                company_name=bd["company"],
                location=bd["location"],
                verified=bd["verified"],
            )
            db.add(buyer)
            db.flush()

            # Add requirements
            if "Cotton" in bd["company"]:
                db.add(BuyerRequirement(
                    buyer_id=buyer.id, crop="cotton",
                    min_quantity=50, max_quantity=500,
                    quality_requirement="A", offered_price=7350,
                    delivery_date=today + timedelta(days=14),
                ))
            elif "Groundnut" in bd["company"]:
                db.add(BuyerRequirement(
                    buyer_id=buyer.id, crop="groundnut",
                    min_quantity=100, max_quantity=1000,
                    quality_requirement="A", offered_price=6250,
                    delivery_date=today + timedelta(days=21),
                ))
            elif "Agro" in bd["company"]:
                db.add(BuyerRequirement(
                    buyer_id=buyer.id, crop="groundnut",
                    min_quantity=200, max_quantity=2000,
                    quality_requirement="B", offered_price=6100,
                    delivery_date=today + timedelta(days=30),
                ))

        db.commit()
        print("DEMO DATA seeded successfully.")
        print(f"   Farmers: {len(DEMO_FARMERS)}")
        print(f"   Buyers:  {len(DEMO_BUYER_USERS)}")
        print(f"   Market price records: {7 * (len(COTTON_MANDI_DATA) + len(GROUNDNUT_MANDI_DATA))}")
        print("   All data is DEMO DATA -- not real market data.")

    except Exception as e:
        db.rollback()
        print(f"Seeding failed: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
