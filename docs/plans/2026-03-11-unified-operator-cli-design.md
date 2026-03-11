# Unified Operator CLI Design

Date: 2026-03-11
Status: Approved for planning
Scope: Consolidate scattered Windows batch workflows into one Python CLI source of truth with structured Windows wrappers and production-first setup paths.

## Problem

The repository currently spreads installation, setup, and runtime behavior across multiple root-level batch files:

- `install_full_dependencies.bat`
- `install_livetalking_deps.bat`
- `run_livetalking_musetalk.bat`
- `run_livetalking_web.bat`
- `setup_livetalking_verbose.bat`
- `setup_musetalk_model.bat`

This creates several problems:

- source of truth is split between Python and batch scripts
- Windows-only logic hides production workflow assumptions
- Fish-Speech setup is not installable end-to-end from the operator CLI
- LiveTalking and MuseTalk setup paths drift from documented architecture
- local verification is weak because setup scripts are not uniformly testable

The target architecture requires:

- one backend control plane
- one main operator CLI source of truth
- production-first setup and runtime behavior
- local install from zero that proves the workflow is real, not dead code
- structured external sidecar folders consistent with `external/livetalking`

## Goals

- Make `scripts/manage.py` the single source of truth for install, setup, start, stop, status, validate, and open workflows.
- Reduce Windows wrappers to minimal operator entrypoints only.
- Move Fish-Speech sidecar into `external/fish-speech/` with explicit runtime structure.
- Keep LiveTalking and MuseTalk setup aligned with current architecture docs.
- Support local Windows install with `uv` so the full production path can be demonstrated.
- Preserve parity with server deployment by keeping path structure and workflow explicit.

## Non-Goals

- No new mock-centric flows.
- No hidden global installs outside the repository as the source of truth.
- No mega batch replacement as the primary runtime contract.
- No redesign of the backend runtime model beyond CLI/orchestration needs.

## Recommended Approach

Use one Python operator CLI as the control surface and keep only one or two thin Windows wrappers.

### Why this approach

- Python CLI is testable and portable.
- Batch wrappers remain simple and human-friendly.
- Local Windows install remains possible through `uv`.
- Server parity improves because path and workflow logic live in Python, not Windows shell scripts.

## Directory Strategy

### LiveTalking

Keep using the canonical vendor path already defined by architecture:

- `external/livetalking/`

### Fish-Speech

Introduce a new canonical sidecar path:

- `external/fish-speech/upstream/`
- `external/fish-speech/checkpoints/`
- `external/fish-speech/runtime/`
- `external/fish-speech/scripts/` if wrapper scripts are needed

Rules:

- install logic must resolve within `external/fish-speech/`
- runtime logs and pid files must stay under `external/fish-speech/runtime/`
- no hidden dependency on user profile folders as the primary contract

## CLI Surface

`scripts/manage.py` becomes the source of truth.

### Setup commands

- `manage.py setup all`
- `manage.py setup app`
- `manage.py setup livetalking`
- `manage.py setup musetalk-model`
- `manage.py setup fish-speech`

### Runtime commands

- `manage.py start app --mock|--real`
- `manage.py start livetalking --mode musetalk|wav2lip`
- `manage.py start fish-speech`
- `manage.py stop app|livetalking|fish-speech|all`

### Inspection commands

- `manage.py status app|livetalking|fish-speech|all`
- `manage.py health`
- `manage.py logs`

### Validation commands

- `manage.py validate readiness|livetalking|fish-speech|pipeline|all`

### Browser/open commands

- `manage.py open dashboard|performer|monitor|docs|vendor`

## Windows Wrapper Strategy

Keep only thin wrappers:

- `scripts/menu.bat` as the operator menu
- optional bootstrap wrapper only if needed for first-run convenience

All legacy root-level `.bat` files should be retired after parity is verified.

## Legacy Batch Migration

Mapping:

- `install_full_dependencies.bat` -> `manage.py setup all`
- `install_livetalking_deps.bat` -> `manage.py setup livetalking`
- `setup_livetalking_verbose.bat` -> `manage.py setup livetalking --verbose`
- `setup_musetalk_model.bat` -> `manage.py setup musetalk-model`
- `run_livetalking_musetalk.bat` -> `manage.py start livetalking --mode musetalk`
- `run_livetalking_web.bat` -> `manage.py start livetalking --mode wav2lip` or `manage.py open vendor`

Legacy files should not keep real logic after migration.

## Command Output Contract

Every operator command should print structured, informative output with explicit next action:

- `TARGET`
- `MODE`
- `PATH`
- `PORT`
- `STATUS`
- `NEXT ACTION`

Failure output must name the real blocker, not a generic failure.

## Production-First Rules

- Real mode must remain the primary operational contract.
- Mock mode may exist only as a clearly separated development path.
- Fish-Speech setup and LiveTalking setup must be installable locally with `uv`.
- A local install must be able to prove production path viability.

## Validation Expectations

At minimum, the unified workflow must verify:

- app dependencies installed
- LiveTalking dependency state
- MuseTalk model placement
- Fish-Speech reference asset presence
- Fish-Speech sidecar reachability
- runtime truth and readiness APIs
- operator pages loading from `dist` through FastAPI

## Documentation Updates Required

After implementation, update:

- `README.md`
- `docs/architecture.md`
- `docs/workflow.md`
- `docs/task_status.md`
- `docs/changelogs.md`
- any setup guide that still points to root-level batch files

## Risks

- Fish-Speech native Windows install may be stricter than Linux and should fail fast with explicit diagnostics.
- Some GPU/runtime combinations may still require pinned dependency handling.
- Existing users may rely on batch filenames, so migration messaging must be explicit.

## Acceptance Criteria

- `manage.py` can drive install/setup/start/stop/status/validate flows for app, LiveTalking, MuseTalk model placement, and Fish-Speech.
- `scripts/menu.bat` exposes the new centralized commands cleanly.
- legacy root-level `.bat` files are removed or reduced to explicit deprecation wrappers, then removed
- docs point to the new commands as the source of truth
- local Windows install demonstrates the production path, not only mock mode
