"""Tests for configuration loader."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

# Set mock mode for tests
os.environ["MOCK_MODE"] = "true"


def test_config_loads_defaults() -> None:
    """Config should load with sensible defaults even without config.yaml."""
    from src.config.loader import Config

    config = Config()
    assert config.app.name == "AI Live Commerce"
    assert config.app.version == "0.1.0"
    assert config.gpu.vram_budget_mb == 20000
    assert config.performance.e2e_latency_target_ms == 2000


def test_config_loads_from_yaml(tmp_path: Path) -> None:
    """Config should parse values from a YAML file."""
    yaml_content = """
app:
  name: "Test App"
  version: "0.0.1"
gpu:
  device: "cuda:1"
"""
    yaml_file = tmp_path / "test_config.yaml"
    yaml_file.write_text(yaml_content)

    # Clear env vars that could override YAML and reset global config
    import src.config.loader as loader_module
    loader_module._config = None
    old_gpu = os.environ.pop("GPU_DEVICE", None)
    old_env = os.environ.pop("ENV", None)
    # Use a non-existent .env so load_dotenv won't re-inject GPU_DEVICE
    empty_env = tmp_path / ".env.empty"
    empty_env.write_text("")
    try:
        config = loader_module.load_config(config_path=yaml_file, env_path=empty_env)
        assert config.app.name == "Test App"
        assert config.app.version == "0.0.1"
        assert config.gpu.device == "cuda:1"
    finally:
        # Restore env vars
        if old_gpu is not None:
            os.environ["GPU_DEVICE"] = old_gpu
        if old_env is not None:
            os.environ["ENV"] = old_env
        loader_module._config = None


def test_is_mock_mode() -> None:
    """Mock mode check should read from environment."""
    os.environ["MOCK_MODE"] = "true"
    from src.config.loader import is_mock_mode

    assert is_mock_mode() is True

    os.environ["MOCK_MODE"] = "false"
    assert is_mock_mode() is False

    # Reset
    os.environ["MOCK_MODE"] = "true"


def test_llm_config_defaults() -> None:
    """LLM config should have proper defaults."""
    from src.config.loader import LLMConfig

    llm = LLMConfig()
    assert llm.gemini.model == "gemini-2.0-flash"
    assert llm.claude.max_tokens == 2000
    assert llm.daily_budget_usd == 5.0
    assert "gemini" in llm.fallback_order


def test_latency_budget_sums_correctly() -> None:
    """All latency budget components should sum to ≤ e2e target."""
    from src.config.loader import PerformanceConfig

    perf = PerformanceConfig()
    budget = perf.latency_budget
    total = (
        budget.chat_processing_ms
        + budget.llm_response_ms
        + budget.tts_ms
        + budget.avatar_rendering_ms
        + budget.composition_ms
        + budget.streaming_buffer_ms
    )
    assert total == perf.e2e_latency_target_ms, (
        f"Latency budget ({total}ms) must equal target ({perf.e2e_latency_target_ms}ms)"
    )
