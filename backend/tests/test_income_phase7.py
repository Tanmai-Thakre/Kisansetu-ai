"""
Phase 7 — Tests for the Farmer Income Dashboard Agent.

Tests:
  - Core calculations (gross revenue, total cost, net income, per-quintal income)
  - quality_adjusted_price
  - All four scenario builders
  - Scenario ranking
  - Missing buyer / missing forecast fallbacks
  - Zero and negative cost handling
  - Invalid quantity guard
  - IncomeService.calculate() end-to-end (all four winner cases)

Run: python -m pytest tests/test_income_phase7.py -v
     (from backend/ directory with PYTHONPATH=.)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# 1. Core calculation functions
# ──────────────────────────────────────────────────────────────────────────────

class TestCoreCalculations:

    def setup_method(self):
        from app.agents.income.calculations import (
            gross_revenue, total_cost, net_income,
            per_quintal_income, quality_adjusted_price,
        )
        self.gross_revenue         = gross_revenue
        self.total_cost            = total_cost
        self.net_income            = net_income
        self.per_quintal_income    = per_quintal_income
        self.quality_adjusted_price = quality_adjusted_price

    def test_gross_revenue(self):
        assert self.gross_revenue(100, 7200) == 720000.0

    def test_gross_revenue_fractional(self):
        assert self.gross_revenue(1.5, 6100) == 9150.0

    def test_total_cost_all_components(self):
        cost = self.total_cost(transport=5000, storage=8000, labour=2000, packaging=1000, other=500)
        assert cost == 16500.0

    def test_total_cost_zeros(self):
        assert self.total_cost() == 0.0

    def test_total_cost_no_negatives(self):
        # Negative input should be treated as 0
        cost = self.total_cost(transport=-100, storage=500)
        assert cost == 500.0

    def test_net_income(self):
        assert self.net_income(720000, 12000) == 708000.0

    def test_net_income_negative_when_costs_exceed_revenue(self):
        result = self.net_income(5000, 8000)
        assert result == -3000.0

    def test_per_quintal_income(self):
        result = self.per_quintal_income(708000, 100)
        assert result == 7080.0

    def test_per_quintal_income_zero_quantity(self):
        assert self.per_quintal_income(100000, 0) == 0.0

    def test_quality_adjusted_price_positive(self):
        price = self.quality_adjusted_price(7200, 2.0)
        assert price == 7344.0

    def test_quality_adjusted_price_negative(self):
        price = self.quality_adjusted_price(7200, -3.0)
        assert price == 6984.0

    def test_quality_adjusted_price_zero(self):
        price = self.quality_adjusted_price(6100, 0.0)
        assert price == 6100.0


# ──────────────────────────────────────────────────────────────────────────────
# 2. Scenario builders
# ──────────────────────────────────────────────────────────────────────────────

class TestScenarioBuilders:

    def setup_method(self):
        from app.agents.income.scenarios import (
            scenario_mandi, scenario_direct_buyer,
            scenario_store, scenario_partial_sell,
        )
        self.scenario_mandi        = scenario_mandi
        self.scenario_direct_buyer = scenario_direct_buyer
        self.scenario_store        = scenario_store
        self.scenario_partial_sell = scenario_partial_sell

    # ── Scenario A ────────────────────────────────────────────────────────────

    def test_mandi_scenario_basic(self):
        s = self.scenario_mandi(
            quantity=100,
            mandi_price=7200,
            transport_per_quintal=50,
        )
        assert s.gross_revenue == 720000.0
        assert s.transport_cost == 5000.0   # 100 × 50
        assert s.storage_cost == 0.0
        assert s.net_income == 715000.0     # 720000 - 5000

    def test_mandi_scenario_with_optional_costs(self):
        s = self.scenario_mandi(
            quantity=100,
            mandi_price=7200,
            transport_per_quintal=50,
            labour_total=2000,
            packaging_total=1000,
            other_total=500,
        )
        assert s.total_cost == 8500.0       # 5000 + 2000 + 1000 + 500
        assert s.net_income == 711500.0

    # ── Scenario B ────────────────────────────────────────────────────────────

    def test_direct_buyer_higher_than_mandi(self):
        s_mandi  = self.scenario_mandi(quantity=100, mandi_price=7200, transport_per_quintal=50)
        s_buyer  = self.scenario_direct_buyer(quantity=100, buyer_price=7380, transport_per_quintal=50)
        assert s_buyer.net_income > s_mandi.net_income

    def test_direct_buyer_below_mandi(self):
        s_mandi = self.scenario_mandi(quantity=100, mandi_price=7200, transport_per_quintal=50)
        s_buyer = self.scenario_direct_buyer(quantity=100, buyer_price=7000, transport_per_quintal=50)
        assert s_mandi.net_income > s_buyer.net_income

    # ── Scenario C ────────────────────────────────────────────────────────────

    def test_store_7_days(self):
        s = self.scenario_store(
            quantity=100,
            forecast_price=7300,
            storage_cost_per_quintal=80,
            horizon_days=7,
            transport_per_quintal=50,
        )
        expected_storage = round(100 * 80 * (7 / 30), 2)
        assert s.storage_cost == expected_storage
        assert s.gross_revenue == 730000.0

    def test_store_15_days(self):
        s = self.scenario_store(
            quantity=100,
            forecast_price=7450,
            storage_cost_per_quintal=80,
            horizon_days=15,
            transport_per_quintal=50,
        )
        expected_storage = round(100 * 80 * (15 / 30), 2)
        assert s.storage_cost == expected_storage
        assert s.gross_revenue == 745000.0

    def test_store_30_days(self):
        s = self.scenario_store(
            quantity=100,
            forecast_price=7500,
            storage_cost_per_quintal=80,
            horizon_days=30,
            transport_per_quintal=50,
        )
        expected_storage = round(100 * 80 * (30 / 30), 2)
        assert s.storage_cost == expected_storage

    def test_storage_scenario_best_when_forecast_high(self):
        """If forecast price is significantly higher, store beats mandi."""
        s_mandi = self.scenario_mandi(
            quantity=100, mandi_price=7200, transport_per_quintal=50
        )
        s_store = self.scenario_store(
            quantity=100, forecast_price=7800,
            storage_cost_per_quintal=80, horizon_days=15,
            transport_per_quintal=50,
        )
        assert s_store.net_income > s_mandi.net_income

    # ── Scenario D ────────────────────────────────────────────────────────────

    def test_partial_sell_totals_correct(self):
        s = self.scenario_partial_sell(
            quantity=100,
            sell_price=7200,
            forecast_price=7450,
            sell_percentage=60,
            storage_cost_per_quintal=80,
            horizon_days=15,
            transport_per_quintal=50,
        )
        # 60 qtl × 7200 + 40 qtl × 7450
        expected_gross = round(60 * 7200 + 40 * 7450, 2)
        assert s.gross_revenue == expected_gross

    def test_partial_sell_partial_storage_cost(self):
        s = self.scenario_partial_sell(
            quantity=100,
            sell_price=7200,
            forecast_price=7450,
            sell_percentage=50,
            storage_cost_per_quintal=80,
            horizon_days=30,
            transport_per_quintal=50,
        )
        # Only 50 qtl stored, storage for 30 days
        expected_storage = round(50 * 80 * (30 / 30), 2)
        assert s.storage_cost == expected_storage

    def test_partial_sell_100_pct_now_equals_mandi(self):
        """If sell_percentage=100, partial equals selling all now (net income same)."""
        s_partial = self.scenario_partial_sell(
            quantity=100,
            sell_price=7200,
            forecast_price=7500,      # irrelevant if 100% sold now
            sell_percentage=100,
            storage_cost_per_quintal=80,
            horizon_days=15,
            transport_per_quintal=50,
        )
        s_mandi = self.scenario_mandi(
            quantity=100, mandi_price=7200, transport_per_quintal=50,
        )
        # Storage cost is 0 for 100% sold (0 qtl stored)
        assert s_partial.net_income == s_mandi.net_income


# ──────────────────────────────────────────────────────────────────────────────
# 3. Scenario ranking
# ──────────────────────────────────────────────────────────────────────────────

class TestScenarioRanking:

    def setup_method(self):
        from app.agents.income.scenarios import (
            scenario_mandi, scenario_direct_buyer, scenario_store,
            rank_scenarios, best_scenario, income_difference,
        )
        self.scenario_mandi        = scenario_mandi
        self.scenario_direct_buyer = scenario_direct_buyer
        self.scenario_store        = scenario_store
        self.rank_scenarios        = rank_scenarios
        self.best_scenario         = best_scenario
        self.income_difference     = income_difference

    def _scenarios(self, mandi_p=7200, buyer_p=7380, forecast_p=7450, horizon=15):
        """Build a standard set of scenarios."""
        sm = self.scenario_mandi(
            quantity=100, mandi_price=mandi_p, transport_per_quintal=50,
        )
        sb = self.scenario_direct_buyer(
            quantity=100, buyer_price=buyer_p, transport_per_quintal=50,
        )
        ss = self.scenario_store(
            quantity=100, forecast_price=forecast_p,
            storage_cost_per_quintal=80, horizon_days=horizon,
            transport_per_quintal=50,
        )
        return [sm, sb, ss]

    def test_mandi_is_best(self):
        # Mandi price highest, buyer below mandi, forecast below mandi
        scenarios = self._scenarios(mandi_p=7500, buyer_p=7200, forecast_p=7000)
        top = self.best_scenario(scenarios)
        assert top is not None
        assert "Mandi" in top.name

    def test_direct_buyer_is_best(self):
        scenarios = self._scenarios(mandi_p=7200, buyer_p=7600, forecast_p=7000)
        top = self.best_scenario(scenarios)
        assert top is not None
        assert "Buyer" in top.name

    def test_storage_is_best(self):
        # Forecast very high, storage cost small relative to gain
        scenarios = self._scenarios(mandi_p=7200, buyer_p=7300, forecast_p=8000)
        top = self.best_scenario(scenarios)
        assert top is not None
        assert "Store" in top.name

    def test_partial_sell_is_best(self):
        """Partial sell can be best if immediate + future combined beats all."""
        from app.agents.income.scenarios import scenario_partial_sell, best_scenario
        sm = self.scenario_mandi(quantity=100, mandi_price=7200, transport_per_quintal=50)
        sb = self.scenario_direct_buyer(quantity=100, buyer_price=7300, transport_per_quintal=50)
        ss = self.scenario_store(
            quantity=100, forecast_price=7100, storage_cost_per_quintal=200,
            horizon_days=30, transport_per_quintal=50,
        )
        # 70% now at good price + 30% at a very high future price
        sp = scenario_partial_sell(
            quantity=100, sell_price=7400, forecast_price=7900,
            sell_percentage=70,
            storage_cost_per_quintal=20, horizon_days=30,
            transport_per_quintal=50,
        )
        scenarios = [sm, sb, ss, sp]
        top = best_scenario(scenarios)
        assert top is not None
        assert "Partial" in top.name

    def test_ranking_order(self):
        scenarios = self._scenarios(mandi_p=7200, buyer_p=7600, forecast_p=7000)
        ranked = self.rank_scenarios(scenarios)
        # Verify descending order
        for i in range(len(ranked) - 1):
            assert ranked[i].net_income >= ranked[i + 1].net_income

    def test_income_difference(self):
        scenarios = self._scenarios(mandi_p=7200, buyer_p=7600, forecast_p=7000)
        diff = self.income_difference(scenarios)
        assert diff > 0

    def test_empty_scenarios(self):
        assert self.best_scenario([]) is None

    def test_single_scenario(self):
        s = self.scenario_mandi(quantity=100, mandi_price=7200, transport_per_quintal=50)
        top = self.best_scenario([s])
        assert top is not None
        assert top.name == s.name


# ──────────────────────────────────────────────────────────────────────────────
# 4. Missing data / edge cases
# ──────────────────────────────────────────────────────────────────────────────

class TestEdgeCases:

    def setup_method(self):
        from app.agents.income.scenarios import scenario_mandi, scenario_store
        self.scenario_mandi  = scenario_mandi
        self.scenario_store  = scenario_store

    def test_zero_quantity_per_quintal(self):
        from app.agents.income.calculations import per_quintal_income
        assert per_quintal_income(100000, 0) == 0.0

    def test_zero_costs(self):
        s = self.scenario_mandi(
            quantity=100, mandi_price=7200, transport_per_quintal=0,
        )
        assert s.total_cost == 0.0
        assert s.net_income == 720000.0

    def test_negative_cost_inputs_clamped(self):
        s = self.scenario_mandi(
            quantity=100, mandi_price=7200, transport_per_quintal=0,
            labour_total=-500,
        )
        assert s.labour_cost == 0.0      # Negative labour treated as 0

    def test_missing_buyer_scenario_omitted(self):
        """
        When buyer_price_override=0 (falsy), no direct-buyer scenario is built,
        but the service should still return valid output with remaining scenarios.
        buyer_price_override=None means 'fetch from Phase 4', so 0 is used to
        explicitly disable it.
        """
        from app.agents.income.income_service import IncomeService
        svc = IncomeService()
        # Pass 0 to disable buyer; the service skips it when price <= 0
        result = svc.calculate(
            crop="cotton",
            quantity=100,
            mandi="Rajkot APMC",
            buyer_price_override=0,
        )
        # Should not crash; best_scenario is still determined from other scenarios
        assert result["best_scenario"] is not None
        assert len(result["scenarios"]) >= 4   # mandi + 3 store + partial

    def test_missing_forecast_uses_fallback(self):
        """
        If forecasting fails, income service falls back to current price.
        Scenarios should still be produced.
        """
        from app.agents.income.income_service import IncomeService
        svc = IncomeService()
        result = svc.calculate(
            crop="groundnut",
            quantity=50,
            mandi="Amreli APMC",
        )
        assert len(result["scenarios"]) >= 4
        # forecast fallback should be the current mandi price, so store
        # scenarios should have forecast prices >= 0
        for s in result["scenarios"]:
            assert s["gross_revenue"] >= 0

    def test_invalid_quantity_rejected_by_schema(self):
        from pydantic import ValidationError
        from app.schemas.income import IncomeRequest
        with pytest.raises(ValidationError):
            IncomeRequest(crop="cotton", quantity=-5)

    def test_invalid_crop_rejected_by_schema(self):
        from pydantic import ValidationError
        from app.schemas.income import IncomeRequest
        with pytest.raises(ValidationError):
            IncomeRequest(crop="wheat", quantity=100)

    def test_negative_cost_rejected_by_schema(self):
        from pydantic import ValidationError
        from app.schemas.income import IncomeRequest
        with pytest.raises(ValidationError):
            IncomeRequest(crop="cotton", quantity=100, labour_total=-100)


# ──────────────────────────────────────────────────────────────────────────────
# 5. IncomeService.calculate() end-to-end
# ──────────────────────────────────────────────────────────────────────────────

class TestIncomeServiceEndToEnd:

    def setup_method(self):
        from app.agents.income.income_service import IncomeService
        self.svc = IncomeService()

    def _calc(self, **kwargs):
        defaults = dict(
            crop="cotton",
            quantity=100,
            mandi="Rajkot APMC",
            storage_cost_per_quintal=80,
        )
        defaults.update(kwargs)
        return self.svc.calculate(**defaults)

    def test_returns_all_required_keys(self):
        r = self._calc()
        required = [
            "crop", "mandi", "quantity", "mandi_price", "buyer_price",
            "forecast_7d", "forecast_15d", "forecast_30d",
            "scenarios", "best_scenario", "best_net_income",
            "income_difference", "deterministic_summary",
            "current_estimated_income", "partial_sell_income",
            "cost_breakdown", "disclaimer", "source_status",
        ]
        for key in required:
            assert key in r, f"Missing key: {key}"

    def test_cotton_calculation(self):
        r = self._calc(crop="cotton", quantity=150)
        assert r["crop"] == "cotton"
        assert r["quantity"] == 150
        assert r["current_estimated_income"] > 0

    def test_groundnut_calculation(self):
        r = self._calc(crop="groundnut", quantity=80)
        assert r["crop"] == "groundnut"
        assert r["best_net_income"] is not None

    def test_scenarios_not_empty(self):
        r = self._calc()
        assert len(r["scenarios"]) >= 4

    def test_scenarios_ranked_descending(self):
        r = self._calc()
        incomes = [s["net_income"] for s in r["scenarios"]]
        assert incomes == sorted(incomes, reverse=True)

    def test_best_scenario_matches_first_ranked(self):
        r = self._calc()
        assert r["best_scenario"] == r["scenarios"][0]["name"]
        assert r["best_net_income"] == r["scenarios"][0]["net_income"]

    def test_quality_adjustment_applied(self):
        r = self._calc(quality_price_impact_pct=2.0)
        assert r["quality_price_impact_pct"] == 2.0
        assert r["quality_adjusted_price"] is not None
        assert r["quality_adjusted_price"] > r["mandi_price"]

    def test_quality_discount_applied(self):
        r = self._calc(quality_price_impact_pct=-3.0)
        assert r["quality_adjusted_price"] < r["mandi_price"]

    def test_optional_expenses_reflected_in_scenarios(self):
        r_no_costs   = self._calc(labour_total=0, packaging_total=0)
        r_with_costs = self._calc(labour_total=2000, packaging_total=1000)
        # Net income should be lower with costs
        assert r_with_costs["current_estimated_income"] < r_no_costs["current_estimated_income"]

    def test_mandi_price_override(self):
        r = self._calc(mandi_price_override=8000.0)
        assert r["mandi_price"] == 8000.0

    def test_buyer_price_override(self):
        r = self._calc(buyer_price_override=7500.0)
        assert r["buyer_price"] == 7500.0
        # Buyer scenario should exist
        buyer_scenarios = [s for s in r["scenarios"] if "Buyer" in s["name"]]
        assert len(buyer_scenarios) == 1
        assert buyer_scenarios[0]["selling_price_per_quintal"] == 7500.0

    def test_income_difference_non_negative(self):
        r = self._calc()
        assert r["income_difference"] >= 0

    def test_deterministic_summary_non_empty(self):
        r = self._calc()
        assert len(r["deterministic_summary"]) > 10
        assert "estimated" in r["deterministic_summary"].lower()

    def test_source_status_is_demo(self):
        r = self._calc()
        assert r["source_status"] == "DEMO"

    def test_all_scenario_net_incomes_are_floats(self):
        r = self._calc(quantity=200)
        for s in r["scenarios"]:
            assert isinstance(s["net_income"], float)
            assert isinstance(s["gross_revenue"], float)
            assert isinstance(s["total_cost"], float)
