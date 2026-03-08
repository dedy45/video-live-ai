# Svelte Dashboard Verification Remediation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Menutup gap verifikasi pada dashboard Svelte agar statusnya bisa dinaikkan dari `PARTIAL` menjadi `LOCAL VERIFIED` dengan bukti yang jujur.

**Architecture:** Pertahankan hasil migrasi yang sudah ada: FastAPI tetap control plane, dashboard Svelte tetap static build yang diserve di `/dashboard`, dan LiveTalking vendor pages tetap debug-only. Fokus plan ini hanya pada penyelarasan kontrak data, test coverage frontend, dan sinkronisasi dokumentasi.

**Tech Stack:** Python 3.12, FastAPI, UV-only untuk Python environment, Svelte 5, Vite, TypeScript, Vitest, Playwright, npm.

---

## 0. Verified Starting State

Hasil verifikasi independen pada 2026-03-08:

- `cd src/dashboard/frontend && npm run build` -> PASS
- `uv run pytest tests -q -p no:cacheprovider` -> `115 passed`
- `uv run python scripts/verify_pipeline.py` -> `11/11 layers passed`
- `uv run python -m src.main` + `GET /dashboard/` -> `200`, served from `src/dashboard/frontend/dist`

Gap yang masih terbuka:

- `cd src/dashboard/frontend && npm run test` -> FAIL karena tidak ada file test
- Panel Engine belum menampilkan `requested_*` vs `resolved_*`
- `docs/task_status.md`, `docs/workflow.md`, dan `docs/changelogs.md` belum sinkron dengan status riil

Non-goals untuk plan ini:

- Tidak menyelesaikan missing `assets/avatar/reference.mp4`
- Tidak mengubah target runtime MuseTalk
- Tidak rewrite lagi struktur dashboard

---

## 1. Execution Order

Kerjakan dalam urutan ini:

1. Rapikan kontrak backend untuk requested/resolved LiveTalking state
2. Tampilkan state tersebut di dashboard Svelte
3. Tambahkan test frontend minimum sampai `npm run test` benar-benar hijau
4. Tambahkan browser smoke test sederhana untuk `/dashboard`
5. Sinkronkan docs status agar tidak overclaim
6. Jalankan verification gate penuh

Jangan loncat ke docs dulu sebelum kontrak data dan test minimum selesai.

---

## 2. Task-by-Task Implementation Plan

### Task 1: Expose requested vs resolved LiveTalking state from backend

**Files:**
- Modify: `src/face/livetalking_manager.py`
- Modify: `src/dashboard/api.py`
- Test: `tests/test_livetalking_integration.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write the failing backend tests**

Tambahkan/ubah test agar memverifikasi:

- `GET /api/engine/livetalking/status` mengembalikan:
  - `requested_model`
  - `resolved_model`
  - `requested_avatar_id`
  - `resolved_avatar_id`
- `GET /api/engine/livetalking/config` juga memuat field yang sama

**Step 2: Run the targeted tests to confirm failure**

Run:

```bash
uv run pytest tests/test_livetalking_integration.py -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- FAIL karena field baru belum ada

**Step 3: Implement the minimal backend contract**

Update `EngineStatus` dan config export supaya requested/resolved state keluar dari API, bukan hanya dari log internal.

**Step 4: Re-run the targeted backend tests**

Run:

```bash
uv run pytest tests/test_livetalking_integration.py -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/face/livetalking_manager.py src/dashboard/api.py tests/test_livetalking_integration.py tests/test_dashboard.py
git commit -m "feat: expose requested and resolved livetalking state"
```

---

### Task 2: Surface requested vs resolved state in the Svelte dashboard

**Files:**
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Modify: `src/dashboard/frontend/src/components/panels/EnginePanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/ReadinessPanel.svelte`
- Test: `src/dashboard/frontend/src/tests/livetalking-panel.test.ts`

**Step 1: Write the failing frontend test**

Tambahkan test yang memverifikasi panel Engine menampilkan:

- requested model
- resolved model
- requested avatar
- resolved avatar

Jika fallback terjadi, UI harus menunjukkan keduanya, bukan satu nilai final saja.

**Step 2: Run the targeted frontend test**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/livetalking-panel.test.ts
```

Expected:
- FAIL

**Step 3: Implement minimal UI changes**

- Perluas tipe API
- Render requested/resolved secara eksplisit
- Jangan pecah layout besar; cukup jelas dan operasional

**Step 4: Re-run the targeted frontend test**

Run:

```bash
cd src/dashboard/frontend
npm run test -- src/tests/livetalking-panel.test.ts
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/lib/types.ts src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/components/panels/EnginePanel.svelte src/dashboard/frontend/src/components/panels/ReadinessPanel.svelte src/dashboard/frontend/src/tests/livetalking-panel.test.ts
git commit -m "feat: show requested and resolved livetalking state in dashboard"
```

---

### Task 3: Establish a minimal frontend test suite

**Files:**
- Create: `src/dashboard/frontend/src/tests/App.test.ts`
- Create: `src/dashboard/frontend/src/tests/api.test.ts`
- Create or modify: `src/dashboard/frontend/vitest.setup.ts`
- Modify: `src/dashboard/frontend/package.json`
- Modify: `src/dashboard/frontend/vite.config.ts`

**Step 1: Write the missing baseline tests**

Buat minimal test suite yang membuktikan:

- `App.svelte` render shell tab utama
- client API parse response shape dasar
- panel Engine render status normal dan fallback state

**Step 2: Run the full frontend unit test command**

Run:

```bash
cd src/dashboard/frontend
npm run test
```

Expected:
- FAIL terlebih dahulu jika setup belum lengkap

**Step 3: Add the smallest test harness needed**

- setup Vitest untuk Svelte DOM tests
- jangan menambah framework test kedua

**Step 4: Re-run the full frontend unit test command**

Run:

```bash
cd src/dashboard/frontend
npm run test
```

Expected:
- PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/tests/App.test.ts src/dashboard/frontend/src/tests/api.test.ts src/dashboard/frontend/src/tests/livetalking-panel.test.ts src/dashboard/frontend/vitest.setup.ts src/dashboard/frontend/package.json src/dashboard/frontend/vite.config.ts
git commit -m "test: add baseline svelte dashboard unit coverage"
```

---

### Task 4: Add a browser smoke test for `/dashboard`

**Files:**
- Modify: `src/dashboard/frontend/package.json`
- Create: `src/dashboard/frontend/playwright.config.ts`
- Create: `src/dashboard/frontend/e2e/dashboard.spec.ts`

**Step 1: Write the smoke spec**

Spec minimum:

- open `/dashboard`
- assert shell loaded
- assert tab `Engine` exists
- assert one readiness indicator exists

Jangan tes seluruh sistem end-to-end di sini. Ini hanya smoke check untuk memastikan build + static serving tidak blank.

**Step 2: Install browser runtime if needed**

Run:

```bash
cd src/dashboard/frontend
npx playwright install chromium
```

Expected:
- Chromium installed locally for smoke test

**Step 3: Run the smoke test**

Run:

```bash
cd src/dashboard/frontend
npx playwright test
```

Expected:
- PASS

**Step 4: Add npm shortcut**

Tambahkan `test:e2e` ke `package.json`.

**Step 5: Commit**

```bash
git add src/dashboard/frontend/package.json src/dashboard/frontend/playwright.config.ts src/dashboard/frontend/e2e/dashboard.spec.ts
git commit -m "test: add dashboard browser smoke test"
```

---

### Task 5: Sync docs with the verified state

**Files:**
- Modify: `docs/task_status.md`
- Modify: `docs/workflow.md`
- Modify: `docs/changelogs.md`
- Modify: `docs/plans/2026-03-08-svelte-dashboard-rebuild-plan.md`

**Step 1: Update task status**

Required changes:

- `Svelte dashboard migration` -> `PARTIAL`, not `TARGET ONLY`
- tambahkan gap yang masih tersisa:
  - frontend tests belum ada atau belum hijau
  - requested/resolved belum tampil
  - docs belum sinkron

**Step 2: Update workflow snapshot**

Required changes:

- ganti snapshot lama `89 passed`
- tambahkan perintah frontend:
  - `npm run build`
  - `npm run test`
  - `npx playwright test`

Jika salah satu masih gagal, tulis status gagal secara jujur.

**Step 3: Update changelog**

Tambahkan entry baru yang menjelaskan:

- migrasi Svelte memang landed
- verifikasi independen menunjukkan status masih `PARTIAL`
- gap yang harus ditutup

**Step 4: Add post-verification note to the original rebuild plan**

Tambahkan catatan jelas di bagian atas plan lama bahwa eksekusi awal sudah landed sebagian, tetapi completion harus mengikuti remediation plan ini.

**Step 5: Commit**

```bash
git add docs/task_status.md docs/workflow.md docs/changelogs.md docs/plans/2026-03-08-svelte-dashboard-rebuild-plan.md docs/plans/2026-03-08-svelte-dashboard-verification-remediation.md
git commit -m "docs: align dashboard plan with verification findings"
```

---

### Task 6: Final verification gate

**Files:**
- Verify all changed files

**Step 1: Run frontend build**

```bash
cd src/dashboard/frontend
npm run build
```

Expected:
- PASS

**Step 2: Run frontend unit tests**

```bash
cd src/dashboard/frontend
npm run test
```

Expected:
- PASS

**Step 3: Run browser smoke test**

```bash
cd src/dashboard/frontend
npx playwright test
```

Expected:
- PASS

**Step 4: Run backend tests**

```bash
uv run pytest tests -q -p no:cacheprovider
```

Expected:
- PASS

**Step 5: Run pipeline verification**

```bash
uv run python scripts/verify_pipeline.py
```

Expected:
- `11/11 layers passed` atau count terbaru jika suite bertambah

**Step 6: Run local manual smoke**

```bash
uv run python -m src.main
```

Manual checks:

- `http://localhost:8000/dashboard` loads
- `Engine` panel loads
- requested vs resolved state visible
- vendor debug links visible
- no blank page

**Step 7: Final commit**

```bash
git add .
git commit -m "feat: complete svelte dashboard verification remediation"
```

---

## 3. Acceptance Criteria

Plan ini dianggap selesai hanya jika semua poin berikut benar:

- `npm run build` PASS
- `npm run test` PASS
- `npx playwright test` PASS
- `uv run pytest tests -q -p no:cacheprovider` PASS
- `uv run python scripts/verify_pipeline.py` PASS
- `/dashboard` served from Svelte build
- Engine panel shows requested vs resolved model/avatar explicitly
- Docs tidak lagi mengklaim dashboard masih `TARGET ONLY`

---

## 4. Recommended Handoff

Agent yang mengerjakan plan ini harus mulai dari Task 1. Jangan mulai dari docs atau styling dulu.

Jika Task 1 gagal karena kontrak backend tidak cukup jelas, stop dan audit `src/face/livetalking_manager.py` serta `src/dashboard/api.py` sebelum menyentuh Svelte panel.

Untuk handoff copy-paste yang lebih ketat ke Claude Opus, gunakan:

- [2026-03-08-svelte-dashboard-remediation-claude-handoff.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/plans/2026-03-08-svelte-dashboard-remediation-claude-handoff.md)
