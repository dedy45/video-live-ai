"""Shared utilities — logging, mocking, validation, health checks, resilience, tracing."""

from src.utils.logging import generate_trace_id, get_logger, setup_logging
from src.utils.mock_mode import (
    MockAudioResult,
    MockAvatarRenderer,
    MockVideoFrame,
    MockVoiceSynthesizer,
    get_mock_avatar,
    get_mock_voice,
)
from src.utils.validators import (
    ValidationResult,
    validate_all_assets,
    validate_avatar_photo,
    validate_background_image,
    validate_product_image,
    validate_voice_sample,
)
from src.utils.health import HealthManager, HealthStatus, get_health_manager

# Lazy imports — these have external dependencies (starlette, torch)
# Import them directly from their modules when needed:
#   from src.utils.gpu_manager import GPUMemoryManager
#   from src.utils.retry import retry_async
#   from src.utils.circuit_breaker import CircuitBreaker
#   from src.utils.tracing import TracingMiddleware

__all__ = [
    # Logging
    "generate_trace_id",
    "get_logger",
    "setup_logging",
    # Mock
    "MockAudioResult",
    "MockAvatarRenderer",
    "MockVideoFrame",
    "MockVoiceSynthesizer",
    "get_mock_avatar",
    "get_mock_voice",
    # Validation
    "ValidationResult",
    "validate_all_assets",
    "validate_avatar_photo",
    "validate_background_image",
    "validate_product_image",
    "validate_voice_sample",
    # Health
    "HealthManager",
    "HealthStatus",
    "get_health_manager",
]
