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
    """Fish Speech TTS — local sidecar API voice cloning.

    Requirements: 3.1, 3.2 — Primary TTS with voice cloning from reference sample.
    Calls local Fish-Speech API sidecar; uses MockVoiceSynthesizer in Mock Mode.
    """

    def __init__(self, voice_sample_path: str = "assets/voice/reference.wav") -> None:
        self.voice_sample_path = voice_sample_path
        self._client = None  # Lazy-init to avoid import at module level
        self._reference_audio_b64: str | None = None
        self._reference_text: str | None = None
        self._trained_model_path: str | None = None
        self._trained_model_available: bool = False
        
        # Check for trained model checkpoint from config
        config = get_config()
        if config.voice.trained_model_path:
            self._trained_model_path = config.voice.trained_model_path
            self._trained_model_available = self._validate_trained_model()
            
            if self._trained_model_available:
                logger.info(
                    "fish_speech_init_with_trained_model",
                    voice_sample=voice_sample_path,
                    trained_model=self._trained_model_path,
                )
            else:
                logger.warning(
                    "fish_speech_init_trained_model_invalid",
                    voice_sample=voice_sample_path,
                    trained_model=self._trained_model_path,
                )
        else:
            logger.info("fish_speech_init", voice_sample=voice_sample_path)
        
        # Update runtime state with trained model availability
        from src.voice.runtime_state import get_voice_runtime_state
        state = get_voice_runtime_state()
        state.trained_model_available = self._trained_model_available

    def _get_client(self):
        """Lazy-init the Fish-Speech client from config."""
        if self._client is None:
            from src.voice.fish_speech_client import FishSpeechClient
            config = get_config()
            self._client = FishSpeechClient(
                base_url=config.voice.fish_speech_base_url,
                timeout_ms=config.voice.fish_speech_timeout_ms,
                trained_model_path=self._trained_model_path,
            )
        return self._client

    def _validate_trained_model(self) -> bool:
        """Validate that trained model checkpoint files exist and are valid.
        
        Returns:
            True if all required checkpoint files exist and are non-empty, False otherwise.
        """
        if not self._trained_model_path:
            return False
        
        from pathlib import Path
        checkpoint_dir = Path(self._trained_model_path)
        if not checkpoint_dir.exists():
            logger.warning(
                "fish_speech_trained_model_dir_not_found",
                path=str(checkpoint_dir),
            )
            return False
        
        # Check for required model files
        required_files = {
            "model.pth": checkpoint_dir / "model.pth",
            "config.json": checkpoint_dir / "config.json",
            "tokenizer.tiktoken": checkpoint_dir / "tokenizer.tiktoken",
        }
        
        missing_files = []
        invalid_files = []
        
        for name, file_path in required_files.items():
            if not file_path.exists():
                missing_files.append(name)
            elif file_path.stat().st_size == 0:
                invalid_files.append(name)
        
        if missing_files:
            logger.warning(
                "fish_speech_trained_model_missing_files",
                path=str(checkpoint_dir),
                missing=missing_files,
            )
            return False
        
        if invalid_files:
            logger.warning(
                "fish_speech_trained_model_invalid_files",
                path=str(checkpoint_dir),
                invalid=invalid_files,
            )
            return False
        
        return True

    def _validate_dataset_quality(self) -> dict[str, Any]:
        """Validate reference audio dataset quality (duration, file count, quality metrics).
        
        Returns:
            Dictionary with validation results:
            - valid: bool - overall validation status
            - total_duration_min: float - total duration in minutes
            - file_count: int - number of valid audio files
            - issues: list[str] - list of validation issues found
            - guidance: str - operator guidance message
        """
        try:
            import wave
        except ImportError:
            return {
                "valid": False,
                "total_duration_min": 0.0,
                "file_count": 0,
                "issues": ["wave module not available"],
                "guidance": "Install wave module to validate audio files",
            }
        
        config = get_config()
        voice_dir = Path("assets/voice")
        training_dir = Path(config.voice.training_dataset_path)
        
        # Collect all WAV files from both directories
        wav_files = []
        if voice_dir.exists():
            wav_files.extend(voice_dir.glob("*.wav"))
        if training_dir.exists():
            wav_files.extend(training_dir.glob("*.wav"))
        
        if not wav_files:
            return {
                "valid": False,
                "total_duration_min": 0.0,
                "file_count": 0,
                "issues": ["No WAV files found in assets/voice/ or training dataset"],
                "guidance": "Record 30-60 minutes of clean Indonesian speech",
            }
        
        issues = []
        total_duration_sec = 0.0
        file_count = 0
        
        for wav_path in wav_files:
            try:
                with wave.open(str(wav_path), "rb") as wav_file:
                    frames = wav_file.getnframes()
                    rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    sampwidth = wav_file.getsampwidth()
                    duration_sec = frames / float(rate)
                    
                    total_duration_sec += duration_sec
                    file_count += 1
                    
                    # Quality checks
                    if rate < 16000:
                        issues.append(f"{wav_path.name}: sample rate {rate}Hz too low (minimum 16kHz)")
                    if channels > 2:
                        issues.append(f"{wav_path.name}: {channels} channels (prefer mono or stereo)")
                    if sampwidth not in (2, 3):
                        issues.append(f"{wav_path.name}: {sampwidth * 8}-bit depth (prefer 16-bit or 24-bit)")
                    if duration_sec < 1.0:
                        issues.append(f"{wav_path.name}: duration {duration_sec:.1f}s too short")
                    
            except Exception as exc:
                issues.append(f"{wav_path.name}: failed to read ({exc})")
        
        total_duration_min = total_duration_sec / 60.0
        
        # Duration requirement check
        if total_duration_min < 30.0:
            issues.append(f"Total duration {total_duration_min:.1f} min insufficient (minimum 30 min)")
        
        # Generate guidance message
        if total_duration_min >= 30.0 and not issues:
            guidance = "Dataset meets quality requirements for fine-tuning"
            valid = True
        elif total_duration_min >= 3.0:
            guidance = f"Dataset sufficient for Quick Clone ({total_duration_min:.1f} min), insufficient for fine-tuning"
            valid = False
        else:
            guidance = f"Dataset insufficient ({total_duration_min:.1f} min). Record 30-60 min Indonesian speech"
            valid = False
        
        return {
            "valid": valid,
            "total_duration_min": round(total_duration_min, 2),
            "file_count": file_count,
            "issues": issues,
            "guidance": guidance,
        }

    def _load_references(self) -> None:
        """Load clone reference assets from config paths and validate dataset quality."""
        if self._reference_audio_b64 is not None and self._reference_text is not None:
            return
        from src.voice.fish_speech_client import FishSpeechClient
        from src.voice.runtime_state import get_voice_runtime_state
        config = get_config()
        try:
            self._reference_audio_b64 = FishSpeechClient.load_reference_audio_b64(
                config.voice.clone_reference_wav
            )
            self._reference_text = FishSpeechClient.load_reference_text(
                config.voice.clone_reference_text
            )
            get_voice_runtime_state().reference_ready = True
            
            # Validate dataset quality (duration, file count, quality metrics)
            dataset_validation = self._validate_dataset_quality()
            
            # Update runtime state with dataset duration
            state = get_voice_runtime_state()
            state.training_dataset_duration_min = dataset_validation.get("total_duration_min")
            
            # Log warnings if dataset quality is insufficient
            if not dataset_validation.get("valid", False):
                total_duration = dataset_validation.get("total_duration_min", 0.0)
                file_count = dataset_validation.get("file_count", 0)
                
                if total_duration < 30.0:
                    logger.warning(
                        "fish_speech_dataset_insufficient_duration",
                        total_duration_min=total_duration,
                        file_count=file_count,
                        minimum_required_min=30.0,
                        guidance=dataset_validation.get("guidance", ""),
                    )
                
                issues = dataset_validation.get("issues", [])
                if issues:
                    logger.warning(
                        "fish_speech_dataset_quality_issues",
                        issues=issues[:5],  # Log first 5 issues to avoid log spam
                        total_issues=len(issues),
                    )
            else:
                logger.info(
                    "fish_speech_dataset_quality_ok",
                    total_duration_min=dataset_validation.get("total_duration_min"),
                    file_count=dataset_validation.get("file_count"),
                )
                
        except (FileNotFoundError, ValueError) as e:
            logger.warning("fish_speech_reference_load_failed", error=str(e))
            get_voice_runtime_state().reference_ready = False
            raise RuntimeError(f"Voice clone reference missing or invalid: {e}") from e

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
        """Run Fish Speech inference via local sidecar API."""
        from src.voice.runtime_state import get_voice_runtime_state

        state = get_voice_runtime_state()
        client = self._get_client()
        self._load_references()
        try:
            audio = await client.synthesize(
                text=text,
                reference_audio_b64=self._reference_audio_b64 or "",
                reference_text=self._reference_text or "",
            )
            state.server_reachable = True
            return audio
        except Exception:
            state.server_reachable = False
            raise

    async def synthesize_with_profile(
        self,
        text: str,
        reference_wav_path: str,
        reference_text: str,
        emotion: str = "neutral",
        speed: float = 1.0,
        language: str = "id",
        style_preset: str = "natural",
        stability: float = 0.75,
        similarity: float = 0.8,
        **kwargs
    ) -> AudioResult:
        """Synthesize with profile-specific reference audio.
        
        Bridges api.py generate_voice() to FishSpeechClient.
        Loads reference from path and passes to client.
        
        Args:
            text: Text to synthesize
            reference_wav_path: Path to reference WAV file
            reference_text: Transcript of reference audio
            emotion: Emotion for synthesis (neutral, happy, sad, etc.)
            speed: Speech speed multiplier
            language: Target language code (id for Indonesian)
            style_preset: Voice style preset (natural, conversational, sales_live)
            stability: Voice stability parameter (0.2-1.0)
            similarity: Voice similarity parameter (0.2-1.0)
            **kwargs: Additional parameters (ignored for compatibility)
            
        Returns:
            AudioResult with synthesized audio data and metadata
        """
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
                trace_id="",
                latency_ms=15.0,
            )

        from src.voice.fish_speech_client import FishSpeechClient
        
        # Load reference from provided path
        ref_b64 = FishSpeechClient.load_reference_audio_b64(reference_wav_path)
        
        start = time.time()
        client = self._get_client()
        
        try:
            audio_data = await client.synthesize(
                text=text,
                reference_audio_b64=ref_b64,
                reference_text=reference_text,
            )
            latency = (time.time() - start) * 1000
            duration_ms = len(audio_data) / (24000 * 2) * 1000  # 16-bit mono
            
            return AudioResult(
                audio_data=audio_data,
                duration_ms=duration_ms,
                sample_rate=24000,
                format="wav",
                emotion=emotion,
                text=text,
                trace_id="",
                latency_ms=latency,
            )
        except Exception as e:
            logger.error("fish_speech_synthesize_with_profile_error", error=str(e))
            raise

    async def health_check(self) -> bool:
        if is_mock_mode():
            return True
        try:
            client = self._get_client()
            health_result = await client.health_check()
            return health_result.get("reachable", False)
        except Exception:
            return False


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
    Updates voice runtime state after each synthesis attempt.
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
        Updates voice runtime state after each attempt.
        """
        from src.voice.runtime_state import get_voice_runtime_state
        state = get_voice_runtime_state()

        # Store original speed for cache key consistency
        original_speed = speed

        # Check cache first (use original speed for cache key)
        cached = self.cache.get(text, emotion, original_speed)
        if cached:
            return cached

        # Apply emotion modulation from config
        if emotion in self.emotion_map:
            em = self.emotion_map[emotion]
            speed *= em.speed

        # Try primary
        primary_error = ""
        try:
            result = await self.primary.synthesize(text, emotion, speed, trace_id)
            self.cache.put(result, original_speed)  # Use original speed for cache key
            state.update_success("fish_speech", result.latency_ms)
            return result
        except Exception as e:
            primary_error = str(e)
            logger.warning("primary_tts_failed", error=primary_error, trace_id=trace_id)

        # Fallback to backup
        try:
            result = await self.backup.synthesize(text, emotion, speed, trace_id)
            self.cache.put(result, original_speed)  # Use original speed for cache key
            state.update_fallback_success("edge_tts", result.latency_ms, primary_error)
            return result
        except Exception as e:
            state.update_failure("none", f"all engines failed: {e}")
            logger.error("all_tts_failed", error=str(e), trace_id=trace_id)
            raise RuntimeError(f"All TTS engines failed: {e}")
