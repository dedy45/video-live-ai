cleat# Unified Operator CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace scattered batch-driven setup/runtime flows with one production-first Python operator CLI and update docs to make it the single source of truth.

**Architecture:** Keep `scripts/manage.py` as the orchestration layer for all setup/install/runtime actions, move Fish-Speech setup into `external/fish-speech/`, and reduce Windows batch files to thin wrappers or remove them entirely after parity is verified. Use TDD for CLI behavior and migrate legacy batch responsibilities one workflow at a time.

**Tech Stack:** Python, argparse, uv, pytest, FastAPI runtime contracts, Windows batch wrappers, existing setup scripts.

---

### Task 1: Freeze the current legacy workflow coverage

**Files:**
- Modify: `tests/test_manage_cli.py`
- Reference: `scripts/manage.py`
- Reference: `scripts/menu.bat`

**Step 1: Write the failing tests**

Add tests that assert the CLI exposes missing setup/runtime targets needed for unified workflow:

- `setup all`
- `setup app`
- `setup musetalk-model`
- `start fish-speech`
- `stop all`
- `status all`
- `open performer`
- `open monitor`

**Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_manage_cli.py -q -p no:cacheprovider
```

Expected: parser/dispatch failures for the new commands.

**Step 3: Implement minimal parser and dispatch additions**

Add only enough parser and routing logic in `scripts/manage.py` to make the new command names valid.

**Step 4: Run test to verify it passes**

Run the same command and confirm the new CLI surface is recognized.

**Step 5: Commit**

```bash
git add tests/test_manage_cli.py scripts/manage.py
git commit -m "feat: extend operator cli command surface"
```

### Task 2: Introduce explicit Fish-Speech external path management

**Files:**
- Modify: `scripts/setup_fish_speech.py`
- Modify: `scripts/manage.py`
- Test: `tests/test_fish_speech_setup.py`

**Step 1: Write the failing tests**

Create tests for:

- canonical Fish-Speech path resolves to `external/fish-speech/`
- setup creates `upstream`, `checkpoints`, and `runtime`
- validation output reports these paths explicitly

**Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_fish_speech_setup.py -q -p no:cacheprovider
```

Expected: missing path helpers and setup behavior.

**Step 3: Implement minimal path helpers and directory creation**

Add path resolution and idempotent directory bootstrap in `scripts/setup_fish_speech.py`. Wire `manage.py setup fish-speech` to use it.

**Step 4: Run test to verify it passes**

Run the same test file until green.

**Step 5: Commit**

```bash
git add tests/test_fish_speech_setup.py scripts/setup_fish_speech.py scripts/manage.py
git commit -m "feat: add canonical fish-speech external layout"
```

### Task 3: Split app, LiveTalking, MuseTalk, and Fish-Speech setup flows cleanly

**Files:**
- Modify: `scripts/manage.py`
- Modify: `scripts/setup_livetalking.py`
- Modify: `scripts/setup_fish_speech.py`
- Test: `tests/test_manage_cli.py`

**Step 1: Write the failing tests**

Add behavior tests for:

- `manage.py setup all` runs setup stages in the expected order
- `manage.py setup app` calls uv sync flow only
- `manage.py setup livetalking` delegates to LiveTalking setup
- `manage.py setup musetalk-model` delegates to model setup flow
- `manage.py setup fish-speech` delegates to Fish-Speech bootstrap

**Step 2: Run test to verify it fails**

Run:

```bash
uv run pytest tests/test_manage_cli.py -q -p no:cacheprovider -k "setup"
```

Expected: missing routing or wrong command behavior.

**Step 3: Implement minimal orchestration**

Keep orchestration in `manage.py`; do not duplicate setup logic in batch files.

**Step 4: Run test to verify it passes**

Run the same command until green.

**Step 5: Commit**

```bash
git add tests/test_manage_cli.py scripts/manage.py scripts/setup_livetalking.py scripts/setup_fish_speech.py
git commit -m "feat: unify setup workflows under manage cli"
```

### Task 4: Add Fish-Speech start/stop/status runtime commands

**Files:**
- Modify: `scripts/manage.py`
- Modify: `scripts/setup_fish_speech.py`
- Test: `tests/test_manage_cli.py`
- Test: `tests/test_fish_speech_setup.py`

**Step 1: Write the failing tests**

Add tests for:

- `start fish-speech` prints target path, port, and next action
- `stop fish-speech` handles missing pid cleanly
- `status fish-speech` reports reachable/unreachable, pid, and runtime dir
- `status all` aggregates app, LiveTalking, and Fish-Speech

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_manage_cli.py tests/test_fish_speech_setup.py -q -p no:cacheprovider -k "fish_speech or status_all"
```

**Step 3: Implement minimal runtime supervision**

Add runtime file and probe helpers in Python. Keep output structured and informative.

**Step 4: Run test to verify it passes**

Re-run the same tests.

**Step 5: Commit**

```bash
git add tests/test_manage_cli.py tests/test_fish_speech_setup.py scripts/manage.py scripts/setup_fish_speech.py
git commit -m "feat: add fish-speech runtime commands"
```

### Task 5: Migrate LiveTalking start/open workflows into CLI

**Files:**
- Modify: `scripts/manage.py`
- Test: `tests/test_manage_cli.py`

**Step 1: Write the failing tests**

Add tests for:

- `start livetalking --mode musetalk`
- `start livetalking --mode wav2lip`
- `open vendor`
- `open performer`
- `open monitor`

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_manage_cli.py -q -p no:cacheprovider -k "livetalking or open"
```

**Step 3: Implement minimal routing**

Use canonical vendor paths and URLs only. Do not reintroduce duplicated batch logic.

**Step 4: Run test to verify it passes**

Run the same command until green.

**Step 5: Commit**

```bash
git add tests/test_manage_cli.py scripts/manage.py
git commit -m "feat: move livetalking runtime commands into manage cli"
```

### Task 6: Redesign `scripts/menu.bat` around the new CLI

**Files:**
- Modify: `scripts/menu.bat`
- Test: `tests/test_menu_batch.py`

**Step 1: Write the failing tests**

Add simple regression coverage for menu labels and expected delegated commands.

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_menu_batch.py -q -p no:cacheprovider
```

**Step 3: Implement minimal menu rewrite**

Organize the menu into:

- Setup
- Start/Stop
- Status
- Validate
- Open

Each option should call one `manage.py` command only.

**Step 4: Run test to verify it passes**

Run the same command until green.

**Step 5: Commit**

```bash
git add tests/test_menu_batch.py scripts/menu.bat
git commit -m "feat: simplify windows operator menu"
```

### Task 7: Remove legacy root-level batch scripts safely

**Files:**
- Delete: `install_full_dependencies.bat`
- Delete: `install_livetalking_deps.bat`
- Delete: `run_livetalking_musetalk.bat`
- Delete: `run_livetalking_web.bat`
- Delete: `setup_livetalking_verbose.bat`
- Delete: `setup_musetalk_model.bat`
- Test: `tests/test_manage_cli.py`

**Step 1: Write the failing tests**

Add coverage that the equivalent `manage.py` commands now exist and are the documented replacements.

**Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_manage_cli.py -q -p no:cacheprovider -k "replacement"
```

**Step 3: Delete the legacy files**

Only delete after the replacement commands are verified.

**Step 4: Run test to verify it passes**

Run the same command until green.

**Step 5: Commit**

```bash
git add tests/test_manage_cli.py
git rm install_full_dependencies.bat install_livetalking_deps.bat run_livetalking_musetalk.bat run_livetalking_web.bat setup_livetalking_verbose.bat setup_musetalk_model.bat
git commit -m "refactor: remove legacy setup batch scripts"
```

### Task 8: Update docs to the new single source of truth

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/workflow.md`
- Modify: `docs/task_status.md`
- Modify: `docs/changelogs.md`

**Step 1: Write the failing doc checklist**

Create a manual checklist in the task notes:

- no active docs point to removed root-level batch files
- Fish-Speech path documented under `external/fish-speech/`
- manage.py commands are shown as the primary workflow
- menu.bat described as a wrapper only

**Step 2: Verify docs fail the checklist**

Run:

```bash
rg -n "install_full_dependencies|install_livetalking_deps|run_livetalking_musetalk|run_livetalking_web|setup_livetalking_verbose|setup_musetalk_model" README.md docs
```

Expected: stale references found.

**Step 3: Update docs**

Replace old script references with the new CLI flow and canonical external paths.

**Step 4: Verify docs pass**

Run the same `rg` command and confirm no active references remain.

**Step 5: Commit**

```bash
git add README.md docs/architecture.md docs/workflow.md docs/task_status.md docs/changelogs.md
git commit -m "docs: align setup workflow with unified operator cli"
```

### Task 9: End-to-end verification

**Files:**
- Verify only

**Step 1: Run focused CLI tests**

```bash
uv run pytest tests/test_manage_cli.py tests/test_fish_speech_setup.py tests/test_menu_batch.py -q -p no:cacheprovider
```

**Step 2: Run broader regression tests**

```bash
uv run pytest tests/test_dashboard.py tests/test_fish_speech_client.py tests/test_voice_engine.py -q -p no:cacheprovider
```

**Step 3: Run frontend verification**

```bash
cd src/dashboard/frontend
npm run test
npm run build
```

**Step 4: Manual smoke**

Run:

```bash
uv run python scripts/manage.py setup all
uv run python scripts/manage.py start app --real
uv run python scripts/manage.py status all
uv run python scripts/manage.py validate all
```

Confirm:

- app status prints clear URLs
- Fish-Speech status prints explicit blocker if sidecar is not reachable
- no legacy batch file is required for the workflow

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: unify operator install and runtime workflows"
```
