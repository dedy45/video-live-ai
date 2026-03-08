# Svelte Dashboard Rebuild Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Merombak dashboard operator `videoliveai` dari satu file HTML/JS statis menjadi dashboard Svelte yang modular, tetap disajikan oleh FastAPI di `/dashboard`, dan mampu mengontrol LiveTalking dari satu tempat.

**Architecture:** Backend tetap `videoliveai` + FastAPI sebagai control plane dan `external/livetalking` tetap sidecar vendor engine. Frontend diganti menjadi Svelte + Vite static build di `src/dashboard/frontend/`, lalu hasil build diserve oleh FastAPI. Halaman vendor `http://localhost:8010/*.html` tetap dipertahankan hanya sebagai debug tools dan diakses lewat link dari dashboard operator baru.

**Tech Stack:** Python 3.12, FastAPI, UV-only untuk Python environment, Svelte 5, Vite, TypeScript, npm untuk build frontend statis, SQLite, structlog, FFmpeg, LiveTalking vendor app.

---

## Status Update — 2026-03-08

Eksekusi awal plan ini **sudah landed sebagian**:

- Svelte build sudah ada
- FastAPI sudah bisa serve `src/dashboard/frontend/dist`
- panel utama sudah muncul di `/dashboard`

Tetapi independent verification menemukan gap yang membuat statusnya **belum boleh dianggap complete**:

- `npm run test` masih gagal karena belum ada frontend test files
- `requested` vs `resolved` LiveTalking state belum benar-benar tampil di dashboard
- `docs/task_status.md`, `docs/workflow.md`, dan `docs/changelogs.md` belum sinkron

Sebelum menandai plan ini selesai, lanjutkan remediation plan berikut:

- `docs/plans/2026-03-08-svelte-dashboard-verification-remediation.md`

---

## 0. Project Context Snapshot

### Current state

- Dashboard operator saat ini masih berupa satu file HTML besar:
  - `src/dashboard/frontend/index.html`
- FastAPI saat ini langsung men-serve folder frontend lama:
  - `src/main.py`
- Backend control API untuk dashboard sudah ada:
  - `src/dashboard/api.py`
- Endpoint LiveTalking yang sudah tersedia:
  - `GET /api/engine/livetalking/status`
  - `POST /api/engine/livetalking/start`
  - `POST /api/engine/livetalking/stop`
  - `GET /api/engine/livetalking/logs`
  - `GET /api/engine/livetalking/config`
  - `GET /api/readiness`
- Dashboard lama belum benar-benar mengontrol LiveTalking end-to-end.
- Vendor LiveTalking pada `http://localhost:8010/dashboard.html` dan `http://localhost:8010/webrtcapi.html` masih dibutuhkan untuk debug langsung.

### What this migration must achieve

- `/dashboard` menjadi operator dashboard tunggal yang nyata, bukan hanya monitor umum.
- Dashboard harus punya panel LiveTalking lengkap:
  - status engine
  - start/stop
  - requested vs resolved model/avatar
  - vendor preview/debug links
  - engine logs
  - readiness summary
- UI harus modular, bisa dirawat, dan siap dikembangkan.
- Python workflow tetap `uv`.
- Tidak boleh ada conda.

### Non-goals

- Tidak membangun Next.js.
- Tidak membangun NestJS.
- Tidak mengubah `external/livetalking` menjadi dashboard utama.
- Tidak melakukan rewrite besar pada backend di luar kebutuhan dashboard bridge.
- Tidak mengejar redesign public marketing site; ini murni internal operator console.

---

## 1. Hard Constraints

### Environment constraints

- Python dependency management wajib `uv`.
- Jangan menambah conda instructions di docs, scripts, atau comments.
- Frontend build boleh memakai `npm` karena Vite/Svelte butuh Node toolchain.
- Jangan memperkenalkan `pnpm`, `yarn`, atau monorepo tool tambahan kecuali benar-benar dibutuhkan. Default: `npm`.

### Runtime constraints

- URL operator tetap: `http://localhost:8000/dashboard`
- URL vendor debug tetap:
  - `http://localhost:8010/dashboard.html`
  - `http://localhost:8010/webrtcapi.html`
- FastAPI tetap source of truth untuk operator dashboard.
- LiveTalking vendor UI hanya linked/debug, bukan embedded as primary operator logic.

### UI constraints

- Preserve visual seriousness of current dashboard, but stop relying on one giant HTML file.
- Avoid default boring scaffolding. Gunakan design system yang jelas, tapi tidak over-engineered.
- Mobile support cukup baik untuk monitoring dasar.
- Desktop tetap prioritas utama.

### Implementation constraints

- TDD untuk perubahan perilaku penting.
- Tiap task kecil, bisa diverifikasi, dan jangan bundle refactor liar.
- Jika ada kontradiksi antara UI lama dan backend nyata, backend contract yang menang.

---

## 2. Target End State

Setelah migrasi selesai:

- `src/dashboard/frontend/` menjadi project Svelte + Vite yang nyata.
- FastAPI serve hasil build statis `dist/` di `/dashboard`.
- Dashboard punya tab atau nav modular berikut:
  - Overview
  - Readiness
  - Engine
  - Preview
  - Stream
  - Commerce
  - Monitor
  - Diagnostics
- Operator bisa:
  - cek health sistem
  - cek readiness
  - start/stop LiveTalking
  - lihat error port collision
  - buka vendor preview
  - lihat log engine
  - validasi RTMP target
- Dashboard lama `index.html` tidak lagi menjadi source of truth. Jika perlu, arsipkan.

---

## 3. Delivery Strategy

### Recommended cutover strategy

Gunakan **incremental replacement**, bukan big-bang rewrite.

1. Scaffold toolchain Svelte dulu.
2. Build shell layout + API client.
3. Migrasikan panel yang paling penting dulu:
   - Readiness
   - Engine
   - Diagnostics
4. Tambahkan Overview / Monitor / Commerce.
5. Integrasikan Preview / Stream.
6. Cut over FastAPI serving ke build output baru.
7. Arsipkan dashboard lama.

### Why this strategy

- Mengurangi risiko blank page.
- Mempermudah debug data flow API.
- Menghindari kehilangan capability saat migrasi.
- Cocok untuk handoff ke agent coding yang perlu checkpoint jelas.

---

## 4. File Strategy

### Existing files to preserve

- `src/dashboard/api.py`
- `src/dashboard/readiness.py`
- `src/face/livetalking_manager.py`
- `src/main.py`
- `external/livetalking/web/*`

### Existing file to replace gradually

- `src/dashboard/frontend/index.html`

### New frontend structure to create

```text
src/dashboard/frontend/
├── package.json
├── package-lock.json
├── tsconfig.json
├── vite.config.ts
├── svelte.config.js
├── index.html
├── src/
│   ├── app.css
│   ├── main.ts
│   ├── App.svelte
│   ├── lib/
│   │   ├── api.ts
│   │   ├── types.ts
│   │   ├── format.ts
│   │   ├── constants.ts
│   │   └── stores/
│   │       ├── app.ts
│   │       ├── health.ts
│   │       ├── livetalking.ts
│   │       └── metrics.ts
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.svelte
│   │   │   ├── Sidebar.svelte
│   │   │   ├── TabNav.svelte
│   │   │   └── PageShell.svelte
│   │   ├── common/
│   │   │   ├── Card.svelte
│   │   │   ├── StatusBadge.svelte
│   │   │   ├── MetricTile.svelte
│   │   │   ├── LogViewer.svelte
│   │   │   ├── ActionButton.svelte
│   │   │   └── EmptyState.svelte
│   │   └── panels/
│   │       ├── OverviewPanel.svelte
│   │       ├── ReadinessPanel.svelte
│   │       ├── EnginePanel.svelte
│   │       ├── PreviewPanel.svelte
│   │       ├── StreamPanel.svelte
│   │       ├── CommercePanel.svelte
│   │       ├── MonitorPanel.svelte
│   │       └── DiagnosticsPanel.svelte
│   └── tests/
│       ├── api.test.ts
│       ├── App.test.ts
│       └── livetalking-panel.test.ts
└── dist/
```

### Existing tests to extend

- `tests/test_dashboard.py`
- `tests/test_livetalking_integration.py`
- optionally new frontend tests inside `src/dashboard/frontend/src/tests/`

---

## 5. Task-by-Task Implementation Plan

### Task 1: Freeze the current dashboard behavior

**Files:**
- Review: `src/dashboard/frontend/index.html`
- Review: `src/dashboard/api.py`
- Review: `src/main.py`
- Create: `docs/decisions/dashboard_rebuild_scope.md`

**Step 1: Write the scope doc**

Document:
- existing tabs
- existing REST calls
- existing WebSocket calls
- which features are real vs cosmetic
- which features must survive migration

**Step 2: Verify the document matches current code**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- pass

**Step 3: Commit**

```bash
git add docs/decisions/dashboard_rebuild_scope.md
git commit -m "docs: freeze current dashboard migration scope"
```

---

### Task 2: Scaffold Svelte + Vite frontend

**Files:**
- Create: `src/dashboard/frontend/package.json`
- Create: `src/dashboard/frontend/tsconfig.json`
- Create: `src/dashboard/frontend/vite.config.ts`
- Create: `src/dashboard/frontend/svelte.config.js`
- Create: `src/dashboard/frontend/index.html`
- Create: `src/dashboard/frontend/src/main.ts`
- Create: `src/dashboard/frontend/src/App.svelte`
- Create: `src/dashboard/frontend/src/app.css`
- Modify: `.gitignore`

**Step 1: Write the failing integration test for build artifacts**

Add backend-side expectation in:
- `tests/test_entrypoints.py`

Test should assert:
- FastAPI can still serve `/dashboard`
- When `dist/` exists, the dashboard route still resolves

**Step 2: Run the targeted test to verify baseline**

```bash
uv run pytest tests/test_entrypoints.py -q -p no:cacheprovider
```

Expected:
- either existing pass or a failing placeholder if new expectation is added

**Step 3: Add minimal frontend scaffold**

Use:
- `svelte`
- `vite`
- `typescript`
- basic `npm` scripts:
  - `dev`
  - `build`
  - `preview`
  - `test`

**Step 4: Verify frontend build**

Run:

```bash
cd src/dashboard/frontend
npm install
npm run build
```

Expected:
- `dist/` generated without error

**Step 5: Commit**

```bash
git add src/dashboard/frontend .gitignore tests/test_entrypoints.py
git commit -m "feat: scaffold svelte dashboard frontend"
```

---

### Task 3: Integrate FastAPI with Svelte build output

**Files:**
- Modify: `src/main.py`
- Modify: `tests/test_entrypoints.py`

**Step 1: Write the failing test**

Add test for:
- `/dashboard/` serves built Svelte app
- fallback to legacy path only if needed during transition

**Step 2: Run the failing test**

```bash
uv run pytest tests/test_entrypoints.py -q -p no:cacheprovider
```

Expected:
- FAIL if current mount path does not handle `dist/`

**Step 3: Implement minimal serving logic**

Rules:
- Prefer `src/dashboard/frontend/dist/` if present
- Transitional fallback to legacy root only if explicitly intended
- Keep `/dashboard` route stable

**Step 4: Re-run tests**

```bash
uv run pytest tests/test_entrypoints.py -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/main.py tests/test_entrypoints.py
git commit -m "feat: serve svelte dashboard build from fastapi"
```

---

### Task 4: Build shared API client and typed frontend state

**Files:**
- Create: `src/dashboard/frontend/src/lib/api.ts`
- Create: `src/dashboard/frontend/src/lib/types.ts`
- Create: `src/dashboard/frontend/src/lib/format.ts`
- Create: `src/dashboard/frontend/src/lib/constants.ts`
- Create: `src/dashboard/frontend/src/lib/stores/app.ts`
- Create: `src/dashboard/frontend/src/lib/stores/health.ts`
- Create: `src/dashboard/frontend/src/lib/stores/livetalking.ts`
- Create: `src/dashboard/frontend/src/lib/stores/metrics.ts`
- Create: `src/dashboard/frontend/src/tests/api.test.ts`

**Step 1: Write failing frontend tests**

Cover:
- API base path handling
- error normalization
- parsing of readiness response
- parsing of LiveTalking engine status response

**Step 2: Run frontend test to verify failure**

```bash
cd src/dashboard/frontend
npm run test -- api.test.ts
```

Expected:
- FAIL

**Step 3: Implement minimal API layer**

Required functions:
- `getStatus()`
- `getMetrics()`
- `getReadiness()`
- `getLiveTalkingStatus()`
- `startLiveTalking()`
- `stopLiveTalking()`
- `getLiveTalkingLogs()`
- `getLiveTalkingConfig()`
- `validateLiveTalkingEngine()`
- `validateRtmpTarget()`

**Step 4: Re-run frontend tests**

```bash
cd src/dashboard/frontend
npm run test -- api.test.ts
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/lib src/dashboard/frontend/src/tests/api.test.ts
git commit -m "feat: add typed dashboard api client and stores"
```

---

### Task 5: Build shell layout and design system

**Files:**
- Create: `src/dashboard/frontend/src/components/layout/Header.svelte`
- Create: `src/dashboard/frontend/src/components/layout/Sidebar.svelte`
- Create: `src/dashboard/frontend/src/components/layout/TabNav.svelte`
- Create: `src/dashboard/frontend/src/components/layout/PageShell.svelte`
- Create: `src/dashboard/frontend/src/components/common/Card.svelte`
- Create: `src/dashboard/frontend/src/components/common/StatusBadge.svelte`
- Create: `src/dashboard/frontend/src/components/common/MetricTile.svelte`
- Create: `src/dashboard/frontend/src/components/common/LogViewer.svelte`
- Create: `src/dashboard/frontend/src/components/common/ActionButton.svelte`
- Create: `src/dashboard/frontend/src/components/common/EmptyState.svelte`
- Modify: `src/dashboard/frontend/src/App.svelte`
- Modify: `src/dashboard/frontend/src/app.css`
- Create: `src/dashboard/frontend/src/tests/App.test.ts`

**Step 1: Write failing component test**

Test:
- App renders nav items:
  - Overview
  - Readiness
  - Engine
  - Preview
  - Stream
  - Commerce
  - Monitor
  - Diagnostics

**Step 2: Run test to verify failure**

```bash
cd src/dashboard/frontend
npm run test -- App.test.ts
```

Expected:
- FAIL

**Step 3: Implement shell**

Requirements:
- modular nav
- responsive desktop-first layout
- visual style consistent with current serious control-room vibe
- no dependence on giant inline JS

**Step 4: Re-run test**

```bash
cd src/dashboard/frontend
npm run test -- App.test.ts
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components src/dashboard/frontend/src/App.svelte src/dashboard/frontend/src/app.css src/dashboard/frontend/src/tests/App.test.ts
git commit -m "feat: build svelte dashboard shell and shared ui components"
```

---

### Task 6: Implement Readiness and Engine panels first

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/ReadinessPanel.svelte`
- Create: `src/dashboard/frontend/src/components/panels/EnginePanel.svelte`
- Create: `src/dashboard/frontend/src/tests/livetalking-panel.test.ts`
- Modify: `src/dashboard/frontend/src/App.svelte`
- Modify: `tests/test_dashboard.py`

**Step 1: Write failing tests**

Frontend tests:
- engine panel renders status
- shows `requested` and `resolved` model/avatar
- shows last error if any
- exposes buttons for start, stop, refresh
- exposes vendor links

Backend tests:
- `/api/engine/livetalking/config` returns debug URLs
- `/api/readiness` remains compatible with panel data needs

**Step 2: Run tests and confirm failure**

```bash
cd src/dashboard/frontend
npm run test -- livetalking-panel.test.ts
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- at least one test fails for missing UI behavior

**Step 3: Implement panels**

Engine panel must show:
- state
- uptime
- port
- transport
- requested model/avatar
- resolved model/avatar
- last error
- app/model/avatar path readiness

Readiness panel must show:
- overall status
- checks list
- blocking issues
- recommended next action

Buttons:
- `Start Engine`
- `Stop Engine`
- `Refresh`
- `Validate Engine`
- `Validate RTMP`
- `Open Vendor Dashboard`
- `Open WebRTC Preview`

**Step 4: Re-run tests**

```bash
cd src/dashboard/frontend
npm run test -- livetalking-panel.test.ts
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels tests/test_dashboard.py
git commit -m "feat: add readiness and livetalking engine panels"
```

---

### Task 7: Implement Overview, Diagnostics, Monitor, and Commerce panels

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/OverviewPanel.svelte`
- Create: `src/dashboard/frontend/src/components/panels/DiagnosticsPanel.svelte`
- Create: `src/dashboard/frontend/src/components/panels/MonitorPanel.svelte`
- Create: `src/dashboard/frontend/src/components/panels/CommercePanel.svelte`
- Modify: `src/dashboard/frontend/src/App.svelte`

**Step 1: Write failing tests**

Cover:
- overview metrics render
- diagnostics can display health/log area
- monitor can display recent chat list
- commerce can display product list and revenue summary

**Step 2: Run tests**

```bash
cd src/dashboard/frontend
npm run test
```

Expected:
- FAIL on missing components or missing expected labels

**Step 3: Implement minimal panels**

Use existing endpoints:
- `/api/status`
- `/api/metrics`
- `/api/health/summary`
- `/api/chat/recent`
- `/api/products`
- `/api/analytics/revenue`

**Step 4: Re-run tests**

```bash
cd src/dashboard/frontend
npm run test
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels
git commit -m "feat: migrate overview diagnostics monitor and commerce panels"
```

---

### Task 8: Implement Preview and Stream panels

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/PreviewPanel.svelte`
- Create: `src/dashboard/frontend/src/components/panels/StreamPanel.svelte`
- Modify: `src/dashboard/frontend/src/App.svelte`
- Modify: `tests/test_dashboard.py`

**Step 1: Write failing tests**

Cover:
- preview panel shows vendor debug URLs from API
- stream panel shows RTMP validation results
- stream panel exposes stream start/stop

**Step 2: Run tests**

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
cd src/dashboard/frontend
npm run test
```

Expected:
- FAIL

**Step 3: Implement panels**

Preview panel:
- show `dashboard.html`
- show `webrtcapi.html`
- show `rtcpushapi.html`
- provide "open in new tab" actions

Stream panel:
- current stream state
- validate RTMP target
- display ffmpeg readiness
- stream start/stop actions

**Step 4: Re-run tests**

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
cd src/dashboard/frontend
npm run test
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels tests/test_dashboard.py
git commit -m "feat: add preview and stream panels"
```

---

### Task 9: Add polling and WebSocket orchestration

**Files:**
- Modify: `src/dashboard/frontend/src/lib/stores/*.ts`
- Modify: `src/dashboard/frontend/src/App.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/*.svelte`

**Step 1: Write failing tests for live update behavior**

Minimum:
- store exposes reconnect state
- fallback polling works when websocket unavailable

**Step 2: Run tests**

```bash
cd src/dashboard/frontend
npm run test
```

Expected:
- FAIL

**Step 3: Implement data flow**

Rules:
- WebSocket for dashboard snapshot if available
- polling fallback for status/readiness/engine/logs
- do not block UI on one failing request
- show stale/error banners clearly

**Step 4: Re-run tests**

```bash
cd src/dashboard/frontend
npm run test
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src
git commit -m "feat: add dashboard live update orchestration"
```

---

### Task 10: Add browser-level smoke test for dashboard load

**Files:**
- Create: `src/dashboard/frontend/playwright.config.ts`
- Create: `src/dashboard/frontend/e2e/dashboard.spec.ts`
- Optionally modify: `src/dashboard/frontend/package.json`

**Step 1: Write failing smoke test**

Scenario:
- `/dashboard` loads
- tab labels visible
- LiveTalking engine panel visible
- Readiness panel visible

**Step 2: Run the failing smoke test**

```bash
cd src/dashboard/frontend
npx playwright test
```

Expected:
- FAIL until wiring complete

**Step 3: Implement whatever is minimally needed to pass**

Keep smoke scope narrow.

**Step 4: Re-run**

```bash
cd src/dashboard/frontend
npx playwright test
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/playwright.config.ts src/dashboard/frontend/e2e src/dashboard/frontend/package.json
git commit -m "test: add dashboard browser smoke coverage"
```

---

### Task 11: Remove legacy HTML dashboard as active implementation

**Files:**
- Archive or replace: `src/dashboard/frontend/index.html`
- Create or update: `docs/archive/legacy_dashboard_html.md`
- Modify: `docs/workflow.md`
- Modify: `docs/task_status.md`
- Modify: `docs/changelogs.md`

**Step 1: Move or neutralize legacy implementation**

Preferred:
- keep Vite `index.html` as build entry
- archive the old monolithic dashboard source into docs/archive or a dedicated legacy location if needed for reference

**Step 2: Update docs**

Docs must state:
- `/dashboard` now served by Svelte build
- vendor pages remain debug-only
- no confusion about legacy HTML ownership

**Step 3: Commit**

```bash
git add src/dashboard/frontend/index.html docs/workflow.md docs/task_status.md docs/changelogs.md docs/archive/legacy_dashboard_html.md
git commit -m "docs: finalize svelte dashboard cutover"
```

---

### Task 12: Final verification gate

**Files:**
- Verify all changed files

**Step 1: Run frontend test suite**

```bash
cd src/dashboard/frontend
npm run test
```

Expected:
- PASS

**Step 2: Run browser smoke test**

```bash
cd src/dashboard/frontend
npx playwright test
```

Expected:
- PASS

**Step 3: Run backend tests**

```bash
uv run pytest tests -q -p no:cacheprovider
```

Expected:
- PASS

**Step 4: Run pipeline verification**

```bash
uv run python scripts/verify_pipeline.py
```

Expected:
- `11/11 layers passed` or current expected count if suite grows

**Step 5: Run app locally and manual smoke**

```bash
uv run python -m src.main
```

Manual checks:
- open `http://localhost:8000/dashboard`
- check `Readiness`
- check `Engine`
- click `Refresh`
- if safe, click `Start Engine`
- confirm port collision shown clearly if `8010` already occupied
- confirm vendor links open

**Step 6: Final commit**

```bash
git add .
git commit -m "feat: rebuild operator dashboard in svelte"
```

---

## 6. Acceptance Criteria

Migration dianggap selesai hanya jika:

- `/dashboard` diserve dari build Svelte, bukan giant legacy HTML runtime.
- Dashboard memiliki panel `Readiness` dan `Engine` yang benar-benar bekerja.
- Dashboard menampilkan requested vs resolved LiveTalking model/avatar.
- Dashboard menampilkan port collision dan error engine secara eksplisit.
- Dashboard menyediakan link langsung ke vendor preview/debug pages.
- Backend tests tetap hijau.
- Frontend tests dan browser smoke tests hijau.
- Docs aktif sudah sinkron.

---

## 7. Risks and Guardrails

### Risk 1: Claude mencoba redesign backend terlalu jauh

Guardrail:
- Jangan rewrite `src/dashboard/api.py` kecuali perlu data contract kecil.
- Gunakan endpoint yang sudah ada sebanyak mungkin.

### Risk 2: Claude mencoba bikin arsitektur frontend berlebihan

Guardrail:
- Tidak perlu router kompleks.
- Tidak perlu SSR.
- Tidak perlu auth system baru.
- Tidak perlu state manager besar selain Svelte stores.

### Risk 3: Dashboard cantik tapi tidak operasional

Guardrail:
- Prioritaskan `Readiness`, `Engine`, `Diagnostics`.
- `Overview` boleh sederhana asalkan data flow benar.

### Risk 4: Frontend migration merusak `/dashboard`

Guardrail:
- Cutover bertahap.
- Pastikan FastAPI fallback/serve logic bisa diverifikasi sebelum arsipkan dashboard lama.

### Risk 5: Tooling drift

Guardrail:
- Python tetap `uv`
- Frontend default `npm`
- Jangan tambah package manager ketiga

---

## 8. Copy-Paste Prompt for Claude Opus

Gunakan prompt berikut apa adanya atau edit sedikit jika perlu:

```text
You are Claude Opus working inside the repo:

C:\\Users\\dedy\\Documents\\!fast-track-income\\videoliveai

Read and execute this plan exactly:

docs/plans/2026-03-08-svelte-dashboard-rebuild-plan.md

Mission:
- Rebuild the operator dashboard from the current monolithic HTML/JS file into a real Svelte + Vite dashboard.
- Keep FastAPI as the backend control plane.
- Keep LiveTalking vendor pages as debug-only links, not the main dashboard.
- Make http://localhost:8000/dashboard the single operator dashboard.

Hard constraints:
- Python environment must remain UV-only. No conda.
- Frontend may use npm for Svelte/Vite build tooling, but do not introduce pnpm, yarn, turborepo, or Next.js.
- Do not rewrite the architecture into Next.js/NestJS.
- Do not treat external/livetalking/web as the main dashboard.
- Use TDD for important behavior changes.
- Prefer minimal, reviewable commits after each task.
- Preserve current backend endpoints unless a small extension is necessary.

Important repo facts:
- Current backend dashboard API is in src/dashboard/api.py
- Current app entry is src/main.py
- Current legacy dashboard is src/dashboard/frontend/index.html
- LiveTalking manager is in src/face/livetalking_manager.py
- Vendor debug pages run on port 8010
- Operator dashboard must stay on /dashboard via FastAPI

Primary UX goals:
- Add a real LiveTalking control surface in the operator dashboard
- Show readiness, engine state, requested vs resolved model/avatar, logs, and vendor preview links
- Make port-collision and engine errors obvious
- Keep the interface internal-tool oriented, not marketing-site styled

Execution rules:
1. Start by reading the plan file and current dashboard-related files.
2. Work task-by-task.
3. Before each behavior change, add or update tests first.
4. Run verification after each task, not only at the end.
5. Keep docs updated when the cutover is complete.
6. Do not claim completion without fresh command output.

Minimum verification required before final handoff:
- npm run build in src/dashboard/frontend
- npm run test in src/dashboard/frontend
- browser smoke test for dashboard load
- uv run pytest tests -q -p no:cacheprovider
- uv run python scripts/verify_pipeline.py
- manual smoke of /dashboard and LiveTalking engine panel

Expected end state:
- Svelte operator dashboard served by FastAPI
- LiveTalking control integrated into operator dashboard
- Legacy giant HTML no longer active implementation
- Documentation updated to reflect the new dashboard ownership
```

---

## 9. Recommended Execution Mode

Untuk agent eksekusi:

- gunakan checkpoint per task
- jangan loncat langsung ke full rewrite
- berhenti jika menemukan mismatch besar antara backend contract dan plan ini
- laporkan blockers secara teknis, bukan generik

---

## 10. Review Checklist for Human

Setelah Claude selesai, review poin ini:

- Apakah `/dashboard` benar-benar Svelte build?
- Apakah panel LiveTalking benar-benar ada?
- Apakah `Start/Stop/Refresh/Validate` benar-benar memanggil backend yang benar?
- Apakah status `requested` vs `resolved` tampil?
- Apakah link ke `8010/dashboard.html` dan `8010/webrtcapi.html` tampil?
- Apakah port bentrok `8010` muncul sebagai error yang jelas?
- Apakah dashboard masih ringan dan tidak jadi SaaS UI generik?
- Apakah docs aktif sudah sinkron?
