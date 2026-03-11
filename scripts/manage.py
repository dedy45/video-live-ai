"""Cross-platform operator CLI for local runtime management.

This script is the source of truth for local operator actions:
- start/stop app
- inspect status and health
- run validation commands
- tail logs
- run setup helpers

Windows `menu.bat` should call this script via:
    uv run python scripts/manage.py <command>
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import socket
import subprocess
import sys
import time
import webbrowser
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Callable

import httpx


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
LOG_DIR = DATA_DIR / "logs"
PID_FILE = DATA_DIR / ".server.pid"
SERVER_LOG = LOG_DIR / "server.log"
APP_LOG = LOG_DIR / "app.log"


@dataclass
class RuntimeSnapshot:
    """Minimal runtime snapshot for local operator actions."""

    state: str
    pid: int | None
    pid_file_exists: bool
    pid_running: bool
    port: int
    port_open: bool
    base_url: str


def build_server_command(include_livetalking: bool = False) -> list[str]:
    """Canonical app launch command."""
    command = ["uv", "run"]
    if include_livetalking:
        command.extend(["--extra", "livetalking"])
    command.extend(["python", "-m", "src.main"])
    return command


def build_runtime_env(mock_mode: bool, base_env: dict[str, str] | None = None) -> dict[str, str]:
    """Build runtime environment with explicit mode and safe stdout encoding."""
    env = dict(base_env or os.environ)
    env["PYTHONUTF8"] = "1"
    env["MOCK_MODE"] = "true" if mock_mode else "false"
    return env


def get_dashboard_port(default: int = 8000) -> int:
    """Resolve configured dashboard port without hard failing on config issues."""
    try:
        from src.config import load_config

        return int(load_config().dashboard.port)
    except Exception:
        return default


def is_port_open(port: int, host: str = "127.0.0.1") -> bool:
    """Check whether a TCP port is accepting connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex((host, port)) == 0


def read_pid(pid_file: Path = PID_FILE) -> int | None:
    """Read PID from file if present and valid."""
    if not pid_file.exists():
        return None
    try:
        return int(pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def pid_is_running(pid: int) -> bool:
    """Check whether a process is alive."""
    if pid <= 0:
        return False
    if os.name == "nt":
        return windows_pid_is_running(pid)
    try:
        os.kill(pid, 0)
    except OSError:
        return False
    return True


def windows_pid_is_running(
    pid: int,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> bool:
    """Check process liveness on Windows via tasklist."""
    if pid <= 0:
        return False
    result = runner(
        ["tasklist", "/FI", f"PID eq {pid}"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return False
    return str(pid) in result.stdout


def get_runtime_snapshot(
    project_root: Path = PROJECT_ROOT,
    port: int | None = None,
    is_port_open: Callable[[int], bool] = is_port_open,
    pid_is_running: Callable[[int], bool] = pid_is_running,
) -> RuntimeSnapshot:
    """Build a runtime snapshot from pid file and port status."""
    resolved_port = port if port is not None else get_dashboard_port()
    pid_file = project_root / "data" / ".server.pid"
    pid = read_pid(pid_file)
    port_open = is_port_open(resolved_port)
    pid_running_flag = pid_is_running(pid) if pid is not None else False

    if pid_running_flag or port_open:
        state = "running"
    elif pid_file.exists():
        state = "stale_pid"
    else:
        state = "stopped"

    return RuntimeSnapshot(
        state=state,
        pid=pid,
        pid_file_exists=pid_file.exists(),
        pid_running=pid_running_flag,
        port=resolved_port,
        port_open=port_open,
        base_url=f"http://127.0.0.1:{resolved_port}",
    )


def run_command(command: list[str], env: dict[str, str] | None = None) -> int:
    """Run a foreground command and return its exit code."""
    completed = subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        env=env,
        check=False,
    )
    return int(completed.returncode)


def start_server(mock_mode: bool) -> int:
    """Start the FastAPI app in the background using uv."""
    snapshot = get_runtime_snapshot()
    if snapshot.port_open:
        print(f"[WARN] Port {snapshot.port} is already in use.")
        print(f"       Base URL: {snapshot.base_url}")
        return 1

    LOG_DIR.mkdir(parents=True, exist_ok=True)
    env = build_runtime_env(mock_mode=mock_mode)
    command = build_server_command(include_livetalking=not mock_mode)

    with SERVER_LOG.open("a", encoding="utf-8") as log_handle:
        popen_kwargs: dict[str, object] = {
            "cwd": PROJECT_ROOT,
            "env": env,
            "stdout": log_handle,
            "stderr": subprocess.STDOUT,
        }
        if os.name == "nt":
            popen_kwargs["creationflags"] = (
                subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS
            )
        else:
            popen_kwargs["start_new_session"] = True

        subprocess.Popen(command, **popen_kwargs)

    for _ in range(12):
        time.sleep(1)
        snapshot = get_runtime_snapshot()
        if snapshot.port_open:
            print(f"[OK] Server running at {snapshot.base_url}")
            print(f"     Dashboard: {snapshot.base_url}/dashboard/")
            print(f"     Docs:      {snapshot.base_url}/docs")
            return 0

    print("[WARN] Server process launched, but port did not open yet.")
    print(f"       Check logs: {SERVER_LOG}")
    return 1


def stop_server() -> int:
    """Stop the FastAPI app using the recorded PID, with a Windows fallback."""
    pid = read_pid()
    if pid is None:
        snapshot = get_runtime_snapshot()
        if snapshot.port_open:
            print("[WARN] Port is open but PID file is missing. Stop manually or inspect logs.")
            return 1
        print("[OK] Server already stopped.")
        return 0

    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(pid)],
                cwd=PROJECT_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )
        else:
            os.kill(pid, signal.SIGTERM)
    finally:
        try:
            PID_FILE.unlink(missing_ok=True)
        except TypeError:
            if PID_FILE.exists():
                PID_FILE.unlink()

    for _ in range(8):
        time.sleep(1)
        snapshot = get_runtime_snapshot()
        if not snapshot.port_open:
            print("[OK] Server stopped.")
            return 0

    print("[WARN] Stop requested, but port still appears open.")
    return 1


def fetch_json(path: str, base_url: str | None = None) -> dict | list:
    """Fetch JSON from the running app."""
    resolved_base = base_url or get_runtime_snapshot().base_url
    with httpx.Client(timeout=5.0) as client:
        response = client.get(f"{resolved_base}{path}")
        response.raise_for_status()
        return response.json()


def print_status(as_json: bool) -> int:
    """Print runtime status summary."""
    snapshot = get_runtime_snapshot()
    payload = asdict(snapshot)

    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print("=== App Status ===")
        print(f"State          : {snapshot.state}")
        print(f"PID            : {snapshot.pid or '-'}")
        print(f"PID file       : {'yes' if snapshot.pid_file_exists else 'no'}")
        print(f"PID running    : {'yes' if snapshot.pid_running else 'no'}")
        print(f"Port {snapshot.port:<9}: {'open' if snapshot.port_open else 'closed'}")
        print(f"Base URL       : {snapshot.base_url}")
        print(f"Dashboard      : {snapshot.base_url}/dashboard/")
        print(f"API Docs       : {snapshot.base_url}/docs")
    return 0


def print_health(as_json: bool) -> int:
    """Print health, readiness, and runtime truth in one place."""
    snapshot = get_runtime_snapshot()
    if not snapshot.port_open:
        print("[ERROR] App is not running. Start it first.")
        return 1

    payload = {
        "status": fetch_json("/api/status", base_url=snapshot.base_url),
        "health_summary": fetch_json("/api/health/summary", base_url=snapshot.base_url),
        "readiness": fetch_json("/api/readiness", base_url=snapshot.base_url),
        "runtime_truth": fetch_json("/api/runtime/truth", base_url=snapshot.base_url),
    }

    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print("=== Health Summary ===")
        print(json.dumps(payload, indent=2))
    return 0


def validate_target(target: str) -> int:
    """Run one validation surface."""
    if target == "tests":
        return run_command(["uv", "run", "pytest", "tests", "-q", "-p", "no:cacheprovider"])
    if target == "pipeline":
        return run_command(["uv", "run", "python", "scripts/verify_pipeline.py"])
    if target == "readiness":
        return run_command(["uv", "run", "python", "scripts/check_real_mode_readiness.py", "--json"])
    if target == "livetalking":
        return run_command(
            ["uv", "run", "--extra", "livetalking", "python", "scripts/smoke_livetalking.py"]
        )
    if target == "fish-speech":
        return run_command(["uv", "run", "python", "scripts/setup_fish_speech.py", "--check"])
    if target == "all":
        for step in ("tests", "pipeline", "readiness", "livetalking", "fish-speech"):
            exit_code = validate_target(step)
            if exit_code != 0:
                return exit_code
        return 0
    raise ValueError(f"Unknown validation target: {target}")


def print_logs(lines: int) -> int:
    """Tail the most relevant log files."""
    found = False
    for path in (SERVER_LOG, APP_LOG):
        if path.exists():
            found = True
            print(f"=== {path.relative_to(PROJECT_ROOT)} (last {lines} lines) ===")
            content = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in content[-lines:]:
                print(line)
            print()
    if not found:
        print("[WARN] No log files found yet.")
    return 0


def run_sync(include_livetalking: bool) -> int:
    """Sync dependencies with uv."""
    command = ["uv", "sync", "--extra", "dev"]
    if include_livetalking:
        command.extend(["--extra", "livetalking"])
    return run_command(command)


def setup_app() -> int:
    """Bootstrap the main app dependencies only."""
    return run_sync(include_livetalking=False)


def load_products() -> int:
    """Load sample products into the local database."""
    return run_command(["uv", "run", "python", "scripts/load_sample_data.py"])


def setup_livetalking(skip_models: bool) -> int:
    """Run the dedicated LiveTalking setup flow."""
    command = ["uv", "run", "--extra", "livetalking", "python", "scripts/setup_livetalking.py"]
    if skip_models:
        command.append("--skip-models")
    return run_command(command)


def setup_fish_speech() -> int:
    """Run the dedicated Fish-Speech setup flow."""
    return run_command(["uv", "run", "python", "scripts/setup_fish_speech.py"])


def setup_musetalk_model() -> int:
    """Run the canonical MuseTalk asset/model setup flow."""
    return run_command(
        ["uv", "run", "--extra", "livetalking", "python", "scripts/setup_musetalk_assets.py"]
    )


def setup_target(target: str) -> int:
    """Run one setup surface from the unified setup namespace."""
    if target == "all":
        for step in ("app", "livetalking", "musetalk-model", "fish-speech"):
            exit_code = setup_target(step)
            if exit_code != 0:
                return exit_code
        return 0
    if target == "app":
        return setup_app()
    if target == "livetalking":
        return setup_livetalking(skip_models=False)
    if target == "musetalk-model":
        return setup_musetalk_model()
    if target == "fish-speech":
        return setup_fish_speech()
    raise ValueError(f"Unknown setup target: {target}")


def start_fish_speech() -> int:
    """Start the Fish-Speech sidecar via the managed setup/runtime helper."""
    return run_command(["uv", "run", "python", "scripts/setup_fish_speech.py", "--start"])


def build_livetalking_command(mode: str) -> list[str]:
    """Build the canonical LiveTalking start command for the selected model mode."""
    avatar_id = "musetalk_avatar1" if mode == "musetalk" else "wav2lip256_avatar1"
    return [
        "uv",
        "run",
        "--extra",
        "livetalking",
        "python",
        "external/livetalking/app.py",
        "--transport",
        "webrtc",
        "--model",
        mode,
        "--avatar_id",
        avatar_id,
        "--listenport",
        "8010",
    ]


def start_target(target: str, mode: str | None = None) -> int:
    """Start one runtime target from the unified start namespace."""
    if target == "app":
        return start_server(mock_mode=False)
    if target == "fish-speech":
        return start_fish_speech()
    if target == "livetalking":
        return run_command(build_livetalking_command(mode or "musetalk"))
    raise ValueError(f"Unknown start target: {target}")


def stop_target(target: str) -> int:
    """Stop one runtime target from the unified stop namespace."""
    if target == "app":
        return stop_server()
    if target == "fish-speech":
        return run_command(["uv", "run", "python", "scripts/setup_fish_speech.py", "--stop"])
    if target == "livetalking":
        print("[WARN] LiveTalking stop is not yet supervised by a managed pid file.")
        return 1
    if target == "all":
        results = [stop_target("fish-speech"), stop_target("app")]
        return 0 if all(result == 0 for result in results) else 1
    raise ValueError(f"Unknown stop target: {target}")


def print_all_status(as_json: bool) -> int:
    """Print an aggregate runtime snapshot for app, vendor, and Fish-Speech."""
    app_snapshot = get_runtime_snapshot()
    payload = {
        "app": asdict(app_snapshot),
        "livetalking": {
            "port": 8010,
            "reachable": is_port_open(8010),
            "url": "http://127.0.0.1:8010/dashboard.html",
        },
        "fish_speech": {
            "port": 8080,
            "reachable": is_port_open(8080),
            "target": str(PROJECT_ROOT / "external" / "fish-speech"),
        },
    }
    if as_json:
        print(json.dumps(payload, indent=2))
    else:
        print("=== Runtime Status ===")
        print(json.dumps(payload, indent=2))
    return 0


def print_target_status(target: str, as_json: bool) -> int:
    """Print status for one managed target."""
    if target == "app":
        return print_status(as_json=as_json)
    if target == "fish-speech":
        command = ["uv", "run", "python", "scripts/setup_fish_speech.py", "--status"]
        if as_json:
            command.append("--json")
        return run_command(command)
    if target == "all":
        return print_all_status(as_json=as_json)
    raise ValueError(f"Unknown status target: {target}")


def open_target(target: str) -> int:
    """Open a local browser target."""
    snapshot = get_runtime_snapshot()
    base = snapshot.base_url
    mapping = {
        "dashboard": f"{base}/dashboard/",
        "performer": f"{base}/dashboard/performer.html",
        "monitor": f"{base}/dashboard/monitor.html",
        "docs": f"{base}/docs",
        "vendor": "http://127.0.0.1:8010/dashboard.html",
    }
    url = mapping[target]
    webbrowser.open(url)
    print(url)
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI parser."""
    parser = argparse.ArgumentParser(description="UV-aligned operator CLI for videoliveai")
    subparsers = parser.add_subparsers(dest="command", required=True)

    serve_parser = subparsers.add_parser("serve", help="Start the app")
    serve_mode = serve_parser.add_mutually_exclusive_group(required=True)
    serve_mode.add_argument("--mock", action="store_true", help="Start with MOCK_MODE=true")
    serve_mode.add_argument("--real", action="store_true", help="Start with MOCK_MODE=false")

    start_parser = subparsers.add_parser("start", help="Start a managed runtime target")
    start_parser.add_argument("target", choices=["app", "livetalking", "fish-speech"])
    start_parser.add_argument(
        "--mode",
        choices=["musetalk", "wav2lip"],
        help="Runtime mode for LiveTalking starts",
    )

    stop_parser = subparsers.add_parser("stop", help="Stop a managed runtime target")
    stop_parser.add_argument(
        "target",
        nargs="?",
        default="app",
        choices=["app", "livetalking", "fish-speech", "all"],
    )

    status_parser = subparsers.add_parser("status", help="Show runtime status")
    status_parser.add_argument("target", nargs="?", default="app", choices=["app", "fish-speech", "all"])
    status_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    health_parser = subparsers.add_parser("health", help="Show health/readiness summary")
    health_parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")

    validate_parser = subparsers.add_parser("validate", help="Run validation flows")
    validate_parser.add_argument(
        "target",
        choices=["tests", "pipeline", "readiness", "livetalking", "fish-speech", "all"],
        help="Validation target",
    )

    logs_parser = subparsers.add_parser("logs", help="Tail logs")
    logs_parser.add_argument("--lines", type=int, default=30, help="Number of lines to print")

    sync_parser = subparsers.add_parser("sync", help="Sync dependencies with uv")
    sync_parser.add_argument("--livetalking", action="store_true", help="Include livetalking extra")

    subparsers.add_parser("load-products", help="Load local sample products")

    setup_livetalking_parser = subparsers.add_parser(
        "setup-livetalking",
        help="Install and normalize vendor LiveTalking dependencies/assets via uv",
    )
    setup_livetalking_parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip model download and only setup deps/assets/layout",
    )

    subparsers.add_parser(
        "setup-fish-speech",
        help="Check Fish-Speech voice clone prerequisites and print startup guidance",
    )

    setup_parser = subparsers.add_parser("setup", help="Run one setup workflow")
    setup_parser.add_argument(
        "target",
        choices=["all", "app", "livetalking", "musetalk-model", "fish-speech"],
    )

    open_parser = subparsers.add_parser("open", help="Open a local URL in the browser")
    open_parser.add_argument("target", choices=["dashboard", "performer", "monitor", "docs", "vendor"])

    return parser


def main(argv: list[str] | None = None) -> int:
    """CLI entrypoint."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "serve":
        return start_server(mock_mode=bool(args.mock))
    if args.command == "start":
        return start_target(target=str(args.target), mode=getattr(args, "mode", None))
    if args.command == "stop":
        return stop_target(target=str(args.target))
    if args.command == "status":
        return print_target_status(target=str(args.target), as_json=bool(args.json))
    if args.command == "health":
        return print_health(as_json=bool(args.json))
    if args.command == "validate":
        return validate_target(str(args.target))
    if args.command == "logs":
        return print_logs(lines=int(args.lines))
    if args.command == "sync":
        return run_sync(include_livetalking=bool(args.livetalking))
    if args.command == "load-products":
        return load_products()
    if args.command == "setup-livetalking":
        return setup_livetalking(skip_models=bool(args.skip_models))
    if args.command == "setup-fish-speech":
        return setup_fish_speech()
    if args.command == "setup":
        return setup_target(str(args.target))
    if args.command == "open":
        return open_target(str(args.target))

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
