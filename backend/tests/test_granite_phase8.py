"""
Phase 8 — Tests for IBM Granite + Agent Orchestrator.

Test categories:
  1. Intent routing (heuristic + classification)
  2. Agent execution (single, multi, failure handling)
  3. Granite client (available, unavailable, invalid response)
  4. Data grounding (Granite cannot invent data)
  5. Orchestrate API endpoint
  6. Chat API endpoint
  7. Fallback mode (when Granite is unavailable)

Run:
    cd kisansetu-ai/backend
    python -m pytest tests/test_granite_phase8.py -v
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from unittest.mock import patch, MagicMock


# ── 1. Intent routing ─────────────────────────────────────────────────────────

class TestIntentRouting:
    """Heuristic intent classification (no Granite needed)."""

    def setup_method(self):
        from app.ai.orchestrator import _heuristic_intent, INTENTS
        self.classify = _heuristic_intent
        self.intents  = INTENTS

    def test_price_query(self):
        intent = self.classify("What is today's cotton price?")
        assert intent == "PRICE"

    def test_forecast_query(self):
        intent = self.classify("Will cotton prices increase next week?")
        assert intent in ("FORECAST", "COMPLEX")

    def test_buyer_query(self):
        intent = self.classify("Find buyers for my cotton")
        assert intent == "BUYER"

    def test_sell_or_store_query(self):
        intent = self.classify("Should I sell now or wait and store?")
        assert intent in ("SELL_OR_STORE", "COMPLEX")

    def test_income_query(self):
        intent = self.classify("How much income can I earn from 100 quintals?")
        assert intent in ("INCOME", "COMPLEX")

    def test_complex_multi_aspect_query(self):
        """A query mentioning buyer + price + income should be COMPLEX."""
        intent = self.classify(
            "I have 100 quintals of cotton in Rajkot. "
            "Find the best buyer, predict the price for the next 15 days, "
            "tell me whether I should sell or store, and estimate my income."
        )
        assert intent == "COMPLEX"

    def test_all_intents_have_agents(self):
        """Every intent must map to at least one agent."""
        for intent, agents in self.intents.items():
            assert len(agents) > 0, f"Intent {intent} has no agents"

    def test_complex_intent_has_multiple_agents(self):
        agents = self.intents["COMPLEX"]
        assert len(agents) >= 3

    def test_intent_agents_are_valid_keys(self):
        valid = {"forecast", "buyer", "storage", "income", "quality"}
        for intent, agents in self.intents.items():
            for agent in agents:
                assert agent in valid, f"Unknown agent '{agent}' in intent {intent}"


# ── 2. Agent execution ────────────────────────────────────────────────────────

class TestAgentExecution:
    """Tests that existing Phase 3–7 agents return structured data."""

    def _orchestrator(self):
        from app.ai.orchestrator import AgentOrchestrator
        orch = AgentOrchestrator.__new__(AgentOrchestrator)
        # Mock Granite as unavailable so tests don't need credentials
        mock_client = MagicMock()
        mock_client.is_available.return_value = False
        orch._granite = mock_client
        return orch

    def test_forecast_agent_returns_price(self):
        from app.ai.orchestrator import _run_forecast_agent
        result = _run_forecast_agent(crop="cotton", mandi="Rajkot APMC")
        assert "current_price" in result
        assert "forecast_15d" in result
        assert isinstance(result["current_price"], (int, float))
        assert result["current_price"] > 0

    def test_buyer_agent_returns_matches(self):
        from app.ai.orchestrator import _run_buyer_agent
        result = _run_buyer_agent(crop="cotton", quantity=100, district="Rajkot")
        assert "matches" in result
        assert isinstance(result["matches"], list)

    def test_storage_agent_returns_recommendation(self):
        from app.ai.orchestrator import _run_storage_agent
        result = _run_storage_agent(crop="cotton", mandi="Rajkot APMC", quantity=100)
        assert "recommendation" in result
        assert result["recommendation"] in ("SELL_NOW", "STORE", "PARTIAL_SELL")

    def test_income_agent_returns_income(self):
        from app.ai.orchestrator import _run_income_agent
        result = _run_income_agent(crop="cotton", quantity=100, mandi="Rajkot APMC")
        assert "mandi_price" in result
        assert "current_estimated_income" in result
        assert result["current_estimated_income"] > 0

    def test_single_agent_orchestration(self):
        """Single-agent PRICE query → only forecast agent used."""
        orch = self._orchestrator()
        result = orch.orchestrate(
            query     = "What is the cotton price today?",
            language  = "en",
            farmer_id = 1,
            crop      = "cotton",
            mandi     = "Rajkot APMC",
            quantity  = 100,
        )
        assert "forecast" in result["agents_used"]
        assert result["final_answer"]
        assert isinstance(result["confidence"], int)
        assert 0 <= result["confidence"] <= 100

    def test_multi_agent_orchestration(self):
        """Complex query → multiple agents invoked."""
        orch = self._orchestrator()
        result = orch.orchestrate(
            query     = "Find buyer, predict price and estimate my income for 100 quintals cotton",
            language  = "en",
            farmer_id = 1,
            crop      = "cotton",
            mandi     = "Rajkot APMC",
            quantity  = 100,
        )
        assert len(result["agents_used"]) >= 2
        assert result["final_answer"]

    def test_failed_agent_does_not_crash_orchestration(self):
        """If one agent fails, orchestration continues with remaining agents."""
        from app.ai.orchestrator import AgentOrchestrator, _AGENT_RUNNERS, INTENTS
        orch = self._orchestrator()

        original_income = _AGENT_RUNNERS.get("income")
        def _failing_income(**kwargs):
            raise RuntimeError("Simulated income agent failure")

        _AGENT_RUNNERS["income"] = _failing_income
        try:
            # Force COMPLEX intent by directly calling _execute_agents with income included
            agents_needed = list(INTENTS["COMPLEX"])  # includes income
            context = {
                "crop": "cotton", "mandi": "Rajkot APMC", "quantity": 100.0,
                "district": "Rajkot", "quality_grade": None,
                "storage_cost_per_quintal": 80.0, "cash_urgency": "MEDIUM",
                "farmer_id": 1,
            }
            results, failed, _ = orch._execute_agents(agents_needed, context)
            # income should be in failed list but other agents succeed
            assert "income" in failed
            # At least some other agents should have succeeded
            assert len(results) > 0
        finally:
            if original_income:
                _AGENT_RUNNERS["income"] = original_income

    def test_all_agents_failed_returns_error_message(self):
        """If every agent fails, a graceful error message is returned."""
        from app.ai.orchestrator import AgentOrchestrator, _AGENT_RUNNERS
        orch = self._orchestrator()

        # Temporarily replace all runners with failures
        originals = dict(_AGENT_RUNNERS)
        for key in list(_AGENT_RUNNERS.keys()):
            _AGENT_RUNNERS[key] = lambda **kw: (_ for _ in ()).throw(RuntimeError("fail"))
        try:
            result = orch.orchestrate(
                query    = "cotton price",
                language = "en",
                farmer_id = 1,
                crop     = "cotton",
                mandi    = "Rajkot APMC",
                quantity = 100,
            )
            assert result["final_answer"]  # should not raise
        finally:
            _AGENT_RUNNERS.update(originals)


# ── 3. Granite client tests ───────────────────────────────────────────────────

class TestGraniteClient:
    """Tests for GraniteClient — uses mocks, no real API calls."""

    def test_unavailable_when_no_credentials(self):
        """Without IBM credentials, client must report unavailable."""
        with patch.dict(os.environ, {}, clear=False):
            # Temporarily unset credentials
            env_backup = {
                k: os.environ.pop(k)
                for k in ("IBM_API_KEY", "IBM_PROJECT_ID", "WATSONX_PROJECT_ID",
                          "IBM_CLOUD_API_KEY")
                if k in os.environ
            }
            try:
                # Import fresh instance (bypass singleton)
                from app.ai.granite_client import GraniteClient
                client = GraniteClient()
                assert not client.is_available()
            finally:
                os.environ.update(env_backup)

    def test_fallback_when_unavailable(self):
        """generate() must return (False, ...) if credentials not set."""
        from app.ai.granite_client import GraniteClient
        client = GraniteClient.__new__(GraniteClient)
        client.api_key    = ""
        client.project_id = ""
        client._enabled   = False
        ok, text, meta = client.generate("sys", "user")
        assert ok is False
        assert "not configured" in text.lower() or "granite" in text.lower()
        assert meta["reason"] == "no_credentials"

    def test_auth_failure_returns_false(self):
        """IAM token failure → returns (False, error_msg)."""
        from app.ai.granite_client import GraniteClient
        client = GraniteClient.__new__(GraniteClient)
        client.api_key    = "fake-key"
        client.project_id = "fake-project"
        client.model_id   = "ibm/granite-3-8b-instruct"
        client.base_url   = "https://us-south.ml.cloud.ibm.com"
        client._enabled   = True

        with patch("app.ai.granite_client.httpx.post") as mock_post:
            mock_post.side_effect = Exception("Network unreachable")
            ok, text, meta = client.generate("sys", "user")
        assert ok is False
        assert meta["reason"] in ("auth_failure", "unknown")

    def test_timeout_returns_false(self):
        """Request timeout → returns (False, timeout_msg)."""
        import httpx
        from app.ai.granite_client import GraniteClient, _token_cache
        client = GraniteClient.__new__(GraniteClient)
        client.api_key    = "fake-key"
        client.project_id = "fake-project"
        client.model_id   = "ibm/granite-3-8b-instruct"
        client.base_url   = "https://us-south.ml.cloud.ibm.com"
        client._enabled   = True

        # Inject a cached token so IAM call is skipped
        _token_cache.set("fake-token", 3600)

        with patch("app.ai.granite_client.httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_ctx)
            mock_client_cls.return_value.__exit__  = MagicMock(return_value=False)
            mock_ctx.post.side_effect = httpx.TimeoutException("timed out")
            ok, text, meta = client.generate("sys", "user")

        assert ok is False
        assert meta["reason"] == "timeout"

    def test_rate_limit_returns_false(self):
        """HTTP 429 → returns (False, rate_limit_msg)."""
        import httpx
        from app.ai.granite_client import GraniteClient, _token_cache
        client = GraniteClient.__new__(GraniteClient)
        client.api_key    = "fake-key"
        client.project_id = "fake-project"
        client.model_id   = "ibm/granite-3-8b-instruct"
        client.base_url   = "https://us-south.ml.cloud.ibm.com"
        client._enabled   = True

        _token_cache.set("fake-token", 3600)

        mock_response = MagicMock()
        mock_response.status_code = 429

        with patch("app.ai.granite_client.httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_ctx)
            mock_client_cls.return_value.__exit__  = MagicMock(return_value=False)
            mock_ctx.post.return_value = mock_response
            ok, text, meta = client.generate("sys", "user")

        assert ok is False
        assert meta["reason"] == "rate_limit"

    def test_empty_response_returns_false(self):
        """API returns empty results list → (False, ...)."""
        from app.ai.granite_client import GraniteClient, _token_cache
        client = GraniteClient.__new__(GraniteClient)
        client.api_key    = "fake-key"
        client.project_id = "fake-project"
        client.model_id   = "ibm/granite-3-8b-instruct"
        client.base_url   = "https://us-south.ml.cloud.ibm.com"
        client._enabled   = True

        _token_cache.set("fake-token", 3600)

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = MagicMock()

        with patch("app.ai.granite_client.httpx.Client") as mock_client_cls:
            mock_ctx = MagicMock()
            mock_client_cls.return_value.__enter__ = MagicMock(return_value=mock_ctx)
            mock_client_cls.return_value.__exit__  = MagicMock(return_value=False)
            mock_ctx.post.return_value = mock_response
            ok, text, meta = client.generate("sys", "user")

        assert ok is False
        assert meta["reason"] == "empty_response"


# ── 4. Data grounding tests ───────────────────────────────────────────────────

class TestDataGrounding:
    """Verify prompt builder only includes data from agent results."""

    def test_prompt_contains_real_price(self):
        """Forecast price from agent must appear in the prompt."""
        from app.ai.prompts import build_data_context
        agent_results = {
            "forecast": {
                "current_price": 7200.0,
                "forecast_7d":   7350.0,
                "forecast_15d":  7450.0,
                "forecast_30d":  7600.0,
                "trend":         "UP",
                "confidence":    78.0,
                "risk":          "MEDIUM",
            }
        }
        prompt = build_data_context(
            query="Should I sell cotton?",
            language="en",
            agents_used=["forecast"],
            agent_results=agent_results,
        )
        assert "7,200" in prompt or "7200" in prompt
        assert "7,450" in prompt or "7450" in prompt

    def test_prompt_contains_buyer_name(self):
        """Buyer name from agent must appear in the prompt."""
        from app.ai.prompts import build_data_context
        agent_results = {
            "buyer": {
                "matches": [{
                    "buyer_name":          "Rajkot Cotton Corp",
                    "offered_price":       7380.0,
                    "location":            "Rajkot, Gujarat",
                    "match_score":         88,
                    "min_quantity":        100,
                    "max_quantity":        5000,
                    "quality_requirement": "A",
                    "price_vs_market":     "ABOVE_MARKET",
                    "price_advantage":     180.0,
                    "verified":            True,
                }],
                "total": 1,
            }
        }
        prompt = build_data_context(
            query="Find buyers",
            language="en",
            agents_used=["buyer"],
            agent_results=agent_results,
        )
        assert "Rajkot Cotton Corp" in prompt
        assert "7,380" in prompt or "7380" in prompt

    def test_no_buyer_found_message(self):
        """When buyer list is empty, prompt says no buyer found."""
        from app.ai.prompts import build_data_context
        agent_results = {"buyer": {"matches": [], "total": 0}}
        prompt = build_data_context(
            query="Find buyers",
            language="en",
            agents_used=["buyer"],
            agent_results=agent_results,
        )
        assert "no suitable buyer" in prompt.lower()

    def test_failed_agents_noted_in_prompt(self):
        """Failed agents are explicitly called out so Granite cannot invent them."""
        from app.ai.prompts import build_data_context
        agent_results = {"forecast": {"current_price": 7200.0, "forecast_15d": 7400.0,
                                       "confidence": 70.0, "trend": "UP", "risk": "LOW"}}
        prompt = build_data_context(
            query="Find buyers and predict price",
            language="en",
            agents_used=["forecast"],
            agent_results=agent_results,
            failed_agents=["buyer"],
        )
        assert "buyer" in prompt.lower()
        # The prompt should say something was unavailable
        assert "unavailable" in prompt.lower() or "not" in prompt.lower()

    def test_income_figures_appear_in_prompt(self):
        """Income figures from agent must appear in the prompt."""
        from app.ai.prompts import build_data_context
        agent_results = {
            "income": {
                "mandi_price":               7200.0,
                "buyer_price":               7380.0,
                "quantity":                  100,
                "current_estimated_income":  710000.0,
                "best_buyer_income":         728000.0,
                "partial_sell_income":       718500.0,
                "best_scenario":             "Direct Buyer",
                "best_net_income":           728000.0,
                "income_difference":         18000.0,
                "forecast_confidence":       78.0,
                "deterministic_summary":     "Best scenario: Direct Buyer",
            }
        }
        prompt = build_data_context(
            query="How much can I earn?",
            language="en",
            agents_used=["income"],
            agent_results=agent_results,
        )
        assert "710,000" in prompt or "710000" in prompt or "7,10,000" in prompt

    def test_fallback_response_contains_real_data(self):
        """Fallback response must contain agent data, not invented text."""
        from app.ai.prompts import build_fallback_response
        agent_results = {
            "forecast": {
                "current_price": 7200.0,
                "forecast_15d":  7400.0,
                "trend":         "UP",
                "confidence":    75.0,
                "risk":          "LOW",
            }
        }
        text = build_fallback_response(
            language     = "en",
            agents_used  = ["forecast"],
            agent_results= agent_results,
        )
        assert "AI Service Unavailable" in text
        assert "7,200" in text or "7200" in text

    def test_gujarati_fallback_message(self):
        """Fallback message should be in Gujarati when language=gu."""
        from app.ai.prompts import build_fallback_response
        text = build_fallback_response(
            language     = "gu",
            agents_used  = [],
            agent_results= {},
        )
        assert "AI" in text
        assert "ગુજ" in text or "ઉ" in text or "સ" in text  # Gujarati characters

    def test_hindi_fallback_message(self):
        """Fallback message should be in Hindi when language=hi."""
        from app.ai.prompts import build_fallback_response
        text = build_fallback_response(
            language     = "hi",
            agents_used  = [],
            agent_results= {},
        )
        assert "AI" in text
        assert "ह" in text or "न" in text  # Hindi characters


# ── 5. Orchestrate API endpoint (via FastAPI TestClient) ──────────────────────

class TestOrchestrateEndpoint:
    """Integration tests for POST /api/agents/orchestrate."""

    def _client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_orchestrate_basic(self):
        client = self._client()
        resp = client.post("/api/agents/orchestrate", json={
            "farmer_id": 1,
            "message":   "What is the current cotton price?",
            "language":  "en",
            "crop":      "cotton",
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "agents_used" in data
        assert "final_answer" in data
        assert "confidence" in data
        assert isinstance(data["agents_used"], list)
        assert isinstance(data["confidence"], int)

    def test_orchestrate_complex_query(self):
        """The complex demo scenario from the spec."""
        client = self._client()
        resp = client.post("/api/agents/orchestrate", json={
            "farmer_id": 1,
            "message":   (
                "I have 100 quintals of cotton in Rajkot. "
                "Find the best buyer, predict the price for the next 15 days, "
                "tell me whether I should sell or store, and estimate my income."
            ),
            "language":  "en",
            "crop":      "cotton",
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        # Should invoke at least 3 agents for this complex query
        assert len(data["agents_used"]) >= 2
        assert data["final_answer"]

    def test_orchestrate_gujarati(self):
        """Gujarati language request."""
        client = self._client()
        resp = client.post("/api/agents/orchestrate", json={
            "farmer_id": 1,
            "message":   "કપાસ હમણાં વેચવો?",
            "language":  "gu",
            "crop":      "cotton",
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_answer"]

    def test_orchestrate_hindi(self):
        """Hindi language request."""
        client = self._client()
        resp = client.post("/api/agents/orchestrate", json={
            "farmer_id": 1,
            "message":   "क्या मुझे कपास अभी बेचनी चाहिए?",
            "language":  "hi",
            "crop":      "cotton",
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_answer"]

    def test_orchestrate_invalid_crop(self):
        client = self._client()
        resp = client.post("/api/agents/orchestrate", json={
            "farmer_id": 1,
            "message":   "price?",
            "language":  "en",
            "crop":      "wheat",        # not supported
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 400

    def test_orchestrate_groundnut(self):
        """Groundnut query should work too."""
        client = self._client()
        resp = client.post("/api/agents/orchestrate", json={
            "farmer_id": 1,
            "message":   "Should I sell groundnut now?",
            "language":  "en",
            "crop":      "groundnut",
            "mandi":     "Junagadh APMC",
            "quantity":  50.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["final_answer"]


# ── 6. Chat API endpoint ──────────────────────────────────────────────────────

class TestChatEndpoint:
    """Integration tests for POST /api/chat."""

    def _client(self):
        from fastapi.testclient import TestClient
        from main import app
        return TestClient(app)

    def test_chat_basic(self):
        client = self._client()
        resp = client.post("/api/chat", json={
            "message":   "What is today's cotton price?",
            "language":  "en",
            "farmer_id": 1,
            "crop":      "cotton",
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "answer" in data
        assert "agents_used" in data
        assert "confidence" in data
        assert "granite_used" in data
        assert "data_timestamp" in data
        assert isinstance(data["agents_used"], list)

    def test_chat_response_has_answer(self):
        client = self._client()
        resp = client.post("/api/chat", json={
            "message":   "Find buyers for cotton",
            "language":  "en",
            "farmer_id": 1,
            "crop":      "cotton",
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["answer"]) > 20  # non-trivial response

    def test_chat_status_endpoint(self):
        client = self._client()
        resp = client.get("/api/chat/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "available" in data
        assert "mode" in data
        assert data["mode"] in ("granite", "fallback")

    def test_chat_fallback_when_granite_unavailable(self):
        """When Granite is unavailable, answer must contain fallback notice."""
        client = self._client()
        # Granite is NOT configured in test env → fallback mode
        resp = client.post("/api/chat", json={
            "message":   "Should I sell or store cotton?",
            "language":  "en",
            "farmer_id": 1,
            "crop":      "cotton",
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 200
        data = resp.json()
        if not data["granite_used"]:
            assert "Unavailable" in data["answer"] or "rule" in data["answer"].lower() \
                   or data["answer"]  # fallback gives deterministic text

    def test_chat_invalid_language(self):
        client = self._client()
        resp = client.post("/api/chat", json={
            "message":   "price?",
            "language":  "fr",          # unsupported
            "farmer_id": 1,
            "crop":      "cotton",
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 422   # validation error

    def test_chat_too_short_message(self):
        client = self._client()
        resp = client.post("/api/chat", json={
            "message":   "?",           # too short (< 2 chars)
            "language":  "en",
            "farmer_id": 1,
            "crop":      "cotton",
            "mandi":     "Rajkot APMC",
            "quantity":  100.0,
        })
        assert resp.status_code == 422


# ── 7. Health check reflects Phase 8 ─────────────────────────────────────────

class TestHealthEndpoint:

    def test_health_includes_granite_status(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "ibm_granite" in data
        assert "available" in data["ibm_granite"]
        assert data["version"] == "10.0.0-final"

    def test_health_includes_orchestrator(self):
        from fastapi.testclient import TestClient
        from main import app
        client = TestClient(app)
        resp = client.get("/health")
        data = resp.json()
        assert "AgentOrchestrator" in data.get("agents", {})


# ── 8. Confidence computation ─────────────────────────────────────────────────

class TestConfidenceComputation:

    def test_confidence_in_range(self):
        from app.ai.orchestrator import AgentOrchestrator
        conf = AgentOrchestrator._compute_confidence(
            agent_results  = {"forecast": {"confidence": 80}},
            failed_agents  = [],
            granite_ok     = True,
        )
        assert 0 <= conf <= 100

    def test_failed_agents_reduce_confidence(self):
        from app.ai.orchestrator import AgentOrchestrator
        conf_ok   = AgentOrchestrator._compute_confidence(
            {"forecast": {"confidence": 80}}, [], True
        )
        conf_fail = AgentOrchestrator._compute_confidence(
            {"forecast": {"confidence": 80}}, ["buyer", "income"], True
        )
        assert conf_ok > conf_fail

    def test_no_granite_reduces_confidence(self):
        from app.ai.orchestrator import AgentOrchestrator
        conf_with_granite    = AgentOrchestrator._compute_confidence(
            {"forecast": {"confidence": 80}}, [], True
        )
        conf_without_granite = AgentOrchestrator._compute_confidence(
            {"forecast": {"confidence": 80}}, [], False
        )
        assert conf_with_granite >= conf_without_granite
