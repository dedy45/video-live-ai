"""Mock Mode — GPU-less local development.

Provides stub implementations for Avatar and Voice that return
placeholder outputs, enabling full state machine testing locally.
Requirements: 31.1, 31.2, 31.3, 31.4, 31.5
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import AsyncIterator

import numpy as np

from src.config import is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("mock")


@dataclass
class MockAudioResult:
    """Mock audio result matching production format."""

    audio_data: bytes = b""
    duration_ms: float = 0.0
    sample_rate: int = 24000
    format: str = "wav"

    @classmethod
    def silence(cls, duration_ms: float = 1000.0) -> "MockAudioResult":
        """Generate silent audio placeholder."""
        sample_rate = 24000
        num_samples = int(sample_rate * duration_ms / 1000)
        silence = np.zeros(num_samples, dtype=np.int16)
        return cls(
            audio_data=silence.tobytes(),
            duration_ms=duration_ms,
            sample_rate=sample_rate,
        )


@dataclass
class MockVideoFrame:
    """Mock video frame matching production format."""

    pixels: np.ndarray = field(default_factory=lambda: np.zeros((512, 512, 3), dtype=np.uint8))
    timestamp_ms: float = 0.0
    width: int = 512
    height: int = 512

    @classmethod
    def placeholder(cls, width: int = 512, height: int = 512) -> "MockVideoFrame":
        """Generate a colored placeholder frame."""
        frame = np.full((height, width, 3), fill_value=128, dtype=np.uint8)
        # Draw a simple face-like pattern for visual feedback
        center_y, center_x = height // 2, width // 2
        # Eyes
        frame[center_y - 50 : center_y - 30, center_x - 60 : center_x - 40] = [255, 255, 255]
        frame[center_y - 50 : center_y - 30, center_x + 40 : center_x + 60] = [255, 255, 255]
        # Mouth
        frame[center_y + 30 : center_y + 40, center_x - 40 : center_x + 40] = [255, 200, 200]
        return cls(pixels=frame, width=width, height=height, timestamp_ms=time.time() * 1000)


class MockVoiceSynthesizer:
    """Mock voice synthesizer — returns silence instead of real TTS.

    Output format is IDENTICAL to production (MockAudioResult matches
    the structure of real AudioResult) per Req 31.5.
    """

    def __init__(self) -> None:
        logger.info("mock_voice_init", msg="MockVoiceSynthesizer initialized (no GPU)")

    async def synthesize(
        self,
        text: str,
        emotion: str = "neutral",
        speed: float = 1.0,
    ) -> MockAudioResult:
        """Return silent audio. Format matches production."""
        duration_ms = len(text) * 60.0  # Rough estimate: 60ms per char
        logger.debug(
            "mock_synthesize",
            text_len=len(text),
            emotion=emotion,
            duration_ms=duration_ms,
        )
        return MockAudioResult.silence(duration_ms=duration_ms)


class MockAvatarRenderer:
    """Mock avatar renderer — returns static frames instead of real inference.

    Output format is IDENTICAL to production per Req 31.5.
    """

    def __init__(self, width: int = 512, height: int = 512) -> None:
        self.width = width
        self.height = height
        self._frame_count = 0
        logger.info("mock_avatar_init", msg="MockAvatarRenderer initialized (no GPU)")

    async def generate_stream(
        self,
        audio_data: bytes,
        duration_ms: float,
    ) -> AsyncIterator[MockVideoFrame]:
        """Yield placeholder frames at ~30 FPS pace."""
        fps = 30
        total_frames = max(1, int(duration_ms / 1000 * fps))

        for i in range(total_frames):
            self._frame_count += 1
            frame = MockVideoFrame.placeholder(self.width, self.height)
            frame.timestamp_ms = (i / fps) * 1000
            yield frame

    async def generate_single_frame(self) -> MockVideoFrame:
        """Return a single placeholder frame."""
        self._frame_count += 1
        return MockVideoFrame.placeholder(self.width, self.height)


def get_mock_voice() -> MockVoiceSynthesizer | None:
    """Get mock voice synthesizer if in Mock Mode."""
    if is_mock_mode():
        return MockVoiceSynthesizer()
    return None


def get_mock_avatar() -> MockAvatarRenderer | None:
    """Get mock avatar renderer if in Mock Mode."""
    if is_mock_mode():
        return MockAvatarRenderer()
    return None
