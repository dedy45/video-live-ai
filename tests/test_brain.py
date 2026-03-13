"""Tests for Layer 1: Intelligence — Multi-LLM Brain.

Tests cover: adapters (mock mode), router fallback, persona prompts,
and safety filter.
"""

from __future__ import annotations

import json
import os
import sqlite3

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
    """Filler tasks should stay on a zero-cost path in mock mode."""
    from src.brain.adapters.base import TaskType
    from src.brain.router import LLMRouter

    router = LLMRouter()
    response = await router.route("System", "Generate filler", task_type=TaskType.FILLER)
    assert response.success
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


def test_prompt_registry_default_revision_contains_v2_core_task_templates(tmp_path) -> None:
    """Default prompt payload should expose core v2 task templates for future task-aware builders."""
    from src.brain.prompt_registry import PromptRegistry

    registry = PromptRegistry(db_path=tmp_path / "prompt-registry.db")
    templates = registry.get_active_revision()["templates"]

    assert "chat_reply" in templates
    assert "product_qa" in templates
    assert "safety_check" in templates
    assert "emotion_detect" in templates


def test_prompt_registry_merges_v2_defaults_for_legacy_active_revision(tmp_path) -> None:
    """Legacy prompt rows missing new fields should be readable with merged v2 defaults."""
    from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES, PromptRegistry

    db_path = tmp_path / "prompt-registry.db"
    registry = PromptRegistry(db_path=db_path)

    legacy_templates = {
        key: DEFAULT_TEMPLATES[key]
        for key in (
            "system_base",
            "selling_mode",
            "reacting_mode",
            "engaging_mode",
            "filler",
            "selling_script",
        )
    }
    legacy_persona = {
        key: DEFAULT_PERSONA[key]
        for key in (
            "name",
            "personality",
            "language",
            "tone",
            "expertise",
            "catchphrases",
            "forbidden_topics",
        )
    }

    with sqlite3.connect(str(db_path)) as conn:
        conn.execute("DELETE FROM prompt_revisions")
        conn.execute(
            """
            INSERT INTO prompt_revisions (slug, version, status, templates_json, persona_json)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "legacy-live-commerce",
                1,
                "active",
                json.dumps(legacy_templates, ensure_ascii=True),
                json.dumps(legacy_persona, ensure_ascii=True),
            ),
        )

    active = registry.get_active_revision()

    assert active["templates"]["chat_reply"] == DEFAULT_TEMPLATES["chat_reply"]
    assert active["templates"]["product_qa"] == DEFAULT_TEMPLATES["product_qa"]
    assert active["templates"]["safety_check"] == DEFAULT_TEMPLATES["safety_check"]
    assert active["persona"]["role"] == DEFAULT_PERSONA["role"]
    assert active["persona"]["unknown_answer_policy"] == DEFAULT_PERSONA["unknown_answer_policy"]


def test_prompt_registry_revision_lifecycle(tmp_path) -> None:
    """Prompt registry should expose a full typed CRUD lifecycle."""
    from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES, PromptRegistry

    registry = PromptRegistry(db_path=tmp_path / "prompt-registry.db")
    created = registry.create_revision(
        slug="campaign-launch",
        templates=DEFAULT_TEMPLATES,
        persona=DEFAULT_PERSONA,
    )

    assert created["slug"] == "campaign-launch"
    assert created["status"] == "draft"

    updated = registry.update_revision(
        created["id"],
        templates={**DEFAULT_TEMPLATES, "filler": "Halo kak, stay tuned ya!"},
        persona={**DEFAULT_PERSONA, "tone": "confident"},
    )
    assert updated["id"] == created["id"]

    published = registry.publish_revision(created["id"])
    assert published["id"] == created["id"]
    assert published["status"] == "active"

    active = registry.get_active_revision()
    assert active["id"] == created["id"]
    assert active["templates"]["filler"] == "Halo kak, stay tuned ya!"
    assert active["persona"]["tone"] == "confident"


def test_prompt_registry_publish_keeps_single_global_active(tmp_path) -> None:
    """Publishing a revision must leave exactly one active revision globally."""
    from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES, PromptRegistry

    registry = PromptRegistry(db_path=tmp_path / "prompt-registry.db")
    first = registry.create_revision(
        slug="campaign-a",
        templates=DEFAULT_TEMPLATES,
        persona=DEFAULT_PERSONA,
    )
    registry.publish_revision(first["id"])

    second = registry.create_revision(
        slug="campaign-b",
        templates=DEFAULT_TEMPLATES,
        persona={**DEFAULT_PERSONA, "name": "Dina"},
    )
    registry.publish_revision(second["id"])

    revisions = registry.list_revisions()
    active_ids = [revision["id"] for revision in revisions if revision["status"] == "active"]

    assert active_ids == [second["id"]]
    assert registry.get_active_revision()["id"] == second["id"]


def test_prompt_registry_rejects_missing_required_template_keys(tmp_path) -> None:
    """Prompt registry should validate required template keys before storing drafts."""
    from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES, PromptRegistry

    registry = PromptRegistry(db_path=tmp_path / "prompt-registry.db")
    invalid_templates = dict(DEFAULT_TEMPLATES)
    invalid_templates.pop("selling_script")

    with pytest.raises(ValueError, match="selling_script"):
        registry.create_revision(
            slug="invalid-campaign",
            templates=invalid_templates,
            persona=DEFAULT_PERSONA,
        )


def test_persona_build_system_prompt_supports_v2_affiliate_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    """System prompt formatting should accept v2 affiliate persona placeholders without KeyError."""
    from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES
    from src.brain.persona import PersonaEngine

    revision = {
        "persona": {
            **DEFAULT_PERSONA,
            "role": "affiliate_host",
            "product_relationship": "recommender_not_owner",
            "knowledge_boundaries": ["cannot_confirm_stock", "cannot_claim_medical_results"],
            "viewer_address_terms": ["kak", "bestie"],
            "soft_cta_patterns": ["cek linknya ya kak", "lihat dulu di keranjang kuning"],
            "unknown_answer_policy": "redirect_to_product_page",
        },
        "templates": {
            **DEFAULT_TEMPLATES,
            "system_base": (
                "Kamu adalah {name} dengan role {role}. "
                "Relasi produk: {product_relationship}. "
                "Batas pengetahuan: {knowledge_boundaries}. "
                "Sapaan: {viewer_address_terms}. "
                "Soft CTA: {soft_cta_patterns}. "
                "Unknown answer policy: {unknown_answer_policy}."
            ),
        },
    }

    class DummyRegistry:
        def get_active_revision(self) -> dict[str, object]:
            return revision

    monkeypatch.setattr("src.brain.persona.get_prompt_registry", lambda: DummyRegistry())

    prompt = PersonaEngine().build_system_prompt(state="SELLING", product_context="Lip Cream - Rp 89.000")

    assert "affiliate_host" in prompt
    assert "recommender_not_owner" in prompt
    assert "cannot_confirm_stock" in prompt
    assert "cek linknya ya kak" in prompt


def test_persona_build_chat_reply_prompt_uses_task_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """Chat reply builder should format viewer and product context through the registry template."""
    from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES
    from src.brain.persona import PersonaEngine

    revision = {
        "persona": DEFAULT_PERSONA,
        "templates": {
            **DEFAULT_TEMPLATES,
            "chat_reply": "Viewer {viewer_name} bilang: {viewer_message}. Produk: {product_context}.",
        },
    }

    class DummyRegistry:
        def get_active_revision(self) -> dict[str, object]:
            return revision

    monkeypatch.setattr("src.brain.persona.get_prompt_registry", lambda: DummyRegistry())

    prompt = PersonaEngine().build_chat_reply_prompt(
        viewer_name="Ayu",
        viewer_message="Kak ini ori ga?",
        product_context="Wireless Earbuds Pro ANC",
    )

    assert "Ayu" in prompt
    assert "Kak ini ori ga?" in prompt
    assert "Wireless Earbuds Pro ANC" in prompt


def test_persona_build_product_qa_prompt_uses_task_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """Product QA builder should format question and product context through the registry template."""
    from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES
    from src.brain.persona import PersonaEngine

    revision = {
        "persona": DEFAULT_PERSONA,
        "templates": {
            **DEFAULT_TEMPLATES,
            "product_qa": "Pertanyaan: {question}. Konteks: {product_context}.",
        },
    }

    class DummyRegistry:
        def get_active_revision(self) -> dict[str, object]:
            return revision

    monkeypatch.setattr("src.brain.persona.get_prompt_registry", lambda: DummyRegistry())

    prompt = PersonaEngine().build_product_qa_prompt(
        question="Bisa buat olahraga?",
        product_context="Waterproof untuk olahraga",
    )

    assert "Bisa buat olahraga?" in prompt
    assert "Waterproof untuk olahraga" in prompt


def test_persona_build_safety_check_prompt_uses_task_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """Safety check builder should format candidate text and context through the registry template."""
    from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES
    from src.brain.persona import PersonaEngine

    revision = {
        "persona": DEFAULT_PERSONA,
        "templates": {
            **DEFAULT_TEMPLATES,
            "safety_check": "Candidate: {candidate_text}. Product: {product_context}.",
        },
    }

    class DummyRegistry:
        def get_active_revision(self) -> dict[str, object]:
            return revision

    monkeypatch.setattr("src.brain.persona.get_prompt_registry", lambda: DummyRegistry())

    prompt = PersonaEngine().build_safety_check_prompt(
        candidate_text="Ini pasti bikin putih dalam 3 hari",
        product_context="Jangan klaim hasil absolut",
    )

    assert "Ini pasti bikin putih dalam 3 hari" in prompt
    assert "Jangan klaim hasil absolut" in prompt


def test_persona_build_emotion_prompt_prefers_registry_template(monkeypatch: pytest.MonkeyPatch) -> None:
    """Emotion prompt should come from the registry template when available."""
    from src.brain.prompt_registry import DEFAULT_PERSONA, DEFAULT_TEMPLATES
    from src.brain.persona import PersonaEngine

    revision = {
        "persona": DEFAULT_PERSONA,
        "templates": {
            **DEFAULT_TEMPLATES,
            "emotion_detect": "Recent chats: {recent_chats}. Return JSON only.",
        },
    }

    class DummyRegistry:
        def get_active_revision(self) -> dict[str, object]:
            return revision

    monkeypatch.setattr("src.brain.persona.get_prompt_registry", lambda: DummyRegistry())

    prompt = PersonaEngine().build_emotion_prompt(["mau dong", "berapa harga kak"])

    assert "mau dong" in prompt
    assert "berapa harga kak" in prompt
    assert "Return JSON only." in prompt


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
