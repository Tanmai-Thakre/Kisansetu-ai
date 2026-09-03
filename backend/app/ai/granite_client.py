"""
Phase 8 — IBM Granite Client.

Wraps the IBM watsonx.ai REST API for text generation with:
  - API key authentication (IAM token exchange)
  - Timeout / unavailability handling
  - Rate-limit handling
  - Invalid-response handling
  - Automatic fallback flag so callers can degrade gracefully

Environment variables required:
    IBM_API_KEY         — IBM Cloud IAM API key
    IBM_PROJECT_ID      — watsonx.ai project ID
    IBM_GRANITE_MODEL   — model ID  (default: ibm/granite-3-8b-instruct)
    IBM_REGION          — region    (default: us-south)

Alternatively the legacy names from .env.example are also accepted:
    WATSONX_URL, WATSONX_PROJECT_ID, WATSONX_MODEL_ID, IBM_CLOUD_API_KEY
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any, Dict, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

IAM_TOKEN_URL = "https://iam.cloud.ibm.com/identity/token"
_DEFAULT_REGION = "us-south"
_DEFAULT_MODEL  = "ibm/granite-3-8b-instruct"
_GENERATE_PATH  = "/ml/v1/text/generation?version=2023-05-29"

# Reasonable limits for a chat assistant
_DEFAULT_MAX_NEW_TOKENS = 600
_DEFAULT_TEMPERATURE    = 0.3   # low temp = more factual
_REQUEST_TIMEOUT        = 30.0  # seconds


def _watsonx_url(region: str) -> str:
    return f"https://{region}.ml.cloud.ibm.com"


# ── IAM token cache (simple in-process cache) ─────────────────────────────────

class _TokenCache:
    def __init__(self) -> None:
        self._token:   Optional[str] = None
        self._expires: float = 0.0  # epoch seconds

    def get(self) -> Optional[str]:
        if self._token and time.time() < self._expires - 60:
            return self._token
        return None

    def set(self, token: str, expires_in: int) -> None:
        self._token   = token
        self._expires = time.time() + expires_in


_token_cache = _TokenCache()


# ── GraniteClient ─────────────────────────────────────────────────────────────

class GraniteClient:
    """
    Thin wrapper around the watsonx.ai text generation REST API.

    Usage::

        client = GraniteClient()
        ok, text, meta = client.generate(system_prompt, user_prompt)
        if not ok:
            # fallback
    """

    def __init__(self) -> None:
        # Accept both naming conventions
        self.api_key    = (
            os.getenv("IBM_API_KEY") or
            os.getenv("IBM_CLOUD_API_KEY") or
            ""
        )
        self.project_id = (
            os.getenv("IBM_PROJECT_ID") or
            os.getenv("WATSONX_PROJECT_ID") or
            ""
        )
        self.model_id   = (
            os.getenv("IBM_GRANITE_MODEL") or
            os.getenv("WATSONX_MODEL_ID") or
            _DEFAULT_MODEL
        )
        region = (
            os.getenv("IBM_REGION") or
            os.getenv("IBM_CLOUD_REGION") or
            _DEFAULT_REGION
        )
        # Allow full URL override
        self.base_url = (
            os.getenv("WATSONX_URL") or
            _watsonx_url(region)
        )
        self._enabled = bool(self.api_key and self.project_id)
        if not self._enabled:
            logger.warning(
                "GraniteClient: IBM_API_KEY or IBM_PROJECT_ID not set. "
                "Running in fallback mode."
            )

    # ── Availability ──────────────────────────────────────────────────────────

    def is_available(self) -> bool:
        """True if credentials are configured (does not make a network call)."""
        return self._enabled

    # ── IAM token ─────────────────────────────────────────────────────────────

    def _get_iam_token(self) -> str:
        cached = _token_cache.get()
        if cached:
            return cached

        try:
            resp = httpx.post(
                IAM_TOKEN_URL,
                data={
                    "grant_type":    "urn:ibm:params:oauth:grant-type:apikey",
                    "apikey":        self.api_key,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            token      = data["access_token"]
            expires_in = int(data.get("expires_in", 3600))
            _token_cache.set(token, expires_in)
            return token
        except httpx.HTTPStatusError as exc:
            raise RuntimeError(
                f"IBM IAM authentication failed ({exc.response.status_code}): "
                "check IBM_API_KEY"
            ) from exc
        except Exception as exc:
            raise RuntimeError(
                f"IBM IAM token request failed: {exc}"
            ) from exc

    # ── Text generation ───────────────────────────────────────────────────────

    def generate(
        self,
        system_prompt: str,
        user_prompt:   str,
        max_new_tokens: int = _DEFAULT_MAX_NEW_TOKENS,
        temperature:   float = _DEFAULT_TEMPERATURE,
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Call watsonx.ai text generation.

        Returns
        -------
        (success: bool, text: str, meta: dict)
        On failure: success=False, text=error_message, meta includes reason.
        """
        if not self._enabled:
            return False, "IBM Granite not configured", {"reason": "no_credentials"}

        try:
            token = self._get_iam_token()
        except RuntimeError as exc:
            logger.error("Granite auth failure: %s", exc)
            return False, str(exc), {"reason": "auth_failure"}

        url = self.base_url.rstrip("/") + _GENERATE_PATH

        # Granite instruction format: <|system|>...<|user|>...<|assistant|>
        combined_prompt = (
            f"<|system|>\n{system_prompt}\n"
            f"<|user|>\n{user_prompt}\n"
            f"<|assistant|>\n"
        )

        payload: Dict[str, Any] = {
            "model_id": self.model_id,
            "input":    combined_prompt,
            "parameters": {
                "max_new_tokens": max_new_tokens,
                "temperature":    temperature,
                "top_p":          0.9,
                "repetition_penalty": 1.1,
                "stop_sequences":  ["<|user|>", "<|system|>"],
            },
            "project_id": self.project_id,
        }

        try:
            with httpx.Client(timeout=_REQUEST_TIMEOUT) as client:
                resp = client.post(
                    url,
                    json=payload,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type":  "application/json",
                        "Accept":        "application/json",
                    },
                )
                if resp.status_code == 429:
                    logger.warning("Granite rate limit hit")
                    return False, "IBM Granite rate limit — please try again shortly", {
                        "reason": "rate_limit"
                    }
                resp.raise_for_status()
                data = resp.json()

        except httpx.TimeoutException:
            logger.error("Granite request timed out")
            return False, "IBM Granite request timed out", {"reason": "timeout"}
        except httpx.HTTPStatusError as exc:
            logger.error("Granite HTTP error %s", exc.response.status_code)
            return False, f"IBM Granite HTTP error {exc.response.status_code}", {
                "reason": "http_error", "status_code": exc.response.status_code
            }
        except Exception as exc:
            logger.error("Granite unexpected error: %s", exc)
            return False, f"IBM Granite unavailable: {exc}", {"reason": "unknown"}

        # Parse response
        try:
            results = data.get("results", [])
            if not results:
                return False, "IBM Granite returned empty results", {"reason": "empty_response"}
            generated = results[0].get("generated_text", "").strip()
            if not generated:
                return False, "IBM Granite returned blank text", {"reason": "blank_response"}
            meta = {
                "model":           data.get("model_id", self.model_id),
                "input_token_count":  results[0].get("input_token_count"),
                "generated_token_count": results[0].get("generated_token_count"),
                "stop_reason":     results[0].get("stop_reason"),
            }
            return True, generated, meta
        except (KeyError, IndexError, TypeError) as exc:
            logger.error("Granite response parse error: %s | raw: %s", exc, data)
            return False, "IBM Granite response could not be parsed", {
                "reason": "parse_error"
            }


# ── Singleton ─────────────────────────────────────────────────────────────────

_client: Optional[GraniteClient] = None


def get_granite_client() -> GraniteClient:
    global _client
    if _client is None:
        _client = GraniteClient()
    return _client
