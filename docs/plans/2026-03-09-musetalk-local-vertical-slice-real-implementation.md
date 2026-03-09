# MuseTalk Local Vertical Slice Real Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Menyelesaikan local non-mock vertical slice yang memakai `LiveTalking + MuseTalk` sebagai satu-satunya acceptance path face runtime, dengan evidence nyata dan docs source of truth yang sinkron.

**Architecture:** FastAPI tetap menjadi control plane utama, dashboard Svelte tetap menjadi operator UI utama, dan `external/livetalking` tetap menjadi vendor sidecar. Fase ini mempersempit active path ke `MuseTalk-only`, menurunkan `Wav2Lip` menjadi secondary fallback only, lalu membuktikan satu local real vertical slice sebelum pindah ke humanization atau live test.

**Tech Stack:** Python 3.12, FastAPI, UV-only, Svelte 5, TypeScript, SQLite, FFmpeg, LiveTalking sidecar, MuseTalk, pytest, Playwright.

---

## 0. Why This Plan Exists

Repo sudah memiliki baseline lokal yang kuat, tetapi acceptance path media/runtime masih ambigu.

Masalah utamanya:

- `MuseTalk` belum menjadi resolved runtime acceptance
- `Wav2Lip` fallback masih menjadi resolved path pada beberapa validasi
- docs source of truth belum membekukan `MuseTalk active / Wav2Lip fallback only`
- local real-mode gate masih belum sepenuhnya mencerminkan target `MuseTalk-only`
- humanization dan live-test akan menjadi kerja berulang jika local real MuseTalk slice belum benar-benar hidup

Plan ini menutup gap tersebut secara berurutan.

---

## 1. Hard Constraints

### Acceptance Path Rule

Milestone ini hanya lulus jika runtime truth final menunjukkan:

- `requested_model = musetalk`
- `resolved_model = musetalk`
- `requested_avatar_id = musetalk_avatar1`
- `resolved_avatar_id = musetalk_avatar1`

Jika resolved runtime masih `wav2lip`, task belum selesai.

### Scope Rule

Jangan memasukkan hal berikut ke critical path milestone ini:

- voice redesign
- `GFPGAN`
- `ER-NeRF`
- blind test
- long-run stability
- production launch work

### Real Local Rule

Semua acceptance akhir harus memakai:

- `MOCK_MODE=false`
- data produk lokal nyata
- reference media nyata
- sidecar vendor nyata
- evidence nyata

---

## 2. End State

Fase ini selesai hanya jika:

- local real-mode gate lulus untuk prasyarat yang termasuk scope milestone ini
- canonical `musetalk_avatar1` tersedia dan terbaca runtime
- sidecar vendor start lewat jalur operator resmi
- dashboard/API menampilkan truth `musetalk`
- satu local non-mock vertical slice berjalan end-to-end
- docs source of truth sinkron dengan kondisi aktual

---

## 3. Execution Strategy

Lakukan dalam 5 blok:

1. `Freeze Truth`
2. `Unblock Real Local Inputs`
3. `Activate MuseTalk`
4. `Prove Operator Path`
5. `Audit and Document`

Jangan mulai humanization sebelum blok 1-5 selesai.

---

## 4. Task-by-Task Implementation Plan

### Task 1: Freeze the active architecture and acceptance truth

**Files:**
- Create: `docs/specs/local_vertical_slice_real_musetalk.md`
- Modify: `docs/architecture.md`
- Modify: `docs/task_status.md`
- Modify: `docs/workflow.md`
- Modify: `README.md`
- Test/Verify: `rg -n "MuseTalk|Wav2Lip|fallback only|resolved_model" docs README.md`

**Step 1: Write the milestone spec**

Define:

- milestone name: `LOCAL_VERTICAL_SLICE_REAL_MUSETALK`
- active path
- fallback rule
- acceptance truth fields
- required evidence

**Step 2: Run grep to verify docs references**

Run:

```bash
rg -n "MuseTalk|Wav2Lip|fallback only|resolved_model" docs README.md
```

Expected:
- active docs explicitly say MuseTalk is the only acceptance path
- Wav2Lip is described only as secondary fallback

**Step 3: Update truth docs**

Rules:

- architecture must no longer imply multiple active face paths
- task status must no longer allow fallback to be described as acceptable completion
- workflow must describe the official real-mode path

**Step 4: Commit**

```bash
git add docs/specs/local_vertical_slice_real_musetalk.md docs/architecture.md docs/task_status.md docs/workflow.md README.md
git commit -m "docs: freeze MuseTalk-only local vertical slice contract"
```

---

### Task 2: Unblock the real-local product data gate

**Files:**
- Modify: `scripts/check_real_mode_readiness.py`
- Modify: `src/dashboard/readiness.py`
- Create or Modify: `data/real_products.json` or the actual canonical product source path used by the project
- Test: `tests/test_layers.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write failing tests**

Add tests proving:

- readiness fails when real product data source is absent
- readiness passes when the real local product source exists
- placeholder/demo-only product content is not counted as pass if the current gate distinguishes that state

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_layers.py -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- FAIL for the missing/ambiguous real product source case

**Step 3: Implement the minimal real-local product source**

Rules:

- use the project's actual product source path
- do not create a mock-only bypass
- keep data minimal but real and operator-readable

**Step 4: Re-run targeted tests**

Run:

```bash
uv run pytest tests/test_layers.py -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add scripts/check_real_mode_readiness.py src/dashboard/readiness.py tests/test_layers.py tests/test_dashboard.py
git add data/real_products.json
git commit -m "feat: unblock real-local product readiness gate"
```

---

### Task 3: Freeze the real asset contract for MuseTalk activation

**Files:**
- Create: `docs/specs/musetalk_asset_contract.md`
- Modify: `scripts/setup_musetalk_assets.py`
- Modify: `src/face/asset_setup.py`
- Test: `tests/test_asset_setup.py`

**Step 1: Write failing tests**

Add tests proving:

- canonical reference paths are recognized
- canonical MuseTalk avatar target path is recognized
- asset setup reports "not ready" cleanly when any required file is missing

**Step 2: Run targeted test**

Run:

```bash
uv run pytest tests/test_asset_setup.py -q -p no:cacheprovider
```

Expected:
- FAIL until the stricter contract is encoded

**Step 3: Implement the minimal contract alignment**

Rules:

- canonical paths must be explicit
- asset setup must not silently succeed on partial state
- reports must tell the operator exactly which asset is missing

**Step 4: Re-run targeted test**

Run:

```bash
uv run pytest tests/test_asset_setup.py -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add docs/specs/musetalk_asset_contract.md scripts/setup_musetalk_assets.py src/face/asset_setup.py tests/test_asset_setup.py
git commit -m "docs: define canonical MuseTalk asset contract"
```

---

### Task 4: Generate and verify the canonical MuseTalk avatar

**Files:**
- Modify: `scripts/setup_musetalk_assets.py`
- Modify: `src/face/asset_setup.py`
- Modify: `scripts/check_real_mode_readiness.py`
- Test: `tests/test_asset_setup.py`
- Test: `tests/test_layers.py`

**Step 1: Write failing tests**

Add tests proving:

- readiness fails if `musetalk_avatar1` is absent
- readiness passes only when canonical MuseTalk avatar assets exist
- fallback to `wav2lip` is still visible as a non-pass condition for the milestone

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_asset_setup.py -q -p no:cacheprovider
uv run pytest tests/test_layers.py -q -p no:cacheprovider
```

Expected:
- FAIL while the avatar is not yet acceptance-ready

**Step 3: Generate and normalize the avatar**

Run the actual canonical generation flow and normalize results into:

```text
external/livetalking/data/avatars/musetalk_avatar1/
```

Rules:

- do not count partial folders as success
- verify required runtime files exist

**Step 4: Re-run readiness and tests**

Run:

```bash
uv run python scripts/setup_musetalk_assets.py --sync-only
uv run pytest tests/test_asset_setup.py -q -p no:cacheprovider
uv run pytest tests/test_layers.py -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add scripts/setup_musetalk_assets.py src/face/asset_setup.py scripts/check_real_mode_readiness.py tests/test_asset_setup.py tests/test_layers.py
git commit -m "feat: activate canonical musetalk avatar path"
```

---

### Task 5: Make fallback to Wav2Lip fail the milestone truth

**Files:**
- Modify: `src/face/engine_resolver.py`
- Modify: `src/face/livetalking_manager.py`
- Modify: `src/dashboard/readiness.py`
- Modify: `src/dashboard/api.py`
- Test: `tests/test_engine_resolver.py`
- Test: `tests/test_livetalking_integration.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write failing tests**

Add tests proving:

- resolved `wav2lip` remains visible as fallback
- readiness summary for this milestone is not `ready` when fallback is active
- API truth shows requested vs resolved clearly

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_engine_resolver.py -q -p no:cacheprovider
uv run pytest tests/test_livetalking_integration.py -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- FAIL until milestone truth is strict enough

**Step 3: Implement stricter milestone truth**

Rules:

- keep fallback behavior for emergencies/dev
- but never allow fallback to masquerade as milestone completion

**Step 4: Re-run targeted tests**

Run:

```bash
uv run pytest tests/test_engine_resolver.py -q -p no:cacheprovider
uv run pytest tests/test_livetalking_integration.py -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/face/engine_resolver.py src/face/livetalking_manager.py src/dashboard/readiness.py src/dashboard/api.py tests/test_engine_resolver.py tests/test_livetalking_integration.py tests/test_dashboard.py
git commit -m "feat: make wav2lip fallback fail musetalk milestone truth"
```

---

### Task 6: Prove the official non-mock operator path

**Files:**
- Modify: `scripts/manage.py`
- Modify: `scripts/smoke_livetalking.py`
- Modify: `tests/test_manage_cli.py`
- Modify: `tests/test_livetalking_integration.py`

**Step 1: Write failing tests**

Add tests proving:

- `serve --real` uses the correct active runtime assumptions
- `validate livetalking` aligns with MuseTalk-only acceptance truth
- operator path reports sidecar reachability and warmup honestly

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_manage_cli.py -q -p no:cacheprovider
uv run pytest tests/test_livetalking_integration.py -q -p no:cacheprovider
```

Expected:
- FAIL if the operator path is still too permissive about fallback

**Step 3: Implement minimal operator-path truth**

Rules:

- the official path must be the same one operators use in docs
- warmup timing can be honest and bounded
- do not hide degraded or fallback state

**Step 4: Re-run targeted tests**

Run:

```bash
uv run pytest tests/test_manage_cli.py -q -p no:cacheprovider
uv run pytest tests/test_livetalking_integration.py -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add scripts/manage.py scripts/smoke_livetalking.py tests/test_manage_cli.py tests/test_livetalking_integration.py
git commit -m "feat: align official operator path with musetalk-only acceptance"
```

---

### Task 7: Run one real local vertical slice through the operator flow

**Files:**
- Modify: `docs/task_status.md`
- Modify: `docs/workflow.md`
- Modify: `README.md`
- Create: `docs/audits/AUDIT_LOCAL_VERTICAL_SLICE_REAL_MUSETALK_2026-03-09.md`

**Step 1: Define the exact operator slice**

The slice must include:

- start non-mock app through official command
- verify `/dashboard` truth
- verify sidecar reachability
- verify product source is real local data
- verify runtime truth resolves to MuseTalk
- record evidence

**Step 2: Run the slice**

Run at minimum:

```bash
uv run python scripts/manage.py setup-livetalking --skip-models
uv run python scripts/manage.py serve --real
uv run python scripts/manage.py health --json
uv run python scripts/manage.py validate livetalking
uv run python scripts/check_real_mode_readiness.py --json
```

Expected:
- commands complete
- health and readiness reflect the local real state honestly
- sidecar is reachable
- MuseTalk is the resolved runtime

**Step 3: Save the audit**

Audit must include:

- exact commands
- exact outcomes
- startup timing
- requested vs resolved runtime values
- remaining blockers, if any

**Step 4: Commit**

```bash
git add docs/audits/AUDIT_LOCAL_VERTICAL_SLICE_REAL_MUSETALK_2026-03-09.md docs/task_status.md docs/workflow.md README.md
git commit -m "docs: record local real musetalk vertical slice evidence"
```

---

### Task 8: Prepare the next milestone for humanization

**Files:**
- Create: `docs/specs/humanization_minimum_contract.md`
- Modify: `docs/task_status.md`
- Modify: `docs/changelogs.md`

**Step 1: Write the minimum humanization contract**

Define the first mandatory realism package:

- blink
- eye drift
- idle head micro-motion
- idle non-speaking presence
- pacing / response delay policy

**Step 2: Verify the milestone handoff is explicit**

Run:

```bash
rg -n "humanization|blink|idle|eye|micro-motion" docs
```

Expected:
- next-step scope exists and is separated from the completed MuseTalk slice milestone

**Step 3: Commit**

```bash
git add docs/specs/humanization_minimum_contract.md docs/task_status.md docs/changelogs.md
git commit -m "docs: define post-slice humanization minimum contract"
```

---

## 5. Review Checklist for Human

Review in this order:

1. Do docs clearly say `MuseTalk active` and `Wav2Lip fallback only`?
2. Does readiness fail if runtime still resolves to `wav2lip`?
3. Does canonical `musetalk_avatar1` exist in the vendor path?
4. Does the official operator path run non-mock locally?
5. Does dashboard/runtime truth say `musetalk`, not `wav2lip`?
6. Is there one local audit with fresh evidence?
7. Is humanization clearly defined as the next milestone, not mixed into this one?

---

## 6. Recommended Execution Mode

Do not batch the whole plan without review.

Suggested checkpoints:

- Checkpoint A: Task 1-2
- Checkpoint B: Task 3-5
- Checkpoint C: Task 6-7
- Checkpoint D: Task 8 and handoff

Human review is required at the end of Checkpoint C before humanization work starts.
