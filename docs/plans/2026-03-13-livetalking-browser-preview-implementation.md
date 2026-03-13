# LiveTalking Browser Preview Activation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Membuat `webrtcapi.html` dan `rtcpushapi.html` aktif kembali sebagai preview browser nyata untuk avatar + audio, dengan dashboard memberi status yang jujur.

**Architecture:** Perbaikan difokuskan pada startup sidecar vendor, lalu manager/API/dashboard diperkuat agar hanya melaporkan success jika port preview benar-benar hidup. Validasi akhir dilakukan lewat browser pada vendor pages.

**Tech Stack:** FastAPI, Svelte, subprocess process manager, LiveTalking vendor sidecar, aiortc/WebRTC, Playwright, pytest, Vitest.

---

### Task 1: Lock The Failure With Tests

**Files:**
- Modify: `tests/test_dashboard.py`
- Modify: `tests/test_control_plane.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write the failing test**

- Tambahkan test yang memastikan `engine start` mengembalikan error/blocked bila subprocess vendor mati cepat.
- Tambahkan test yang memastikan `debug-targets` tidak menyatakan preview reachable bila port `8010` tidak hidup.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: FAIL pada contract baru manager/API.

**Step 3: Write minimal implementation**

- Belum. Tunggu Task 2.

**Step 4: Run test to verify it still captures the bug**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: FAIL tetap relevan.

### Task 2: Fix LiveTalking Manager Startup Contract

**Files:**
- Modify: `src/face/livetalking_manager.py`
- Modify: `src/dashboard/api.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write the failing test**

- Tambahkan unit/integration test untuk:
  - subprocess fast-exit -> state `error`
  - stderr startup tercatat
  - start tidak boleh return `running` jika port belum reachable

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: FAIL karena manager sekarang terlalu optimistis.

**Step 3: Write minimal implementation**

- Tambahkan startup wait window pada manager
- cek process poll + reachability port
- simpan startup stderr ringkas
- surface `last_error` yang berguna
- ubah API `engine.start` agar status `error`/`blocked` sesuai hasil nyata

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: PASS untuk test manager/API baru.

### Task 3: Fix Sidecar Runtime Environment

**Files:**
- Modify: `src/face/livetalking_manager.py`
- Modify: `docs/operations/livetiktokubuntu.md`
- Possibly modify: `pyproject.toml` or runtime bootstrap scripts if needed
- Test: manual runtime smoke

**Step 1: Reproduce startup failure**

Run:

```powershell
Set-Location C:\Users\dedy\Documents\!fast-track-income\videoliveai\external\livetalking
& 'C:\Users\dedy\Documents\!fast-track-income\videoliveai\.venv\Scripts\python.exe' app.py --transport webrtc --model musetalk --avatar_id musetalk_avatar1 --listenport 8010
```

Expected: observe exact startup failure.

**Step 2: Implement minimal environment fix**

- pilih interpreter sidecar yang benar
- tambah compatibility fallback bila env utama tidak layak
- jika perlu, fallback model/transport yang lebih ringan untuk local preview smoke

**Step 3: Verify sidecar stays alive**

Run:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 8010
```

Expected: `TcpTestSucceeded = True`

### Task 4: Make WebRTC / RTCPush Preview Reachability Visible

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/frontend/src/components/panels/PerformerPreviewPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/PerformerTechnicalPanel.svelte`
- Test: `src/dashboard/frontend/src/tests/performer-preview-panel.test.ts`

**Step 1: Write the failing test**

- Tambahkan test frontend untuk state:
  - process belum start
  - startup failed
  - reachable but not yet connected

**Step 2: Run test to verify it fails**

Run: `npm test -- --run src/tests/performer-preview-panel.test.ts`

Expected: FAIL karena messaging/state belum lengkap.

**Step 3: Write minimal implementation**

- API debug-targets tambahkan reason/status yang lebih spesifik
- panel Preview tampilkan penyebab nyata dan langkah operator

**Step 4: Run test to verify it passes**

Run: `npm test -- --run src/tests/performer-preview-panel.test.ts`

Expected: PASS

### Task 5: Browser Validation For `webrtcapi.html`

**Files:**
- No new production file required unless browser-specific bug found
- Test: manual browser + Playwright smoke

**Step 1: Start sidecar in `webrtc` transport**

Use dashboard/API or direct manager.

**Step 2: Open vendor page**

Open: `http://localhost:8010/webrtcapi.html`

**Step 3: Start media session**

- click `Start`
- confirm `/offer` succeeds
- confirm `audio` and `video` elements receive stream objects

**Step 4: Verify**

- no fatal console errors
- page reachable
- media tracks attached

### Task 6: Browser Validation For `rtcpushapi.html`

**Files:**
- Modify: `src/face/livetalking_manager.py` if transport switching/bootstrap is missing
- Modify: `src/dashboard/api.py` if transport override endpoint is needed
- Test: browser/manual smoke

**Step 1: Write the failing test**

- Tambahkan backend test untuk transport override/switch jika diperlukan.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`

Expected: FAIL jika transport switching belum ada.

**Step 3: Write minimal implementation**

- tambah cara eksplisit memilih `webrtc` vs `rtcpush`
- boot sidecar dengan transport yang diminta

**Step 4: Verify**

- `http://localhost:8010/rtcpushapi.html` reachable
- no fatal console errors

### Task 7: Final Verification And Docs

**Files:**
- Modify: `docs/operations/livetiktokubuntu.md`
- Modify: `docs/task_status.md`
- Modify: `README.md` if operator flow changes

**Step 1: Run backend verification**

Run: `uv run pytest tests/test_dashboard.py tests/test_control_plane.py -q -p no:cacheprovider`

Expected: PASS

**Step 2: Run frontend verification**

Run: `npm test -- --run src/tests/performer-preview-panel.test.ts src/tests/performer-page.test.ts`

Expected: PASS

**Step 3: Run build**

Run: `npm run build`

Expected: PASS

**Step 4: Run browser smoke**

- `http://localhost:8010/webrtcapi.html`
- `http://localhost:8010/rtcpushapi.html`
- `http://127.0.0.1:8001/dashboard/#/performer`

Expected:

- vendor pages reachable
- dashboard preview status consistent
- no fatal console errors

**Step 5: Update docs**

- tulis langkah local Windows preview capture untuk TikTok LIVE Studio
- tandai batas validasi yang benar
