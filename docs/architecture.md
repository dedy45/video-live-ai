# VideoLiveAI Architecture

> Version: 0.4.0  
> Last Updated: 2026-03-07  
> Target: Internal live system first  
> Package Manager Policy: UV only

## Ringkasan

`videoliveai` adalah **control plane utama** untuk sistem live internal.  
`external/livetalking` adalah **sidecar engine vendor** untuk avatar, lip sync, preview, dan output realtime.

Arsitektur ini sengaja **tidak** mengikuti `fullstack.md` untuk fase sekarang. Fokus saat ini adalah:

- satu backend utama
- satu dashboard operator utama
- satu engine vendor untuk wajah/lip sync/output
- alur live minimal yang stabil dan mudah dipindah ke Ubuntu server

## Keputusan Arsitektur

| Komponen | Peran | Status |
|----------|------|--------|
| `videoliveai/src/main.py` | Entry point FastAPI | Main runtime |
| `videoliveai/src/dashboard` | Dashboard operator utama | Source of truth UI |
| `videoliveai/src/brain` | LLM routing dan behavior | Owned by project |
| `videoliveai/src/voice` | TTS orchestration | Owned by project |
| `videoliveai/src/stream` | RTMP stream management | Owned by project |
| `videoliveai/src/data` | SQLite dan state lokal | Owned by project |
| `videoliveai/external/livetalking` | Face engine vendor | Sidecar |
| `videoliveai/external/livetalking/web` | Debug pages vendor | Debug only |

## Diagram Sistem

```text
                           +-----------------------+
                           |   Operator Browser    |
                           |  /dashboard (utama)   |
                           +-----------+-----------+
                                       |
                                       v
                     +----------------------------------------+
                     |        VideoLiveAI FastAPI             |
                     |----------------------------------------|
                     | - config + env loader                  |
                     | - readiness + diagnostics              |
                     | - dashboard API                        |
                     | - orchestrator                         |
                     | - stream control                       |
                     | - LiveTalking process bridge           |
                     +---+----------------+-------------------+
                         |                | 
             +-----------+---+        +---+------------------+
             |   Brain Layer |        |  Voice Layer         |
             |---------------|        |----------------------|
             | LiteLLM       |        | FishSpeech / EdgeTTS |
             | Persona       |        | humanization policy  |
             | Safety        |        | audio routing        |
             +-----------+---+        +---+------------------+
                         |                |
                         +--------+-------+
                                  |
                                  v
                     +----------------------------------------+
                     |      Live Output Coordination          |
                     |----------------------------------------|
                     | - script/text dispatch                 |
                     | - face engine control                  |
                     | - preview links                        |
                     | - RTMP dry-run / live run              |
                     +----------------+-----------------------+
                                      |
                                      v
                  +-----------------------------------------------+
                  |      external/livetalking (vendor sidecar)    |
                  |-----------------------------------------------|
                  | - app.py                                      |
                  | - wav2lip / musetalk runtime                  |
                  | - WebRTC preview                              |
                  | - RTMP / rtcpush transport                    |
                  | - vendor web debug pages                      |
                  +----------------+------------------------------+
                                   |
                        +----------+----------+
                        |                     |
                        v                     v
              +----------------+    +------------------------+
              | Preview Debug   |    | RTMP / platform output |
              | localhost:8010  |    | TikTok / Shopee / test |
              +----------------+    +------------------------+
```

## Operator UI vs Vendor UI

Ini pemisahan paling penting agar tidak bingung:

| UI | URL | Fungsi |
|----|-----|--------|
| Operator Dashboard | `http://localhost:8000/dashboard` | Dashboard utama untuk validasi dan kontrol sistem |
| Vendor Debug Pages | `http://localhost:8010/*.html` | Halaman debug LiveTalking, bukan dashboard operator |

### Aturan penggunaan

- Operator harian harus mulai dari `/dashboard`
- Vendor pages hanya dipakai saat:
  - test engine langsung
  - cek preview WebRTC
  - debug input text ke LiveTalking
  - verifikasi apakah masalah ada di engine vendor atau di orchestration layer

## Siapa Menangani Apa

### Tanggung jawab `videoliveai`

- load config
- load env
- health checks
- diagnostics
- readiness validation
- LLM routing
- TTS orchestration
- stream orchestration
- dashboard API
- dashboard UI
- process manager untuk LiveTalking
- logging dan run history

### Tanggung jawab `LiveTalking`

- avatar runtime
- lip sync runtime
- preview realtime
- transport output (`webrtc`, `rtcpush`, sebagian `rtmp`)
- vendor debug UI

### Bukan tugas utama `LiveTalking`

- database
- dashboard utama
- LLM router
- voice cloning strategy project-wide
- TTS humanizer layer
- scene renderer penuh
- reliability supervisor 18 jam

## Pemetaan ke Phase Build

| Phase | Owner utama | Peran LiveTalking |
|-------|-------------|-------------------|
| Phase 0: Foundation & Environment | `videoliveai` | dependency dan engine readiness |
| Phase 1: Database & API Foundation | `videoliveai` | none |
| Phase 2: Voice Cloning Setup | `videoliveai` | none |
| Phase 3: TTS Humanizer Layer | `videoliveai` | none |
| Phase 4: Face Animation | project integration | optional / outside core vendor role |
| Phase 5: Lip Sync | LiveTalking | core responsibility |
| Phase 6: Face Compositor & Humanizer | shared | partial support only |
| Phase 7: LLM Brain & Router | `videoliveai` | none |
| Phase 8: Stream Pipeline | shared | strong support on engine side |
| Phase 9: Scene Renderer | `videoliveai` | none or partial |
| Phase 10: Control Panel UI | `videoliveai` | none |
| Phase 11: 18-Hour Stability Layer | `videoliveai` | engine must be supervised |
| Phase 12: Integration & Testing | shared | one subsystem being verified |

## Jalur Data Operasional

```text
Dashboard operator
  -> FastAPI API
  -> Orchestrator / controller
  -> Brain decides text/script
  -> Voice layer creates audio
  -> LiveTalking receives text/audio/runtime command
  -> LiveTalking renders avatar output
  -> Preview and/or RTMP output
  -> Dashboard displays health, logs, readiness
```

## Runtime Topology

### Port utama

| Komponen | Port | Catatan |
|----------|------|---------|
| FastAPI main app | `8000` | dashboard operator, API, diagnostic |
| LiveTalking vendor engine | `8010` | preview dan debug vendor |

### Entry points

| Entry point | Fungsi |
|-------------|--------|
| `uv run python -m src.main` | Menjalankan FastAPI utama |
| `external/livetalking/app.py` | Entry point engine vendor |

### Source of truth yang dipakai

Arsitektur target internal harus menuju satu kebijakan path yang tegas:

- model runtime LiveTalking: `external/livetalking/models/`
- avatar runtime LiveTalking: `external/livetalking/data/avatars/`
- dashboard frontend build: `src/dashboard/frontend/`

Catatan:
- root-level `models/` dan `data/avatars/` masih ada di repo saat ini karena warisan script lama
- untuk fase berikutnya, path ini harus disederhanakan agar tidak ganda

## Struktur Direktori Arsitektur

```text
videoliveai/
├── src/
│   ├── main.py
│   ├── brain/
│   ├── voice/
│   ├── face/
│   │   ├── pipeline.py
│   │   ├── livetalking_adapter.py
│   │   └── livetalking_manager.py          # target
│   ├── stream/
│   ├── dashboard/
│   │   ├── api.py
│   │   ├── diagnostic.py
│   │   └── frontend/
│   ├── data/
│   ├── config/
│   └── utils/
├── scripts/
├── tests/
├── docs/
├── external/
│   └── livetalking/
│       ├── app.py
│       ├── web/
│       ├── models/
│       └── data/
├── config/
├── .env.example
└── pyproject.toml
```

## Startup Flow

```text
1. FastAPI starts
2. Config and env loaded
3. Database initialized
4. Dashboard API registered
5. Health manager registered
6. LiveTalking bridge checks readiness
7. Operator opens /dashboard
8. Operator validates readiness
9. Operator starts LiveTalking if needed
10. Preview tested
11. RTMP path validated
12. Internal live slice executed
```

## Dashboard Strategy

### Sekarang

- dashboard utama masih HTML statis
- sudah cukup untuk baseline observability

### Target

- frontend diganti ke Svelte ringan
- tetap static build
- tetap disajikan oleh FastAPI
- tidak memakai Next.js

Alasan:

- lebih ringan
- tidak perlu SSR
- cocok untuk panel operator internal
- minim friction saat dipindah ke Ubuntu server

## Environment Policy

Semua dokumentasi aktif harus mengikuti aturan ini:

- gunakan `uv sync`
- gunakan `uv run`
- gunakan `uv pip`
- jangan gunakan conda
- jangan jadikan environment Windows-specific sebagai sumber kebenaran

### Command resmi

```bash
uv sync --extra dev
uv run pytest tests -q -p no:cacheprovider
uv run python scripts/verify_pipeline.py --verbose
uv run python -m src.main
```

## Status Saat Ini

### Sudah ada

- FastAPI control plane
- dashboard API
- diagnostic endpoints
- SQLite
- LiteLLM router
- RTMP manager baseline
- LiveTalking vendor repo
- batch scripts untuk run dan setup awal

### Belum selesai

- process bridge LiveTalking yang rapi
- satu source of truth model/avatar path
- readiness API yang lengkap
- dashboard Svelte
- vertical slice live yang benar-benar terpaku
- reliability layer untuk penggunaan panjang

## Dokumen Terkait

- `docs/README.md`
- `docs/decisions/architecture_internal_live.md`
- `docs/audits/AUDIT_CONTEXT_2026-03-07.md`
- `docs/plans/2026-03-07-unified-dashboard-livetalking-plan.md`
- `docs/guides/LIVETALKING_WEB_ACCESS_ID.md`
- `docs/guides/LIVETALKING_QUICKSTART.md`
