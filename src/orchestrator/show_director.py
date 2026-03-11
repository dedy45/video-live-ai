"""Persistent show director runtime service.

Owns the operator-facing lifecycle state for the live commerce runtime.
This replaces dashboard-global pipeline variables with a queryable service.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

PHASE_SEQUENCE = ["hook", "problem", "solution", "features", "social_proof", "urgency", "cta"]
MAX_HISTORY = 100

VALID_TRANSITIONS: dict[str, list[str]] = {
    "IDLE": ["SELLING", "PAUSED"],
    "SELLING": ["REACTING", "ENGAGING", "PAUSED", "IDLE"],
    "REACTING": ["SELLING", "ENGAGING", "PAUSED"],
    "ENGAGING": ["SELLING", "REACTING", "PAUSED"],
    "PAUSED": ["IDLE", "SELLING"],
    "STOPPED": ["IDLE"],
}


@dataclass
class ShowDirector:
    """Persistent runtime state for the live operator flow."""

    state: str = "IDLE"
    stream_running: bool = False
    emergency_stopped: bool = False
    manual_override: bool = False
    current_phase: str = "hook"
    active_provider: str = "auto"
    active_model: str = "unknown"
    active_prompt_revision: str = "default-live-commerce:v1"
    session_started_at: float | None = None
    state_entered_at: float = field(default_factory=time.time)
    history: list[dict[str, Any]] = field(default_factory=list)

    def get_valid_transitions(self) -> list[str]:
        return VALID_TRANSITIONS.get(self.state, ["IDLE"])

    def transition(self, target_state: str) -> dict[str, Any]:
        target = target_state.upper()
        valid = self.get_valid_transitions()
        if target not in valid:
            raise ValueError(f"Invalid transition: {self.state} -> {target}. Valid: {valid}")

        previous = self.state
        now = time.time()
        self.state = target
        self.state_entered_at = now
        if target == "SELLING" and self.session_started_at is None:
            self.session_started_at = now
        if target == "SELLING":
            self.current_phase = "hook"
        elif target == "REACTING":
            self.current_phase = "reacting"
        elif target == "ENGAGING":
            self.current_phase = "engaging"
        elif target in {"PAUSED", "IDLE", "STOPPED"}:
            self.current_phase = "hook"

        self.history.append({
            "from": previous,
            "to": target,
            "timestamp": now,
        })
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)
        return self.get_runtime_snapshot()

    def start_stream(self) -> dict[str, Any]:
        if self.emergency_stopped:
            raise RuntimeError("Emergency stop active. Reset director before starting stream.")
        self.stream_running = True
        if self.state == "IDLE":
            return self.transition("SELLING")
        return self.get_runtime_snapshot()

    def stop_stream(self) -> dict[str, Any]:
        self.stream_running = False
        self.manual_override = True
        return self.get_runtime_snapshot()

    def emergency_stop(self) -> dict[str, Any]:
        self.stream_running = False
        self.emergency_stopped = True
        self.manual_override = True
        if self.state != "STOPPED":
            previous = self.state
            now = time.time()
            self.state = "STOPPED"
            self.state_entered_at = now
            self.history.append({
                "from": previous,
                "to": "STOPPED",
                "timestamp": now,
            })
            if len(self.history) > MAX_HISTORY:
                self.history.pop(0)
        return self.get_runtime_snapshot()

    def reset_emergency(self) -> dict[str, Any]:
        self.emergency_stopped = False
        self.stream_running = False
        self.manual_override = False
        self.state = "IDLE"
        self.state_entered_at = time.time()
        self.current_phase = "hook"
        return self.get_runtime_snapshot()

    def update_brain_runtime(
        self,
        *,
        provider: str | None = None,
        model: str | None = None,
        prompt_revision: str | None = None,
    ) -> dict[str, Any]:
        if provider:
            self.active_provider = provider
        if model:
            self.active_model = model
        if prompt_revision:
            self.active_prompt_revision = prompt_revision
        return self.get_runtime_snapshot()

    def get_runtime_snapshot(self) -> dict[str, Any]:
        now = time.time()
        uptime = 0.0 if self.session_started_at is None else round(now - self.session_started_at, 1)
        return {
            "state": self.state,
            "stream_running": self.stream_running,
            "emergency_stopped": self.emergency_stopped,
            "manual_override": self.manual_override,
            "current_phase": self.current_phase,
            "phase_sequence": PHASE_SEQUENCE[:],
            "active_provider": self.active_provider,
            "active_model": self.active_model,
            "active_prompt_revision": self.active_prompt_revision,
            "uptime_sec": uptime,
            "history": self.history[-20:],
            "valid_transitions": self.get_valid_transitions(),
        }


_show_director: ShowDirector | None = None


def get_show_director() -> ShowDirector:
    global _show_director
    if _show_director is None:
        _show_director = ShowDirector()
    return _show_director


def reset_show_director() -> ShowDirector:
    global _show_director
    _show_director = ShowDirector()
    return _show_director
