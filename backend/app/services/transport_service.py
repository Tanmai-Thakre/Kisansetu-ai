"""
Phase 2 — TransportCostService
Deterministic transport cost estimation.
Formula: transport_cost = distance_km × cost_per_km_per_quintal + fixed_overheads
All estimates are clearly labelled — not official logistics rates.
"""
import math
from typing import Optional, Dict
from .master_data import TRANSPORT_CONFIG, MANDI_DISTANCE_FROM_RAJKOT_KM


class TransportCostResult:
    def __init__(
        self,
        mandi: str,
        distance_km: float,
        cost_per_quintal: float,
        quantity: float,
        total_cost: float,
        net_price_per_quintal: float,
        modal_price: float,
        is_estimated: bool = True,
    ):
        self.mandi = mandi
        self.distance_km = distance_km
        self.cost_per_quintal = round(cost_per_quintal, 2)
        self.quantity = quantity
        self.total_cost = round(total_cost, 2)
        self.net_price_per_quintal = round(net_price_per_quintal, 2)
        self.modal_price = modal_price
        self.is_estimated = is_estimated

    def to_dict(self) -> Dict:
        return {
            "mandi": self.mandi,
            "distance_km": self.distance_km,
            "cost_per_quintal": self.cost_per_quintal,
            "quantity_quintals": self.quantity,
            "total_transport_cost": self.total_cost,
            "modal_price": self.modal_price,
            "net_price_per_quintal": self.net_price_per_quintal,
            "is_estimated": self.is_estimated,
            "note": "Estimated transport — not official logistics rates",
        }


class TransportCostService:
    """
    Estimates transport costs from a reference location to a mandi.
    Reference location is configurable; defaults to Rajkot (major cotton belt).
    All results are labelled as ESTIMATED.
    """

    def __init__(self, reference_location: str = "Rajkot"):
        self.reference_location = reference_location
        self._config = TRANSPORT_CONFIG
        self._distances = MANDI_DISTANCE_FROM_RAJKOT_KM

    def get_distance_km(self, mandi_name: str) -> float:
        """Return approximate road distance in km, or a default if unknown."""
        return self._distances.get(mandi_name, 100.0)  # default 100km if unknown

    def estimate_cost(
        self,
        mandi_name: str,
        modal_price: float,
        quantity_quintals: float = 100.0,
        distance_km: Optional[float] = None,
    ) -> TransportCostResult:
        """
        Estimate transport cost per quintal and net effective price.
        net_price = modal_price - transport_cost_per_quintal - mandi_commission
        """
        dist = distance_km if distance_km is not None else self.get_distance_km(mandi_name)

        # Variable transport cost
        variable = dist * self._config["cost_per_km_per_quintal"]
        # Fixed overhead (loading/unloading)
        fixed = self._config["loading_unloading"]
        # Mandi commission (% of modal price)
        commission = modal_price * (self._config["mandi_commission_pct"] / 100)

        cost_per_quintal = max(
            variable + fixed + commission,
            self._config["min_transport_cost"],
        )
        total_cost = cost_per_quintal * quantity_quintals
        net_price = modal_price - cost_per_quintal

        return TransportCostResult(
            mandi=mandi_name,
            distance_km=dist,
            cost_per_quintal=cost_per_quintal,
            quantity=quantity_quintals,
            total_cost=total_cost,
            net_price_per_quintal=net_price,
            modal_price=modal_price,
            is_estimated=True,
        )


# Singleton
_transport_service: Optional[TransportCostService] = None

def get_transport_service() -> TransportCostService:
    global _transport_service
    if _transport_service is None:
        _transport_service = TransportCostService()
    return _transport_service
