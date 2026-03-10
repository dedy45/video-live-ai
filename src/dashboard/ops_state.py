from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class OpsState:
    deployment_mode: str = "cold"
    session_id: str = "local-session"
    host_role: str = "local_lab"

    def to_dict(self) -> dict[str, Any]:
        return {
            "deployment_mode": self.deployment_mode,
            "session_id": self.session_id,
            "host_role": self.host_role,
        }


_ops_state: OpsState | None = None


def get_ops_state() -> OpsState:
    global _ops_state
    if _ops_state is None:
        _ops_state = OpsState()
    return _ops_state


def reset_ops_state() -> None:
    global _ops_state
    _ops_state = None
