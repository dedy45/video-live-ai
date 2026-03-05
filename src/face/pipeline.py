"""Layer 3: Face — Avatar Rendering Pipeline.

Manages MuseTalk lip-sync, GFPGAN face enhancement, and temporal smoothing.
Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.6, 4.7
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import deque
from dataclasses import dataclass, field
from typing import Any, AsyncIterator

import numpy as np

from src.config import get_config, is_mock_mode
from src.utils.logging import get_logger
from src.utils.mock_mode import MockAvatarRenderer, MockVideoFrame

logger = get_logger("face")


@dataclass
class VideoFrame:
    """Single video frame — production format."""

    pixels: np.ndarray
    timestamp_ms: float
    width: int = 512
    height: int = 512
    frame_number: int = 0
    enhanced: bool = False
    trace_id: str = ""


class BaseAvatarEngine(ABC):
    """Abstract avatar rendering engine."""

    @abstractmethod
    async def generate_frames(
        self,
        audio_data: bytes,
        duration_ms: float,
        trace_id: str = "",
    ) -> AsyncIterator[VideoFrame]:
        """Generate lip-synced video frames from audio."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        ...


class MuseTalkEngine(BaseAvatarEngine):
    """MuseTalk lip-sync engine — GPU-accelerated avatar rendering.

    Requirements: 4.1, 4.2 — Real-time lip-sync from audio.
    Uses MuseTalk model for generating talking-head video frames.
    """

    def __init__(
        self,
        reference_image: str = "assets/avatar/face.png",
        resolution: tuple[int, int] = (512, 512),
        fps: int = 30,
    ) -> None:
        self.reference_image = reference_image
        self.resolution = resolution
        self.fps = fps
        self._model: Any = None
        logger.info(
            "musetalk_init",
            reference=reference_image,
            resolution=resolution,
            fps=fps,
        )

    async def generate_frames(
        self,
        audio_data: bytes,
        duration_ms: float,
        trace_id: str = "",
    ) -> AsyncIterator[VideoFrame]:
        if is_mock_mode():
            mock = MockAvatarRenderer(self.resolution[0], self.resolution[1])
            async for mock_frame in mock.generate_stream(audio_data, duration_ms):
                yield VideoFrame(
                    pixels=mock_frame.pixels,
                    timestamp_ms=mock_frame.timestamp_ms,
                    width=mock_frame.width,
                    height=mock_frame.height,
                    trace_id=trace_id,
                )
            return

        # Production: run MuseTalk inference on GPU
        raise NotImplementedError("MuseTalk GPU inference requires GPU server deployment")

    async def health_check(self) -> bool:
        if is_mock_mode():
            return True
        return self._model is not None


class GFPGANEnhancer:
    """GFPGAN face enhancement — improves face quality.

    Requirements: 4.3 — face restoration and enhancement.
    Applied after MuseTalk to fix artifacts and improve sharpness.
    """

    def __init__(self, upscale_factor: int = 2) -> None:
        self.upscale_factor = upscale_factor
        self._model: Any = None
        logger.info("gfpgan_init", upscale=upscale_factor)

    async def enhance(self, frame: VideoFrame) -> VideoFrame:
        """Enhance a single video frame with GFPGAN."""
        if is_mock_mode():
            frame.enhanced = True
            return frame

        # Production: GFPGAN inference
        raise NotImplementedError("GFPGAN requires GPU server deployment")

    async def health_check(self) -> bool:
        if is_mock_mode():
            return True
        return self._model is not None


class TemporalSmoother:
    """Temporal smoothing to reduce jitter between frames.

    Requirements: 4.4 — weighted averaging of recent frames
    to prevent visual flickering and ensure smooth transitions.
    """

    def __init__(self, window_size: int = 3, blend_weight: float = 0.7) -> None:
        self.window_size = window_size
        self.blend_weight = blend_weight
        self._buffer: deque[np.ndarray] = deque(maxlen=window_size)

    def smooth(self, frame: VideoFrame) -> VideoFrame:
        """Apply temporal smoothing to a frame."""
        self._buffer.append(frame.pixels.copy())

        if len(self._buffer) < 2:
            return frame

        # Weighted average of recent frames
        blended = frame.pixels.astype(np.float32) * self.blend_weight
        weight_remaining = 1.0 - self.blend_weight
        for prev_frame in list(self._buffer)[:-1]:
            w = weight_remaining / (len(self._buffer) - 1)
            blended += prev_frame.astype(np.float32) * w

        frame.pixels = blended.astype(np.uint8)
        return frame

    def reset(self) -> None:
        """Reset buffer (e.g., on identity reset)."""
        self._buffer.clear()


class IdentityController:
    """Identity drift prevention.

    Requirements: 4.5 — periodic identity reset every N minutes
    by re-injecting the reference face into the pipeline.
    """

    def __init__(self, reset_interval_min: int = 15) -> None:
        self.reset_interval_sec = reset_interval_min * 60
        self._last_reset = time.time()
        self._reset_count = 0

    def needs_reset(self) -> bool:
        """Check if identity reset is needed."""
        return (time.time() - self._last_reset) >= self.reset_interval_sec

    def mark_reset(self) -> None:
        """Record an identity reset."""
        self._last_reset = time.time()
        self._reset_count += 1
        logger.info("identity_reset", count=self._reset_count)


class AvatarPipeline:
    """Full avatar rendering pipeline: MuseTalk → GFPGAN → Smoother.

    Orchestrates the face rendering components into a complete pipeline.
    """

    def __init__(self) -> None:
        config = get_config()
        avatar_cfg = config.avatar

        self.engine = MuseTalkEngine(
            reference_image=avatar_cfg.reference_image,
            resolution=tuple(avatar_cfg.resolution),
            fps=avatar_cfg.fps,
        )
        self.enhancer = GFPGANEnhancer(
            upscale_factor=avatar_cfg.gfpgan.upscale_factor,
        )
        self.smoother = TemporalSmoother(
            window_size=avatar_cfg.temporal_smoother.window_size,
            blend_weight=avatar_cfg.temporal_smoother.blend_weight,
        )
        self.identity = IdentityController(
            reset_interval_min=avatar_cfg.identity_reset_minutes,
        )

        logger.info("avatar_pipeline_init")

    async def render(
        self,
        audio_data: bytes,
        duration_ms: float,
        trace_id: str = "",
    ) -> AsyncIterator[VideoFrame]:
        """Full rendering pipeline: generate → enhance → smooth.

        Yields processed video frames ready for composition.
        """
        # Check identity drift
        if self.identity.needs_reset():
            self.smoother.reset()
            self.identity.mark_reset()

        frame_num = 0
        async for frame in self.engine.generate_frames(audio_data, duration_ms, trace_id):
            frame.frame_number = frame_num
            frame_num += 1

            # GFPGAN enhancement
            if not is_mock_mode():
                frame = await self.enhancer.enhance(frame)

            # Temporal smoothing
            frame = self.smoother.smooth(frame)

            yield frame
