"""Single-host stream runtime bound to persisted dashboard control-plane targets."""

from __future__ import annotations

import asyncio
from typing import Any

from src.stream.rtmp import RTMPStreamer, StreamStatus
from src.utils.logging import get_logger

logger = get_logger("stream.runtime")


class SingleHostStreamRuntime:
    """Own the active RTMP publisher for the single-host control plane."""

    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._streamer: RTMPStreamer | None = None
        self._active_target: dict[str, Any] | None = None
        self._last_error = ""

    async def start_target(self, target: dict[str, Any]) -> dict[str, Any]:
        """Start publishing to the persisted RTMP target."""
        async with self._lock:
            if self._streamer is not None:
                current = self.get_snapshot()
                if current["stream_running"] and self._active_target and self._active_target.get("id") == target.get("id"):
                    return current
                await self._streamer.stop()

            streamer = RTMPStreamer(
                platform=target["platform"],
                rtmp_url=target["rtmp_url"],
                stream_key=target.get("stream_key", ""),
            )
            started = await streamer.start()
            if not started:
                health = streamer.get_health()
                self._streamer = None
                self._active_target = None
                self._last_error = health.last_error or f"Failed to start {target['platform']} RTMP publisher"
                logger.error(
                    "stream_runtime_start_failed",
                    platform=target["platform"],
                    target_label=target.get("label", ""),
                    error=self._last_error,
                )
                raise RuntimeError(self._last_error)

            self._streamer = streamer
            self._active_target = {key: value for key, value in target.items() if key != "stream_key"}
            self._last_error = ""
            logger.info(
                "stream_runtime_started",
                platform=target["platform"],
                target_label=target.get("label", ""),
            )
            return self.get_snapshot()

    async def stop_active(self) -> dict[str, Any]:
        """Stop the active publisher if one exists."""
        async with self._lock:
            if self._streamer is not None:
                await self._streamer.stop()
            self._streamer = None
            self._active_target = None
            logger.info("stream_runtime_stopped")
            return self.get_snapshot()

    def get_snapshot(self) -> dict[str, Any]:
        """Return the runtime snapshot for operator/status endpoints."""
        if self._streamer is None:
            return {
                "stream_running": False,
                "stream_status": "idle",
                "platform": self._active_target["platform"] if self._active_target else None,
                "target_label": self._active_target["label"] if self._active_target else None,
                "uptime_sec": 0.0,
                "last_error": self._last_error,
            }

        health = self._streamer.get_health()
        return {
            "stream_running": health.status == StreamStatus.LIVE,
            "stream_status": health.status.value,
            "platform": self._active_target["platform"] if self._active_target else None,
            "target_label": self._active_target["label"] if self._active_target else None,
            "uptime_sec": round(float(health.uptime_sec), 1),
            "last_error": health.last_error or self._last_error,
        }
