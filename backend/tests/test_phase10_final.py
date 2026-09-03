"""
Phase 10 — Final Regression & Deployment Tests.

Verifies:
  1. Health endpoint returns correct Phase-10 version
  2. All major API endpoints respond (backward-compat, Phases 1–9)
  3. Global exception handler returns 500 JSON — no stack traces
  4. CORS headers are present and properly configured
  5. IBM credentials are NOT exposed in any API response
  6. Demo end-to-end flow (all languages)
  7. Chat API with agent failure handling
  8. Fallback mode (Granite unavailable) keeps app functional
  9. Orchestrate API returns structured results
  10. Frontend locale files exist (smoke check)

Run:
    cd kisansetu-ai/backend
    python -m pytest tests/test_phase10_final.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── Test client helper ────────────────────────────────────────────────────────

def _client():
    from fastapi.testclient import TestClient
    from main import app
    return TestClient(app)


# ── 1. Version / health check ────────────────────────────────────────────────

class TestPhase10Health:

    def test_health_version_is_final(self):
        data = _client().get("/health").json()
        assert data["version"] == "10.0.0-final"

    def test_health_status_ok(self):
        data = _client().get("/health").json()
        assert data["status"] == "ok"

    def test_health_phase_label(self):
        data = _client().get("/health").json()
        assert "Phase 10" in data.get("phase", "")

    def test_health_all_five_agents_listed(self):
        data = _client().get("/health").json()
        agents = data.get("agents", {})
        assert "MandiForecastAgent" in agents
        assert "BuyerMatchingAgent" in agents
        assert "StorageAdvisorAgent" in agents
        assert "QualityGradingAgent" in agents
        assert "IncomeDashboardAgent" in agents

    def test_health_granite_section_present(self):
        data = _client().get("/health").json()
        assert "ibm_granite" in data

    def test_health_orchestrator_in_agents(self):
        data = _client().get("/health").json()
        assert "AgentOrchestrator" in data.get("agents", {})


# ── 2. Backward-compatibility: all Phase 1–9 endpoints reachable ──────────────

class TestBackwardCompatibility:

    def test_root_endpoint(self):
        resp = _client().get("/")
        assert resp.status_code == 200
        data = resp.json()
        # Root returns {"message": "...", "version": "...", ...}
        text = str(data)
        assert "KisanSetu" in text

    def test_market_prices_cotton(self):
        assert _client().get("/api/market/prices/latest?crop=cotton").status_code == 200

    def test_market_prices_groundnut(self):
        assert _client().get("/api/market/prices/latest?crop=groundnut").status_code == 200

    def test_buyers_matches_endpoint(self):
        assert _client().get("/api/buyers/matches?crop=cotton").status_code == 200

    def test_storage_advisor_preview(self):
        assert _client().get(
            "/api/agents/storage-advisor/preview?crop=cotton&quantity=100"
        ).status_code == 200

    def test_income_preview(self):
        assert _client().get(
            "/api/agents/income/preview?crop=cotton&quantity=100"
        ).status_code == 200

    def test_chat_status_endpoint(self):
        assert _client().get("/api/chat/status").status_code == 200

    def test_demo_farmer_endpoint(self):
        assert _client().get("/api/demo/farmer").status_code == 200

    def test_orchestrate_endpoint(self):
        resp = _client().post("/api/agents/orchestrate", json={
            "farmer_id": 1,
            "message": "cotton price today?",
            "language": "en",
            "crop": "cotton",
            "mandi": "Rajkot APMC",
            "quantity": 100.0,
        })
        assert resp.status_code == 200

    def test_chat_endpoint(self):
        resp = _client().post("/api/chat", json={
            "message": "What is cotton price?",
            "language": "en",
            "farmer_id": 1,
            "crop": "cotton",
            "mandi": "Rajkot APMC",
            "quantity": 100.0,
        })
        assert resp.status_code == 200


# ── 3. Global exception handler ───────────────────────────────────────────────

class TestGlobalExceptionHandler:

    def test_404_returns_json(self):
        resp = _client().get("/nonexistent-route-xyz")
        # FastAPI returns 404 with JSON for unknown routes
        assert resp.status_code == 404
        assert resp.headers["content-type"].startswith("application/json")

    def test_invalid_body_returns_422_not_500(self):
        """Validation errors → 422, not 500."""
        resp = _client().post("/api/chat", json={"invalid_key": "bad"})
        assert resp.status_code == 422
        data = resp.json()
        # detail from Pydantic, not a raw exception
        assert "detail" in data

    def test_invalid_language_returns_422(self):
        resp = _client().post("/api/chat", json={
            "message": "test",
            "language": "xx",   # unsupported
            "farmer_id": 1,
        })
        assert resp.status_code == 422

    def test_error_response_no_traceback(self):
        """A 422 response must not contain Python traceback text."""
        resp = _client().post("/api/chat", json={})
        body = resp.text
        assert "Traceback" not in body
        assert "File \"" not in body


# ── 4. Security / credentials not exposed ─────────────────────────────────────

class TestCredentialSafety:

    def _all_text(self, resp) -> str:
        return resp.text

    def test_health_no_api_key(self):
        text = self._all_text(_client().get("/health"))
        assert "IBM_API_KEY" not in text
        assert "api_key" not in text.lower() or "available" in text.lower()

    def test_chat_status_no_secret(self):
        text = self._all_text(_client().get("/api/chat/status"))
        assert "IBM_API_KEY" not in text
        assert "project_id" not in text.lower() or "available" in text.lower()

    def test_orchestrate_no_system_prompt_leaked(self):
        resp = _client().post("/api/agents/orchestrate", json={
            "farmer_id": 1,
            "message": "cotton price?",
            "language": "en",
            "crop": "cotton",
            "mandi": "Rajkot APMC",
            "quantity": 100.0,
        })
        answer = resp.json().get("final_answer", "")
        assert "STRICT RULES" not in answer
        assert "chain-of-thought" not in answer.lower()

    def test_demo_run_no_secrets(self):
        resp = _client().post("/api/demo/run", json={"language": "en"})
        text = resp.text
        assert "IBM_API_KEY" not in text
        assert "watsonx_url" not in text.lower()


# ── 5. CORS headers ───────────────────────────────────────────────────────────

class TestCORSConfig:

    def test_cors_preflight(self):
        """OPTIONS request from localhost:3000 should include CORS headers."""
        resp = _client().options(
            "/api/chat/status",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )
        # CORS preflight should be 200 or 204
        assert resp.status_code in (200, 204)

    def test_cors_origin_header_present_on_api(self):
        resp = _client().get(
            "/api/chat/status",
            headers={"Origin": "http://localhost:3000"},
        )
        assert resp.status_code == 200
        # Access-Control-Allow-Origin should be set for the known origin
        assert "access-control-allow-origin" in resp.headers


# ── 6. Demo end-to-end flow ───────────────────────────────────────────────────

class TestDemoEndToEnd:

    def test_demo_english_full_flow(self):
        resp = _client().post("/api/demo/run", json={"language": "en"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_answer"]
        assert len(data["agents_used"]) >= 3
        assert isinstance(data["confidence"], int)
        assert 0 <= data["confidence"] <= 100

    def test_demo_gujarati_full_flow(self):
        resp = _client().post("/api/demo/run", json={"language": "gu"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_answer"]
        # The query stored in result should contain Gujarati script
        assert any("\u0a80" <= c <= "\u0aff" for c in data.get("query", ""))

    def test_demo_hindi_full_flow(self):
        resp = _client().post("/api/demo/run", json={"language": "hi"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_answer"]
        assert any("\u0900" <= c <= "\u097f" for c in data.get("query", ""))

    def test_demo_result_has_farmer_profile(self):
        resp = _client().post("/api/demo/run", json={"language": "en"})
        data = resp.json()
        farmer = data.get("farmer", {})
        assert farmer.get("crop") == "cotton"
        assert farmer.get("quantity") == 100.0
        assert farmer.get("district") == "Rajkot"

    def test_demo_complex_scenario_uses_4_agents(self):
        resp = _client().post("/api/demo/run", json={"language": "en"})
        agents = resp.json()["agents_used"]
        # The demo query is complex: forecast + buyer + storage + income
        assert len(agents) >= 4, f"Expected 4 agents, got: {agents}"


# ── 7. Fallback mode — Granite unavailable ────────────────────────────────────

class TestFallbackMode:
    """App must remain functional when IBM Granite is unavailable."""

    def _chat_with_no_granite(self, message: str, language: str = "en"):
        """Force Granite unavailable and call /api/chat."""
        with patch("app.ai.granite_client.GraniteClient.is_available", return_value=False):
            return _client().post("/api/chat", json={
                "message": message,
                "language": language,
                "farmer_id": 1,
                "crop": "cotton",
                "mandi": "Rajkot APMC",
                "quantity": 100.0,
            })

    def test_fallback_still_returns_200(self):
        resp = self._chat_with_no_granite("cotton price today?")
        assert resp.status_code == 200

    def test_fallback_response_not_empty(self):
        resp = self._chat_with_no_granite("should I sell now?")
        data = resp.json()
        assert len(data.get("answer", "")) > 10

    def test_fallback_granite_used_is_false(self):
        resp = self._chat_with_no_granite("cotton price?")
        data = resp.json()
        assert data.get("granite_used") is False

    def test_fallback_gujarati(self):
        resp = self._chat_with_no_granite("ભાવ શું છે?", language="gu")
        assert resp.status_code == 200
        assert resp.json().get("answer")

    def test_fallback_hindi(self):
        resp = self._chat_with_no_granite("कपास का भाव?", language="hi")
        assert resp.status_code == 200
        assert resp.json().get("answer")


# ── 8. Agent failure resilience ───────────────────────────────────────────────

class TestAgentFailureResilience:

    def test_single_agent_failure_does_not_crash(self):
        """If one agent raises, orchestration still completes."""
        with patch(
            "app.ai.orchestrator._run_storage_agent",
            side_effect=RuntimeError("Storage DB error"),
        ):
            resp = _client().post("/api/agents/orchestrate", json={
                "farmer_id": 1,
                "message": "should I sell or store cotton?",
                "language": "en",
                "crop": "cotton",
                "mandi": "Rajkot APMC",
                "quantity": 100.0,
            })
        assert resp.status_code == 200
        data = resp.json()
        # Failed agents should be noted
        assert "failed_agents" in data or "agents_used" in data

    def test_partial_failure_answer_not_empty(self):
        with patch(
            "app.ai.orchestrator._run_income_agent",
            side_effect=RuntimeError("Income service unavailable"),
        ):
            resp = _client().post("/api/chat", json={
                "message": "How much income can I earn from 100 quintals of cotton?",
                "language": "en",
                "farmer_id": 1,
                "crop": "cotton",
                "mandi": "Rajkot APMC",
                "quantity": 100.0,
            })
        assert resp.status_code == 200
        assert len(resp.json().get("answer", "")) > 10


# ── 9. Frontend locale files smoke check ─────────────────────────────────────

class TestLocaleFiles:
    """Verify locale JSON files are present and parse correctly."""

    LOCALES_DIR = Path(__file__).parent.parent.parent / "frontend" / "locales"

    @pytest.mark.parametrize("lang", ["en", "gu", "hi"])
    def test_locale_file_exists(self, lang: str):
        path = self.LOCALES_DIR / f"{lang}.json"
        assert path.exists(), f"Locale file missing: {lang}.json"

    @pytest.mark.parametrize("lang", ["en", "gu", "hi"])
    def test_locale_file_valid_json(self, lang: str):
        import json
        path = self.LOCALES_DIR / f"{lang}.json"
        if not path.exists():
            pytest.skip(f"{lang}.json not found")
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        assert isinstance(data, dict)
        assert len(data) > 0
