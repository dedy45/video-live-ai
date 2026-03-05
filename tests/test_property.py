"""Property tests using Hypothesis.

Requirements: 19.11 — Configuration round-trip
"""
import pytest
from hypothesis import given, settings, strategies as st
from pydantic import ValidationError

from src.config.loader import AppConfig, LLMProviderConfig

@given(
    name=st.text(min_size=1),
    version=st.from_regex(r"^[0-9]+\.[0-9]+\.[0-9]+$"),
    env=st.sampled_from(["development", "production", "test"])
)
@settings(max_examples=50)
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
