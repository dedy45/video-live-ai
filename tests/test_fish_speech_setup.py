"""Regression tests for Fish-Speech setup/runtime helpers."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "setup_fish_speech.py"


def load_setup_module():
    """Load scripts/setup_fish_speech.py as a module for focused tests."""
    spec = importlib.util.spec_from_file_location("setup_fish_speech", SCRIPT_PATH)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_resolve_layout_uses_canonical_external_paths(tmp_path: Path) -> None:
    """Fish-Speech layout should resolve inside external/fish-speech only."""
    setup = load_setup_module()

    layout = setup.resolve_layout(tmp_path)

    assert layout.root == tmp_path / "external" / "fish-speech"
    assert layout.upstream_dir == layout.root / "upstream"
    assert layout.checkout_dir == layout.upstream_dir / "fish-speech"
    assert layout.checkpoints_dir == layout.root / "checkpoints"
    assert layout.runtime_dir == layout.root / "runtime"
    assert layout.venv_dir == layout.runtime_dir / ".venv"
    assert layout.venv_python == layout.venv_dir / "Scripts" / "python.exe"
    assert layout.pid_file == layout.runtime_dir / "fish-speech.pid"
    assert layout.log_file == layout.runtime_dir / "fish-speech.log"


def test_ensure_layout_creates_expected_directories(tmp_path: Path) -> None:
    """Bootstrap should create upstream, checkpoints, runtime, and scripts dirs."""
    setup = load_setup_module()

    layout = setup.ensure_layout(tmp_path)

    assert layout.upstream_dir.is_dir()
    assert layout.checkpoints_dir.is_dir()
    assert layout.runtime_dir.is_dir()
    assert layout.scripts_dir.is_dir()


def test_build_status_payload_reports_layout_paths(tmp_path: Path) -> None:
    """Status payload should expose canonical layout paths for operator diagnostics."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    payload = setup.build_status_payload(
        project_root=tmp_path,
        server_reachable=lambda *_args, **_kwargs: False,
        pid_running=lambda *_args, **_kwargs: False,
    )

    assert payload["paths"]["root"] == str(layout.root)
    assert payload["paths"]["upstream"] == str(layout.upstream_dir)
    assert payload["paths"]["checkpoints"] == str(layout.checkpoints_dir)
    assert payload["paths"]["runtime"] == str(layout.runtime_dir)
    assert payload["runtime"]["reachable"] is False
    assert payload["runtime"]["pid"] is None


def test_build_start_command_uses_canonical_checkout_and_checkpoint_paths(tmp_path: Path) -> None:
    """Start command should target the managed checkout and canonical checkpoint locations."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_start_command(layout, listen="127.0.0.1:8080")

    assert command[:3] == [str(layout.venv_python), "-m", "tools.api_server"]
    assert "--listen" in command
    assert "127.0.0.1:8080" in command
    assert str(layout.checkpoints_dir / "fish-speech-1.5") in command
    assert str(
        layout.checkpoints_dir / "fish-speech-1.5" / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth"
    ) in command


def test_build_clone_command_uses_official_repo_and_pinned_tag(tmp_path: Path) -> None:
    """Checkout clone command should target the official repo and the pinned v1.5.1 tag."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_clone_command(layout)

    assert command == [
        "git",
        "clone",
        "--depth",
        "1",
        "--branch",
        "v1.5.1",
        "https://github.com/fishaudio/fish-speech.git",
        str(layout.checkout_dir),
    ]


def test_build_venv_command_targets_runtime_sidecar_env(tmp_path: Path) -> None:
    """Dedicated Fish-Speech env should be created under runtime/.venv."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_venv_command(layout)

    assert command == ["uv", "venv", str(layout.venv_dir), "--allow-existing"]


def test_build_torch_install_command_pins_cuda_runtime(tmp_path: Path) -> None:
    """Torch install should explicitly request the CUDA 12.4 wheels for the sidecar env."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_torch_install_command(layout)

    assert command == [
        "uv",
        "pip",
        "install",
        "--python",
        str(layout.venv_python),
        "--reinstall-package",
        "torch",
        "--reinstall-package",
        "torchaudio",
        "--default-index",
        "https://download.pytorch.org/whl/cu124",
        "torch==2.4.1",
        "torchaudio==2.4.1",
    ]


def test_build_install_command_uses_uv_pip_editable_stable_extra(tmp_path: Path) -> None:
    """Dependency install should use uv pip editable install with the stable extra in the sidecar env."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    command = setup.build_install_command(layout)

    assert command == [
        "uv",
        "pip",
        "install",
        "--python",
        str(layout.venv_python),
        "-e",
        ".[stable]",
    ]


def test_build_checkpoint_download_specs_use_official_repo_files(tmp_path: Path) -> None:
    """Checkpoint downloader should pull the official v1.5 file set into the canonical checkpoint root."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)

    specs = setup.build_checkpoint_download_specs(layout)

    assert specs[0]["repo_id"] == "fishaudio/fish-speech-1.5"
    assert specs[0]["local_dir"] == layout.checkpoints_dir / "fish-speech-1.5"
    assert "model.pth" in specs[0]["files"]
    assert "firefly-gan-vq-fsq-8x1024-21hz-generator.pth" in specs[0]["files"]


def test_bootstrap_install_runs_clone_install_and_checkpoint_download(tmp_path: Path) -> None:
    """Bootstrap should clone the pinned checkout, install deps, and hydrate checkpoints when missing."""
    setup = load_setup_module()
    calls: list[tuple[str, object]] = []

    def fake_run(command: list[str], cwd: Path | None = None) -> bool:
        calls.append(("run", (command, cwd)))
        return True

    def fake_download(layout, downloader=None) -> bool:  # type: ignore[no-untyped-def]
        calls.append(("download", layout.checkpoints_dir))
        return True

    exit_code = setup.bootstrap_install(
        project_root=tmp_path,
        runner=fake_run,
        checkpoint_downloader=fake_download,
    )

    layout = setup.resolve_layout(tmp_path)
    assert exit_code == 0
    assert calls[0] == ("run", (setup.build_clone_command(layout), None))
    assert calls[1] == ("run", (setup.build_venv_command(layout), None))
    assert calls[2] == ("run", (setup.build_torch_install_command(layout), layout.checkout_dir))
    assert calls[3] == ("run", (setup.build_install_command(layout), layout.checkout_dir))
    assert calls[4] == ("download", layout.checkpoints_dir)


def test_validate_checkpoint_files_detects_missing_files(tmp_path: Path) -> None:
    """Checkpoint validation should detect missing required files."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create checkpoint directory but leave it empty
    checkpoint_root = layout.checkpoints_dir / "fish-speech-1.5"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    
    valid, message = setup.validate_checkpoint_files(layout)
    
    assert valid is False
    assert "Missing checkpoint files" in message
    assert "model.pth" in message


def test_validate_checkpoint_files_detects_empty_files(tmp_path: Path) -> None:
    """Checkpoint validation should detect empty (invalid) checkpoint files."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    checkpoint_root = layout.checkpoints_dir / "fish-speech-1.5"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    
    # Create empty files
    (checkpoint_root / "model.pth").touch()
    (checkpoint_root / "config.json").touch()
    (checkpoint_root / "tokenizer.tiktoken").touch()
    (checkpoint_root / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth").touch()
    
    valid, message = setup.validate_checkpoint_files(layout)
    
    assert valid is False
    assert "Invalid (empty) checkpoint files" in message


def test_validate_checkpoint_files_passes_with_valid_files(tmp_path: Path) -> None:
    """Checkpoint validation should pass when all required files exist and are non-empty."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    checkpoint_root = layout.checkpoints_dir / "fish-speech-1.5"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    
    # Create non-empty files
    (checkpoint_root / "model.pth").write_bytes(b"fake model data")
    (checkpoint_root / "config.json").write_bytes(b'{"config": "data"}')
    (checkpoint_root / "tokenizer.tiktoken").write_bytes(b"fake tokenizer")
    (checkpoint_root / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth").write_bytes(b"fake decoder")
    
    valid, message = setup.validate_checkpoint_files(layout)
    
    assert valid is True
    assert "All checkpoint files valid" in message


def test_detect_trained_model_finds_trained_checkpoint(tmp_path: Path) -> None:
    """Trained model detection should find trained checkpoint in expected locations."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create trained model in one of the expected locations
    trained_dir = layout.checkpoints_dir / "trained"
    trained_dir.mkdir(parents=True, exist_ok=True)
    (trained_dir / "model.pth").write_bytes(b"trained model data")
    
    has_trained, trained_path = setup.detect_trained_model(layout)
    
    assert has_trained is True
    assert trained_path == trained_dir


def test_detect_trained_model_returns_false_when_no_trained_model(tmp_path: Path) -> None:
    """Trained model detection should return False when no trained model exists."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    has_trained, trained_path = setup.detect_trained_model(layout)
    
    assert has_trained is False
    assert trained_path is None


def test_check_health_endpoint_returns_false_when_server_down(tmp_path: Path) -> None:
    """Health endpoint check should return False when server is not reachable."""
    setup = load_setup_module()
    
    # Use a URL that definitely won't be reachable
    result = setup.check_health_endpoint("http://127.0.0.1:9999")
    
    assert result is False


def test_start_server_validates_checkpoints_before_starting(tmp_path: Path) -> None:
    """Start server should validate checkpoint files before attempting to start the process."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create checkout and venv but leave checkpoints invalid
    layout.checkout_dir.mkdir(parents=True, exist_ok=True)
    layout.venv_python.parent.mkdir(parents=True, exist_ok=True)
    layout.venv_python.touch()
    
    # Mock build_status_payload to return server not reachable
    original_build_status = setup.build_status_payload
    
    def mock_build_status(*args, **kwargs):  # type: ignore[no-untyped-def]
        payload = original_build_status(*args, **kwargs)
        payload["runtime"]["reachable"] = False
        return payload
    
    setup.build_status_payload = mock_build_status
    
    try:
        exit_code = setup.start_server(project_root=tmp_path)
        # Should fail due to invalid checkpoints
        assert exit_code == 1
    finally:
        setup.build_status_payload = original_build_status


def test_start_server_detects_trained_model_when_available(tmp_path: Path) -> None:
    """Start server should detect and log when a trained model is available."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create all prerequisites including trained model
    layout.checkout_dir.mkdir(parents=True, exist_ok=True)
    layout.venv_python.parent.mkdir(parents=True, exist_ok=True)
    layout.venv_python.touch()
    
    checkpoint_root = layout.checkpoints_dir / "fish-speech-1.5"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    (checkpoint_root / "model.pth").write_bytes(b"base model")
    (checkpoint_root / "config.json").write_bytes(b'{"config": "data"}')
    (checkpoint_root / "tokenizer.tiktoken").write_bytes(b"tokenizer")
    (checkpoint_root / "firefly-gan-vq-fsq-8x1024-21hz-generator.pth").write_bytes(b"decoder")
    
    trained_dir = layout.checkpoints_dir / "trained"
    trained_dir.mkdir(parents=True, exist_ok=True)
    (trained_dir / "model.pth").write_bytes(b"trained model")
    
    # Mock the server to be already reachable to avoid actual startup
    original_build_status = setup.build_status_payload
    
    def mock_build_status(*args, **kwargs):  # type: ignore[no-untyped-def]
        payload = original_build_status(*args, **kwargs)
        payload["runtime"]["reachable"] = True
        return payload
    
    setup.build_status_payload = mock_build_status
    
    try:
        exit_code = setup.start_server(project_root=tmp_path)
        assert exit_code == 0
    finally:
        setup.build_status_payload = original_build_status



def test_build_train_command_validates_training_enabled_flag(tmp_path: Path) -> None:
    """build_train_command should raise ValueError when training_enabled is False."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create config directory with training disabled
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.yaml"
    config_file.write_text("voice:\n  training_enabled: false\n")
    
    # Create minimal dataset structure
    voice_dir = tmp_path / "assets" / "voice" / "training_dataset"
    voice_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        setup.build_train_command(layout, tmp_path)
        assert False, "Expected ValueError for training_enabled=False"
    except ValueError as exc:
        assert "Training is disabled" in str(exc)
        assert "training_enabled" in str(exc)


def test_build_train_command_validates_dataset_readiness(tmp_path: Path) -> None:
    """build_train_command should raise ValueError when dataset is not ready."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create config directory and minimal config
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.yaml"
    config_file.write_text("voice:\n  training_enabled: true\n")
    
    # Create insufficient dataset (no WAV files)
    voice_dir = tmp_path / "assets" / "voice" / "training_dataset"
    voice_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        setup.build_train_command(layout, tmp_path)
        assert False, "Expected ValueError for insufficient dataset"
    except ValueError as exc:
        assert "Dataset not ready for training" in str(exc)


def test_build_train_command_constructs_valid_command(tmp_path: Path) -> None:
    """build_train_command should construct a valid training command with proper hyperparameters."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create config directory and config with training enabled
    config_dir = tmp_path / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "config.yaml"
    config_file.write_text("""
voice:
  training_enabled: true
  training_epochs: 50
  training_batch_size: 4
  training_learning_rate: 0.0001
  training_dataset_path: assets/voice/training_dataset/
""")
    
    # Create sufficient dataset (mock 30+ min of audio)
    voice_dir = tmp_path / "assets" / "voice" / "training_dataset"
    voice_dir.mkdir(parents=True, exist_ok=True)
    
    # Create mock WAV files with transcripts (simplified - actual test would need valid WAV)
    import wave
    for i in range(10):
        wav_path = voice_dir / f"audio_{i}.wav"
        txt_path = voice_dir / f"audio_{i}.txt"
        
        # Create a minimal valid WAV file (3 minutes each = 30 min total)
        with wave.open(str(wav_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(16000)
            # 3 minutes = 180 seconds * 16000 samples/sec
            wav_file.writeframes(b"\x00\x00" * (180 * 16000))
        
        txt_path.write_text("Sample Indonesian transcript for training.")
    
    # Create base checkpoint files
    checkpoint_root = layout.checkpoints_dir / "fish-speech-1.5"
    checkpoint_root.mkdir(parents=True, exist_ok=True)
    (checkpoint_root / "model.pth").write_bytes(b"base model")
    (checkpoint_root / "config.json").write_bytes(b'{"config": "data"}')
    
    command, config = setup.build_train_command(layout, tmp_path)
    
    # Verify command structure
    assert command[0] == str(layout.venv_python)
    assert command[1:3] == ["-m", "tools.train"]
    assert "--epochs" in command
    assert "50" in command
    assert "--batch-size" in command
    assert "4" in command
    assert "--learning-rate" in command
    assert "0.0001" in command
    
    # Verify config
    assert config["epochs"] == 50
    assert config["batch_size"] == 4
    assert config["learning_rate"] == 0.0001
    assert config["checkpoint_frequency"] == 5  # 50 / 10


def test_check_trained_model_returns_false_when_no_model_exists(tmp_path: Path) -> None:
    """check_trained_model should return exists=False when no trained model is found."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    result = setup.check_trained_model(layout, tmp_path)
    
    assert result["exists"] is False
    assert result["valid"] is False
    assert result["path"] is None
    assert result["size_mb"] is None
    assert "No valid trained model found" in result["message"]


def test_check_trained_model_detects_valid_trained_model(tmp_path: Path) -> None:
    """check_trained_model should detect and validate a properly trained model."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create trained model directory with all required files
    trained_dir = layout.checkpoints_dir / "trained"
    trained_dir.mkdir(parents=True, exist_ok=True)
    
    (trained_dir / "model.pth").write_bytes(b"trained model data" * 1000)
    (trained_dir / "config.json").write_bytes(b'{"trained": true}')
    (trained_dir / "tokenizer.tiktoken").write_bytes(b"trained tokenizer")
    
    result = setup.check_trained_model(layout, tmp_path)
    
    assert result["exists"] is True
    assert result["valid"] is True
    assert result["path"] == str(trained_dir)
    assert result["size_mb"] is not None
    assert result["size_mb"] > 0
    assert "Valid trained model found" in result["message"]
    assert result["model_files"]["model.pth"] is True
    assert result["model_files"]["config.json"] is True
    assert result["model_files"]["tokenizer.tiktoken"] is True


def test_check_trained_model_rejects_incomplete_model(tmp_path: Path) -> None:
    """check_trained_model should reject models with missing required files."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create trained model directory with only some files
    trained_dir = layout.checkpoints_dir / "trained"
    trained_dir.mkdir(parents=True, exist_ok=True)
    
    (trained_dir / "model.pth").write_bytes(b"trained model data")
    # Missing config.json and tokenizer.tiktoken
    
    result = setup.check_trained_model(layout, tmp_path)
    
    assert result["exists"] is False
    assert result["valid"] is False


def test_check_trained_model_rejects_empty_files(tmp_path: Path) -> None:
    """check_trained_model should reject models with empty (invalid) files."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create trained model directory with empty files
    trained_dir = layout.checkpoints_dir / "trained"
    trained_dir.mkdir(parents=True, exist_ok=True)
    
    (trained_dir / "model.pth").touch()  # Empty file
    (trained_dir / "config.json").write_bytes(b'{"trained": true}')
    (trained_dir / "tokenizer.tiktoken").write_bytes(b"trained tokenizer")
    
    result = setup.check_trained_model(layout, tmp_path)
    
    assert result["exists"] is False
    assert result["valid"] is False


def test_build_status_payload_includes_training_information(tmp_path: Path) -> None:
    """Status payload should include training status, dataset info, and trained model status."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create minimal voice directory
    voice_dir = tmp_path / "assets" / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    (voice_dir / "reference.wav").write_bytes(b"RIFF" + b"\x00" * 100)
    (voice_dir / "reference.txt").write_text("Reference text")
    
    payload = setup.build_status_payload(
        project_root=tmp_path,
        server_reachable=lambda *_args, **_kwargs: False,
        pid_running=lambda *_args, **_kwargs: False,
    )
    
    # Verify training section exists
    assert "training" in payload
    assert "status" in payload["training"]
    assert "enabled" in payload["training"]
    assert "trained_model" in payload["training"]
    assert "dataset" in payload["training"]
    
    # Verify trained model status structure
    trained_model = payload["training"]["trained_model"]
    assert "exists" in trained_model
    assert "valid" in trained_model
    assert "path" in trained_model
    assert "message" in trained_model
    
    # Verify dataset status structure
    dataset = payload["training"]["dataset"]
    assert "valid" in dataset
    assert "total_duration_min" in dataset
    assert "file_count" in dataset
    assert "ready_for_training" in dataset
    assert "guidance" in dataset


def test_build_status_payload_reports_training_completed_when_model_exists(tmp_path: Path) -> None:
    """Status payload should report training_status=completed when valid trained model exists."""
    setup = load_setup_module()
    layout = setup.ensure_layout(tmp_path)
    
    # Create minimal voice directory
    voice_dir = tmp_path / "assets" / "voice"
    voice_dir.mkdir(parents=True, exist_ok=True)
    (voice_dir / "reference.wav").write_bytes(b"RIFF" + b"\x00" * 100)
    (voice_dir / "reference.txt").write_text("Reference text")
    
    # Create valid trained model
    trained_dir = layout.checkpoints_dir / "trained"
    trained_dir.mkdir(parents=True, exist_ok=True)
    (trained_dir / "model.pth").write_bytes(b"trained model")
    (trained_dir / "config.json").write_bytes(b'{"trained": true}')
    (trained_dir / "tokenizer.tiktoken").write_bytes(b"tokenizer")
    
    payload = setup.build_status_payload(
        project_root=tmp_path,
        server_reachable=lambda *_args, **_kwargs: False,
        pid_running=lambda *_args, **_kwargs: False,
    )
    
    assert payload["training"]["status"] == "completed"
    assert payload["training"]["trained_model"]["valid"] is True
