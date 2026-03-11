"""Tests for Layer 1: Intelligence — Multi-LLM Brain.

Tests cover: adapters (mock mode), router fallback, persona prompts,
and safety filter.
"""

from __future__ import annotations

import os

import pytest

os.environ["MOCK_MODE"] = "true"


# === Adapter Tests ===

@pytest.mark.asyncio
async def test_gemini_adapter_mock() -> None:
    """Gemini adapter returns mock response in Mock Mode."""
    from src.brain.adapters.gemini import GeminiAdapter

    adapter = GeminiAdapter()
    response = await adapter.generate("System", "Hello", trace_id="test-001")
    assert response.success
    assert response.provider == "gemini"
    assert "[MOCK-Gemini]" in response.text
    assert response.trace_id == "test-001"


@pytest.mark.asyncio
async def test_claude_adapter_mock() -> None:
    """Claude adapter returns mock response in Mock Mode."""
    from src.brain.adapters.claude import ClaudeAdapter

    adapter = ClaudeAdapter()
    response = await adapter.generate("System", "Write script")
    assert response.success
    assert response.provider == "claude"
    assert "[MOCK-Claude]" in response.text


@pytest.mark.asyncio
async def test_gpt4o_adapter_mock() -> None:
    """GPT-4o adapter returns mock response with emotion format."""
    from src.brain.adapters.gpt4o import GPT4oAdapter

    adapter = GPT4oAdapter()
    response = await adapter.generate("System", "Detect emotion")
    assert response.success
    assert response.provider == "gpt4o"
    assert "Emotion" in response.text or "MOCK" in response.text


@pytest.mark.asyncio
async def test_groq_adapter_mock() -> None:
    """Groq adapter returns ultra-fast mock response."""
    from src.brain.adapters.groq import GroqAdapter

    adapter = GroqAdapter()
    response = await adapter.generate("System", "Fast reply")
    assert response.success
    assert response.provider == "groq"
    assert response.latency_ms <= 50  # Mock Groq = 10ms
    assert "[MOCK-Groq" in response.text


@pytest.mark.asyncio
async def test_local_adapter_mock() -> None:
    """Local adapter returns zero-cost mock response."""
    from src.brain.adapters.local import LocalAdapter

    adapter = LocalAdapter()
    response = await adapter.generate("System", "Generate filler")
    assert response.success
    assert response.provider == "local"
    assert response.cost_usd == 0.0


# === Usage Stats Tests ===

def test_usage_stats_tracking() -> None:
    """Adapter should correctly track usage statistics."""
    from src.brain.adapters.base import LLMResponse, LLMUsageStats, TaskType

    stats = LLMUsageStats()
    response = LLMResponse(
        text="test", provider="test", model="test",
        task_type=TaskType.CHAT_REPLY,
        input_tokens=100, output_tokens=50,
        latency_ms=200.0, cost_usd=0.001,
    )

    from src.brain.adapters.gemini import GeminiAdapter
    adapter = GeminiAdapter()
    adapter.record_usage(response)

    assert adapter.stats.total_calls == 1
    assert adapter.stats.total_tokens == 150
    assert adapter.stats.total_cost_usd == 0.001


# === Router Tests ===

@pytest.mark.asyncio
async def test_router_routes_by_task_type() -> None:
    """Router should select appropriate provider by task type."""
    from src.brain.adapters.base import TaskType
    from src.brain.router import LLMRouter

    router = LLMRouter()
    response = await router.route(
        "System", "Hello viewer!",
        task_type=TaskType.CHAT_REPLY,
        trace_id="test-router-001",
    )
    assert response.success
    assert response.trace_id == "test-router-001"


@pytest.mark.asyncio
async def test_router_filler_uses_local() -> None:
    """Filler tasks should route to a free (local/zero-cost) provider first."""
    from src.brain.adapters.base import TaskType
    from src.brain.router import LLMRouter

    router = LLMRouter()
    response = await router.route("System", "Generate filler", task_type=TaskType.FILLER)
    assert response.success
    # Routing table: gemini_local_flash → groq → local → gemini_25_flash → gemini
    # All Cherry Studio providers and local are free (cost_usd == 0.0)
    FREE_PROVIDERS = {"gemini_local_flash", "gemini_25_flash", "gemini_local_pro",
                      "claude_local", "gpt4o_local", "local"}
    assert response.provider in FREE_PROVIDERS, (
        f"Expected free provider, got: {response.provider}"
    )
    assert response.cost_usd == 0.0


@pytest.mark.asyncio
async def test_router_usage_stats() -> None:
    """Router should track usage across all providers."""
    from src.brain.adapters.base import TaskType
    from src.brain.router import LLMRouter

    router = LLMRouter()
    await router.route("System", "Test", task_type=TaskType.CHAT_REPLY)
    stats = router.get_usage_stats()
    assert "_summary" in stats
    assert stats["_summary"]["daily_budget"] == 5.0


# === Persona Tests ===

def test_persona_selling_prompt() -> None:
    """Persona should generate selling mode prompt with product context."""
    from src.brain.persona import PersonaEngine

    engine = PersonaEngine()
    prompt = engine.build_system_prompt(
        state="SELLING",
        product_context="Lipstik Matte Red - Rp 99.000",
    )
    assert "SELLING MODE" in prompt
    assert "Lipstik Matte Red" in prompt
    assert "Sari" in prompt  # Default persona name


def test_persona_engaging_prompt() -> None:
    """Persona should include catchphrases in engaging mode."""
    from src.brain.persona import PersonaEngine

    engine = PersonaEngine()
    prompt = engine.build_system_prompt(state="ENGAGING", viewer_count=150)
    assert "ENGAGING MODE" in prompt
    assert "150" in prompt


def test_selling_script_prompt_has_7_phases() -> None:
    """Selling script prompt should request 7-phase structure."""
    from src.brain.persona import PersonaEngine

    engine = PersonaEngine()
    prompt = engine.build_selling_script_prompt(
        product_name="Moisturizer SPF 50",
        price=150000,
        features=["SPF 50", "Lightweight", "12-hour protection"],
    )
    assert "HOOK" in prompt
    assert "CTA" in prompt
    assert "7 fase" in prompt


def test_prompt_registry_bootstraps_default_revision(tmp_path) -> None:
    """Prompt registry should always bootstrap a default active revision."""
    from src.brain.prompt_registry import PromptRegistry

    registry = PromptRegistry(db_path=tmp_path / "prompt-registry.db")
    active = registry.get_active_revision()

    assert active["slug"] == "default-live-commerce"
    assert active["status"] == "active"
    assert active["version"] >= 1
    assert "templates" in active
    assert "system_base" in active["templates"]


def test_prompt_registry_default_revision_contains_runtime_templates(tmp_path) -> None:
    """Default prompt registry payload should contain the templates needed by PersonaEngine."""
    from src.brain.prompt_registry import PromptRegistry

    registry = PromptRegistry(db_path=tmp_path / "prompt-registry.db")
    active = registry.get_active_revision()
    templates = active["templates"]

    assert "selling_mode" in templates
    assert "reacting_mode" in templates
    assert "engaging_mode" in templates
    assert "filler" in templates
    assert "selling_script" in templates


# === Safety Filter Tests ===

def test_safety_catches_blacklisted_word() -> None:
    """Safety filter should catch blacklisted keywords."""
    from src.brain.safety import SafetyFilter

    sf = SafetyFilter()
    result = sf.check("Produk ini bagus banget anjing!")
    assert not result.safe
    assert result.trigger_type == "keyword_blacklist"
    assert result.triggered_keywords is not None
    assert len(result.filtered_text) > 0


def test_safety_passes_clean_text() -> None:
    """Safety filter should pass clean text unchanged."""
    from src.brain.safety import SafetyFilter

    sf = SafetyFilter()
    result = sf.check("Produk ini bagus banget kak! Yuk checkout!")
    assert result.safe
    assert result.filtered_text == result.original_text


def test_safety_catches_excessive_caps() -> None:
    """Safety filter should flag excessive caps as aggressive."""
    from src.brain.safety import SafetyFilter

    sf = SafetyFilter()
    result = sf.check("BELI SEKARANG ATAU KAMU RUGI BESAR BANGET HUAAAA")
    assert not result.safe
    assert result.trigger_type == "pattern"


def test_safety_incident_counter() -> None:
    """Safety filter should count incidents."""
    from src.brain.safety import SafetyFilter

    sf = SafetyFilter()
    sf.check("kata anjing terlarang")
    sf.check("kata bangsat juga")
    assert sf.incident_count == 2
