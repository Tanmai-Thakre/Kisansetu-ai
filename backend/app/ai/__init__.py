"""Phase 8 — IBM Granite AI layer."""
from .granite_client import get_granite_client, GraniteClient
from .orchestrator   import get_orchestrator, AgentOrchestrator

__all__ = ["get_granite_client", "GraniteClient", "get_orchestrator", "AgentOrchestrator"]
