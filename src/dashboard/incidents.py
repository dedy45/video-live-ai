from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


_SEVERITY_ORDER = {
    "none": 0,
    "info": 1,
    "warn": 2,
    "error": 3,
    "critical": 4,
}


@dataclass
class IncidentRegistry:
    incidents: list[dict[str, Any]] = field(default_factory=list)

    def open(self, code: str, severity: str, subsystem: str) -> dict[str, Any]:
        incident = {
            "id": str(uuid4()),
            "code": code,
            "severity": severity,
            "subsystem": subsystem,
            "resolved": False,
            "acknowledged": False,
            "first_seen": datetime.now(timezone.utc).isoformat(),
            "last_seen": datetime.now(timezone.utc).isoformat(),
        }
        self.incidents.insert(0, incident)
        return incident

    def resolve(self, incident_id: str) -> None:
        for incident in self.incidents:
            if incident["id"] == incident_id:
                incident["resolved"] = True
                incident["last_seen"] = datetime.now(timezone.utc).isoformat()
                return

    def acknowledge(self, incident_id: str, actor: str = "operator") -> None:
        for incident in self.incidents:
            if incident["id"] == incident_id:
                incident["acknowledged"] = True
                incident["acknowledged_by"] = actor
                incident["acknowledged_at"] = datetime.now(timezone.utc).isoformat()
                incident["last_seen"] = datetime.now(timezone.utc).isoformat()
                return

    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return self.incidents[:limit]

    def summary(self) -> dict[str, Any]:
        open_incidents = [incident for incident in self.incidents if not incident["resolved"]]
        highest = "none"
        for incident in open_incidents:
            if _SEVERITY_ORDER.get(incident["severity"], 0) > _SEVERITY_ORDER.get(highest, 0):
                highest = incident["severity"]
        return {
            "open_count": len(open_incidents),
            "highest_severity": highest,
        }


_registry: IncidentRegistry | None = None


def get_incident_registry() -> IncidentRegistry:
    global _registry
    if _registry is None:
        _registry = IncidentRegistry()
    return _registry


def reset_incident_registry() -> None:
    global _registry
    _registry = None
