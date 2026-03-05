"""Layer 5: Streaming — RTMP Stream Manager.

Manages RTMP stream output to TikTok/Shopee with auto-reconnect.
Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any

from src.config import get_config, get_env, is_mock_mode
from src.utils.logging import get_logger

logger = get_logger("stream")


class StreamStatus(str, Enum):
    """Stream connection statuses."""

    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    LIVE = "live"
    RECONNECTING = "reconnecting"
    ERROR = "error"


@dataclass
class StreamHealth:
    """Stream health metrics."""

    status: StreamStatus = StreamStatus.DISCONNECTED
    uptime_sec: float = 0.0
    frames_sent: int = 0
    fps_actual: float = 0.0
    bitrate_kbps: float = 0.0
    reconnect_count: int = 0
    last_error: str = ""


class RTMPStreamer:
    """RTMP streaming manager with auto-reconnect.

    Sends composed video to platform RTMP endpoints.
    Supports TikTok and Shopee simultaneously.
    """

    def __init__(self, platform: str = "tiktok") -> None:
        self.platform = platform
        self.config = get_config().streaming
        self._process: subprocess.Popen[bytes] | None = None
        self._status = StreamStatus.DISCONNECTED
        self._start_time = 0.0
        self._frames_sent = 0
        self._reconnect_count = 0

        logger.info("streamer_init", platform=platform)

    def _get_rtmp_url(self) -> str:
        """Get RTMP URL for configured platform."""
        env = get_env()
        if self.platform == "tiktok":
            return f"{env.tiktok_rtmp_url}{env.tiktok_stream_key}"
        elif self.platform == "shopee":
            return f"{env.shopee_rtmp_url}{env.shopee_stream_key}"
        else:
            raise ValueError(f"Unknown platform: {self.platform}")

    async def start(self) -> bool:
        """Start RTMP streaming."""
        if is_mock_mode():
            self._status = StreamStatus.LIVE
            self._start_time = time.time()
            logger.info("mock_stream_start", platform=self.platform)
            return True

        self._status = StreamStatus.CONNECTING
        try:
            rtmp_url = self._get_rtmp_url()
            cmd = self._build_ffmpeg_command(rtmp_url)
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
            )
            self._status = StreamStatus.LIVE
            self._start_time = time.time()
            logger.info("stream_started", platform=self.platform)
            return True

        except Exception as e:
            self._status = StreamStatus.ERROR
            logger.error("stream_start_failed", error=str(e))
            return False

    def _build_ffmpeg_command(self, rtmp_url: str) -> list[str]:
        """Build FFmpeg command for RTMP output."""
        cfg = self.config
        return [
            "ffmpeg",
            "-re",
            "-i", "pipe:0",
            "-c:v", cfg.video_codec,
            "-b:v", cfg.video_bitrate,
            "-c:a", cfg.audio_codec,
            "-b:a", cfg.audio_bitrate,
            "-g", str(cfg.keyframe_interval),
            "-preset", cfg.preset,
            "-tune", cfg.tune,
            "-f", "flv",
            rtmp_url,
        ]

    async def stop(self) -> None:
        """Stop streaming gracefully."""
        if self._process:
            self._process.terminate()
            self._process = None
        self._status = StreamStatus.DISCONNECTED
        logger.info("stream_stopped", platform=self.platform)

    async def reconnect(self) -> bool:
        """Attempt reconnection with exponential backoff."""
        cfg = self.config.reconnect
        for attempt in range(cfg.max_attempts):
            wait = min(cfg.backoff_base_sec * (2 ** attempt), cfg.backoff_max_sec)
            logger.info("reconnecting", attempt=attempt + 1, wait_sec=wait)
            self._status = StreamStatus.RECONNECTING

            await asyncio.sleep(wait)
            self._reconnect_count += 1

            if await self.start():
                return True

        self._status = StreamStatus.ERROR
        return False

    def get_health(self) -> StreamHealth:
        """Get current stream health metrics."""
        uptime = time.time() - self._start_time if self._start_time else 0.0
        return StreamHealth(
            status=self._status,
            uptime_sec=uptime,
            frames_sent=self._frames_sent,
            reconnect_count=self._reconnect_count,
        )
