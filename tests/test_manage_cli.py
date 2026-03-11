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


def test_parser_accepts_nested_setup_targets() -> None:
    """Unified setup namespace should expose all, app, livetalking, musetalk-model, fish-speech."""
    manage = load_manage_module()
    parser = manage.build_parser()

    for target in ("all", "app", "livetalking", "musetalk-model", "fish-speech"):
        args = parser.parse_args(["setup", target])
        assert args.command == "setup"
        assert args.target == target


def test_setup_all_runs_expected_sequence() -> None:
    """setup all should orchestrate app, livetalking, musetalk-model, then fish-speech."""
    manage = load_manage_module()
    steps: list[str] = []

    manage.setup_app = lambda: steps.append("app") or 0
    manage.setup_livetalking = lambda skip_models=False: steps.append("livetalking") or 0
    manage.setup_musetalk_model = lambda: steps.append("musetalk-model") or 0
    manage.setup_fish_speech = lambda: steps.append("fish-speech") or 0

    exit_code = manage.main(["setup", "all"])

    assert exit_code == 0
    assert steps == ["app", "livetalking", "musetalk-model", "fish-speech"]


def test_setup_app_runs_uv_sync_dev_only() -> None:
    """setup app should only sync the main app dependencies."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command

    exit_code = manage.main(["setup", "app"])

    assert exit_code == 0
    assert captured["command"] == ["uv", "sync", "--extra", "dev"]


def test_setup_musetalk_model_delegates_to_assets_script() -> None:
    """setup musetalk-model should delegate to the canonical MuseTalk asset setup script."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command

    exit_code = manage.main(["setup", "musetalk-model"])

    assert exit_code == 0
    assert captured["command"] == [
        "uv", "run", "--extra", "livetalking", "python", "scripts/setup_musetalk_assets.py",
    ]


def test_parser_accepts_start_fish_speech() -> None:
    """Unified start namespace should expose fish-speech target."""
    manage = load_manage_module()
    parser = manage.build_parser()

    args = parser.parse_args(["start", "fish-speech"])

    assert args.command == "start"
    assert args.target == "fish-speech"


def test_start_fish_speech_delegates_to_runtime_helper() -> None:
    """start fish-speech should delegate to setup_fish_speech.py --start."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command

    exit_code = manage.main(["start", "fish-speech"])

    assert exit_code == 0
    assert captured["command"] == ["uv", "run", "python", "scripts/setup_fish_speech.py", "--start"]


def test_start_livetalking_musetalk_uses_canonical_vendor_command() -> None:
    """start livetalking --mode musetalk should use canonical vendor app.py args."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command

    exit_code = manage.main(["start", "livetalking", "--mode", "musetalk"])

    assert exit_code == 0
    assert captured["command"] == [
        "uv",
        "run",
        "--extra",
        "livetalking",
        "python",
        "external/livetalking/app.py",
        "--transport",
        "webrtc",
        "--model",
        "musetalk",
        "--avatar_id",
        "musetalk_avatar1",
        "--listenport",
        "8010",
    ]


def test_start_livetalking_wav2lip_uses_canonical_vendor_command() -> None:
    """start livetalking --mode wav2lip should use canonical vendor app.py args."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command

    exit_code = manage.main(["start", "livetalking", "--mode", "wav2lip"])

    assert exit_code == 0
    assert captured["command"] == [
        "uv",
        "run",
        "--extra",
        "livetalking",
        "python",
        "external/livetalking/app.py",
        "--transport",
        "webrtc",
        "--model",
        "wav2lip",
        "--avatar_id",
        "wav2lip256_avatar1",
        "--listenport",
        "8010",
    ]


def test_parser_accepts_stop_all() -> None:
    """stop should accept all as an aggregate target."""
    manage = load_manage_module()
    parser = manage.build_parser()

    args = parser.parse_args(["stop", "all"])

    assert args.command == "stop"
    assert args.target == "all"


def test_stop_fish_speech_delegates_to_runtime_helper() -> None:
    """stop fish-speech should delegate to setup_fish_speech.py --stop."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command

    exit_code = manage.main(["stop", "fish-speech"])

    assert exit_code == 0
    assert captured["command"] == ["uv", "run", "python", "scripts/setup_fish_speech.py", "--stop"]


def test_parser_accepts_status_all() -> None:
    """status should accept all as an aggregate target."""
    manage = load_manage_module()
    parser = manage.build_parser()

    args = parser.parse_args(["status", "all"])

    assert args.command == "status"
    assert args.target == "all"


def test_status_fish_speech_delegates_to_runtime_helper() -> None:
    """status fish-speech should delegate to setup_fish_speech.py --status."""
    manage = load_manage_module()
    captured: dict[str, list[str]] = {}

    def fake_run_command(command: list[str], env=None) -> int:
        captured["command"] = command
        return 0

    manage.run_command = fake_run_command

    exit_code = manage.main(["status", "fish-speech"])

    assert exit_code == 0
    assert captured["command"] == ["uv", "run", "python", "scripts/setup_fish_speech.py", "--status"]


def test_print_all_status_reports_fish_speech_target_path(capsys) -> None:
    """status all should expose the canonical fish-speech target path."""
    manage = load_manage_module()

    manage.get_runtime_snapshot = lambda: manage.RuntimeSnapshot(
        state="stopped",
        pid=None,
        pid_file_exists=False,
        pid_running=False,
        port=8000,
        port_open=False,
        base_url="http://127.0.0.1:8000",
    )
    manage.is_port_open = lambda port, host="127.0.0.1": False

    exit_code = manage.print_all_status(as_json=True)
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "external\\\\fish-speech" in captured


def test_open_target_supports_operator_surfaces() -> None:
    """open should support performer and monitor operator pages."""
    manage = load_manage_module()
    opened: list[str] = []

    manage.webbrowser.open = opened.append
    manage.get_runtime_snapshot = lambda: manage.RuntimeSnapshot(
        state="running",
        pid=123,
        pid_file_exists=True,
        pid_running=True,
        port=8000,
        port_open=True,
        base_url="http://127.0.0.1:8000",
    )

    assert manage.main(["open", "performer"]) == 0
    assert manage.main(["open", "monitor"]) == 0
    assert opened == [
        "http://127.0.0.1:8000/dashboard/performer.html",
        "http://127.0.0.1:8000/dashboard/monitor.html",
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
