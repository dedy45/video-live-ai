"""Tests for hardening: error handling, health checks, edge cases."""

from __future__ import annotations

import os

import pytest

os.environ["MOCK_MODE"] = "true"


# === Health Manager Tests ===

@pytest.mark.asyncio
async def test_health_manager_register_and_check() -> None:
    """Health manager should run registered checks."""
    from src.utils.health import HealthManager, HealthStatus

    manager = HealthManager()

    async def mock_check() -> HealthStatus:
        return HealthStatus(name="test", healthy=True, status="healthy", message="OK")

    manager.register("test", mock_check)
    results = await manager.check_all()
    assert len(results) == 1
    assert results[0].healthy is True


@pytest.mark.asyncio
async def test_health_manager_timeout() -> None:
    """Health check should timeout if component is slow."""
    import asyncio
    from src.utils.health import HealthManager, HealthStatus

    manager = HealthManager(timeout_sec=0.1)

    async def slow_check() -> HealthStatus:
        await asyncio.sleep(5)
        return HealthStatus(name="slow", healthy=True, status="healthy")

    manager.register("slow", slow_check)
    results = await manager.check_all()
    assert results[0].healthy is False
    assert "timed out" in results[0].message


@pytest.mark.asyncio
async def test_health_manager_exception() -> None:
    """Health check should catch exceptions gracefully."""
    from src.utils.health import HealthManager, HealthStatus

    manager = HealthManager()

    async def broken_check() -> HealthStatus:
        raise ConnectionError("Cannot connect")

    manager.register("broken", broken_check)
    results = await manager.check_all()
    assert results[0].healthy is False
    assert "Cannot connect" in results[0].message


def test_health_manager_overall_status() -> None:
    """Overall status should reflect worst component."""
    from src.utils.health import HealthManager, HealthStatus

    manager = HealthManager()
    manager._last_results = {
        "a": HealthStatus(name="a", healthy=True, status="healthy"),
        "b": HealthStatus(name="b", healthy=True, status="healthy"),
    }
    assert manager.overall_status == "healthy"

    manager._last_results["c"] = HealthStatus(name="c", healthy=False, status="failed")
    assert manager.overall_status == "degraded"


# === Database Health Tests ===

def test_database_health_missing_file() -> None:
    """Database health check should report missing file."""
    from pathlib import Path
    from src.data.database import check_database_health

    result = check_database_health(Path("/nonexistent/db.sqlite"))
    assert result["healthy"] is False
    assert "not found" in str(result["message"])


def test_database_init_creates_file(tmp_path: Path) -> None:
    """Database init should create the file + tables."""
    from pathlib import Path
    from src.data.database import check_database_health, init_database

    db_path = tmp_path / "test.db"
    init_database(db_path)
    assert db_path.exists()

    health = check_database_health(db_path)
    assert health["healthy"] is True
    assert health["tables"] > 0


# === Adapter Error Handling Tests ===

@pytest.mark.asyncio
async def test_adapter_empty_prompt_rejected() -> None:
    """All adapters should reject empty prompts gracefully."""
    from src.brain.adapters.gemini import GeminiAdapter

    # Empty prompt in mock mode succeeds (mock doesn't validate)
    # But in non-mock with empty prompt, it should fail
    os.environ["MOCK_MODE"] = "false"
    adapter = GeminiAdapter()
    response = await adapter.generate("System", "   ", trace_id="test-empty")
    assert not response.success
    assert "Empty prompt" in response.error
    os.environ["MOCK_MODE"] = "true"


# === Safety Filter Edge Cases ===

def test_safety_empty_text() -> None:
    """Safety filter should handle empty text."""
    from src.brain.safety import SafetyFilter

    sf = SafetyFilter()
    result = sf.check("")
    assert result.safe is True  # Empty = safe (nothing to filter)


def test_safety_unicode_text() -> None:
    """Safety filter should handle unicode/emoji text."""
    from src.brain.safety import SafetyFilter

    sf = SafetyFilter()
    result = sf.check("😍🔥✨ Bagus banget kak!")
    assert result.safe is True


def test_safety_very_long_text() -> None:
    """Safety filter should handle very long text."""
    from src.brain.safety import SafetyFilter

    sf = SafetyFilter()
    result = sf.check("Bagus " * 10000)
    assert result.safe is True


# === Config Edge Cases ===

def test_config_from_nonexistent_yaml() -> None:
    """Config should load defaults when YAML doesn't exist."""
    from src.config.loader import load_config

    config = load_config(config_path="/nonexistent/config.yaml")
    assert config.app.name == "AI Live Commerce"
    assert config.gpu.vram_budget_mb == 20000


# === Router Concurrent Safety ===

@pytest.mark.asyncio
async def test_router_handles_all_failures() -> None:
    """Router should return graceful error when all providers fail."""
    from src.brain.adapters.base import TaskType
    from src.brain.router import LLMRouter

    router = LLMRouter()
    # Disable all adapters
    for adapter in router.adapters.values():
        adapter.is_available = False

    response = await router.route("System", "Test", task_type=TaskType.CHAT_REPLY)
    assert not response.success
    # Error message contains either "no_providers_available" (all disabled)
    # or a pipe-separated list of per-provider errors
    assert response.error  # must be non-empty
    assert response.provider == "none"
