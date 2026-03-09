"""Voice runtime state — singleton tracking requested/resolved voice engine state.

Updated by VoiceRouter after each synthesis attempt. Exposed via dashboard truth.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VoiceRuntimeState:
    """Tracks the runtime state of the voice synthesis path."""

    requested_engine: str = "fish_speech"
    resolved_engine: str = "unknown"
    fallback_active: bool = False
    server_reachable: bool = False
    reference_ready: bool = False
    last_latency_ms: float | None = None
    last_error: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "requested_engine": self.requested_engine,
            "resolved_engine": self.resolved_engine,
            "fallback_active": self.fallback_active,
            "server_reachable": self.server_reachable,
            "reference_ready": self.reference_ready,
            "last_latency_ms": self.last_latency_ms,
            "last_error": self.last_error,
        }

    def update_success(self, engine: str, latency_ms: float) -> None:
        """Record a successful synthesis."""
        self.resolved_engine = engine
        self.fallback_active = engine != self.requested_engine
        if engine == "fish_speech":
            self.server_reachable = True
            self.reference_ready = True
        self.last_latency_ms = latency_ms
        self.last_error = None

    def update_failure(self, engine: str, error: str) -> None:
        """Record a failed synthesis attempt."""
        self.resolved_engine = engine
        self.fallback_active = False
        self.last_error = error

    def update_fallback_success(self, fallback_engine: str, latency_ms: float, primary_error: str) -> None:
        """Record a successful fallback synthesis."""
        self.resolved_engine = fallback_engine
        self.fallback_active = True
        self.last_latency_ms = latency_ms
        self.last_error = f"primary failed: {primary_error}"


# Module-level singleton
_voice_runtime_state: VoiceRuntimeState | None = None


def get_voice_runtime_state() -> VoiceRuntimeState:
    """Get or create the voice runtime state singleton."""
    global _voice_runtime_state
    if _voice_runtime_state is None:
        _voice_runtime_state = VoiceRuntimeState()
    return _voice_runtime_state


def reset_voice_runtime_state() -> None:
    """Reset the voice runtime state (for testing)."""
    global _voice_runtime_state
    _voice_runtime_state = None
