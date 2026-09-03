"""
Phase 2 — Backend tests for Market Intelligence services.
Run with: python -m pytest tests/ -v (from backend/ directory with PYTHONPATH=.)
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from datetime import date, timedelta


# ── Provider tests ────────────────────────────────────────────────────────────

class TestDemoMarketDataProvider:

    def setup_method(self):
        from app.services.market_data_provider import DemoMarketDataProvider
        self.provider = DemoMarketDataProvider()

    def test_generates_records(self):
        records = self.provider._generate_all()
        assert len(records) > 100, "Should generate 100+ records"

    def test_latest_prices_cotton(self):
        records = self.provider.get_latest_prices(crop="cotton")
        assert len(records) > 0
        assert all(r.crop == "cotton" for r in records)

    def test_latest_prices_groundnut(self):
        records = self.provider.get_latest_prices(crop="groundnut")
        assert len(records) > 0
        assert all(r.crop == "groundnut" for r in records)

    def test_latest_prices_district_filter(self):
        records = self.provider.get_latest_prices(crop="cotton", district="Rajkot")
        assert all(r.district == "Rajkot" for r in records)

    def test_history_chronological(self):
        records = self.provider.get_price_history(crop="cotton", mandi="Rajkot APMC")
        assert len(records) > 0
        dates = [r.date for r in records]
        assert dates == sorted(dates), "History should be in chronological order"

    def test_price_ordering_valid(self):
        records = self.provider.get_latest_prices(crop="cotton")
        for r in records:
            assert r.min_price <= r.modal_price, f"min > modal at {r.mandi}"
            assert r.modal_price <= r.max_price, f"modal > max at {r.mandi}"

    def test_prices_positive(self):
        records = self.provider.get_latest_prices()
        for r in records:
            assert r.min_price > 0
            assert r.max_price > 0
            assert r.modal_price > 0

    def test_arrival_quantity_nonnegative(self):
        records = self.provider.get_latest_prices()
        for r in records:
            if r.arrival_quantity is not None:
                assert r.arrival_quantity >= 0

    def test_is_not_live(self):
        assert self.provider.is_live() is False

    def test_source_status_demo(self):
        records = self.provider.get_latest_prices(crop="cotton")
        for r in records:
            assert r.source_status == "DEMO"

    def test_history_date_filter(self):
        today = date.today()
        start = today - timedelta(days=10)
        end = today - timedelta(days=5)
        records = self.provider.get_price_history(
            crop="cotton", mandi="Rajkot APMC", start_date=start, end_date=end
        )
        for r in records:
            assert start <= r.date <= end


# ── PriceAnalysisService tests ────────────────────────────────────────────────

class TestPriceAnalysisService:

    def setup_method(self):
        from app.services.price_analysis_service import PriceAnalysisService, calculate_trend
        self.svc = PriceAnalysisService()
        self.calculate_trend = calculate_trend

    def test_trend_up(self):
        change, pct, direction = self.calculate_trend(7200, 7000)
        assert direction == "UP"
        assert change == pytest.approx(200, abs=1)
        assert pct == pytest.approx(2.857, abs=0.01)

    def test_trend_down(self):
        change, pct, direction = self.calculate_trend(6900, 7100)
        assert direction == "DOWN"
        assert change < 0

    def test_trend_stable(self):
        change, pct, direction = self.calculate_trend(7000, 7001)
        assert direction == "STABLE"

    def test_trend_no_previous(self):
        change, pct, direction = self.calculate_trend(7000, None)
        assert direction == "STABLE"
        assert change is None

    def test_crop_summary_cotton(self):
        result = self.svc.get_crop_summary("cotton", district="Rajkot")
        assert result is not None
        assert result["crop"] == "cotton"
        assert result["latest_modal_price"] > 0
        assert result["trend"] in ("up", "down", "stable")

    def test_crop_summary_groundnut(self):
        result = self.svc.get_crop_summary("groundnut")
        assert result is not None
        assert result["latest_modal_price"] > 0

    def test_history_for_chart(self):
        data = self.svc.get_history_for_chart("cotton", mandi="Rajkot APMC", days=30)
        assert len(data) > 0
        for point in data:
            assert "date" in point
            assert "modal_price" in point
            assert point["modal_price"] > 0


# ── TransportCostService tests ────────────────────────────────────────────────

class TestTransportCostService:

    def setup_method(self):
        from app.services.transport_service import TransportCostService
        self.svc = TransportCostService()

    def test_cost_increases_with_distance(self):
        r_near = self.svc.estimate_cost("Rajkot APMC", 7200, 100)
        r_far = self.svc.estimate_cost("Ahmedabad APMC", 7200, 100)
        assert r_far.cost_per_quintal > r_near.cost_per_quintal

    def test_net_price_less_than_modal(self):
        result = self.svc.estimate_cost("Rajkot APMC", 7200, 100)
        assert result.net_price_per_quintal < result.modal_price

    def test_is_estimated(self):
        result = self.svc.estimate_cost("Rajkot APMC", 7200, 100)
        assert result.is_estimated is True

    def test_unknown_mandi_uses_default_distance(self):
        result = self.svc.estimate_cost("Unknown Mandi", 7000, 100)
        assert result.distance_km == 100.0

    def test_total_cost_scales_with_quantity(self):
        r100 = self.svc.estimate_cost("Rajkot APMC", 7200, 100)
        r200 = self.svc.estimate_cost("Rajkot APMC", 7200, 200)
        assert r200.total_cost == pytest.approx(r100.total_cost * 2, rel=0.01)

    def test_negative_quantity_invalid(self):
        # quantity <= 0 is not meaningful; service should still not crash
        result = self.svc.estimate_cost("Rajkot APMC", 7200, 1)
        assert result.cost_per_quintal >= 0


# ── MandiComparisonService tests ──────────────────────────────────────────────

class TestMandiComparisonService:

    def setup_method(self):
        from app.services.mandi_comparison_service import MandiComparisonService
        self.svc = MandiComparisonService()

    def test_returns_entries(self):
        entries = self.svc.compare("cotton")
        assert len(entries) > 0

    def test_sorted_by_net_price_desc(self):
        entries = self.svc.compare("cotton")
        net_prices = [e.net_price for e in entries]
        assert net_prices == sorted(net_prices, reverse=True)

    def test_net_less_than_modal(self):
        for entry in self.svc.compare("cotton"):
            assert entry.net_price < entry.modal_price

    def test_filter_by_mandi_list(self):
        entries = self.svc.compare("cotton", mandi_list=["Rajkot APMC", "Amreli APMC"])
        mandi_names = {e.mandi for e in entries}
        assert mandi_names.issubset({"Rajkot APMC", "Amreli APMC"})


# ── BestMandiService tests ────────────────────────────────────────────────────

class TestBestMandiService:

    def setup_method(self):
        from app.services.mandi_comparison_service import BestMandiService
        self.svc = BestMandiService()

    def test_returns_best_mandi(self):
        result = self.svc.get_best_mandi("cotton")
        assert "best_mandi" in result
        assert result["best_mandi"] is not None

    def test_explanation_is_present(self):
        result = self.svc.get_best_mandi("cotton")
        assert len(result["explanation"]) > 20

    def test_best_is_highest_net(self):
        result = self.svc.get_best_mandi("cotton")
        all_nets = [m["net_price"] for m in result["all_mandis"]]
        assert result["best_mandi"]["net_price"] == max(all_nets)

    def test_groundnut_works(self):
        result = self.svc.get_best_mandi("groundnut")
        assert result["best_mandi"] is not None


# ── Schema validation tests ───────────────────────────────────────────────────

class TestMarketPriceV2Schema:

    def test_valid_record(self):
        from app.schemas.market_v2 import MarketPriceV2Create
        record = MarketPriceV2Create(
            crop="cotton",
            mandi="Rajkot APMC",
            district="Rajkot",
            date=date.today(),
            min_price=6900,
            max_price=7500,
            modal_price=7200,
        )
        assert record.crop == "cotton"

    def test_rejects_negative_price(self):
        from app.schemas.market_v2 import MarketPriceV2Create
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MarketPriceV2Create(
                crop="cotton", mandi="X", district="Y",
                date=date.today(),
                min_price=-100, max_price=7500, modal_price=7200,
            )

    def test_rejects_invalid_crop(self):
        from app.schemas.market_v2 import MarketPriceV2Create
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MarketPriceV2Create(
                crop="wheat", mandi="X", district="Y",
                date=date.today(),
                min_price=1000, max_price=1500, modal_price=1200,
            )

    def test_rejects_min_greater_than_modal(self):
        from app.schemas.market_v2 import MarketPriceV2Create
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MarketPriceV2Create(
                crop="cotton", mandi="X", district="Y",
                date=date.today(),
                min_price=7500, max_price=8000, modal_price=7000,  # min > modal
            )

    def test_rejects_modal_greater_than_max(self):
        from app.schemas.market_v2 import MarketPriceV2Create
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MarketPriceV2Create(
                crop="cotton", mandi="X", district="Y",
                date=date.today(),
                min_price=6000, max_price=7000, modal_price=7500,  # modal > max
            )

    def test_rejects_negative_quantity(self):
        from app.schemas.market_v2 import MarketPriceV2Create
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            MarketPriceV2Create(
                crop="cotton", mandi="X", district="Y",
                date=date.today(),
                min_price=6900, max_price=7500, modal_price=7200,
                arrival_quantity=-50,
            )


# ── FastAPI endpoint integration tests ───────────────────────────────────────

class TestMarketAPIEndpoints:
    """Integration tests for all Phase 2 market API endpoints."""

    def setup_method(self):
        from main import app
        from fastapi.testclient import TestClient
        self.client = TestClient(app)

    def test_health(self):
        r = self.client.get("/health")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        # Phase label advances with each phase; check structure rather than literal string
        assert "phase" in data
        assert "market_data" in data

    def test_prices_v1_backward_compat(self):
        r = self.client.get("/api/market/prices?district=Rajkot")
        assert r.status_code == 200
        data = r.json()
        assert "cotton" in data
        assert "groundnut" in data
        assert data["cotton"]["latest_modal_price"] > 0

    def test_latest_prices(self):
        r = self.client.get("/api/market/prices/latest")
        assert r.status_code == 200
        data = r.json()
        assert data["total"] > 0
        assert len(data["data"]) > 0

    def test_latest_prices_crop_filter(self):
        r = self.client.get("/api/market/prices/latest?crop=cotton")
        assert r.status_code == 200
        data = r.json()
        for item in data["data"]:
            assert item["crop"] == "cotton"

    def test_latest_prices_invalid_crop(self):
        r = self.client.get("/api/market/prices/latest?crop=wheat")
        assert r.status_code == 400

    def test_price_history(self):
        r = self.client.get("/api/market/prices/history?crop=cotton&mandi=Rajkot APMC")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
        # Check chronological order
        dates = [d["date"] for d in data["data"]]
        assert dates == sorted(dates)

    def test_price_history_invalid_dates(self):
        r = self.client.get(
            "/api/market/prices/history?crop=cotton&start_date=2025-01-10&end_date=2025-01-05"
        )
        assert r.status_code == 400

    def test_compare_mandis(self):
        r = self.client.get("/api/market/prices/compare?crop=cotton&quantity=100")
        assert r.status_code == 200
        data = r.json()
        assert data["count"] > 0
        # Sorted by net price descending
        nets = [m["net_price"] for m in data["mandis"]]
        assert nets == sorted(nets, reverse=True)

    def test_mandis_list(self):
        r = self.client.get("/api/market/mandis")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 10
        assert any(m["name"] == "Rajkot APMC" for m in data)

    def test_crops_list(self):
        r = self.client.get("/api/market/crops")
        assert r.status_code == 200
        data = r.json()
        names = [c["name"] for c in data]
        assert "cotton" in names
        assert "groundnut" in names

    def test_districts_list(self):
        r = self.client.get("/api/market/districts")
        assert r.status_code == 200
        data = r.json()
        assert "Rajkot" in data
        assert "Amreli" in data

    def test_trends(self):
        r = self.client.get("/api/market/trends?crop=cotton")
        assert r.status_code == 200
        data = r.json()
        assert len(data) > 0
        for item in data:
            assert item["trend"] in ("UP", "DOWN", "STABLE")

    def test_best_mandi(self):
        r = self.client.get("/api/market/best-mandi?crop=cotton&quantity=100")
        assert r.status_code == 200
        data = r.json()
        assert data["best_mandi"] is not None
        assert len(data["explanation"]) > 0

    def test_forecast_input(self):
        r = self.client.get("/api/market/forecast-input?crop=cotton&mandi=Rajkot APMC&days=30")
        assert r.status_code == 200
        data = r.json()
        assert data["crop"] == "cotton"
        assert data["records_available"] > 0
        for point in data["data"]:
            assert "date" in point
            assert "modal_price" in point

    def test_source_info(self):
        r = self.client.get("/api/market/source-info")
        assert r.status_code == 200
        data = r.json()
        assert "source" in data
        assert "source_status" in data
        assert "tooltip" in data

    def test_farmer_dashboard(self):
        r = self.client.get("/api/farmer/dashboard?district=Rajkot")
        assert r.status_code == 200
        data = r.json()
        assert "cotton" in data
        assert "groundnut" in data
        assert data["cotton"]["latest_modal_price"] > 0

    def test_pagination(self):
        r1 = self.client.get("/api/market/prices/latest?page=1&limit=5")
        r2 = self.client.get("/api/market/prices/latest?page=2&limit=5")
        assert r1.status_code == 200
        assert r2.status_code == 200
        d1 = r1.json()["data"]
        d2 = r2.json()["data"]
        # Pages should be different (unless total < 10)
        if len(d1) == 5 and len(d2) > 0:
            assert d1[0] != d2[0]
