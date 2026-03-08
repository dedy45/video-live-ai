# Dashboard Single Truth Real Validation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Mengubah dashboard `videoliveai` dari panel monitor campuran menjadi single source of truth operasional yang bisa memvalidasi status nyata seluruh proyek dengan data, aset, dan runtime real, bukan dummy atau synthetic.

**Architecture:** FastAPI tetap menjadi control plane utama dan Svelte dashboard tetap diserve di `/dashboard`. Fase ini tidak lagi fokus ke migrasi UI, tetapi ke truth model, provenance, validation evidence, realtime state, dan operator controls yang benar-benar terhubung ke runtime proyek. Semua validasi final harus berjalan dengan `MOCK_MODE=false`, aset nyata, dan endpoint/runtime nyata. Jika prasyarat real-mode belum ada, task harus berhenti sebagai `BLOCKED`, bukan diganti dengan simulasi.

**Tech Stack:** Python 3.12, FastAPI, UV-only, Svelte 5, Vite, TypeScript, Vitest, Playwright, SQLite, FFmpeg, LiveTalking sidecar, WebSocket, real RTMP target, real operator assets.

---

## 0. Why This Plan Exists

Dashboard saat ini sudah:

- diserve dari build Svelte
- punya panel utama
- bisa memanggil beberapa API control

Tetapi dashboard belum bisa disebut single truth operasional karena:

- banyak panel masih snapshot `onMount`, bukan realtime state
- beberapa aksi frontend masih `catch { /* ignore */ }`
- dashboard belum membedakan tegas antara `mock`, `real-local`, `real-live`, dan `unverified`
- validation UI belum menjadi sumber audit runtime
- sebagian operasi backend masih valid secara control plane tetapi belum membuktikan media plane real

Plan ini menutup gap itu.

> Note: selama Task 1-9 masih berjalan, dashboard boleh masih menampilkan `mock` di UI jika runtime memang belum masuk fase real acceptance. Status `mock` baru dianggap masalah jika masih muncul setelah Task 10 dijalankan dengan `MOCK_MODE=false` dan prasyarat real-mode sudah tersedia.

---

## 1. Hard Constraints

### Real Validation Rules

- Final validation phase wajib `MOCK_MODE=false`.
- Jangan gunakan dummy product, synthetic chat, fake avatar, fake stream target, atau fake success banner untuk menyelesaikan plan ini.
- Jika platform external belum siap, tandai `BLOCKED` dengan alasan teknis yang eksplisit.
- Test UI/unit boleh memakai mock untuk development loop terbatas, tetapi acceptance akhir harus memakai runtime dan data nyata.

### Data Provenance Rules

Setiap data surface di dashboard harus bisa diklasifikasikan sebagai salah satu:

- `mock`
- `real_local`
- `real_live`
- `derived`
- `unknown`

Dashboard tidak boleh menyajikan data seolah final jika asalnya belum jelas.

### Scope Rules

- Tidak rewrite arsitektur ke Next.js/NestJS.
- Tidak menghapus `external/livetalking/web`; tetap debug-only.
- Tidak memakai conda.
- Tidak menambah sumber data palsu untuk “membuat dashboard terlihat hidup”.
- Jangan mengklaim real validation sukses jika hanya control plane yang berubah, tapi media/chat/runtime belum tervalidasi.

---

## 2. Target End State

Setelah plan ini selesai:

- `/dashboard` menjadi operator console utama untuk validasi runtime proyek
- dashboard punya `Truth Bar` global yang selalu terlihat
- setiap panel menunjukkan:
  - runtime mode
  - provenance/source
  - freshness / last updated
  - validation status
  - last action result
- semua aksi operator utama memberikan receipt/error yang jelas
- state penting diperbarui via polling atau WebSocket, bukan snapshot sekali-load
- dashboard memiliki `Validation Console` untuk menjalankan check nyata dan menyimpan evidence
- final acceptance dilakukan dengan `MOCK_MODE=false`

---

## 3. Truth Model

### Global Truth Fields

Dashboard harus bisa menampilkan minimal field berikut:

- `mock_mode`
- `runtime_mode`
- `voice_runtime_mode`
- `face_runtime_mode`
- `stream_runtime_mode`
- `data_origin`
- `validation_state`
- `last_validated_at`
- `last_action_at`
- `last_action_status`
- `last_action_message`

### Source-of-Truth Principle

Untuk fase ini, dashboard dianggap benar hanya jika:

- status ditarik dari API backend nyata
- backend API mengambil state dari runtime/service nyata atau dari evidence log yang tersimpan
- tidak ada status “hijau” yang berasal dari asumsi UI lokal

---

## 4. Non-Negotiable Acceptance Criteria

Fase ini dianggap selesai hanya jika semua poin berikut benar:

- dashboard memiliki global truth bar
- dashboard menampilkan provenance/source badges di panel penting
- silent failure (`catch { /* ignore */ }`) dihilangkan dari panel operator inti
- operator actions memiliki success/error receipts yang terlihat
- dashboard memakai realtime updates untuk state penting
- product switch, pipeline transition, brain test, engine control, stream control, dan emergency reset tersedia dari dashboard
- validation console bisa menjalankan check nyata dan menampilkan evidence
- real validation dijalankan dengan `MOCK_MODE=false`
- docs menyebut jelas mana yang `LOCAL VERIFIED`, `REAL VERIFIED`, dan `BLOCKED`

---

## 5. Execution Strategy

Lakukan dalam 4 blok besar:

1. `Truth Layer`
2. `Operator Control Layer`
3. `Realtime + Validation Layer`
4. `Real-Mode Acceptance`

Jangan mulai dari kosmetik. Jangan mulai dari dokumentasi. Jangan mulai dari platform integration jika truth layer belum ada.

---

## 6. Task-by-Task Implementation Plan

### Task 1: Freeze the dashboard truth model and provenance taxonomy

**Files:**
- Create: `docs/specs/dashboard_truth_model.md`
- Modify: `docs/architecture.md`
- Modify: `docs/task_status.md`
- Test/Verify: `rg -n "mock|real_local|real_live|derived|unknown" docs/specs/dashboard_truth_model.md`

**Step 1: Write the truth model spec**

Define:

- provenance classes
- validation states
- operator action receipt schema
- panel-level truth responsibilities
- what counts as `REAL VERIFIED`

**Step 2: Verify the spec is referenced by architecture docs**

Run:

```bash
rg -n "dashboard_truth_model" docs
```

Expected:
- spec path appears in docs references

**Step 3: Update architecture truth**

Add a short section in `docs/architecture.md` clarifying:

- dashboard is now expected to expose runtime truth, not only status cards
- no panel may hide provenance

**Step 4: Commit**

```bash
git add docs/specs/dashboard_truth_model.md docs/architecture.md docs/task_status.md
git commit -m "docs: define dashboard truth model and provenance taxonomy"
```

---

### Task 2: Add backend runtime truth and evidence contract

**Files:**
- Create: `src/dashboard/truth.py`
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/readiness.py`
- Modify: `src/face/livetalking_manager.py`
- Modify: `src/stream/rtmp.py`
- Modify: `src/voice/engine.py`
- Test: `tests/test_dashboard.py`
- Test: `tests/test_livetalking_integration.py`

**Step 1: Write failing backend tests**

Add tests for a new consolidated contract, recommended endpoint:

- `GET /api/runtime/truth`

Minimum expected fields:

- `mock_mode`
- `voice_runtime_mode`
- `face_runtime_mode`
- `stream_runtime_mode`
- `validation_state`
- `last_validated_at`
- `provenance`

Also add tests proving existing endpoints include provenance where relevant:

- readiness
- engine status
- stream status

**Step 2: Run targeted tests to confirm failure**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
uv run pytest tests/test_livetalking_integration.py -q -p no:cacheprovider
```

Expected:
- FAIL because consolidated truth contract does not exist yet

**Step 3: Implement the minimal backend truth layer**

Rules:

- centralize runtime truth assembly in `src/dashboard/truth.py`
- do not scatter ad-hoc provenance strings across endpoints
- derive runtime modes from actual config/runtime objects
- `mock_mode` must come from the real config/env path

**Step 4: Re-run targeted tests**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
uv run pytest tests/test_livetalking_integration.py -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/truth.py src/dashboard/api.py src/dashboard/readiness.py src/face/livetalking_manager.py src/stream/rtmp.py src/voice/engine.py tests/test_dashboard.py tests/test_livetalking_integration.py
git commit -m "feat: add backend runtime truth and provenance contract"
```

---

### Task 3: Add a global Truth Bar to the dashboard shell

**Files:**
- Modify: `src/dashboard/frontend/src/App.svelte`
- Modify: `src/dashboard/frontend/src/components/layout/Header.svelte`
- Create: `src/dashboard/frontend/src/components/common/TruthBar.svelte`
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Test: `src/dashboard/frontend/src/tests/App.test.ts`

**Step 1: Write the failing frontend test**

Add test assertions that the top shell shows:

- mock/live mode
- validation state
- data origin
- last validation timestamp or placeholder

**Step 2: Run the targeted test**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/App.test.ts
```

Expected:
- FAIL

**Step 3: Implement the Truth Bar**

UI rules:

- always visible
- concise, operator-first
- must not rely on local inferred state
- must display red/yellow/green severity clearly

**Step 4: Re-run the targeted test**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/App.test.ts
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/App.svelte src/dashboard/frontend/src/components/layout/Header.svelte src/dashboard/frontend/src/components/common/TruthBar.svelte src/dashboard/frontend/src/lib/types.ts src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/tests/App.test.ts
git commit -m "feat: add dashboard truth bar"
```

---

### Task 4: Add provenance badges and freshness metadata to critical panels

**Files:**
- Create: `src/dashboard/frontend/src/components/common/ProvenanceBadge.svelte`
- Create: `src/dashboard/frontend/src/components/common/FreshnessBadge.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/OverviewPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/ReadinessPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/EnginePanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/StreamPanel.svelte`
- Test: `src/dashboard/frontend/src/tests/engine-panel.test.ts`
- Test: `src/dashboard/frontend/src/tests/App.test.ts`

**Step 1: Write failing tests**

Add assertions proving:

- Engine panel shows provenance
- Stream panel shows runtime mode/provenance
- Readiness panel shows freshness or validation timestamp

**Step 2: Run targeted frontend tests**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/engine-panel.test.ts
cd src/dashboard/frontend
npm run test -- src/tests/App.test.ts
```

Expected:
- FAIL

**Step 3: Implement the provenance/freshness badges**

Rules:

- no silent fallback to “green”
- unknown provenance must be visually obvious
- mock provenance must never look production-ready

**Step 4: Re-run targeted tests**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/engine-panel.test.ts
cd src/dashboard/frontend
npm run test -- src/tests/App.test.ts
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/common/ProvenanceBadge.svelte src/dashboard/frontend/src/components/common/FreshnessBadge.svelte src/dashboard/frontend/src/components/panels/OverviewPanel.svelte src/dashboard/frontend/src/components/panels/ReadinessPanel.svelte src/dashboard/frontend/src/components/panels/EnginePanel.svelte src/dashboard/frontend/src/components/panels/StreamPanel.svelte src/dashboard/frontend/src/tests/engine-panel.test.ts src/dashboard/frontend/src/tests/App.test.ts
git commit -m "feat: expose provenance and freshness in dashboard panels"
```

---

### Task 5: Replace silent failures with action receipts and visible errors

**Files:**
- Create: `src/dashboard/frontend/src/lib/stores/actions.ts`
- Create: `src/dashboard/frontend/src/components/common/ActionReceipt.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/EnginePanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/StreamPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/CommercePanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/DiagnosticsPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/PreviewPanel.svelte`
- Test: `src/dashboard/frontend/src/tests/engine-panel.test.ts`
- Test: `src/dashboard/frontend/src/tests/api.test.ts`

**Step 1: Write failing tests**

Add tests ensuring:

- failed actions display an error receipt
- successful actions display a success receipt
- receipts include timestamp and message

**Step 2: Run targeted tests**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/engine-panel.test.ts
cd src/dashboard/frontend
npm run test -- src/tests/api.test.ts
```

Expected:
- FAIL

**Step 3: Implement action receipts**

Rules:

- eliminate `catch { /* ignore */ }` in operator-critical panels
- map API errors to visible UI
- record last action result in a small operator-visible surface

**Step 4: Re-run targeted tests**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/engine-panel.test.ts
cd src/dashboard/frontend
npm run test -- src/tests/api.test.ts
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/lib/stores/actions.ts src/dashboard/frontend/src/components/common/ActionReceipt.svelte src/dashboard/frontend/src/components/panels/EnginePanel.svelte src/dashboard/frontend/src/components/panels/StreamPanel.svelte src/dashboard/frontend/src/components/panels/CommercePanel.svelte src/dashboard/frontend/src/components/panels/DiagnosticsPanel.svelte src/dashboard/frontend/src/components/panels/PreviewPanel.svelte src/dashboard/frontend/src/tests/engine-panel.test.ts src/dashboard/frontend/src/tests/api.test.ts
git commit -m "feat: add visible action receipts and remove silent failures"
```

---

### Task 6: Make missing operator controls real from the dashboard

**Files:**
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Modify: `src/dashboard/frontend/src/components/panels/CommercePanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/DiagnosticsPanel.svelte`
- Create: `src/dashboard/frontend/src/components/panels/PipelinePanel.svelte` or extend existing relevant panel
- Modify: `src/dashboard/frontend/src/components/layout/PageShell.svelte`
- Test: `src/dashboard/frontend/src/tests/api.test.ts`
- Test: `src/dashboard/frontend/src/tests/App.test.ts`

**Step 1: Write failing tests**

Cover at least these controls:

- product switch
- pipeline transition
- brain test trigger
- emergency reset

**Step 2: Run targeted tests**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/api.test.ts
cd src/dashboard/frontend
npm run test -- src/tests/App.test.ts
```

Expected:
- FAIL

**Step 3: Implement the missing controls**

Rules:

- only wire controls that backend already supports
- do not fake completion
- every control must show result receipt

**Step 4: Re-run targeted tests**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/api.test.ts
cd src/dashboard/frontend
npm run test -- src/tests/App.test.ts
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/lib/types.ts src/dashboard/frontend/src/components/panels/CommercePanel.svelte src/dashboard/frontend/src/components/panels/DiagnosticsPanel.svelte src/dashboard/frontend/src/components/panels/PipelinePanel.svelte src/dashboard/frontend/src/components/layout/PageShell.svelte src/dashboard/frontend/src/tests/api.test.ts src/dashboard/frontend/src/tests/App.test.ts
git commit -m "feat: wire dashboard operator controls to backend actions"
```

---

### Task 7: Add realtime state via WebSocket and polling fallback

**Files:**
- Modify: `src/dashboard/api.py`
- Create: `src/dashboard/frontend/src/lib/realtime.ts`
- Modify: `src/dashboard/frontend/src/lib/stores/health.ts`
- Modify: `src/dashboard/frontend/src/lib/stores/livetalking.ts`
- Modify: `src/dashboard/frontend/src/components/panels/MonitorPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/OverviewPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/DiagnosticsPanel.svelte`
- Test: `tests/test_dashboard.py`
- Test: `src/dashboard/frontend/src/tests/App.test.ts`

**Step 1: Write failing tests**

Add tests proving:

- dashboard WebSocket payload has structured truth fields
- frontend handles realtime updates without full reload

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
cd src/dashboard/frontend
npm run test -- src/tests/App.test.ts
```

Expected:
- FAIL

**Step 3: Implement realtime layer**

Rules:

- use existing WebSocket surfaces where possible
- fallback to polling if socket unavailable
- no panel should stay frozen after operator actions

**Step 4: Re-run targeted tests**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
cd src/dashboard/frontend
npm run test -- src/tests/App.test.ts
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/api.py src/dashboard/frontend/src/lib/realtime.ts src/dashboard/frontend/src/lib/stores/health.ts src/dashboard/frontend/src/lib/stores/livetalking.ts src/dashboard/frontend/src/components/panels/MonitorPanel.svelte src/dashboard/frontend/src/components/panels/OverviewPanel.svelte src/dashboard/frontend/src/components/panels/DiagnosticsPanel.svelte tests/test_dashboard.py src/dashboard/frontend/src/tests/App.test.ts
git commit -m "feat: add realtime dashboard state updates"
```

---

### Task 8: Add Validation Console and evidence history

**Files:**
- Create: `src/dashboard/validation_history.py`
- Modify: `src/dashboard/api.py`
- Create: `src/dashboard/frontend/src/components/panels/ValidationPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/layout/PageShell.svelte`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Create: `src/dashboard/frontend/src/tests/validation-panel.test.ts`
- Test: `tests/test_dashboard.py`

**Step 1: Write failing tests**

Validation console must be able to:

- run engine validation
- run RTMP validation
- run runtime truth validation
- list last validation results
- display evidence timestamp

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
cd src/dashboard/frontend
npm run test -- src/tests/validation-panel.test.ts
```

Expected:
- FAIL

**Step 3: Implement validation history**

Requirements:

- persist recent validation results to a project-local store or log-backed history
- evidence record must include:
  - check name
  - input context
  - result
  - timestamp
  - provenance

**Step 4: Re-run targeted tests**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
cd src/dashboard/frontend
npm run test -- src/tests/validation-panel.test.ts
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/validation_history.py src/dashboard/api.py src/dashboard/frontend/src/components/panels/ValidationPanel.svelte src/dashboard/frontend/src/components/layout/PageShell.svelte src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/lib/types.ts src/dashboard/frontend/src/tests/validation-panel.test.ts tests/test_dashboard.py
git commit -m "feat: add validation console and evidence history"
```

---

### Task 9: Create a strict real-mode readiness gate

**Files:**
- Create: `scripts/check_real_mode_readiness.py`
- Modify: `src/dashboard/readiness.py`
- Modify: `docs/workflow.md`
- Modify: `docs/task_status.md`
- Test: `tests/test_layers.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write failing tests**

Add tests that fail if:

- `MOCK_MODE=true`
- required real avatar assets are missing
- required RTMP config is placeholder/empty
- products are absent or still marked demo/seed if such flag exists
- LiveTalking runtime path is still unresolved

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_layers.py -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- FAIL

**Step 3: Implement the real-mode gate**

Rules:

- this script must not silently downgrade to mock
- if real-mode prerequisites are absent, return non-zero and clear blockers
- wire summary into dashboard validation console

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
git add scripts/check_real_mode_readiness.py src/dashboard/readiness.py docs/workflow.md docs/task_status.md tests/test_layers.py tests/test_dashboard.py
git commit -m "feat: add strict real-mode readiness gate"
```

---

### Task 10: Run full real-mode validation with evidence, no synthetic substitutions

**Files:**
- Create: `scripts/run_dashboard_real_validation.py`
- Create: `docs/audits/AUDIT_REAL_VALIDATION_2026-03-08.md`
- Modify: `docs/changelogs.md`
- Modify: `docs/task_status.md`
- Modify: `docs/workflow.md`

**Step 1: Define required real prerequisites**

Do not start execution until these are real and present:

- `MOCK_MODE=false`
- real `assets/avatar/reference.mp4`
- real `assets/voice/reference.wav`
- canonical MuseTalk assets ready
- real RTMP target configured
- real product data loaded
- LiveTalking sidecar reachable

If any item missing:

- stop task as `BLOCKED`
- record blocker in audit doc
- do not substitute fake data

**Step 2: Run real readiness script**

Run:

```bash
uv run python scripts/check_real_mode_readiness.py
```

Expected:
- PASS or explicit BLOCKED reasons

**Step 3: Run full app in real mode**

Run:

```bash
set MOCK_MODE=false
uv run python -m src.main
```

Then manually validate from dashboard:

- truth bar shows non-mock mode
- Engine panel shows real runtime provenance
- Stream panel validates RTMP target
- Validation Console records evidence
- dashboard does not show “verified” for blocked real assets/services

**Step 4: Run real browser validation**

Run:

```bash
cd src/dashboard/frontend
npx playwright test e2e/dashboard.spec.ts
```

Expected:
- PASS in real server context

**Step 5: Save evidence**

Create an audit snapshot including:

- exact command outputs
- screenshots if needed
- blocked items if any
- final verdict:
  - `REAL VERIFIED`
  - `PARTIAL REAL`
  - `BLOCKED`

**Step 6: Commit**

```bash
git add scripts/run_dashboard_real_validation.py docs/audits/AUDIT_REAL_VALIDATION_2026-03-08.md docs/changelogs.md docs/task_status.md docs/workflow.md
git commit -m "docs: record real dashboard validation evidence"
```

---

## 7. Real Data Policy

### Allowed

- real operator assets
- real DB rows
- real connector traffic
- real FFmpeg process
- real RTMP bytes to a real target
- real vendor sidecar process
- real local service outputs

### Not allowed for final acceptance

- generated dummy product rows
- hardcoded fake viewer counts
- fake “healthy” provider states
- mock stream status while claiming live
- placeholder avatar assets while claiming real validation
- UI-only success without backend evidence

---

## 8. Review Checklist for Human

Saat Claude selesai, review dengan urutan ini:

1. Apakah truth bar selalu tampil?
2. Apakah dashboard jelas menunjukkan `mock` vs `real`?
3. Apakah setiap aksi operator memberi receipt/error?
4. Apakah status panel diperbarui realtime?
5. Apakah Validation Console menyimpan evidence?
6. Apakah `MOCK_MODE=false` benar-benar dipakai saat final validation?
7. Apakah ada satu pun klaim real verification yang sebenarnya masih synthetic?
8. Apakah blocker ditulis jujur jika platform/asset belum siap?

---

## 9. Recommended Execution Mode

Untuk fase ini, jangan batch full implementation tanpa checkpoint.

Checkpoint yang disarankan:

- Checkpoint A: Task 1-3 selesai
- Checkpoint B: Task 4-6 selesai
- Checkpoint C: Task 7-9 selesai
- Checkpoint D: Task 10 real acceptance

Task 10 harus direview manusia sebelum dianggap final.
