"""Fish-Speech local sidecar API client adapter.

Handles communication with the Fish-Speech server running as a local sidecar.
Provides health check and synthesis endpoints with explicit error handling.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Any

import httpx
import msgpack

from src.utils.logging import get_logger

logger = get_logger("voice.fish_speech_client")


class FishSpeechClientError(Exception):
    """Raised when Fish-Speech API returns an error or is unreachable."""


class FishSpeechClient:
    """HTTP client for local Fish-Speech sidecar API.

    Communicates with a Fish-Speech server at the configured base URL.
    Uses httpx for async HTTP with explicit timeouts.
    Supports trained model checkpoints for improved voice cloning quality.
    """

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:8080",
        timeout_ms: int = 10000,
        trained_model_path: str | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_ms / 1000.0
        self.trained_model_path = trained_model_path
        self._trained_model_available: bool | None = None

    async def health_check(self) -> dict[str, Any]:
        """Check if the Fish-Speech sidecar is reachable and healthy.

        Returns a dictionary with health status including:
        - reachable: bool - whether server responds
        - trained_model_available: bool - whether trained model checkpoint is valid
        - training_status: str - training status (not_started, in_progress, completed, failed)
        - endpoint: str | None - which endpoint responded successfully
        """
        result: dict[str, Any] = {
            "reachable": False,
            "trained_model_available": False,
            "training_status": "not_started",
            "endpoint": None,
        }
        
        try:
            async with httpx.AsyncClient(timeout=min(self.timeout_s, 5.0)) as client:
                # Fish-Speech variants expose different probe surfaces:
                # - newer builds may expose /v1/health or /v1/models
                # - Kui-powered v1.5 serves OpenAPI at /json
                for path in ("/v1/health", "/health", "/v1/models", "/json"):
                    try:
                        resp = await client.get(f"{self.base_url}{path}")
                        if resp.is_success:
                            logger.info("fish_speech_health_ok", endpoint=path, status=resp.status_code)
                            result["reachable"] = True
                            result["endpoint"] = path
                            break
                    except httpx.RequestError:
                        continue
                
                # Check trained model availability
                if self.trained_model_path:
                    trained_model_valid = self._validate_trained_model_checkpoint()
                    result["trained_model_available"] = trained_model_valid
                    result["training_status"] = "completed" if trained_model_valid else "failed"
                    
                    if trained_model_valid:
                        logger.info(
                            "fish_speech_trained_model_available",
                            path=self.trained_model_path,
                        )
                    else:
                        logger.warning(
                            "fish_speech_trained_model_invalid",
                            path=self.trained_model_path,
                        )
                
                return result
                
        except Exception as e:
            logger.warning("fish_speech_health_failed", error=str(e))
            return result

    async def synthesize(
        self,
        text: str,
        reference_audio_b64: str = "",
        reference_text: str = "",
    ) -> bytes:
        """Synthesize speech via Fish-Speech API.

        Args:
            text: The text to synthesize.
            reference_audio_b64: Base64-encoded reference audio for voice cloning.
            reference_text: Transcript of the reference audio.

        Returns:
            Raw audio bytes from synthesis.

        Raises:
            FishSpeechClientError: If the API returns non-200 or is unreachable.
        """
        # Check for trained model checkpoint before synthesis
        use_trained_model = False
        if self.trained_model_path:
            if self._trained_model_available is None:
                # Lazy validation on first synthesis call
                self._trained_model_available = self._validate_trained_model_checkpoint()
            
            if self._trained_model_available:
                use_trained_model = True
                logger.info(
                    "fish_speech_using_trained_model",
                    path=self.trained_model_path,
                )
            else:
                logger.warning(
                    "fish_speech_trained_model_not_found_fallback_to_zero_shot",
                    path=self.trained_model_path,
                )
        
        # Build API payload
        payload: dict[str, Any] = {
            "text": text,
        }
        
        # Add trained model path to payload if available
        if use_trained_model:
            payload["trained_model_path"] = self.trained_model_path
        
        # Add reference audio/text for zero-shot cloning (always included for fallback)
        if reference_audio_b64 or reference_text:
            reference: dict[str, Any] = {}
            if reference_audio_b64:
                reference["audio"] = base64.b64decode(reference_audio_b64)
            if reference_text:
                reference["text"] = reference_text
            payload["references"] = [reference]

        try:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                resp = await client.post(
                    f"{self.base_url}/v1/tts",
                    content=msgpack.packb(payload, use_bin_type=True),
                    headers={"Content-Type": "application/msgpack"},
                )
                if resp.status_code != 200:
                    raise FishSpeechClientError(
                        f"Fish-Speech API returned {resp.status_code}: {resp.text[:200]}"
                    )
                return resp.content
        except httpx.TimeoutException as e:
            raise FishSpeechClientError(
                f"Fish-Speech API timed out after {self.timeout_s}s: {e}"
            ) from e
        except httpx.RequestError as e:
            raise FishSpeechClientError(
                f"Fish-Speech API unreachable at {self.base_url}: {e}"
            ) from e

    @staticmethod
    def load_reference_audio_b64(wav_path: str | Path) -> str:
        """Load a WAV file and return its base64 encoding."""
        path = Path(wav_path)
        if not path.exists():
            raise FileNotFoundError(f"Voice clone reference not found: {path}")
        return base64.b64encode(path.read_bytes()).decode("utf-8")

    @staticmethod
    def load_reference_text(txt_path: str | Path) -> str:
        """Load a reference text file."""
        path = Path(txt_path)
        if not path.exists():
            raise FileNotFoundError(f"Voice clone reference text not found: {path}")
        text = path.read_text(encoding="utf-8").strip()
        if not text:
            raise ValueError(f"Voice clone reference text is empty: {path}")
        return text

    def _validate_trained_model_checkpoint(self) -> bool:
        """Validate that trained model checkpoint files exist and are valid.
        
        Returns:
            True if all required checkpoint files exist and are non-empty, False otherwise.
        """
        if not self.trained_model_path:
            return False
        
        checkpoint_dir = Path(self.trained_model_path)
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
