# VideoLiveAI Architecture

> Version: 0.5.17
> Last Updated: 2026-03-12  
> Target: Internal live system first  
> Package Manager Policy: UV only

## Ringkasan

`videoliveai` adalah **control plane utama** untuk sistem live internal dan server-hosted operations controller.
`external/livetalking` adalah **sidecar engine vendor** untuk avatar, lip sync, preview, dan output realtime.

Arsitektur ini adalah **evolusi operasional**, bukan rewrite fondasi. Fokus saat ini adalah:

- satu backend utama
- satu dashboard operator utama di `/dashboard`
- satu engine vendor untuk wajah/lip sync/output
- truth model yang host-aware untuk local lab dan server production
- alur live yang tetap berjalan di server walau browser operator terputus

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
| `videoliveai/external/fish-speech` | Voice sidecar checkout/checkpoints/runtime | Sidecar |
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
| Operator Dashboard | `http://localhost:8000/dashboard` atau `http://SERVER_IP_OR_DOMAIN/dashboard` | Dashboard utama untuk validasi, kontrol, incident review, dan ops summary |
| Vendor Debug Pages | `http://localhost:8010/*.html` | Halaman debug LiveTalking, bukan dashboard operator |

### Aturan penggunaan

- Operator harian harus mulai dari `/dashboard`
- Untuk production, `/dashboard` harus dipublish lewat reverse proxy dengan auth + TLS
- Browser operator boleh putus; proses live harus tetap berjalan di host server
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
| `uv run python scripts/manage.py serve --mock` | Menjalankan FastAPI utama untuk local mock mode |
| `uv run python scripts/manage.py serve --real` | Menjalankan FastAPI utama dengan LiveTalking extra ter-hydrate |
| `external/livetalking/app.py` | Entry point engine vendor |

### Source of truth yang dipakai

Arsitektur target internal harus menuju satu kebijakan path yang tegas:

- model runtime LiveTalking: `external/livetalking/models/`
- avatar runtime LiveTalking: `external/livetalking/data/avatars/`
- fish-speech checkout/runtime: `external/fish-speech/`
- fish-speech python env: `external/fish-speech/runtime/.venv/`
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
│   ├── fish-speech/
│   │   ├── upstream/
│   │   ├── checkpoints/
│   │   └── runtime/
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

- dashboard utama adalah Svelte SPA, diserve dari `src/dashboard/frontend/dist`
- dashboard bukan hanya status cards — harus mengekspos runtime truth
- setiap panel wajib menunjukkan provenance (asal data) dan tidak boleh menyembunyikannya
- workflow operator resmi sekarang terdiri dari 6 surface:
  - `Setup & Validasi`
  - `Produk & Penawaran`
  - `Avatar & Suara`
  - `Streaming & Platform`
  - `Konsol Live`
  - `Monitor & Insiden`
- `Avatar & Suara` sendiri adalah workspace bertab dengan 6 tab operator:
  - `Ringkasan`
  - `Suara`
  - `Avatar`
  - `Preview`
  - `Validasi`
  - `Teknis`
- `Setup & Validasi` sekarang juga memuat surface `Brain & Prompt` untuk membaca prompt aktif, routing provider, persona aktif, dan budget runtime
- `Konsol Live` sekarang memuat surface `Director Runtime` untuk membaca state director, fase show aktif, provider/model aktif, prompt aktif, dan riwayat transisi
- `Validation` dan `Diagnostics` bukan lagi halaman operator terpisah; keduanya digabung ke `Setup & Validasi` dan `Monitor & Insiden`
- standalone operator entrypoints tetap didukung untuk debugging production-first:
  - `index.html`
  - `setup.html`
  - `products.html`
  - `performer.html`
  - `stream.html`
  - `monitor.html`

### Truth Model

Dashboard mengikuti truth model yang didefinisikan di:

- `docs/specs/dashboard_truth_model.md`

Setiap data surface diklasifikasikan sebagai: `mock`, `real_local`, `real_live`, `derived`, atau `unknown`.
Backend menyediakan `GET /api/runtime/truth` sebagai consolidated truth endpoint.

### Brain Runtime Control Plane

Control plane runtime live sekarang tidak lagi bertumpu pada variabel global privat di dashboard API.

- `src/orchestrator/show_director.py` menjadi state service persistent selama proses FastAPI hidup
- `src/brain/prompt_registry.py` menyimpan prompt revision aktif yang versioned di SQLite
- `src/brain/persona.py` sekarang berperan sebagai composer yang membaca prompt aktif dari registry
- `GET /api/director/runtime` menjadi kontrak agregat untuk `director`, `brain`, `prompt`, `persona`, dan `script`
- `GET /api/runtime/truth` juga membawa snapshot `director` agar shell operator melihat state runtime yang sama dengan backend

Konsekuensinya:

- state `stream`, `emergency`, dan `pipeline` tidak lagi boleh diverifikasi dari browser state lokal
- prompt aktif, provider aktif, dan fase show aktif bisa dibaca langsung dari UI operator
- pengembangan berikutnya untuk draft/publish prompt dan override director tinggal menambah mutation endpoints di atas contract ini

### Layout Shell

Shell dashboard operator sekarang mengikuti aturan layout berikut:

- sidebar punya lebar tetap dan sticky, sehingga tidak ikut bergeser saat halaman panjang atau saat viewport berubah
- content memakai centered frame dengan max-width yang konsisten
- pada viewport sempit sidebar mengerut ke mode ikon, tetapi kolom sidebar tetap stabil
- `scrollbar-gutter: stable` dipakai untuk mengurangi layout shift antar halaman

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
- untuk command LiveTalking langsung di luar `manage.py`, gunakan `uv run --extra livetalking ...`
- jangan gunakan conda
- jangan jadikan environment Windows-specific sebagai sumber kebenaran

### Command resmi

```bash
uv sync --extra dev
uv run python scripts/manage.py setup all
uv run python scripts/manage.py setup fish-speech
uv run python scripts/manage.py start fish-speech
uv run python scripts/manage.py start livetalking --mode musetalk
uv run python scripts/manage.py status all
uv run python scripts/manage.py open performer
uv run python scripts/manage.py open monitor
uv run pytest tests -q -p no:cacheprovider
uv run python scripts/verify_pipeline.py --verbose
uv run python scripts/manage.py serve --mock
uv run python scripts/manage.py serve --real
```

### Operator CLI policy

`scripts/manage.py` adalah single source of truth untuk:

- `setup`
- `start`
- `stop`
- `status`
- `validate`
- `open`

`scripts/menu.bat` hanyalah wrapper Windows tipis. Batch root lama bukan lagi sumber kebenaran.

Untuk Fish-Speech:

- checkout dipin ke line `v1.5.1`
- checkpoint acceptance disimpan di `external/fish-speech/checkpoints/fish-speech-1.5/`
- sidecar tidak boleh diinstall ke `.venv` control plane
- sidecar wajib memakai env UV terpisah di `external/fish-speech/runtime/.venv/`

## Active Milestones

### Face: `LOCAL_VERTICAL_SLICE_REAL_MUSETALK` — `LOCAL VERIFIED`

See `docs/specs/local_vertical_slice_real_musetalk.md`

- Active face runtime: **MuseTalk** (only acceptance path)
- Secondary fallback only: **Wav2Lip** (not counted as milestone pass)
- Target only / not in active path: `GFPGAN`, `ER-NeRF`

Current local verdict: **complete for the local vertical slice**. Official operator evidence now resolves to `musetalk / musetalk_avatar1` without fallback.

### Audio: `LOCAL_AUDIO_VERTICAL_SLICE_FISH_SPEECH` — `LOCAL VERIFIED`

See `docs/specs/local_audio_vertical_slice_fish_speech.md`

- Active voice runtime: **Fish-Speech** via local sidecar API (only acceptance path)
- Emergency fallback only: **Edge TTS** (does NOT count as acceptance pass)
- Voice clone assets required: `assets/voice/reference.wav` + `assets/voice/reference.txt`
- Runtime truth must expose requested/resolved voice engine with fallback visibility
- `voice_runtime_mode` stays `unknown` until the engine is actually resolved by a real synthesis
- Current local caveat: the direct-test slice now resolves `fish_speech_local` without fallback, but observed smoke latency on the current GTX 1650 setup is still around `20.9s`

## Status Saat Ini

### Sudah ada

- FastAPI control plane
- dashboard API + Svelte operator UI
- diagnostic endpoints
- SQLite
- LiteLLM router
- RTMP manager baseline
- LiveTalking vendor repo
- batch scripts dan manage.py CLI
- MuseTalk model weights in vendor path
- canonical MuseTalk avatar in vendor path
- local non-mock operator slice verified with MuseTalk resolved runtime
- Real product data source
- Real reference media

### Belum selesai

- latency reduction / chunking discipline for the now-working Fish-Speech direct-test path
- humanization layer di atas output MuseTalk
- reliability layer untuk penggunaan panjang
- validasi GPU host Ubuntu untuk real live run

## Dokumen Terkait

- `docs/README.md`
- `docs/decisions/architecture_internal_live.md`
- `docs/audits/AUDIT_CONTEXT_2026-03-07.md`
- `docs/plans/2026-03-07-unified-dashboard-livetalking-plan.md`
- `docs/guides/LIVETALKING_WEB_ACCESS_ID.md`
- `docs/guides/LIVETALKING_QUICKSTART.md`
