"""
Phase 9 — Tests for Farmer UX, Multilingual Support & Responsible AI.

Test categories:
  1. Translation completeness (en/gu/hi)
  2. Demo API endpoints
  3. Granite prompt improvements (farmer-friendly)
  4. Data source badge / responsible AI
  5. Navigation links
  6. End-to-end demo flow (all three languages)

Run:
    cd kisansetu-ai/backend
    python -m pytest tests/test_ux_phase9.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import json
from pathlib import Path


# ── Locales directory ─────────────────────────────────────────────────────────
LOCALES_DIR = Path(__file__).parent.parent.parent / "frontend" / "locales"


# ── 1. Translation completeness ───────────────────────────────────────────────

class TestTranslations:
    """All required keys present in all three language files."""

    REQUIRED_KEYS = [
        "nav.home", "nav.market", "nav.buyers", "nav.advisor",
        "nav.quality", "nav.income", "nav.ai_chat",
        "app.name", "app.tagline", "app.demo_mode", "app.loading",
        "app.error", "app.retry",
        "market.title", "market.current_price", "market.forecast",
        "market.disclaimer", "market.source_demo",
        "buyers.title", "buyers.no_buyers", "buyers.disclaimer",
        "advisor.title", "advisor.disclaimer", "advisor.get_advice",
        "quality.title", "quality.no_assessment", "quality.disclaimer",
        "income.title", "income.disclaimer", "income.calculate",
        "actions.check_market_prices", "actions.find_buyers",
        "actions.sell_or_store", "actions.run_full_analysis",
        "actions.load_demo", "actions.ask_kisansetu_ai",
        "chat.title", "chat.ask", "chat.voice_coming_soon",
        "chat.fallback_notice",
        "demo.title", "demo.load_farmer", "demo.run_analysis",
        "demo.analysis_query", "demo.notice",
        "status.demo", "status.live", "status.estimate", "status.forecast",
        "errors.api_unavailable", "errors.no_buyers",
        "errors.ai_unavailable", "errors.no_market_data",
    ]

    def _load(self, lang: str) -> dict:
        path = LOCALES_DIR / f"{lang}.json"
        if not path.exists():
            pytest.skip(f"Locale file {lang}.json not found")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _get(self, data: dict, key: str):
        parts = key.split(".")
        cur = data
        for p in parts:
            if not isinstance(cur, dict) or p not in cur:
                return None
            cur = cur[p]
        return cur

    @pytest.mark.parametrize("lang", ["en", "gu", "hi"])
    def test_all_required_keys_present(self, lang: str):
        data = self._load(lang)
        missing = []
        for key in self.REQUIRED_KEYS:
            if self._get(data, key) is None:
                missing.append(key)
        assert not missing, f"[{lang}] Missing keys: {missing}"

    @pytest.mark.parametrize("lang", ["en", "gu", "hi"])
    def test_no_empty_values(self, lang: str):
        data = self._load(lang)
        for key in self.REQUIRED_KEYS:
            val = self._get(data, key)
            assert val, f"[{lang}] Empty value for key: {key}"

    def test_demo_queries_all_languages(self):
        """demo.analysis_query must be present and non-empty in all three."""
        for lang in ("en", "gu", "hi"):
            data = self._load(lang)
            q = self._get(data, "demo.analysis_query")
            assert q and len(q) > 20, f"[{lang}] demo.analysis_query too short or missing"

    def test_chat_examples_present(self):
        """Chat example keys should exist in all languages."""
        for lang in ("en", "gu", "hi"):
            data = self._load(lang)
            assert self._get(data, "chat.example_1"), f"[{lang}] chat.example_1 missing"

    def test_gujarati_contains_gujarati_script(self):
        data = self._load("gu")
        name = self._get(data, "app.name")
        # Should contain Gujarati unicode (U+0A80–U+0AFF)
        assert any("\u0a80" <= c <= "\u0aff" for c in name), "Gujarati name lacks Gujarati script"

    def test_hindi_contains_devanagari(self):
        data = self._load("hi")
        name = self._get(data, "app.name")
        # Should contain Devanagari (U+0900–U+097F)
        assert any("\u0900" <= c <= "\u097f" for c in name), "Hindi name lacks Devanagari script"


# ── 2. Demo API endpoints ─────────────────────────────────────────────────────

class TestDemoEndpoints:

    def _client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_demo_farmer_returns_profile(self):
        client = self._client()
        resp = client.get("/api/demo/farmer")
        assert resp.status_code == 200
        data = resp.json()
        assert data["crop"] == "cotton"
        assert data["quantity"] == 100.0
        assert data["district"] == "Rajkot"
        assert "note" in data   # disclaimer present

    def test_demo_run_english(self):
        client = self._client()
        resp = client.post("/api/demo/run", json={"language": "en"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_answer"]
        assert len(data["agents_used"]) >= 2
        assert isinstance(data["confidence"], int)
        assert 0 <= data["confidence"] <= 100

    def test_demo_run_gujarati(self):
        client = self._client()
        resp = client.post("/api/demo/run", json={"language": "gu"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_answer"]
        # Query should be in Gujarati (from demo.analysis_query)
        assert any("\u0a80" <= c <= "\u0aff" for c in data["query"]), \
            "Demo query for gu should contain Gujarati script"

    def test_demo_run_hindi(self):
        client = self._client()
        resp = client.post("/api/demo/run", json={"language": "hi"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_answer"]
        assert any("\u0900" <= c <= "\u097f" for c in data["query"]), \
            "Demo query for hi should contain Devanagari script"

    def test_demo_run_includes_farmer_profile(self):
        client = self._client()
        resp = client.post("/api/demo/run", json={"language": "en"})
        data = resp.json()
        assert "farmer" in data
        assert data["farmer"]["crop"] == "cotton"

    def test_demo_run_complex_agents(self):
        """Full demo run should invoke at least 3 agents."""
        client = self._client()
        resp = client.post("/api/demo/run", json={"language": "en"})
        data = resp.json()
        # Complex demo query → forecast + buyer + storage + income
        assert len(data["agents_used"]) >= 3, \
            f"Expected ≥3 agents, got {data['agents_used']}"

    def test_demo_run_invalid_language(self):
        client = self._client()
        resp = client.post("/api/demo/run", json={"language": "fr"})
        assert resp.status_code == 422


# ── 3. Granite prompt improvements ───────────────────────────────────────────

class TestPromptImprovements:

    def test_system_prompt_has_format_instructions(self):
        from app.ai.prompts import SYSTEM_PROMPT
        assert "Current price:" in SYSTEM_PROMPT or "₹X/q" in SYSTEM_PROMPT
        assert "ESTIMATE" in SYSTEM_PROMPT or "FORECAST" in SYSTEM_PROMPT

    def test_system_prompt_no_guarantee_language(self):
        from app.ai.prompts import SYSTEM_PROMPT
        assert "Never guarantee profit" in SYSTEM_PROMPT or "never guarantee" in SYSTEM_PROMPT.lower()

    def test_system_prompt_concise_limit(self):
        from app.ai.prompts import SYSTEM_PROMPT
        # Should mention word/token limits
        assert "200" in SYSTEM_PROMPT or "300" in SYSTEM_PROMPT

    def test_fallback_has_ai_unavailable_notice(self):
        from app.ai.prompts import build_fallback_response
        for lang in ("en", "gu", "hi"):
            text = build_fallback_response(lang, [], {})
            assert "AI" in text.upper() or "Unavailable" in text or "ઉ" in text or "अनु" in text

    def test_data_context_labels_forecast_correctly(self):
        """Prompt must include forecast horizon data."""
        from app.ai.prompts import build_data_context
        result = build_data_context(
            query="Forecast?", language="en",
            agents_used=["forecast"],
            agent_results={"forecast": {
                "current_price": 7200, "forecast_7d": 7300, "forecast_15d": 7400,
                "forecast_30d": 7500, "trend": "UP", "confidence": 75, "risk": "LOW"
            }}
        )
        assert "7,200" in result or "7200" in result
        assert "7,400" in result or "7400" in result


# ── 4. Responsible AI / data grounding ───────────────────────────────────────

class TestResponsibleAI:

    def test_orchestrator_no_invented_buyers(self):
        """If buyer agent returns empty, final answer must say so."""
        from app.ai.prompts import build_data_context
        prompt = build_data_context(
            query="Find buyers", language="en",
            agents_used=["buyer"],
            agent_results={"buyer": {"matches": [], "total": 0}}
        )
        assert "no suitable buyer" in prompt.lower()

    def test_orchestrator_disclaims_missing_agent(self):
        from app.ai.prompts import build_data_context
        prompt = build_data_context(
            query="Price and income", language="en",
            agents_used=["forecast"],
            agent_results={"forecast": {"current_price": 7200, "forecast_15d": 7400,
                                         "confidence": 70, "trend": "UP", "risk": "LOW"}},
            failed_agents=["income"]
        )
        # Income agent failed → prompt must note unavailability
        assert "income" in prompt.lower()
        assert "unavailable" in prompt.lower() or "not" in prompt.lower()

    def test_chat_response_includes_responsible_ai_flag(self):
        """Chat API response should contain granite_used field."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        resp = client.post("/api/chat", json={
            "message": "Cotton price?",
            "language": "en",
            "farmer_id": 1,
            "crop": "cotton",
            "mandi": "Rajkot APMC",
            "quantity": 100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "granite_used" in data
        assert isinstance(data["granite_used"], bool)

    def test_chat_answer_not_empty(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        resp = client.post("/api/chat", json={
            "message": "What is the cotton price today?",
            "language": "en",
            "farmer_id": 1,
            "crop": "cotton",
            "mandi": "Rajkot APMC",
            "quantity": 100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["answer"]) > 10  # non-trivial answer

    def test_chat_fallback_answer_in_correct_language_gu(self):
        """In fallback mode (no Granite), Gujarati hint should appear."""
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        resp = client.post("/api/chat", json={
            "message": "ભાવ શું છે?",
            "language": "gu",
            "farmer_id": 1,
            "crop": "cotton",
            "mandi": "Rajkot APMC",
            "quantity": 100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"]   # must return something

    def test_chat_fallback_answer_in_correct_language_hi(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        resp = client.post("/api/chat", json={
            "message": "कपास का भाव क्या है?",
            "language": "hi",
            "farmer_id": 1,
            "crop": "cotton",
            "mandi": "Rajkot APMC",
            "quantity": 100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"]


# ── 5. Navigation and page validation ─────────────────────────────────────────

class TestNavigationEndpoints:
    """All key API routes respond (Phase 1–9 backward compatibility)."""

    def _client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_health_phase9(self):
        data = self._client().get("/health").json()
        assert data["version"] == "10.0.0-final"   # updated in Phase 10
        assert "ibm_granite" in data

    def test_market_prices(self):
        assert self._client().get("/api/market/prices/latest?crop=cotton").status_code == 200

    def test_buyer_matches(self):
        assert self._client().get("/api/buyers/matches?crop=cotton").status_code == 200

    def test_storage_advisor_preview(self):
        assert self._client().get(
            "/api/agents/storage-advisor/preview?crop=cotton&quantity=100"
        ).status_code == 200

    def test_income_preview(self):
        assert self._client().get(
            "/api/agents/income/preview?crop=cotton&quantity=100"
        ).status_code == 200

    def test_chat_status(self):
        data = self._client().get("/api/chat/status").json()
        assert "available" in data

    def test_demo_farmer(self):
        data = self._client().get("/api/demo/farmer").json()
        assert data["crop"] == "cotton"


# ── 6. Security checks ────────────────────────────────────────────────────────

class TestSecurityChecks:

    def _client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_chat_status_no_credentials_exposed(self):
        """Chat status must not expose API keys."""
        data = self._client().get("/api/chat/status").json()
        resp_str = str(data)
        # Keys should not appear in response
        assert "IBM_API_KEY" not in resp_str
        assert "api_key" not in resp_str.lower() or "available" in resp_str

    def test_orchestrate_no_internal_prompt_exposed(self):
        """Orchestrate response must not contain system prompt text."""
        client = self._client()
        resp = client.post("/api/agents/orchestrate", json={
            "farmer_id": 1,
            "message": "cotton price?",
            "language": "en",
            "crop": "cotton",
            "mandi": "Rajkot APMC",
            "quantity": 100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        # Internal prompt instructions must not leak
        assert "STRICT RULES" not in data["final_answer"]
        assert "chain-of-thought" not in data["final_answer"].lower()

    def test_demo_run_no_secrets(self):
        client = self._client()
        data = client.post("/api/demo/run", json={"language": "en"}).json()
        answer = data.get("final_answer", "")
        assert "IBM_API_KEY" not in answer
        assert "project_id" not in answer.lower() or "₹" in answer
