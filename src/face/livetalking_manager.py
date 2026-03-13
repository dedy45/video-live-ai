"""LiveTalking Process Manager.

Manages the LiveTalking engine as a subprocess: start, stop, status, logs.
Used by the dashboard API to control the engine without manual batch files.

Runtime contract: see docs/specs/livetalking_runtime_contract.md
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from src.config import get_config, is_mock_mode
from src.face.engine_resolver import resolve_avatar_id, resolve_engine
from src.face.livetalking_adapter import (
    DEFAULT_AVATAR_ID,
    DEFAULT_MODEL,
    DEFAULT_PORT,
    SUPPORTED_MODELS,
    SUPPORTED_TRANSPORTS,
)
from src.utils.logging import get_logger

logger = get_logger("livetalking.manager")

MAX_LOG_LINES = 500


class EngineState(str, Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class EngineStatus:
    state: EngineState = EngineState.STOPPED
    pid: int | None = None
    port: int = DEFAULT_PORT
    model: str = DEFAULT_MODEL
    avatar_id: str = DEFAULT_AVATAR_ID
    transport: str = "webrtc"
    uptime_sec: float = 0.0
    last_error: str = ""
    app_py_exists: bool = False
    model_path_exists: bool = False
    avatar_path_exists: bool = False
    requested_model: str = DEFAULT_MODEL
    requested_avatar_id: str = DEFAULT_AVATAR_ID
    python_executable: str = sys.executable
    python_executable_exists: bool = True
    startup_timeout_sec: float = 60.0
    push_url: str = "http://localhost:1985/rtc/v1/whip/?app=live&stream=livestream"

    def to_dict(self) -> dict[str, Any]:
        return {
            "state": self.state.value,
            "pid": self.pid,
            "port": self.port,
            "model": self.model,
            "avatar_id": self.avatar_id,
            "requested_model": self.requested_model,
            "resolved_model": self.model,
            "requested_avatar_id": self.requested_avatar_id,
            "resolved_avatar_id": self.avatar_id,
            "transport": self.transport,
            "uptime_sec": round(self.uptime_sec, 1),
            "last_error": self.last_error,
            "app_py_exists": self.app_py_exists,
            "model_path_exists": self.model_path_exists,
            "avatar_path_exists": self.avatar_path_exists,
            "python_executable": self.python_executable,
            "python_executable_exists": self.python_executable_exists,
            "startup_timeout_sec": round(self.startup_timeout_sec, 1),
            "push_url": self.push_url,
        }


class LiveTalkingManager:
    """Manages LiveTalking engine as a subprocess."""

    def __init__(self) -> None:
        self._process: subprocess.Popen | None = None
        self._state = EngineState.STOPPED
        self._start_time: float = 0.0
        self._last_error: str = ""
        self._log_buffer: deque[str] = deque(maxlen=MAX_LOG_LINES)
        self._log_thread: threading.Thread | None = None

        # Paths
        self.livetalking_dir = Path("external/livetalking")
        self.app_py = self.livetalking_dir / "app.py"
        self.models_dir = self.livetalking_dir / "models"
        self.avatars_dir = self.livetalking_dir / "data" / "avatars"

        # Settings from env
        self.port = int(os.getenv("LIVETALKING_PORT", str(DEFAULT_PORT)))
        self.transport = os.getenv("LIVETALKING_TRANSPORT", "webrtc")
        self.push_url = os.getenv(
            "LIVETALKING_PUSH_URL",
            "http://localhost:1985/rtc/v1/whip/?app=live&stream=livestream",
        )
        self.python_executable = os.getenv("LIVETALKING_PYTHON_EXE", "").strip() or sys.executable
        self.startup_timeout_sec = max(
            0.0,
            float(os.getenv("LIVETALKING_STARTUP_TIMEOUT_SEC", "60")),
        )
        self.requested_avatar_id = os.getenv("LIVETALKING_AVATAR_ID", DEFAULT_AVATAR_ID)

        # Resolve engine: musetalk → wav2lip fallback if models missing
        self.requested_model = os.getenv("LIVETALKING_MODEL", DEFAULT_MODEL)
        self.model = resolve_engine(
            self.requested_model,
            musetalk_model_dir=self.models_dir / "musetalk",
            musetalk_avatar_dir=self.avatars_dir / self.requested_avatar_id,
        )
        self.avatar_id = resolve_avatar_id(
            self.requested_avatar_id,
            self.model,
            avatars_dir=self.avatars_dir,
        )

        logger.info(
            "livetalking_manager_init",
            port=self.port,
            transport=self.transport,
            requested_model=self.requested_model,
            resolved_model=self.model,
            requested_avatar_id=self.requested_avatar_id,
            avatar_id=self.avatar_id,
            python_executable=self.python_executable,
            startup_timeout_sec=self.startup_timeout_sec,
        )

    def build_launch_command(self) -> list[str]:
        """Build the exact command to launch LiveTalking."""
        cmd = [
            self.python_executable,
            "app.py",
            "--transport", self.transport,
            "--model", self.model,
            "--avatar_id", self.avatar_id,
            "--listenport", str(self.port),
        ]
        if self.transport == "rtcpush":
            cmd.extend(["--push_url", self.push_url])
        return cmd

    def _python_executable_exists(self) -> bool:
        candidate = Path(self.python_executable)
        return candidate.exists() or shutil.which(self.python_executable) is not None

    def _check_port_free(self) -> bool:
        """Check if the engine port is available."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(1)
                result = s.connect_ex(("127.0.0.1", self.port))
                return result != 0
        except Exception:
            return True

    def _check_port_reachable(self) -> bool:
        """Check if the engine port is reachable (engine running)."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(2)
                result = s.connect_ex(("127.0.0.1", self.port))
                return result == 0
        except Exception:
            return False

    def _read_process_output(self) -> None:
        """Background thread to read process stdout/stderr."""
        proc = self._process
        if proc is None:
            return
        stream = getattr(proc, "stdout", None) or getattr(proc, "stderr", None)
        if stream is None:
            return
        try:
            for line in iter(stream.readline, b""):
                decoded = line.decode("utf-8", errors="replace").rstrip()
                if decoded:
                    self._log_buffer.append(decoded)
        except Exception:
            pass

    def _summarize_recent_logs(self, tail: int = 6) -> str:
        recent_lines = [line.strip() for line in self.get_logs(tail=tail) if line.strip()]
        if not recent_lines:
            return ""
        return " | ".join(recent_lines[-tail:])

    def _build_child_env(self) -> dict[str, str]:
        """Build a clean environment for the sidecar interpreter."""
        child_env = {key: value for key, value in os.environ.items()}
        for key in ("PYTHONHOME", "PYTHONPATH", "__PYVENV_LAUNCHER__", "VIRTUAL_ENV"):
            child_env.pop(key, None)
        child_env["PYTHONUNBUFFERED"] = "1"
        return child_env

    def _terminate_process(self) -> None:
        """Stop the child process without mutating the public manager state."""
        proc = self._process
        if proc is None:
            return
        try:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        except Exception:
            pass
        finally:
            self._process = None

    def _wait_for_startup(self) -> EngineStatus:
        """Wait until the preview port is reachable or startup fails."""
        deadline = time.monotonic() + self.startup_timeout_sec
        while True:
            if self._check_port_reachable():
                self._state = EngineState.RUNNING
                self._last_error = ""
                logger.info("livetalking_ready", port=self.port, pid=self._process.pid if self._process else None)
                return self.get_status()

            proc = self._process
            if proc is None:
                self._state = EngineState.ERROR
                self._last_error = "LiveTalking process disappeared during startup"
                return self.get_status()

            poll = proc.poll()
            if poll is not None:
                log_hint = self._summarize_recent_logs()
                self._state = EngineState.ERROR
                self._last_error = (
                    f"Process exited with code {poll}"
                    + (f": {log_hint}" if log_hint else "")
                )
                self._process = None
                return self.get_status()

            if time.monotonic() >= deadline:
                self._state = EngineState.ERROR
                self._last_error = (
                    f"Preview port {self.port} did not become reachable within "
                    f"{self.startup_timeout_sec:.1f}s"
                )
                self._terminate_process()
                return self.get_status()

            time.sleep(1.0)

    def start(self) -> EngineStatus:
        """Start the LiveTalking engine subprocess."""
        if self._state == EngineState.RUNNING and self._process and self._process.poll() is None:
            return self.get_status()

        if is_mock_mode():
            self._state = EngineState.RUNNING
            self._start_time = time.time()
            logger.info("livetalking_mock_start")
            return self.get_status()

        # Validate prerequisites
        if not self.app_py.exists():
            self._state = EngineState.ERROR
            self._last_error = f"app.py not found: {self.app_py}"
            return self.get_status()

        if not self._python_executable_exists():
            self._state = EngineState.ERROR
            self._last_error = f"Python executable not found: {self.python_executable}"
            return self.get_status()

        if not self._check_port_free():
            self._state = EngineState.ERROR
            self._last_error = f"Port {self.port} is already in use"
            return self.get_status()

        # Build and execute command
        cmd = self.build_launch_command()
        self._state = EngineState.STARTING
        self._log_buffer.clear()

        try:
            logger.info("livetalking_starting", cmd=" ".join(cmd))
            self._process = subprocess.Popen(
                cmd,
                cwd=str(self.livetalking_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=self._build_child_env(),
            )
            self._start_time = time.time()
            self._state = EngineState.STARTING
            self._last_error = ""

            # Start log reader thread
            self._log_thread = threading.Thread(
                target=self._read_process_output, daemon=True
            )
            self._log_thread.start()

            logger.info("livetalking_started", pid=self._process.pid)
            return self._wait_for_startup()

        except Exception as e:
            self._state = EngineState.ERROR
            self._last_error = str(e)
            logger.error("livetalking_start_failed", error=str(e))

        return self.get_status()

    def stop(self) -> EngineStatus:
        """Stop the LiveTalking engine subprocess."""
        if is_mock_mode():
            self._state = EngineState.STOPPED
            self._start_time = 0.0
            logger.info("livetalking_mock_stop")
            return self.get_status()

        if self._process is None:
            self._state = EngineState.STOPPED
            return self.get_status()

        self._state = EngineState.STOPPING
        try:
            self._process.terminate()
            try:
                self._process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=5)

            logger.info("livetalking_stopped")
        except Exception as e:
            self._last_error = str(e)
            logger.error("livetalking_stop_failed", error=str(e))
        finally:
            self._process = None
            self._state = EngineState.STOPPED
            self._start_time = 0.0

        return self.get_status()

    def is_running(self) -> bool:
        """Check if the engine process is currently running."""
        if is_mock_mode():
            return self._state == EngineState.RUNNING

        if self._process is None:
            return False

        poll = self._process.poll()
        if poll is not None:
            # Process has exited
            self._state = EngineState.ERROR
            self._last_error = f"Process exited with code {poll}"
            self._process = None
            return False

        return True

    def get_logs(self, tail: int = 100) -> list[str]:
        """Get recent log lines from the engine process."""
        lines = list(self._log_buffer)
        return lines[-tail:]

    def get_status(self) -> EngineStatus:
        """Get current engine status."""
        # Refresh state if process died
        if self._state == EngineState.RUNNING:
            self.is_running()

        uptime = 0.0
        if self._start_time > 0 and self._state == EngineState.RUNNING:
            uptime = time.time() - self._start_time

        return EngineStatus(
            state=self._state,
            pid=self._process.pid if self._process else None,
            port=self.port,
            model=self.model,
            avatar_id=self.avatar_id,
            transport=self.transport,
            uptime_sec=uptime,
            last_error=self._last_error,
            app_py_exists=self.app_py.exists(),
            model_path_exists=self.models_dir.exists(),
            avatar_path_exists=(self.avatars_dir / self.avatar_id).exists(),
            requested_model=self.requested_model,
            requested_avatar_id=self.requested_avatar_id,
            python_executable=self.python_executable,
            python_executable_exists=self._python_executable_exists(),
            startup_timeout_sec=self.startup_timeout_sec,
            push_url=self.push_url,
        )

    def get_config_dict(self) -> dict[str, Any]:
        """Get current engine configuration as dict."""
        return {
            "port": self.port,
            "transport": self.transport,
            "model": self.model,
            "avatar_id": self.avatar_id,
            "requested_model": self.requested_model,
            "resolved_model": self.model,
            "requested_avatar_id": self.requested_avatar_id,
            "resolved_avatar_id": self.avatar_id,
            "livetalking_dir": str(self.livetalking_dir),
            "app_py": str(self.app_py),
            "models_dir": str(self.models_dir),
            "avatars_dir": str(self.avatars_dir),
            "supported_transports": list(SUPPORTED_TRANSPORTS),
            "supported_models": list(SUPPORTED_MODELS),
            "python_executable": self.python_executable,
            "python_executable_exists": self._python_executable_exists(),
            "startup_timeout_sec": self.startup_timeout_sec,
            "push_url": self.push_url,
            "rtcpush_requires_local_relay": True,
            "rtcpush_local_fallback": "direct-webrtc-preview",
            "launch_command": " ".join(self.build_launch_command()),
        }


# Global singleton
_manager: LiveTalkingManager | None = None


def get_livetalking_manager() -> LiveTalkingManager:
    """Get or create the global LiveTalking manager."""
    global _manager
    if _manager is None:
        _manager = LiveTalkingManager()
    return _manager
