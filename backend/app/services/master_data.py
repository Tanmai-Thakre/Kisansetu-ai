"""
Phase 2 — Gujarat mandi master data with geolocation.
Used by the mandi comparison and transport cost services.
"""
from typing import List, Dict

# ── Mandi master records ─────────────────────────────────────────────────────
# latitude/longitude are approximate district centroid coordinates.
MANDI_MASTER_DATA: List[Dict] = [
    # Rajkot district
    {"name": "Rajkot APMC",         "short_name": "Rajkot",         "district": "Rajkot",         "lat": 22.3039, "lon": 70.8022},
    {"name": "Gondal APMC",         "short_name": "Gondal",         "district": "Rajkot",         "lat": 21.9617, "lon": 70.5258},
    {"name": "Jetpur APMC",         "short_name": "Jetpur",         "district": "Rajkot",         "lat": 21.7527, "lon": 70.6237},
    # Amreli district
    {"name": "Amreli APMC",         "short_name": "Amreli",         "district": "Amreli",         "lat": 21.6009, "lon": 71.2188},
    {"name": "Savarkundla APMC",    "short_name": "Savarkundla",    "district": "Amreli",         "lat": 21.3392, "lon": 71.2879},
    # Junagadh district
    {"name": "Junagadh APMC",       "short_name": "Junagadh",       "district": "Junagadh",       "lat": 21.5222, "lon": 70.4579},
    {"name": "Keshod APMC",         "short_name": "Keshod",         "district": "Junagadh",       "lat": 21.3028, "lon": 70.2473},
    # Bhavnagar district
    {"name": "Bhavnagar APMC",      "short_name": "Bhavnagar",      "district": "Bhavnagar",      "lat": 21.7645, "lon": 72.1519},
    {"name": "Talaja APMC",         "short_name": "Talaja",         "district": "Bhavnagar",      "lat": 21.3542, "lon": 72.0306},
    # Ahmedabad district
    {"name": "Ahmedabad APMC",      "short_name": "Ahmedabad",      "district": "Ahmedabad",      "lat": 23.0225, "lon": 72.5714},
    {"name": "Deesa APMC",          "short_name": "Deesa",          "district": "Banaskantha",    "lat": 24.2592, "lon": 72.1898},
    # Surendranagar district
    {"name": "Surendranagar APMC",  "short_name": "Surendranagar",  "district": "Surendranagar",  "lat": 22.7273, "lon": 71.6490},
    {"name": "Wadhwan APMC",        "short_name": "Wadhwan",        "district": "Surendranagar",  "lat": 22.7026, "lon": 71.6765},
    # Jamnagar district
    {"name": "Jamnagar APMC",       "short_name": "Jamnagar",       "district": "Jamnagar",       "lat": 22.4707, "lon": 70.0577},
    # Mehsana district
    {"name": "Mehsana APMC",        "short_name": "Mehsana",        "district": "Mehsana",        "lat": 23.5880, "lon": 72.3693},
    # Banaskantha district
    {"name": "Banaskantha APMC",    "short_name": "Banaskantha",    "district": "Banaskantha",    "lat": 24.1745, "lon": 72.4440},
]

# ── Crop master records ───────────────────────────────────────────────────────
CROP_MASTER_DATA: List[Dict] = [
    {
        "name": "cotton",
        "display_name": "Cotton",
        "unit": "quintal",
        "description": "Bt Cotton, Desi Cotton — major kharif crop in Gujarat",
    },
    {
        "name": "groundnut",
        "display_name": "Groundnut",
        "unit": "quintal",
        "description": "Bold, Java, TG varieties — major oilseed crop in Gujarat",
    },
]

# ── Transport configuration ───────────────────────────────────────────────────
# These rates are approximate and clearly labelled as estimates.
TRANSPORT_CONFIG = {
    "cost_per_km_per_quintal": 0.85,   # ₹ per km per quintal (approx truck rate)
    "min_transport_cost": 50.0,         # ₹ per quintal (min overhead)
    "mandi_commission_pct": 1.0,        # 1% mandi commission
    "loading_unloading": 30.0,          # ₹ per quintal fixed
    "note": "Estimated transport costs — not official rates",
}

# ── Approximate distances from major farming locations (km) ──────────────────
# Reference point: Rajkot (major cotton belt)
# These are road-distance approximations, not GPS-precise.
MANDI_DISTANCE_FROM_RAJKOT_KM: Dict[str, float] = {
    "Rajkot APMC":        5.0,
    "Gondal APMC":       40.0,
    "Jetpur APMC":       60.0,
    "Amreli APMC":      115.0,
    "Savarkundla APMC": 130.0,
    "Junagadh APMC":    100.0,
    "Keshod APMC":      120.0,
    "Bhavnagar APMC":   160.0,
    "Talaja APMC":      180.0,
    "Ahmedabad APMC":   215.0,
    "Deesa APMC":       370.0,
    "Surendranagar APMC": 95.0,
    "Wadhwan APMC":      98.0,
    "Jamnagar APMC":    105.0,
    "Mehsana APMC":     245.0,
    "Banaskantha APMC": 320.0,
}
