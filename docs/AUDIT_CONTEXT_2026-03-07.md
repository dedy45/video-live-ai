# Audit Konteks VideoLiveAI

Tanggal audit: 2026-03-07  
Scope: `videoliveai/` (kode, test, script, dokumentasi, jalur run)

## Ringkasan Eksekutif

Status saat ini **belum siap produksi end-to-end**, tapi **siap development dalam MOCK_MODE**.

- Validasi lokal via UV berjalan: test lulus dan server bisa start.
- Banyak dokumen/setup entrypoint sudah stale atau hilang, memicu kesan "project tidak jalan".
- Komponen core real-time produksi (voice/face LiveTalking/GPU path) masih stub (`NotImplementedError` / TODO), sehingga arsitektur final belum benar-benar terintegrasi.

## Metodologi dan Bukti Reproduksi

### 1) Reproduksi test failure (global env)

Command:

```powershell
pytest tests -q -p no:cacheprovider
```

Hasil:
- Gagal collection (`ModuleNotFoundError: No module named 'src'`)
- `hypothesis` tidak terpasang di env global

Makna:
- Menjalankan di luar UV/venv resmi menghasilkan false negative.

### 2) Reproduksi test success (env resmi proyek)

Command:

```powershell
uv run pytest tests -q -p no:cacheprovider
```

Hasil:
- `79 passed`

Makna:
- Runtime test stack proyek valid jika lewat `uv run`.

### 3) Reproduksi masalah CLI verifikasi

Command:

```powershell
$env:MOCK_MODE='true'; uv run python scripts/verify_pipeline.py --verbose
```

Hasil:
- Gagal `UnicodeEncodeError` (terminal cp1252 saat print simbol emoji/unicode).

Command pembanding:

```powershell
$env:MOCK_MODE='true'; $env:PYTHONUTF8='1'; uv run python scripts/verify_pipeline.py --verbose
```

Hasil:
- Lulus `11/11 layers`.

Makna:
- Bukan bug logika pipeline, tapi bug kompatibilitas encoding output CLI.

### 4) Reproduksi startup service

Validasi endpoint root dan diagnostic pada server yang dijalankan di `MOCK_MODE` berhasil (`status=running`, diagnostic healthy).

## Temuan Utama (Prioritas)

## P0 - Kesenjangan fungsi produksi (blocker)

Komponen produksi inti belum diimplementasikan penuh:

- `src/voice/engine.py`: FishSpeech production path melempar `NotImplementedError`.
- `src/face/pipeline.py`: MuseTalk + GFPGAN production path melempar `NotImplementedError`.
- `src/face/livetalking_adapter.py`: Start server/streaming masih TODO + `NotImplementedError`.

Dampak:
- Arsitektur "hyper-realistic production" belum operasional di real mode.

## P1 - Dokumentasi entrypoint stale/putus

Di README/workflow terdapat rujukan file yang tidak ada:

- `START_HERE.md`, `livetalking_menu.bat`, `test_livetalking.bat`
- `docs/02-LIVE-STREAMING-AI/tech-stack/*` relatif dari `videoliveai/` tidak valid
- `PROJECT_SUMMARY.md`, `AGENTS.md` (di dalam `videoliveai/`) tidak ada
- `quick_setup.bat`, `setup_livetalking_uv.bat`, `simple_setup_uv.bat`, `SETUP_GUIDE.md` tidak ada

Dampak:
- Onboarding macet walau core mock stack sebenarnya bisa jalan.

## P1 - Validasi status dokumen tidak sinkron

`docs/task_status.md` menyatakan `67/67` + beberapa status pending, padahal runtime aktual menunjukkan `79 passed`.

Dampak:
- Audit progress jadi ambigu, sulit dipakai untuk decision making.

## P2 - Script test/debug membingungkan

`tests/test_router_init.py` bukan unit test murni, tetapi script debug side-effect dan menambahkan path yang salah (`tests/` alih-alih root proyek).

Dampak:
- Saat dipanggil lewat pytest global, memperbesar peluang error import yang misleading.

## P2 - Quality debt linting tinggi

`scripts/validate.bat` lulus tetapi menghasilkan banyak warning Ruff (unused import, line too long, dsb).

Dampak:
- Menurunkan maintainability, tapi belum blocker fungsi.

## Referensi File Bukti

- `README` stale refs: `README.md` lines 23, 27, 179, 185-188
- Router init path bug: `tests/test_router_init.py` lines 7-8
- Unicode output CLI: `scripts/verify_pipeline.py` lines 279, 286, 290, 293
- TODO/NotImplemented:
  - `src/voice/engine.py` line 115
  - `src/face/pipeline.py` lines 98, 125
  - `src/face/livetalking_adapter.py` lines 128, 194-196, 218
- Workflow stale refs: `docs/workflow.md` lines 11, 15, 19, 28
- Task status drift: `docs/task_status.md` lines 6, 50, 62

## Sprint Update (Audit View)

### Exit criteria fase saat ini

- Dev mode (`MOCK_MODE`) stabil: **PASS**.
- Jalur real production (GPU + LiveTalking streaming end-to-end): **FAIL / belum implementasi penuh**.

### 3 aksi prioritas optimal

1. **Bekukan dan rapikan entrypoint (P1, cepat, high-impact)**
   - Sinkronkan README + workflow ke file yang benar-benar ada.
   - Tetapkan satu jalur resmi:
     - setup: `uv sync --extra dev`
     - test: `uv run pytest tests -v`
     - verify: `cmd /c scripts\validate.bat`
   - Exit criteria: user baru bisa setup/run tanpa dead-link.

2. **Hardening jalur verifikasi & debugging (P1)**
   - Patch `verify_pipeline.py` agar aman di cp1252 (fallback ASCII icons/line).
   - Pindahkan `tests/test_router_init.py` menjadi util script non-test (mis. `scripts/router_init_debug.py`) atau perbaiki path root.
   - Exit criteria: `uv run python scripts/verify_pipeline.py --verbose` selalu sukses tanpa env tweak tambahan.

3. **Definisikan jalur produksi minimal yang benar-benar runnable (P0)**
   - Pilih target realistis tahap 1:
     - opsi A: production voice+face tetap mock tapi streaming real RTMP, atau
     - opsi B: LiveTalking subprocess bridge minimal (start app.py + health + frame ingress/egress contract).
   - Buat acceptance test untuk target tersebut.
   - Exit criteria: satu skenario produksi minimal bisa dijalankan reproducible, bukan hanya mock/unit pass.

## Rekomendasi Strategi Lanjut

Untuk momentum tercepat, lakukan urutan:

1) **Docs/entrypoint cleanup** → 2) **verify/debug hardening** → 3) **production minimal slice**.

Urutan ini mengurangi friksi operasional dulu, baru investasi ke integrasi GPU yang paling mahal dan berisiko.

