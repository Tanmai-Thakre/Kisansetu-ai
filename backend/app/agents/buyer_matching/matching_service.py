"""
Phase 4 — BuyerMatchingService: orchestrates the buyer–farmer matching pipeline.

Pipeline:
    Farmer Crop Listing (crop, qty, grade, district, harvest_date)
          ↓
    Load all active buyer requirements
          ↓
    Compute match score per (crop, buyer) pair  [scoring.py]
          ↓
    Filter: only buyers that want this crop (crop_score > 0)
          ↓
    Rank by total match score (descending)
          ↓
    Return top-N matches with breakdown + reasons

Market price reference comes from Phase 2 DemoMarketDataProvider.
No LLM, no randomness — fully deterministic.
"""
from __future__ import annotations

from typing import List, Optional, Dict
from datetime import date

from app.services.market_data_provider import get_market_data_provider
from app.services.demo_data import DEMO_BUYERS
from app.schemas.buyer import BuyerListItem
from .scoring import compute_match_score, MatchScore


# ── Demo buyer enrichment ─────────────────────────────────────────────────────
# Extend DEMO_BUYERS with district and delivery_date for matching purposes.
# These are stored here rather than in the buyer record itself to keep the
# existing Phase 1 schema unchanged.

BUYER_EXTRA: Dict[int, Dict] = {
    1:  {"district": "Rajkot",         "delivery_date": None,                         "lat": 22.3039, "lon": 70.8022},
    2:  {"district": "Amreli",         "delivery_date": None,                         "lat": 21.6009, "lon": 71.2188},
    3:  {"district": "Junagadh",       "delivery_date": None,                         "lat": 21.5222, "lon": 70.4579},
    4:  {"district": "Bhavnagar",      "delivery_date": None,                         "lat": 21.7645, "lon": 72.1519},
    5:  {"district": "Ahmedabad",      "delivery_date": None,                         "lat": 23.0225, "lon": 72.5714},
    6:  {"district": "Surendranagar",  "delivery_date": None,                         "lat": 22.7273, "lon": 71.6490},
    7:  {"district": "Rajkot",         "delivery_date": None,                         "lat": 22.3039, "lon": 70.8022},
    8:  {"district": "Jamnagar",       "delivery_date": None,                         "lat": 22.4707, "lon": 70.0577},
    9:  {"district": "Ahmedabad",      "delivery_date": None,                         "lat": 23.0225, "lon": 72.5714},
    10: {"district": "Rajkot",         "delivery_date": None,                         "lat": 22.3039, "lon": 70.8022},
    11: {"district": "Amreli",         "delivery_date": None,                         "lat": 21.6009, "lon": 71.2188},
    12: {"district": "Junagadh",       "delivery_date": None,                         "lat": 21.5222, "lon": 70.4579},
}


class MatchedBuyer:
    """One buyer result in a matching response."""

    def __init__(
        self,
        buyer:       BuyerListItem,
        match:       MatchScore,
    ):
        self.buyer_id        = buyer.id
        self.buyer_name      = buyer.company_name
        self.location        = buyer.location
        self.verified        = buyer.verified
        self.crop            = buyer.crop
        self.offered_price   = buyer.offered_price
        self.min_quantity    = buyer.min_quantity
        self.max_quantity    = buyer.max_quantity
        self.quality_requirement = buyer.quality_requirement
        self.match_score     = match.match_score
        self.breakdown       = match.breakdown.to_dict()
        self.reasons         = match.reasons
        self.price_vs_market = match.price_vs_market
        self.price_advantage = match.price_advantage
        self.distance_km     = match.distance_km
        self.market_price    = match.market_price

    def to_dict(self) -> dict:
        return {
            "buyer_id":           self.buyer_id,
            "buyer_name":         self.buyer_name,
            "location":           self.location,
            "verified":           self.verified,
            "crop":               self.crop,
            "offered_price":      self.offered_price,
            "min_quantity":       self.min_quantity,
            "max_quantity":       self.max_quantity,
            "quality_requirement": self.quality_requirement,
            "match_score":        self.match_score,
            "breakdown":          self.breakdown,
            "reasons":            self.reasons,
            "price_vs_market":    self.price_vs_market,
            "price_advantage":    self.price_advantage,
            "distance_km":        self.distance_km,
            "market_price":       self.market_price,
        }


class BuyerMatchingService:
    """
    Orchestrates the buyer–farmer matching pipeline.
    Deterministic, no LLM.
    """

    def __init__(self):
        self._provider = get_market_data_provider()

    def _get_market_price(self, crop: str, district: str) -> Optional[float]:
        """Get latest modal price for crop+district from Phase 2 provider."""
        try:
            mandi = f"{district.strip().title()} APMC"
            records = self._provider.get_price_history(
                crop=crop.lower(), mandi=mandi, limit=3
            )
            if records:
                return float(records[-1].modal_price)
            # Fallback: try any mandi in district
            latest = self._provider.get_latest_prices(crop=crop.lower(), limit=20)
            for r in latest:
                if district.lower() in (r.district or "").lower():
                    return float(r.modal_price)
            # Final fallback: overall latest
            if latest:
                return float(latest[0].modal_price)
        except Exception:
            pass
        return None

    def find_matches(
        self,
        crop:            str,
        quantity:        Optional[float] = None,
        quality_grade:   Optional[str]   = None,
        farmer_district: Optional[str]   = None,
        harvest_date:    Optional[date]  = None,
        top_n:           int             = 10,
    ) -> List[MatchedBuyer]:
        """
        Find and rank buyers for a farmer's crop listing.
        Returns up to top_n buyers sorted by match_score descending.
        Only buyers requiring this crop are returned.
        """
        crop_lower = crop.lower().strip()

        # Get current market price as reference
        market_price = self._get_market_price(crop_lower, farmer_district or "Rajkot")

        results: List[MatchedBuyer] = []

        for buyer in DEMO_BUYERS:
            if buyer.crop.lower() != crop_lower:
                continue   # hard filter: crop must match

            match = compute_match_score(
                farmer_crop=crop_lower,
                farmer_grade=quality_grade,
                farmer_quantity=quantity,
                farmer_district=farmer_district,
                harvest_date=harvest_date,
                buyer_crop=buyer.crop.lower(),
                buyer_grade=buyer.quality_requirement,
                buyer_min_qty=buyer.min_quantity,
                buyer_max_qty=buyer.max_quantity,
                offered_price=buyer.offered_price,
                buyer_location=buyer.location,
                delivery_date=BUYER_EXTRA.get(buyer.id, {}).get("delivery_date"),
                market_price=market_price,
            )

            results.append(MatchedBuyer(buyer=buyer, match=match))

        # Sort by match score descending
        results.sort(key=lambda m: m.match_score, reverse=True)
        return results[:top_n]


# ── Singleton ─────────────────────────────────────────────────────────────────
_matching_service: Optional[BuyerMatchingService] = None


def get_buyer_matching_service() -> BuyerMatchingService:
    global _matching_service
    if _matching_service is None:
        _matching_service = BuyerMatchingService()
    return _matching_service
