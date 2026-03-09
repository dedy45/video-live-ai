"""Property tests using Hypothesis.

Requirements: 19.11 — Configuration round-trip
"""
import pytest
from hypothesis import HealthCheck, given, settings, strategies as st
from pydantic import ValidationError

from src.config.loader import AppConfig, LLMProviderConfig, VoiceConfig

@given(
    name=st.text(min_size=1, max_size=128),
    version=st.tuples(
        st.integers(min_value=0, max_value=999),
        st.integers(min_value=0, max_value=999),
        st.integers(min_value=0, max_value=999),
    ).map(lambda parts: f"{parts[0]}.{parts[1]}.{parts[2]}"),
    env=st.sampled_from(["development", "production", "test"])
)
@settings(max_examples=50, suppress_health_check=[HealthCheck.too_slow])
def test_app_config_property(name: str, version: str, env: str):
    """Property test: AppConfig should accept and preserve valid strings."""
    config = AppConfig(name=name, version=version, env=env)
    assert config.name == name
    assert config.version == version
    assert config.env == env

@given(
    model=st.text(min_size=1),
    max_tokens=st.integers(min_value=1, max_value=8000),
    timeout_ms=st.integers(min_value=100, max_value=30000)
)
@settings(max_examples=50)
def test_llm_provider_property(model: str, max_tokens: int, timeout_ms: int):
    """Property test: LLM parameters bounds."""
    config = LLMProviderConfig(model=model, max_tokens=max_tokens, timeout_ms=timeout_ms)
    assert config.model == model
    assert config.max_tokens == max_tokens
    assert config.timeout_ms == timeout_ms


def test_voice_config_includes_fish_speech_runtime_fields():
    """VoiceConfig must include Fish-Speech local sidecar fields."""
    cfg = VoiceConfig()
    assert hasattr(cfg, "fish_speech_base_url")
    assert hasattr(cfg, "fish_speech_timeout_ms")
    assert hasattr(cfg, "clone_reference_wav")
    assert hasattr(cfg, "clone_reference_text")
    assert hasattr(cfg, "indonesian_smoke_text")


def test_voice_config_defaults_are_sane():
    """VoiceConfig defaults must be sensible for local development."""
    cfg = VoiceConfig()
    assert cfg.fish_speech_base_url == "http://127.0.0.1:8080"
    assert cfg.fish_speech_timeout_ms > 0
    assert "reference.wav" in cfg.clone_reference_wav
    assert "reference.txt" in cfg.clone_reference_text
    assert len(cfg.indonesian_smoke_text) > 0


def test_voice_config_loaded_from_yaml():
    """get_config().voice must have Fish-Speech fields from config.yaml."""
    from src.config import get_config
    cfg = get_config()
    assert cfg.voice.fish_speech_base_url == "http://127.0.0.1:8080"
    assert cfg.voice.fish_speech_timeout_ms > 0
    assert cfg.voice.clone_reference_wav == "assets/voice/reference.wav"
    assert cfg.voice.clone_reference_text == "assets/voice/reference.txt"
