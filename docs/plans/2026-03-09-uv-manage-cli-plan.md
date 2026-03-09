# UV Manage CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the fragile Windows-only batch logic with a thin interactive BAT wrapper over a uv-aligned Python management CLI.

**Architecture:** `scripts/manage.py` becomes the source of truth for local operator commands such as start, stop, status, health, validation, logs, and setup. `scripts/menu.bat` remains a Windows convenience launcher that delegates every action to `uv run python scripts/manage.py ...`, while Ubuntu continues to use the same Python CLI directly.

**Tech Stack:** Python 3.10+, argparse, subprocess, uv, Windows batch, FastAPI runtime endpoints.

---

### Task 1: Add failing tests for uv-aligned manage helpers

**Files:**
- Create: `tests/test_manage_cli.py`
- Create: `scripts/manage.py`

**Steps:**
1. Write tests that assert server command construction uses `uv run python -m src.main`.
2. Write tests that assert server environment always sets `PYTHONUTF8=1` and explicit `MOCK_MODE`.
3. Write tests that assert runtime snapshot reports `stopped` when no pid file and no open port exist.

### Task 2: Implement Python manage CLI

**Files:**
- Create: `scripts/manage.py`

**Steps:**
1. Add helper functions for command construction, environment construction, log paths, and runtime snapshot.
2. Add subcommands for `serve`, `stop`, `status`, `health`, `validate`, `logs`, `sync`, `load-products`, and `open`.
3. Ensure all subprocess invocations use `uv` for Python and dependency flows.

### Task 3: Refactor Windows menu wrapper

**Files:**
- Modify: `scripts/menu.bat`

**Steps:**
1. Replace direct `.venv\Scripts\python.exe` usage with `uv run python scripts/manage.py ...`.
2. Reduce the menu to the required operational surfaces: start/stop, health, validation, logs, setup, and open URLs.
3. Keep the script safe for paths containing `!`.

### Task 4: Update user-facing docs

**Files:**
- Modify: `README.md`
- Modify: `docs/changelogs.md`
- Modify: `docs/workflow.md`

**Steps:**
1. Document `menu.bat` as a Windows convenience wrapper.
2. Document `uv run python scripts/manage.py ...` as the canonical cross-platform operator CLI.
3. Keep Ubuntu examples on the same uv-aligned command path.

### Task 5: Verify end-to-end behavior

**Files:**
- Test: `tests/test_manage_cli.py`

**Steps:**
1. Run targeted tests for the manage helpers.
2. Run the manage CLI status and health commands directly.
3. Confirm documentation and menu commands match the implemented CLI.
