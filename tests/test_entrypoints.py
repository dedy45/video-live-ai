"""Regression tests for CLI and application entrypoints."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_main_import_tolerates_empty_sys_path_entry() -> None:
    """Importing src.main should not crash when sys.path contains an empty entry."""
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, ''); import src.main; print(callable(src.main.main))",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "True" in result.stdout


def test_verify_pipeline_report_handles_cp1252_stdout() -> None:
    """verify_pipeline report should render without crashing on cp1252 consoles."""
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "cp1252"

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "from scripts.verify_pipeline import PipelineVerifier, VerifyResult; "
                "verifier = PipelineVerifier(); "
                "verifier.results = [VerifyResult('config', True, 'ok', 1.0, [])]; "
                "verifier.print_report()"
            ),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "Result: 1/1 layers passed" in result.stdout
