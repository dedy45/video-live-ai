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
    """

    def __init__(self, base_url: str = "http://127.0.0.1:8080", timeout_ms: int = 10000) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_ms / 1000.0

    async def health_check(self) -> bool:
        """Check if the Fish-Speech sidecar is reachable and healthy.

        Returns True if the server responds to a health/version probe.
        """
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
                            return True
                    except httpx.RequestError:
                        continue
                return False
        except Exception as e:
            logger.warning("fish_speech_health_failed", error=str(e))
            return False

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
        payload: dict[str, Any] = {
            "text": text,
        }
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
