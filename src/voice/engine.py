"""Layer 2: Voice — TTS Engine Interface and Router.

Manages text-to-speech synthesis with Fish Speech (primary)
and Edge TTS (backup). Includes emotion-aware voice modulation.
Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8
"""

from __future__ import annotations

import hashlib
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from src.config import get_config, is_mock_mode
from src.utils.logging import get_logger
from src.utils.mock_mode import MockAudioResult, MockVoiceSynthesizer

logger = get_logger("voice")


@dataclass
class AudioResult:
    """Output from TTS synthesis — production format."""

    audio_data: bytes
    duration_ms: float
    sample_rate: int = 24000
    format: str = "wav"
    emotion: str = "neutral"
    text: str = ""
    trace_id: str = ""
    latency_ms: float = 0.0
    cached: bool = False


class BaseTTSEngine(ABC):
    """Abstract TTS engine interface."""

    @abstractmethod
    async def synthesize(
        self,
        text: str,
        emotion: str = "neutral",
        speed: float = 1.0,
        trace_id: str = "",
    ) -> AudioResult:
        """Convert text to speech audio."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check engine availability."""
        ...


class FishSpeechEngine(BaseTTSEngine):
    """Fish Speech TTS — GPU-accelerated, high-quality voice cloning.

    Requirements: 3.1, 3.2 — Primary TTS with voice cloning from reference sample.
    Runs on GPU server; uses MockVoiceSynthesizer in Mock Mode.
    """

    def __init__(self, voice_sample_path: str = "assets/voice/reference.wav") -> None:
        self.voice_sample_path = voice_sample_path
        self._model: Any = None
        logger.info("fish_speech_init", voice_sample=voice_sample_path)

    async def synthesize(
        self,
        text: str,
        emotion: str = "neutral",
        speed: float = 1.0,
        trace_id: str = "",
    ) -> AudioResult:
        if is_mock_mode():
            mock = MockVoiceSynthesizer()
            mock_result = await mock.synthesize(text, emotion, speed)
            return AudioResult(
                audio_data=mock_result.audio_data,
                duration_ms=mock_result.duration_ms,
                sample_rate=mock_result.sample_rate,
                format=mock_result.format,
                emotion=emotion,
                text=text,
                trace_id=trace_id,
                latency_ms=15.0,
            )

        start = time.time()
        try:
            # Production: call Fish Speech inference
            # This will be activated when GPU models are loaded
            audio_data = await self._run_inference(text, emotion, speed)
            latency = (time.time() - start) * 1000
            duration_ms = len(audio_data) / (24000 * 2) * 1000  # 16-bit mono

            return AudioResult(
                audio_data=audio_data,
                duration_ms=duration_ms,
                sample_rate=24000,
                emotion=emotion,
                text=text,
                trace_id=trace_id,
                latency_ms=latency,
            )
        except Exception as e:
            logger.error("fish_speech_error", error=str(e), trace_id=trace_id)
            raise

    async def _run_inference(self, text: str, emotion: str, speed: float) -> bytes:
        """Run Fish Speech GPU inference. Implemented when deployed to GPU server."""
        raise NotImplementedError("Fish Speech GPU inference requires GPU server deployment")

    async def health_check(self) -> bool:
        if is_mock_mode():
            return True
        return self._model is not None


class EdgeTTSEngine(BaseTTSEngine):
    """Edge TTS — Free Microsoft TTS as backup.

    Requirements: 3.3 — Backup TTS when Fish Speech is unavailable.
    No GPU required, uses Microsoft's cloud API.
    """

    def __init__(self, voice: str = "id-ID-ArdiNeural") -> None:
        self.voice = voice
        logger.info("edge_tts_init", voice=voice)

    async def synthesize(
        self,
        text: str,
        emotion: str = "neutral",
        speed: float = 1.0,
        trace_id: str = "",
    ) -> AudioResult:
        if is_mock_mode():
            mock = MockVoiceSynthesizer()
            mock_result = await mock.synthesize(text, emotion, speed)
            return AudioResult(
                audio_data=mock_result.audio_data,
                duration_ms=mock_result.duration_ms,
                sample_rate=mock_result.sample_rate,
                emotion=emotion,
                text=text,
                trace_id=trace_id,
                latency_ms=20.0,
            )

        start = time.time()
        try:
            import edge_tts

            rate = f"+{int((speed - 1) * 100)}%" if speed >= 1 else f"{int((speed - 1) * 100)}%"
            communicate = edge_tts.Communicate(text, self.voice, rate=rate)

            audio_chunks: list[bytes] = []
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_chunks.append(chunk["data"])

            audio_data = b"".join(audio_chunks)
            latency = (time.time() - start) * 1000
            duration_ms = len(text) * 60.0  # Rough estimate

            return AudioResult(
                audio_data=audio_data,
                duration_ms=duration_ms,
                sample_rate=24000,
                emotion=emotion,
                text=text,
                trace_id=trace_id,
                latency_ms=latency,
            )
        except Exception as e:
            logger.error("edge_tts_error", error=str(e), trace_id=trace_id)
            raise

    async def health_check(self) -> bool:
        return True  # Edge TTS is cloud-based, usually available


class AudioCache:
    """Cache for synthesized audio to avoid redundant TTS calls.

    Uses content hash (text + emotion + speed) as key.
    Requirements: 3.4 — Audio caching for repeated phrases.
    """

    def __init__(self, cache_dir: str = "data/cache/audio", max_size_mb: int = 1024) -> None:
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size_mb = max_size_mb
        self._cache: dict[str, AudioResult] = {}

    def _make_key(self, text: str, emotion: str, speed: float) -> str:
        """Generate cache key from content hash."""
        content = f"{text}|{emotion}|{speed}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def get(self, text: str, emotion: str = "neutral", speed: float = 1.0) -> AudioResult | None:
        """Look up cached audio."""
        key = self._make_key(text, emotion, speed)
        result = self._cache.get(key)
        if result:
            logger.debug("audio_cache_hit", key=key)
            result.cached = True
        return result

    def put(self, result: AudioResult, speed: float = 1.0) -> None:
        """Store audio in cache."""
        key = self._make_key(result.text, result.emotion, speed)
        self._cache[key] = result
        logger.debug("audio_cache_put", key=key, text_len=len(result.text))

    @property
    def size(self) -> int:
        return len(self._cache)


class VoiceRouter:
    """Voice synthesis router with primary/backup TTS and caching.

    Routes to Fish Speech (primary) with Edge TTS fallback.
    """

    def __init__(self) -> None:
        config = get_config()
        self.primary = FishSpeechEngine()
        self.backup = EdgeTTSEngine()
        self.cache = AudioCache(max_size_mb=config.voice.cache_max_mb)
        self.emotion_map = config.voice.emotion_mapping

        logger.info("voice_router_init", primary="fish_speech", backup="edge_tts")

    async def synthesize(
        self,
        text: str,
        emotion: str = "neutral",
        speed: float = 1.0,
        trace_id: str = "",
    ) -> AudioResult:
        """Synthesize speech with caching and fallback.

        1. Check cache → 2. Try primary (Fish Speech) → 3. Fallback to Edge TTS.
        """
        # Check cache first
        cached = self.cache.get(text, emotion, speed)
        if cached:
            return cached

        # Apply emotion modulation from config
        if emotion in self.emotion_map:
            em = self.emotion_map[emotion]
            speed *= em.speed

        # Try primary
        try:
            result = await self.primary.synthesize(text, emotion, speed, trace_id)
            self.cache.put(result, speed)
            return result
        except Exception as e:
            logger.warning("primary_tts_failed", error=str(e), trace_id=trace_id)

        # Fallback to backup
        try:
            result = await self.backup.synthesize(text, emotion, speed, trace_id)
            self.cache.put(result, speed)
            return result
        except Exception as e:
            logger.error("all_tts_failed", error=str(e), trace_id=trace_id)
            raise RuntimeError(f"All TTS engines failed: {e}")
