"""
Phase 7 — Income Calculations (pure functions, no side effects).

All financial formulas are centralised here.
No duplication in the API layer.

Units:
  quantity     — quintals (qtl)
  prices       — ₹ per quintal
  costs/income — ₹ total
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ── Core calculation functions ────────────────────────────────────────────────

def gross_revenue(quantity: float, selling_price: float) -> float:
    """Total revenue before any cost deduction."""
    return round(quantity * selling_price, 2)


def total_cost(
    transport: float = 0.0,
    storage: float = 0.0,
    labour: float = 0.0,
    packaging: float = 0.0,
    other: float = 0.0,
) -> float:
    """Sum of all applicable costs."""
    return round(max(0.0, transport) + max(0.0, storage) + max(0.0, labour)
                 + max(0.0, packaging) + max(0.0, other), 2)


def net_income(gross: float, cost: float) -> float:
    """Net income after all costs."""
    return round(gross - cost, 2)


def per_quintal_income(net: float, quantity: float) -> float:
    """Net income per quintal."""
    if quantity <= 0:
        return 0.0
    return round(net / quantity, 2)


def quality_adjusted_price(
    reference_price: float,
    price_impact_percent: float,
) -> float:
    """
    Estimated price with quality premium/discount applied.
    price_impact_percent: signed float, e.g. +2.0 or -3.5
    """
    return round(reference_price * (1 + price_impact_percent / 100), 2)


# ── Scenario result dataclass ─────────────────────────────────────────────────

@dataclass
class ScenarioResult:
    name: str
    selling_price_per_quintal: float
    gross_revenue: float
    transport_cost: float
    storage_cost: float
    labour_cost: float
    packaging_cost: float
    other_cost: float
    total_cost: float
    net_income: float
    net_income_per_quintal: float
    notes: list = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "name":                     self.name,
            "selling_price_per_quintal": self.selling_price_per_quintal,
            "gross_revenue":            self.gross_revenue,
            "transport_cost":           self.transport_cost,
            "storage_cost":             self.storage_cost,
            "labour_cost":              self.labour_cost,
            "packaging_cost":           self.packaging_cost,
            "other_cost":               self.other_cost,
            "total_cost":               self.total_cost,
            "net_income":               self.net_income,
            "net_income_per_quintal":   self.net_income_per_quintal,
            "notes":                    self.notes,
        }


def build_scenario(
    name: str,
    quantity: float,
    selling_price: float,
    transport: float = 0.0,
    storage: float = 0.0,
    labour: float = 0.0,
    packaging: float = 0.0,
    other: float = 0.0,
    notes: Optional[list] = None,
) -> ScenarioResult:
    """
    Construct a ScenarioResult from inputs.
    All cost fields are totals (not per-quintal) unless the caller computes them.
    """
    cost = total_cost(transport, storage, labour, packaging, other)
    gr   = gross_revenue(quantity, selling_price)
    ni   = net_income(gr, cost)
    ni_q = per_quintal_income(ni, quantity)

    return ScenarioResult(
        name=name,
        selling_price_per_quintal=round(selling_price, 2),
        gross_revenue=gr,
        transport_cost=round(max(0.0, transport), 2),
        storage_cost=round(max(0.0, storage), 2),
        labour_cost=round(max(0.0, labour), 2),
        packaging_cost=round(max(0.0, packaging), 2),
        other_cost=round(max(0.0, other), 2),
        total_cost=cost,
        net_income=ni,
        net_income_per_quintal=ni_q,
        notes=notes or [],
    )
