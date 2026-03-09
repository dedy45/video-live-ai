"""Tests for the uv-aligned management CLI helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
MANAGE_PATH = PROJECT_ROOT / "scripts" / "manage.py"


def load_manage_module():
    """Load scripts/manage.py as a module for unit-style tests."""
    spec = importlib.util.spec_from_file_location("manage_cli", MANAGE_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_build_server_command_uses_uv_run_python() -> None:
    """Server launch must always go through uv, not direct venv Python."""
    manage = load_manage_module()

    command = manage.build_server_command()

    assert command == ["uv", "run", "python", "-m", "src.main"]


def test_build_server_command_can_include_livetalking_extra() -> None:
    """Real-mode server launch should opt into the managed LiveTalking extra."""
    manage = load_manage_module()

    command = manage.build_server_command(include_livetalking=True)

    assert command == ["uv", "run", "--extra", "livetalking", "python", "-m", "src.main"]


def test_build_runtime_env_sets_utf8_and_explicit_mock_mode() -> None:
    """Runtime env should force UTF-8 and make mock mode explicit."""
    manage = load_manage_module()

    env = manage.build_runtime_env(mock_mode=True, base_env={"EXAMPLE": "1"})

    assert env["EXAMPLE"] == "1"
    assert env["PYTHONUTF8"] == "1"
    assert env["MOCK_MODE"] == "true"


def test_runtime_snapshot_reports_stopped_when_no_pid_and_no_port(tmp_path: Path) -> None:
    """Status should be stopped when neither pid file nor port indicate a running app."""
    manage = load_manage_module()

    snapshot = manage.get_runtime_snapshot(
        project_root=tmp_path,
        port=8000,
        is_port_open=lambda _port: False,
        pid_is_running=lambda _pid: False,
    )

    assert snapshot.state == "stopped"
    assert snapshot.pid is None
    assert snapshot.port_open is False


def test_windows_pid_check_uses_tasklist_output() -> None:
    """Windows PID probing should use tasklist rather than os.kill(pid, 0)."""
    manage = load_manage_module()

    class Result:
        returncode = 0
        stdout = "python.exe                   24296 Console                    1    170,816 K"

    running = manage.windows_pid_is_running(
        24296,
        runner=lambda *args, **kwargs: Result(),
    )

    assert running is True


def test_parser_accepts_setup_livetalking_command() -> None:
    """CLI should expose a dedicated LiveTalking setup command."""
    manage = load_manage_module()

    parser = manage.build_parser()
    args = parser.parse_args(["setup-livetalking", "--skip-models"])

    assert args.command == "setup-livetalking"
    assert args.skip_models is True


def test_setup_livetalking_runs_with_livetalking_extra() -> None:
    """LiveTalking setup should run in an env that includes the optional extra."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command

    exit_code = manage.setup_livetalking(skip_models=True)

    assert exit_code == 0
    assert captured["command"] == [
        "uv",
        "run",
        "--extra",
        "livetalking",
        "python",
        "scripts/setup_livetalking.py",
        "--skip-models",
    ]


# === Task 6: Operator path aligns with MuseTalk-only acceptance ===


def test_serve_real_includes_livetalking_extra() -> None:
    """serve --real must include --extra livetalking so vendor deps are available."""
    manage = load_manage_module()

    command = manage.build_server_command(include_livetalking=True)

    assert "--extra" in command
    assert "livetalking" in command
    assert command == ["uv", "run", "--extra", "livetalking", "python", "-m", "src.main"]


def test_serve_real_sets_mock_mode_false() -> None:
    """serve --real must set MOCK_MODE=false in the runtime environment."""
    manage = load_manage_module()

    env = manage.build_runtime_env(mock_mode=False, base_env={})

    assert env["MOCK_MODE"] == "false"


def test_validate_livetalking_uses_livetalking_extra() -> None:
    """validate livetalking must run with --extra livetalking."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command
    manage.validate_target("livetalking")

    assert captured["command"] == [
        "uv", "run", "--extra", "livetalking",
        "python", "scripts/smoke_livetalking.py",
    ]


def test_parser_serve_real_flag() -> None:
    """CLI parser must accept serve --real."""
    manage = load_manage_module()

    parser = manage.build_parser()
    args = parser.parse_args(["serve", "--real"])

    assert args.command == "serve"
    assert args.real is True
    assert args.mock is False


def test_validate_target_accepts_all_surfaces() -> None:
    """validate command must accept tests, pipeline, readiness, livetalking, all."""
    manage = load_manage_module()
    parser = manage.build_parser()

    for target in ("tests", "pipeline", "readiness", "livetalking", "all"):
        args = parser.parse_args(["validate", target])
        assert args.target == target


# === Task 7: Fish-Speech operator CLI hooks ===


def test_parser_accepts_setup_fish_speech_command() -> None:
    """CLI should expose a dedicated Fish-Speech setup command."""
    manage = load_manage_module()

    parser = manage.build_parser()
    args = parser.parse_args(["setup-fish-speech"])

    assert args.command == "setup-fish-speech"


def test_setup_fish_speech_runs_setup_script() -> None:
    """setup-fish-speech must invoke scripts/setup_fish_speech.py via uv run."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command

    exit_code = manage.setup_fish_speech()

    assert exit_code == 0
    assert captured["command"] == [
        "uv", "run", "python", "scripts/setup_fish_speech.py",
    ]


def test_validate_target_accepts_fish_speech() -> None:
    """validate command must accept fish-speech as a target."""
    manage = load_manage_module()
    parser = manage.build_parser()

    args = parser.parse_args(["validate", "fish-speech"])
    assert args.target == "fish-speech"


def test_validate_fish_speech_runs_setup_script_with_check_flag() -> None:
    """validate fish-speech must run setup_fish_speech.py --check for validation."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command
    manage.validate_target("fish-speech")

    assert captured["command"] == [
        "uv", "run", "python", "scripts/setup_fish_speech.py", "--check",
    ]


def test_main_dispatches_setup_fish_speech() -> None:
    """main(['setup-fish-speech']) must dispatch to setup_fish_speech()."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command
    exit_code = manage.main(["setup-fish-speech"])

    assert exit_code == 0
    assert "setup_fish_speech.py" in captured["command"][-1]


def test_validate_target_accepts_all_including_fish_speech() -> None:
    """validate command must accept fish-speech alongside existing targets."""
    manage = load_manage_module()
    parser = manage.build_parser()

    for target in ("tests", "pipeline", "readiness", "livetalking", "fish-speech", "all"):
        args = parser.parse_args(["validate", target])
        assert args.target == target


def test_smoke_livetalking_reports_requested_vs_resolved() -> None:
    """smoke_livetalking.py must expose requested vs resolved model/avatar."""
    import importlib.util

    smoke_path = PROJECT_ROOT / "scripts" / "smoke_livetalking.py"
    spec = importlib.util.spec_from_file_location("smoke_lt", smoke_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    assert hasattr(module, "REQUESTED_MODEL")
    assert hasattr(module, "RESOLVED_MODEL")
    assert hasattr(module, "REQUESTED_AVATAR_ID")
    assert hasattr(module, "RESOLVED_AVATAR_ID")
    # Requested must be musetalk (source of truth default)
    assert module.REQUESTED_MODEL == "musetalk"
    assert module.REQUESTED_AVATAR_ID == "musetalk_avatar1"
