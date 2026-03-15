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
    assert config.dashboard.port == 8001


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


def test_env_dashboard_port_default_matches_runtime_port() -> None:
    """Env defaults should align with the canonical app port."""
    from src.config.loader import EnvSettings

    env = EnvSettings()
    assert env.dashboard_port == 8001


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


def test_voice_training_config_defaults() -> None:
    """Voice training config should have proper defaults."""
    from src.config.loader import VoiceConfig

    voice = VoiceConfig()
    assert voice.training_enabled is False
    assert voice.training_dataset_path == "assets/voice/training_dataset/"
    assert voice.training_epochs == 100
    assert voice.training_batch_size == 8
    assert voice.training_learning_rate == 1e-4
    assert voice.trained_model_path is None


def test_voice_training_env_overrides(tmp_path: Path) -> None:
    """Voice training config should respect environment variable overrides."""
    import src.config.loader as loader_module
    
    # Clear global config
    loader_module._config = None
    
    # Set training env vars
    old_vars = {}
    test_vars = {
        "VOICE_TRAINING_ENABLED": "true",
        "VOICE_TRAINING_EPOCHS": "200",
        "VOICE_TRAINING_BATCH_SIZE": "16",
        "VOICE_TRAINING_LEARNING_RATE": "0.0002",
        "VOICE_TRAINED_MODEL_PATH": "external/fish-speech/checkpoints/trained/test.ckpt",
        "VOICE_TRAINING_DATASET_PATH": "assets/voice/custom_dataset/",
    }
    
    for key, value in test_vars.items():
        old_vars[key] = os.environ.get(key)
        os.environ[key] = value
    
    # Use empty env file to avoid conflicts
    empty_env = tmp_path / ".env.empty"
    empty_env.write_text("")
    
    try:
        config = loader_module.load_config(env_path=empty_env)
        assert config.voice.training_enabled is True
        assert config.voice.training_epochs == 200
        assert config.voice.training_batch_size == 16
        assert config.voice.training_learning_rate == 0.0002
        assert config.voice.trained_model_path == "external/fish-speech/checkpoints/trained/test.ckpt"
        assert config.voice.training_dataset_path == "assets/voice/custom_dataset/"
    finally:
        # Restore env vars
        for key, old_value in old_vars.items():
            if old_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old_value
        loader_module._config = None
