"""Voice Lab service for profile-specific Fish-Speech synthesis."""

from __future__ import annotations

from src.config import get_config
from src.utils.logging import get_logger
from src.voice.engine import AudioResult
from src.voice.fish_speech_client import FishSpeechClient
from src.voice.runtime_state import get_voice_runtime_state

logger = get_logger("voice.lab")


class VoiceLabEngine:
    """Profile-aware Fish-Speech wrapper for dashboard-driven voice lab flows."""

    def __init__(self) -> None:
        config = get_config()
        self._client = FishSpeechClient(
            base_url=config.voice.fish_speech_base_url,
            timeout_ms=config.voice.fish_speech_timeout_ms,
        )

    async def health_check(self) -> bool:
        reachable = await self._client.health_check()
        state = get_voice_runtime_state()
        state.server_reachable = reachable
        return reachable

    async def synthesize_with_profile(
        self,
        *,
        text: str,
        reference_wav_path: str,
        reference_text: str,
        emotion: str = "neutral",
        language: str = "id",
        style_preset: str = "natural",
        stability: float = 0.75,
        similarity: float = 0.8,
        speed: float = 1.0,
        trace_id: str = "",
    ) -> AudioResult:
        import time

        start = time.time()
        ref_audio_b64 = FishSpeechClient.load_reference_audio_b64(reference_wav_path)
        audio_bytes = await self._client.synthesize(
            text=text,
            reference_audio_b64=ref_audio_b64,
            reference_text=reference_text,
        )
        latency_ms = (time.time() - start) * 1000
        duration_ms = len(audio_bytes) / (24000 * 2) * 1000 if audio_bytes else 0.0

        state = get_voice_runtime_state()
        state.update_success("fish_speech", latency_ms)
        state.server_reachable = True
        state.reference_ready = True
        state.requested_engine = "fish_speech"

        logger.info(
            "voice_lab_synthesized",
            trace_id=trace_id,
            bytes=len(audio_bytes),
            latency_ms=round(latency_ms, 2),
            emotion=emotion,
            language=language,
            style_preset=style_preset,
            stability=stability,
            similarity=similarity,
            speed=speed,
        )
        return AudioResult(
            audio_data=audio_bytes,
            duration_ms=duration_ms,
            sample_rate=24000,
            format="wav",
            emotion=emotion,
            text=text,
            trace_id=trace_id,
            latency_ms=latency_ms,
        )


_voice_lab_engine: VoiceLabEngine | None = None


def get_voice_lab_engine() -> VoiceLabEngine:
    global _voice_lab_engine
    if _voice_lab_engine is None:
        _voice_lab_engine = VoiceLabEngine()
    return _voice_lab_engine
