"""
Phase 8 — Agent Orchestrator.

Accepts a farmer query + context, determines which agents are needed,
invokes them, validates results, calls IBM Granite for synthesis, and
returns a structured response.

Intent → Agent mapping
──────────────────────
PRICE         → forecast
FORECAST      → forecast
BUYER         → buyer
SELL_OR_STORE → storage, forecast
QUALITY       → quality
INCOME        → income, forecast, buyer
GENERAL       → storage, forecast
COMPLEX       → forecast, buyer, storage, income

This module only orchestrates; it never duplicates business logic.
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple

from app.ai.granite_client import get_granite_client
from app.ai.prompts import SYSTEM_PROMPT, build_data_context, build_fallback_response

logger = logging.getLogger(__name__)

# ── Intent definitions ────────────────────────────────────────────────────────

INTENTS = {
    "PRICE":        ["forecast"],
    "FORECAST":     ["forecast"],
    "BUYER":        ["buyer"],
    "SELL_OR_STORE":["storage", "forecast"],
    "QUALITY":      ["quality"],
    "INCOME":       ["income", "forecast", "buyer"],
    "GENERAL":      ["storage", "forecast"],
    "COMPLEX":      ["forecast", "buyer", "storage", "income"],
}

# Keyword → intent heuristics (used when Granite is unavailable or as fallback)
_KEYWORD_MAP: List[Tuple[str, str]] = [
    # COMPLEX first — most specific
    (r"(sell|store|buy|income|earn|price|forecast)", "COMPLEX"),
    # Then specific
    (r"(forecast|predict|price.*rise|price.*fall|next.*day|will.*price)", "FORECAST"),
    (r"(buy|buyer|purchaser|company|who.*buy|best.*buyer|find.*buyer)", "BUYER"),
    (r"(income|earn|profit|revenue|how.*much|money|rupee|₹)", "INCOME"),
    (r"(sell.*now|store|wait|store.*sell|hold|when.*sell)", "SELL_OR_STORE"),
    (r"(quality|grade|test|check.*quality|assess)", "QUALITY"),
    (r"(price|rate|today.*price|current.*price|mandi.*rate)", "PRICE"),
]


def _heuristic_intent(query: str) -> str:
    """Simple keyword-based intent detection as Granite fallback."""
    import re
    q = query.lower()
    # Check for multi-aspect queries first (COMPLEX)
    has_price   = bool(re.search(r"\bprice\b|\brate\b|\bmandi\b", q))
    has_buyer   = bool(re.search(r"\bbuyer\b|\bpurchaser\b|\bwho.*buy\b", q))
    has_income  = bool(re.search(r"\beach?\b|\bprofit\b|\brupee\b|₹|\bhow much\b|\bincome\b", q))
    has_storage = bool(re.search(r"\bsell\b|\bstore\b|\bwait\b|\bhold\b", q))

    count = sum([has_price, has_buyer, has_income, has_storage])
    if count >= 3:
        return "COMPLEX"
    if count == 2 and (has_buyer or has_income):
        return "COMPLEX"

    for pattern, intent in _KEYWORD_MAP[1:]:  # skip COMPLEX
        if re.search(pattern, q):
            return intent
    return "GENERAL"


# ── Agent adapters ────────────────────────────────────────────────────────────
# Each adapter calls the corresponding Phase 3–7 service and normalises output.

def _run_forecast_agent(
    crop: str,
    mandi: str,
    **_kwargs,
) -> dict:
    """Phase 3 — MandiForecastAgent."""
    from app.forecasting.forecasting_service import get_forecasting_service
    svc = get_forecasting_service()
    result = svc.forecast(crop, mandi)
    return {
        "crop":          result.crop,
        "mandi":         result.mandi,
        "current_price": result.current_price,
        "forecast_7d":   result.forecast_7d,
        "forecast_15d":  result.forecast_15d,
        "forecast_30d":  result.forecast_30d,
        "trend":         result.trend,
        "confidence":    result.confidence,
        "risk":          result.risk,
        "explanation":   result.explanation,
        "model_name":    result.model_name,
    }


def _run_buyer_agent(
    crop: str,
    quantity: Optional[float] = None,
    quality_grade: Optional[str] = None,
    district: Optional[str] = None,
    **_kwargs,
) -> dict:
    """Phase 4 — BuyerMatchingAgent."""
    from app.agents.buyer_matching.matching_service import get_buyer_matching_service
    svc = get_buyer_matching_service()
    matches = svc.find_matches(
        crop=crop,
        quantity=quantity,
        quality_grade=quality_grade,
        farmer_district=district or "Rajkot",
        top_n=5,
    )
    return {
        "matches": [m.to_dict() for m in matches],
        "total":   len(matches),
    }


def _run_storage_agent(
    crop: str,
    mandi: str,
    quantity: Optional[float] = None,
    storage_cost_per_quintal: float = 80.0,
    cash_urgency: str = "MEDIUM",
    **_kwargs,
) -> dict:
    """Phase 5 — StorageAdvisorAgent."""
    from app.agents.storage_advisor import get_advisor_service
    svc = get_advisor_service()
    return svc.advise(
        crop=crop,
        mandi=mandi,
        quantity=quantity or 100.0,
        storage_cost_per_quintal=storage_cost_per_quintal,
        cash_urgency=cash_urgency,
    )


def _run_income_agent(
    crop: str,
    quantity: float,
    mandi: str,
    storage_cost_per_quintal: float = 80.0,
    **_kwargs,
) -> dict:
    """Phase 7 — IncomeDashboardAgent."""
    from app.agents.income import get_income_service
    svc = get_income_service()
    return svc.calculate(
        crop=crop,
        quantity=quantity,
        mandi=mandi,
        storage_cost_per_quintal=storage_cost_per_quintal,
    )


def _run_quality_agent(
    db,
    farmer_id: int,
    crop: str,
    manual_params: Optional[dict] = None,
    **_kwargs,
) -> dict:
    """Phase 6 — QualityGradingAgent (text-only path, no image)."""
    from app.agents.quality.quality_service import get_quality_service
    svc = get_quality_service()
    return svc.assess(
        db=db,
        farmer_id=farmer_id,
        crop=crop,
        manual_params=manual_params or {},
    )


# Agent registry: name → callable
_AGENT_RUNNERS = {
    "forecast": _run_forecast_agent,
    "buyer":    _run_buyer_agent,
    "storage":  _run_storage_agent,
    "income":   _run_income_agent,
    "quality":  _run_quality_agent,
}


# ── Orchestrator ──────────────────────────────────────────────────────────────

class AgentOrchestrator:
    """
    Central orchestrator for Phase 8 KisanSetu AI.

    Flow::

        query + context
              ↓
        intent classification
              ↓
        required agents list
              ↓
        execute agents (collect JSON, handle failures)
              ↓
        validate grounding
              ↓
        IBM Granite synthesis (or deterministic fallback)
              ↓
        structured response
    """

    def __init__(self):
        self._granite = get_granite_client()

    # ── Intent classification ─────────────────────────────────────────────────

    def classify_intent(self, query: str, language: str = "en") -> str:
        """
        Classify the farmer's intent.
        Uses Granite when available; falls back to keyword heuristic.
        """
        if self._granite.is_available():
            system = (
                "You are an intent classifier for an agricultural AI assistant. "
                "Classify the user's query into exactly one of these intents: "
                "PRICE, FORECAST, BUYER, SELL_OR_STORE, QUALITY, INCOME, GENERAL, COMPLEX. "
                "Respond with ONLY the intent name and nothing else."
            )
            ok, intent, _ = self._granite.generate(
                system_prompt=system,
                user_prompt=query,
                max_new_tokens=10,
                temperature=0.0,
            )
            if ok:
                intent = intent.strip().upper().split()[0]  # guard against extra text
                if intent in INTENTS:
                    return intent
        return _heuristic_intent(query)

    # ── Agent execution ───────────────────────────────────────────────────────

    def _execute_agents(
        self,
        agents_needed:  List[str],
        context:        Dict[str, Any],
        db=None,
    ) -> Tuple[Dict[str, Any], List[str], Dict[str, float]]:
        """
        Run each required agent and collect results.

        Returns (results, failed_agents, latencies).
        Failed agents are skipped gracefully — remaining results are still returned.
        """
        results: Dict[str, Any]    = {}
        failed:  List[str]         = []
        latencies: Dict[str, float] = {}

        for agent_name in agents_needed:
            runner = _AGENT_RUNNERS.get(agent_name)
            if runner is None:
                logger.warning("Unknown agent: %s — skipped", agent_name)
                continue

            t0 = time.perf_counter()
            try:
                kwargs = dict(context)
                if agent_name == "quality" and db is not None:
                    kwargs["db"] = db
                result = runner(**kwargs)
                results[agent_name] = result
                latencies[agent_name] = round(time.perf_counter() - t0, 3)
                logger.info("Agent '%s' succeeded in %.3fs", agent_name, latencies[agent_name])
            except Exception as exc:
                latencies[agent_name] = round(time.perf_counter() - t0, 3)
                failed.append(agent_name)
                logger.error("Agent '%s' failed: %s", agent_name, exc)

        return results, failed, latencies

    # ── Confidence score ──────────────────────────────────────────────────────

    @staticmethod
    def _compute_confidence(
        agent_results: Dict[str, Any],
        failed_agents: List[str],
        granite_ok:    bool,
    ) -> int:
        """
        Compute an integer confidence % from available signals.
        Range: 0–100.
        """
        base = 80

        # Forecast confidence
        if "forecast" in agent_results:
            fc_conf = agent_results["forecast"].get("confidence", 60)
            base = int((base + fc_conf) / 2)

        # Penalise for failures
        base -= len(failed_agents) * 8

        # Penalise if Granite unavailable (explanation quality lower)
        if not granite_ok:
            base -= 5

        # Clamp
        return max(20, min(100, base))

    # ── Main entry point ──────────────────────────────────────────────────────

    def orchestrate(
        self,
        query:      str,
        language:   str            = "en",
        farmer_id:  int            = 1,
        crop:       str            = "cotton",
        mandi:      str            = "Rajkot APMC",
        quantity:   float          = 100.0,
        district:   Optional[str]  = None,
        quality_grade: Optional[str] = None,
        storage_cost_per_quintal: float = 80.0,
        cash_urgency: str          = "MEDIUM",
        db=None,
        request_id: Optional[str]  = None,
    ) -> Dict[str, Any]:
        """
        Full orchestration pipeline.

        Parameters
        ----------
        query     : Farmer's natural-language question.
        language  : "en", "gu", or "hi".
        farmer_id : Authenticated farmer ID.
        crop      : Crop context (default: cotton).
        mandi     : Mandi context (default: Rajkot APMC).
        quantity  : Quantity in quintals.
        district  : Optional farmer district.
        db        : SQLAlchemy Session (needed only when quality agent is used).
        request_id: Optional trace ID for observability.

        Returns
        -------
        Structured response dict with answer, agents_used, data_timestamp, confidence.
        """
        rid = request_id or str(uuid.uuid4())[:8]
        t_total = time.perf_counter()

        logger.info("[%s] orchestrate | farmer=%s | lang=%s | query=%r",
                    rid, farmer_id, language, query[:80])

        # ── 1. Intent classification ──────────────────────────────────────────
        intent = self.classify_intent(query, language)
        agents_needed = list(INTENTS.get(intent, INTENTS["GENERAL"]))

        logger.info("[%s] intent=%s | agents=%s", rid, intent, agents_needed)

        # ── 2. Build agent context dict ───────────────────────────────────────
        context: Dict[str, Any] = {
            "crop":                    crop.lower().strip(),
            "mandi":                   mandi,
            "quantity":                quantity,
            "district":                district or crop,   # use crop as rough fallback
            "quality_grade":           quality_grade,
            "storage_cost_per_quintal": storage_cost_per_quintal,
            "cash_urgency":            cash_urgency,
            "farmer_id":               farmer_id,
        }

        # ── 3. Execute agents ─────────────────────────────────────────────────
        agent_results, failed_agents, latencies = self._execute_agents(
            agents_needed, context, db=db
        )

        # Which agents actually succeeded
        agents_used = [a for a in agents_needed if a in agent_results]

        logger.info("[%s] agents_success=%s agents_failed=%s latencies=%s",
                    rid, agents_used, failed_agents, latencies)

        # ── 4. Validate grounding (remove disallowed keys) ────────────────────
        # (Agents already return only factual structured data — no free-form text
        #  that could smuggle invented values into the prompt.)

        # ── 5. Synthesise with Granite (or deterministic fallback) ─────────────
        granite_ok   = False
        granite_meta: Dict[str, Any] = {}

        if agents_used:
            user_prompt = build_data_context(
                query         = query,
                language      = language,
                agents_used   = agents_used,
                agent_results = agent_results,
                failed_agents = failed_agents if failed_agents else None,
            )

            if self._granite.is_available():
                t_granite = time.perf_counter()
                ok, text, meta = self._granite.generate(
                    system_prompt = SYSTEM_PROMPT,
                    user_prompt   = user_prompt,
                )
                granite_latency = round(time.perf_counter() - t_granite, 3)
                logger.info("[%s] granite ok=%s latency=%.3fs", rid, ok, granite_latency)

                if ok:
                    final_answer = text
                    granite_ok   = True
                    granite_meta = meta
                else:
                    logger.warning("[%s] Granite failed (%s) → deterministic fallback", rid, meta.get("reason"))
                    final_answer = build_fallback_response(
                        language, agents_used, agent_results, failed_agents
                    )
            else:
                final_answer = build_fallback_response(
                    language, agents_used, agent_results, failed_agents
                )
        else:
            # No agents succeeded — generic error message
            final_answer = {
                "en": "Unable to retrieve market data at this time. Please try again.",
                "gu": "અત્યારે બજાર ડેટા ઉપલબ્ધ નથી. કૃપા કરી ફરી પ્રયાસ કરો.",
                "hi": "अभी बाज़ार डेटा उपलब्ध नहीं है। कृपया पुनः प्रयास करें।",
            }.get(language, "Unable to retrieve market data at this time.")

        # ── 6. Compute confidence ─────────────────────────────────────────────
        confidence = self._compute_confidence(agent_results, failed_agents, granite_ok)

        total_latency = round(time.perf_counter() - t_total, 3)
        logger.info("[%s] done | total_latency=%.3fs | confidence=%d | granite=%s",
                    rid, total_latency, confidence, granite_ok)

        from datetime import datetime, timezone
        return {
            "request_id":    rid,
            "query":         query,
            "intent":        intent,
            "agents_used":   agents_used,
            "agents_failed": failed_agents,
            "results":       agent_results,
            "final_answer":  final_answer,
            "granite_used":  granite_ok,
            "confidence":    confidence,
            "latency_ms":    int(total_latency * 1000),
            "data_timestamp": datetime.now(timezone.utc).isoformat(),
        }


# ── Singleton ─────────────────────────────────────────────────────────────────

_orchestrator: Optional[AgentOrchestrator] = None


def get_orchestrator() -> AgentOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AgentOrchestrator()
    return _orchestrator
