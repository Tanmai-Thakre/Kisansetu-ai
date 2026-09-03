"""
Phase 2 — MarketDataProvider abstraction.

Architecture:
    MarketDataProvider (abstract interface)
        ├── DemoMarketDataProvider   — synthetic dataset (Phase 2)
        └── LiveMarketDataProvider   — real API stub (Phase 3+)

This abstraction ensures the data source can be swapped without
changing any application or API code.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from datetime import date, timedelta
from typing import List, Optional, Dict
import math
import random


# ── Data transfer objects ─────────────────────────────────────────────────────

class MarketRecord:
    """A single market price observation."""
    def __init__(
        self,
        crop: str,
        variety: str,
        mandi: str,
        district: str,
        state: str,
        record_date: date,
        min_price: float,
        max_price: float,
        modal_price: float,
        arrival_quantity: Optional[float],
        unit: str,
        source: str,
        source_status: str,
    ):
        self.crop = crop
        self.variety = variety
        self.mandi = mandi
        self.district = district
        self.state = state
        self.date = record_date
        self.min_price = round(min_price, 2)
        self.max_price = round(max_price, 2)
        self.modal_price = round(modal_price, 2)
        self.arrival_quantity = round(arrival_quantity, 1) if arrival_quantity else None
        self.unit = unit
        self.source = source
        self.source_status = source_status

    def to_dict(self) -> Dict:
        return {
            "crop": self.crop,
            "variety": self.variety,
            "mandi": self.mandi,
            "district": self.district,
            "state": self.state,
            "date": str(self.date),
            "min_price": self.min_price,
            "max_price": self.max_price,
            "modal_price": self.modal_price,
            "arrival_quantity": self.arrival_quantity,
            "unit": self.unit,
            "source": self.source,
            "source_status": self.source_status,
        }


# ── Abstract interface ────────────────────────────────────────────────────────

class MarketDataProvider(ABC):
    """
    Abstract base class for all market data providers.
    Implement this interface to swap data sources without touching API or service code.
    """
    SOURCE_NAME: str = "Unknown"
    SOURCE_STATUS: str = "DEMO"

    @abstractmethod
    def get_latest_prices(
        self,
        crop: Optional[str] = None,
        district: Optional[str] = None,
        mandi: Optional[str] = None,
    ) -> List[MarketRecord]:
        """Return the latest available price for each mandi/crop combination."""
        ...

    @abstractmethod
    def get_price_history(
        self,
        crop: str,
        mandi: Optional[str] = None,
        district: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 90,
    ) -> List[MarketRecord]:
        """Return chronological price history for charting and trend analysis."""
        ...

    @abstractmethod
    def is_live(self) -> bool:
        """True if this provider returns real-time data."""
        ...

    def get_source_info(self) -> Dict:
        return {
            "source": self.SOURCE_NAME,
            "source_status": self.SOURCE_STATUS,
            "is_live": self.is_live(),
        }


# ── Demo Provider ─────────────────────────────────────────────────────────────

# Base prices per mandi (modal, approximate Gujarat market levels)
_COTTON_BASE: Dict[str, Dict] = {
    "Rajkot APMC":        {"modal": 7200, "spread": 400, "variety": "Bt Cotton"},
    "Gondal APMC":        {"modal": 7180, "spread": 380, "variety": "Bt Cotton"},
    "Jetpur APMC":        {"modal": 7150, "spread": 360, "variety": "Desi Cotton"},
    "Amreli APMC":        {"modal": 7100, "spread": 370, "variety": "Bt Cotton"},
    "Savarkundla APMC":   {"modal": 7120, "spread": 350, "variety": "Bt Cotton"},
    "Junagadh APMC":      {"modal": 7250, "spread": 400, "variety": "Bt Cotton"},
    "Keshod APMC":        {"modal": 7090, "spread": 340, "variety": "Bt Cotton"},
    "Bhavnagar APMC":     {"modal": 7150, "spread": 380, "variety": "Bt Cotton"},
    "Talaja APMC":        {"modal": 7080, "spread": 350, "variety": "Desi Cotton"},
    "Ahmedabad APMC":     {"modal": 7400, "spread": 450, "variety": "Bt Cotton"},
    "Surendranagar APMC": {"modal": 7300, "spread": 420, "variety": "Bt Cotton"},
    "Wadhwan APMC":       {"modal": 7280, "spread": 400, "variety": "Bt Cotton"},
    "Jamnagar APMC":      {"modal": 7050, "spread": 340, "variety": "Desi Cotton"},
    "Mehsana APMC":       {"modal": 7350, "spread": 430, "variety": "Bt Cotton"},
    "Banaskantha APMC":   {"modal": 7200, "spread": 380, "variety": "Bt Cotton"},
    "Deesa APMC":         {"modal": 7170, "spread": 360, "variety": "Bt Cotton"},
}

_GROUNDNUT_BASE: Dict[str, Dict] = {
    "Rajkot APMC":        {"modal": 6100, "spread": 350, "variety": "Bold"},
    "Gondal APMC":        {"modal": 6150, "spread": 360, "variety": "Bold"},
    "Jetpur APMC":        {"modal": 6050, "spread": 320, "variety": "Java"},
    "Amreli APMC":        {"modal": 6000, "spread": 330, "variety": "Bold"},
    "Savarkundla APMC":   {"modal": 6080, "spread": 340, "variety": "Bold"},
    "Junagadh APMC":      {"modal": 6200, "spread": 370, "variety": "Bold"},
    "Keshod APMC":        {"modal": 5980, "spread": 310, "variety": "Java"},
    "Bhavnagar APMC":     {"modal": 6050, "spread": 330, "variety": "Bold"},
    "Talaja APMC":        {"modal": 6020, "spread": 310, "variety": "Java"},
    "Ahmedabad APMC":     {"modal": 6250, "spread": 390, "variety": "Bold"},
    "Surendranagar APMC": {"modal": 6150, "spread": 360, "variety": "Bold"},
    "Wadhwan APMC":       {"modal": 6130, "spread": 350, "variety": "Bold"},
    "Jamnagar APMC":      {"modal": 5950, "spread": 300, "variety": "Java"},
    "Mehsana APMC":       {"modal": 6100, "spread": 340, "variety": "Bold"},
    "Banaskantha APMC":   {"modal": 6080, "spread": 330, "variety": "Bold"},
    "Deesa APMC":         {"modal": 6020, "spread": 310, "variety": "Java"},
}

_MANDI_DISTRICT: Dict[str, str] = {
    "Rajkot APMC": "Rajkot", "Gondal APMC": "Rajkot", "Jetpur APMC": "Rajkot",
    "Amreli APMC": "Amreli", "Savarkundla APMC": "Amreli",
    "Junagadh APMC": "Junagadh", "Keshod APMC": "Junagadh",
    "Bhavnagar APMC": "Bhavnagar", "Talaja APMC": "Bhavnagar",
    "Ahmedabad APMC": "Ahmedabad",
    "Surendranagar APMC": "Surendranagar", "Wadhwan APMC": "Surendranagar",
    "Jamnagar APMC": "Jamnagar",
    "Mehsana APMC": "Mehsana",
    "Banaskantha APMC": "Banaskantha", "Deesa APMC": "Banaskantha",
}


def _simulate_price(base_modal: float, base_spread: float, day_offset: int, seed: int) -> tuple:
    """
    Simulate realistic price movement using a random-walk with seasonal trend.
    Returns (min_price, max_price, modal_price).
    """
    rng = random.Random(seed + day_offset * 13)
    # Gentle upward drift over 90 days (seasonal kharif market)
    trend = base_modal * 0.001 * (day_offset / 10)
    # Daily noise
    noise = rng.uniform(-base_spread * 0.06, base_spread * 0.07)
    modal = max(base_modal * 0.80, base_modal + trend + noise)
    modal = round(modal / 10) * 10  # round to nearest 10
    half_spread = base_spread * rng.uniform(0.35, 0.55)
    min_p = round((modal - half_spread) / 10) * 10
    max_p = round((modal + half_spread) / 10) * 10
    arrival = round(rng.uniform(300, 2500), 0)
    return min_p, max_p, modal, arrival


class DemoMarketDataProvider(MarketDataProvider):
    """
    Synthetic demo data provider — generates 90 days of realistic market data.
    Clearly labelled as DEMO — not official government or exchange data.
    """
    SOURCE_NAME = "KisanSetu Demo Dataset"
    SOURCE_STATUS = "DEMO"
    DAYS_OF_HISTORY = 90

    def __init__(self):
        self._cache: Optional[List[MarketRecord]] = None

    def _generate_all(self) -> List[MarketRecord]:
        """Generate the full synthetic dataset (lazy, cached)."""
        if self._cache is not None:
            return self._cache

        records: List[MarketRecord] = []
        today = date.today()
        start = today - timedelta(days=self.DAYS_OF_HISTORY - 1)

        for day_offset in range(self.DAYS_OF_HISTORY):
            record_date = start + timedelta(days=day_offset)
            # Skip ~15% of days to simulate market closure / missing data
            rng_skip = random.Random(day_offset * 7)
            if rng_skip.random() < 0.10:
                continue

            for mandi, c_data in _COTTON_BASE.items():
                seed = abs(hash(f"cotton-{mandi}")) % 100000
                min_p, max_p, modal, arrival = _simulate_price(
                    c_data["modal"], c_data["spread"], day_offset, seed
                )
                records.append(MarketRecord(
                    crop="cotton", variety=c_data["variety"],
                    mandi=mandi, district=_MANDI_DISTRICT.get(mandi, "Unknown"),
                    state="Gujarat", record_date=record_date,
                    min_price=min_p, max_price=max_p, modal_price=modal,
                    arrival_quantity=arrival, unit="quintal",
                    source=self.SOURCE_NAME, source_status=self.SOURCE_STATUS,
                ))

            for mandi, g_data in _GROUNDNUT_BASE.items():
                seed = abs(hash(f"groundnut-{mandi}")) % 100000
                min_p, max_p, modal, arrival = _simulate_price(
                    g_data["modal"], g_data["spread"], day_offset, seed
                )
                records.append(MarketRecord(
                    crop="groundnut", variety=g_data["variety"],
                    mandi=mandi, district=_MANDI_DISTRICT.get(mandi, "Unknown"),
                    state="Gujarat", record_date=record_date,
                    min_price=min_p, max_price=max_p, modal_price=modal,
                    arrival_quantity=arrival, unit="quintal",
                    source=self.SOURCE_NAME, source_status=self.SOURCE_STATUS,
                ))

        self._cache = records
        return records

    def is_live(self) -> bool:
        return False

    def get_latest_prices(
        self,
        crop: Optional[str] = None,
        district: Optional[str] = None,
        mandi: Optional[str] = None,
    ) -> List[MarketRecord]:
        all_records = self._generate_all()
        # Find the latest date per mandi+crop combination
        latest: Dict[str, MarketRecord] = {}
        for r in all_records:
            if crop and r.crop != crop.lower():
                continue
            if district and r.district.lower() != district.lower():
                continue
            if mandi and r.mandi.lower() != mandi.lower():
                continue
            key = f"{r.crop}::{r.mandi}"
            if key not in latest or r.date > latest[key].date:
                latest[key] = r
        return sorted(latest.values(), key=lambda x: (x.crop, x.district, x.mandi))

    def get_price_history(
        self,
        crop: str,
        mandi: Optional[str] = None,
        district: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 90,
    ) -> List[MarketRecord]:
        all_records = self._generate_all()
        filtered = [
            r for r in all_records
            if r.crop == crop.lower()
            and (mandi is None or r.mandi.lower() == mandi.lower())
            and (district is None or r.district.lower() == district.lower())
            and (start_date is None or r.date >= start_date)
            and (end_date is None or r.date <= end_date)
        ]
        # Sort chronologically and apply limit
        filtered.sort(key=lambda x: (x.mandi, x.date))
        return filtered[-limit:]


class LiveMarketDataProvider(MarketDataProvider):
    """
    Live market data provider stub — to be implemented in Phase 3+.
    Will connect to AgMarkNet / eNAM or equivalent government API.
    """
    SOURCE_NAME = "Live Market API (Not Configured)"
    SOURCE_STATUS = "DEMO"

    def __init__(self):
        self._configured = False

    def is_live(self) -> bool:
        return self._configured

    def get_latest_prices(self, crop=None, district=None, mandi=None) -> List[MarketRecord]:
        raise NotImplementedError(
            "LiveMarketDataProvider is not yet configured. "
            "Set MARKET_API_KEY and MARKET_API_URL in .env to enable."
        )

    def get_price_history(self, crop, mandi=None, district=None,
                          start_date=None, end_date=None, limit=90) -> List[MarketRecord]:
        raise NotImplementedError("LiveMarketDataProvider is not yet configured.")


# ── Singleton provider instance ───────────────────────────────────────────────
# Switch to LiveMarketDataProvider once API credentials are available.
_demo_provider = DemoMarketDataProvider()

def get_market_data_provider() -> MarketDataProvider:
    """Return the active market data provider."""
    return _demo_provider
