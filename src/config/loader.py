"""Configuration loader for AI Live Commerce Platform.

Loads config.yaml + .env with environment variable overrides.
Validates schema and provides typed access to all settings.
Requirements: 12.1, 12.2, 12.3, 12.5, 12.9
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


# ─── Pydantic Config Models ───────────────────────────────────────

class LLMProviderConfig(BaseModel):
    model: str
    max_tokens: int = 150
    timeout_ms: int = 500
    tasks: list[str] = Field(default_factory=list)


class LLMConfig(BaseModel):
    gemini: LLMProviderConfig = LLMProviderConfig(model="gemini-2.0-flash")
    claude: LLMProviderConfig = LLMProviderConfig(model="claude-sonnet-4-20250514", max_tokens=2000, timeout_ms=5000)
    gpt4o: LLMProviderConfig = LLMProviderConfig(model="gpt-4o-mini", max_tokens=200, timeout_ms=1000)
    qwen: LLMProviderConfig = LLMProviderConfig(model="qwen-local", max_tokens=100)
    fallback_order: list[str] = Field(default_factory=lambda: ["gemini", "gpt4o", "qwen"])
    daily_budget_usd: float = 5.0


class EmotionParams(BaseModel):
    pitch: float = 1.0
    speed: float = 1.0
    energy: float = 1.0


class VoiceConfig(BaseModel):
    primary: str = "fish_speech"
    backup: str = "edge_tts"
    sample_rate: int = 24000
    bitrate: int = 128000
    cache_max_mb: int = 1024
    emotion_mapping: dict[str, EmotionParams] = Field(default_factory=dict)


class TemporalSmootherConfig(BaseModel):
    window_size: int = 3
    blend_weight: float = 0.7


class GFPGANConfig(BaseModel):
    enabled: bool = True
    upscale_factor: int = 2


class LiveTalkingConfig(BaseModel):
    enabled: bool = False
    reference_video: str = "assets/avatar/reference.mp4"
    reference_audio: str = "assets/avatar/reference.wav"
    use_webrtc: bool = False
    use_rtmp: bool = True
    livetalking_fps: int = 30
    livetalking_resolution: list[int] = Field(default_factory=lambda: [512, 512])
    port: int = 8010
    transport: str = "webrtc"
    model: str = "wav2lip"
    avatar_id: str = "wav2lip256_avatar1"


class AvatarConfig(BaseModel):
    engine: str = "musetalk"
    reference_image: str = "assets/avatar/face.png"
    resolution: list[int] = Field(default_factory=lambda: [512, 512])
    fps: int = 30
    identity_reset_minutes: int = 15
    temporal_smoother: TemporalSmootherConfig = TemporalSmootherConfig()
    gfpgan: GFPGANConfig = GFPGANConfig()
    livetalking: LiveTalkingConfig = LiveTalkingConfig()


class ReconnectConfig(BaseModel):
    max_attempts: int = 5
    backoff_base_sec: int = 1
    backoff_max_sec: int = 30


class StreamingConfig(BaseModel):
    video_codec: str = "h264"
    video_bitrate: str = "2500k"
    audio_codec: str = "aac"
    audio_bitrate: str = "128k"
    keyframe_interval: int = 60
    preset: str = "veryfast"
    tune: str = "zerolatency"
    buffer_size_sec: int = 3
    reconnect: ReconnectConfig = ReconnectConfig()


class LatencyBudget(BaseModel):
    chat_processing_ms: int = 50
    llm_response_ms: int = 200
    tts_ms: int = 500
    avatar_rendering_ms: int = 800
    composition_ms: int = 100
    streaming_buffer_ms: int = 350


class PerformanceConfig(BaseModel):
    e2e_latency_target_ms: int = 2000
    latency_budget: LatencyBudget = LatencyBudget()


class GPUConfig(BaseModel):
    device: str = "cuda:0"
    vram_budget_mb: int = 20000
    degradation_threshold: float = 0.90
    temp_max_celsius: int = 80


class LoggingConfig(BaseModel):
    level: str = "DEBUG"
    format: str = "json"
    file: str = "data/logs/app.log"
    rotate_days: int = 30
    components: dict[str, str] = Field(default_factory=dict)


class CompositionConfig(BaseModel):
    resolution: list[int] = Field(default_factory=lambda: [720, 1280])
    fps: int = 30
    encoding: str = "libx264"
    bitrate: str = "4M"
    avatar_anchor_pct: float = 0.30
    product_focus_pct: float = 0.60


class DashboardConfig(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])


class AppConfig(BaseModel):
    name: str = "AI Live Commerce"
    version: str = "0.1.0"
    env: str = "development"


# ─── Root Config ──────────────────────────────────────────────────

class Config(BaseModel):
    """Root configuration model — single source of truth."""

    app: AppConfig = AppConfig()
    llm_providers: LLMConfig = LLMConfig()
    voice: VoiceConfig = VoiceConfig()
    avatar: AvatarConfig = AvatarConfig()
    composition: CompositionConfig = CompositionConfig()
    streaming: StreamingConfig = StreamingConfig()
    performance: PerformanceConfig = PerformanceConfig()
    gpu: GPUConfig = GPUConfig()
    logging: LoggingConfig = LoggingConfig()
    dashboard: DashboardConfig = DashboardConfig()


# ─── Environment Settings (from .env) ────────────────────────────

class EnvSettings(BaseSettings):
    """Environment variables loaded from .env file."""

    # LLM Keys
    gemini_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Platform
    tiktok_session_id: str = ""
    shopee_api_key: str = ""

    # Groq
    groq_api_key: str = ""

    # Local LLM
    local_llm_url: str = "http://localhost:11434/v1"

    # Streaming
    tiktok_rtmp_url: str = ""
    tiktok_stream_key: str = ""
    shopee_rtmp_url: str = ""
    shopee_stream_key: str = ""

    # System
    mock_mode: bool = True
    env: str = "development"
    log_level: str = "DEBUG"

    # LiveTalking
    livetalking_enabled: bool = False
    livetalking_reference_video: str = "assets/avatar/reference.mp4"
    livetalking_reference_audio: str = "assets/avatar/reference.wav"
    livetalking_use_webrtc: bool = False
    livetalking_use_rtmp: bool = True
    livetalking_fps: int = 30
    livetalking_resolution: str = "512,512"

    # GPU
    gpu_device: str = "cuda:0"

    # Dashboard
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8000
    dashboard_username: str = "admin"
    dashboard_password: str = "changeme"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


# ─── Loader ───────────────────────────────────────────────────────

_config: Config | None = None
_env: EnvSettings | None = None


def load_config(
    config_path: str | Path | None = None,
    env_path: str | Path | None = None,
) -> Config:
    """Load and validate configuration from YAML + .env.

    Args:
        config_path: Path to config.yaml. Defaults to config/config.yaml.
        env_path: Path to .env file. Defaults to .env.

    Returns:
        Validated Config instance.
    """
    global _config

    # Resolve paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    if config_path is None:
        config_path = project_root / "config" / "config.yaml"
    if env_path is None:
        env_path = project_root / ".env"

    # Load .env
    if Path(env_path).exists():
        load_dotenv(env_path)

    # Load YAML
    config_data: dict[str, Any] = {}
    config_file = Path(config_path)
    if config_file.exists():
        with open(config_file, "r", encoding="utf-8") as f:
            config_data = yaml.safe_load(f) or {}

    # Apply env overrides
    env_name = os.getenv("ENV", config_data.get("app", {}).get("env", "development"))
    if "app" not in config_data:
        config_data["app"] = {}
    config_data["app"]["env"] = env_name

    gpu_device = os.getenv("GPU_DEVICE")
    if gpu_device:
        if "gpu" not in config_data:
            config_data["gpu"] = {}
        config_data["gpu"]["device"] = gpu_device

    log_level = os.getenv("LOG_LEVEL")
    if log_level:
        if "logging" not in config_data:
            config_data["logging"] = {}
        config_data["logging"]["level"] = log_level

    # LiveTalking env overrides
    lt_enabled = os.getenv("LIVETALKING_ENABLED")
    if lt_enabled is not None:
        if "avatar" not in config_data:
            config_data["avatar"] = {}
        if "livetalking" not in config_data["avatar"]:
            config_data["avatar"]["livetalking"] = {}
        lt = config_data["avatar"]["livetalking"]
        lt["enabled"] = lt_enabled.lower() in ("true", "1", "yes")

        for env_key, cfg_key in [
            ("LIVETALKING_REFERENCE_VIDEO", "reference_video"),
            ("LIVETALKING_REFERENCE_AUDIO", "reference_audio"),
        ]:
            val = os.getenv(env_key)
            if val:
                lt[cfg_key] = val

        lt_webrtc = os.getenv("LIVETALKING_USE_WEBRTC")
        if lt_webrtc is not None:
            lt["use_webrtc"] = lt_webrtc.lower() in ("true", "1", "yes")
        lt_rtmp = os.getenv("LIVETALKING_USE_RTMP")
        if lt_rtmp is not None:
            lt["use_rtmp"] = lt_rtmp.lower() in ("true", "1", "yes")
        lt_fps = os.getenv("LIVETALKING_FPS")
        if lt_fps:
            lt["livetalking_fps"] = int(lt_fps)
        lt_res = os.getenv("LIVETALKING_RESOLUTION")
        if lt_res:
            lt["livetalking_resolution"] = [int(x) for x in lt_res.split(",")]

        # Switch engine to livetalking when enabled
        if lt.get("enabled"):
            config_data["avatar"]["engine"] = "livetalking"

    _config = Config(**config_data)
    return _config


def get_config() -> Config:
    """Get the loaded config. Raises if not loaded yet."""
    if _config is None:
        return load_config()
    return _config


def load_env() -> EnvSettings:
    """Load environment settings."""
    global _env
    if _env is None:
        _env = EnvSettings()  # type: ignore[call-arg]
    return _env


def get_env() -> EnvSettings:
    """Get loaded env settings."""
    if _env is None:
        return load_env()
    return _env


def is_mock_mode() -> bool:
    """Check if running in Mock Mode (no GPU)."""
    return os.getenv("MOCK_MODE", "true").lower() in ("true", "1", "yes")
