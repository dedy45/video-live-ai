"""GPU Memory Manager — Monitors and manages GPU VRAM usage.

Implements graceful degradation strategy when GPU memory is constrained.
Requirements: 9.1, 9.2, 9.3, 9.4
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.config import is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("gpu")


@dataclass
class GPUStatus:
    """Current GPU status snapshot."""

    available: bool = False
    device_name: str = "unknown"
    vram_total_mb: int = 0
    vram_used_mb: int = 0
    vram_free_mb: int = 0
    utilization_pct: float = 0.0
    temperature_c: int = 0


class DegradationLevel:
    """Degradation stages — applied progressively as VRAM drops."""

    NORMAL = 0        # Full quality
    REDUCED_BATCH = 1  # Reduce batch size
    REDUCED_RES = 2    # Reduce resolution to 256px
    NO_GFPGAN = 3      # Disable face enhancement
    CPU_TTS = 4        # Move TTS to CPU
    EMERGENCY = 5      # Stop GPU-intensive work


class GPUMemoryManager:
    """Monitors GPU VRAM and enforces degradation strategy.

    Degradation order (Requirements 9.3):
    1. Reduce batch size
    2. Reduce resolution (512 → 256)
    3. Disable GFPGAN
    4. Switch TTS to CPU
    5. Emergency — halt GPU work
    """

    def __init__(
        self,
        vram_budget_mb: int = 20_000,
        degradation_threshold: float = 0.90,
        temp_max_celsius: int = 80,
    ) -> None:
        self.vram_budget_mb = vram_budget_mb
        self.degradation_threshold = degradation_threshold
        self.temp_max_celsius = temp_max_celsius
        self.degradation_level = DegradationLevel.NORMAL
        self._torch_available = False

        if not is_mock_mode():
            try:
                import torch
                self._torch_available = torch.cuda.is_available()
            except ImportError:
                self._torch_available = False

        logger.info(
            "gpu_manager_init",
            torch_available=self._torch_available,
            budget_mb=vram_budget_mb,
        )

    def get_status(self) -> GPUStatus:
        """Get current GPU status."""
        if is_mock_mode() or not self._torch_available:
            return GPUStatus(
                available=False,
                device_name="Mock GPU" if is_mock_mode() else "No GPU",
                vram_total_mb=self.vram_budget_mb,
                vram_used_mb=0,
                vram_free_mb=self.vram_budget_mb,
            )

        try:
            import torch
            device = torch.cuda.current_device()
            props = torch.cuda.get_device_properties(device)
            mem_total = props.total_mem // (1024 * 1024)
            mem_used = torch.cuda.memory_allocated(device) // (1024 * 1024)
            mem_free = mem_total - mem_used

            return GPUStatus(
                available=True,
                device_name=props.name,
                vram_total_mb=mem_total,
                vram_used_mb=mem_used,
                vram_free_mb=mem_free,
                utilization_pct=round(mem_used / mem_total * 100, 1) if mem_total > 0 else 0,
            )
        except Exception as e:
            logger.error("gpu_status_error", error=str(e))
            return GPUStatus(available=False)

    def check_and_degrade(self) -> int:
        """Check VRAM and adjust degradation level if needed.

        Returns current degradation level.
        """
        status = self.get_status()
        if not status.available:
            return self.degradation_level

        usage_ratio = status.vram_used_mb / max(status.vram_total_mb, 1)

        old_level = self.degradation_level

        if usage_ratio >= 0.98:
            self.degradation_level = DegradationLevel.EMERGENCY
        elif usage_ratio >= 0.95:
            self.degradation_level = DegradationLevel.CPU_TTS
        elif usage_ratio >= self.degradation_threshold:
            self.degradation_level = DegradationLevel.NO_GFPGAN
        elif usage_ratio >= 0.80:
            self.degradation_level = DegradationLevel.REDUCED_RES
        elif usage_ratio >= 0.70:
            self.degradation_level = DegradationLevel.REDUCED_BATCH
        else:
            self.degradation_level = DegradationLevel.NORMAL

        if self.degradation_level != old_level:
            logger.warning(
                "gpu_degradation_change",
                old_level=old_level,
                new_level=self.degradation_level,
                vram_usage_pct=round(usage_ratio * 100, 1),
            )

        return self.degradation_level

    def clear_cache(self) -> None:
        """Clear CUDA cache to free unused memory."""
        if self._torch_available and not is_mock_mode():
            try:
                import torch
                torch.cuda.empty_cache()
                logger.info("gpu_cache_cleared")
            except Exception as e:
                logger.error("gpu_cache_clear_error", error=str(e))

    async def health_check(self) -> bool:
        """GPU health check for HealthManager."""
        if is_mock_mode():
            return True
        status = self.get_status()
        return status.available and status.utilization_pct < 99

    @property
    def should_use_gfpgan(self) -> bool:
        return self.degradation_level < DegradationLevel.NO_GFPGAN

    @property
    def should_use_gpu_tts(self) -> bool:
        return self.degradation_level < DegradationLevel.CPU_TTS

    @property
    def target_resolution(self) -> int:
        if self.degradation_level >= DegradationLevel.REDUCED_RES:
            return 256
        return 512
