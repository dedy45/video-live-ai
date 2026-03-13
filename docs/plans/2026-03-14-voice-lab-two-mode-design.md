# Voice Lab Two-Mode Design

## Goal

Membuat tab `Suara` menjadi `Voice Lab` penuh untuk operasi harian dengan dua mode yang jelas:

- `Standalone Fish TTS`
- `Attach ke Avatar/MuseTalk`

Target day-1:

- Fish-Speech bisa diuji langsung dari web tanpa avatar hidup
- operator bisa memilih clone/profile suara
- operator bisa generate audio dari prompt teks langsung di web
- hasil audio bisa dipreview dari browser
- mode attach bisa mengirim audio hasil generate ke sesi avatar aktif
- dashboard tetap menjadi single source of truth untuk state operator

## Scope Day-1

### In scope

- profile suara durable di SQLite
- state workspace suara durable di SQLite
- generation history durable di SQLite
- browser preview audio hasil generate
- handoff audio ke LiveTalking lewat endpoint vendor `/humanaudio`
- mode `standalone` dan `attach_avatar` di UI
- prompt teks manual dari web

### Out of scope

- training voice clone baru di server
- waveform editor
- multi-user slots
- autoplay sinkron penuh dengan TikTok LIVE Studio
- scheduler voice batch

## Architecture

### Source of truth

`dashboard/FastAPI + SQLite` menjadi owner untuk:

- profile suara
- mode voice lab aktif
- profile aktif
- avatar attach session yang aktif
- riwayat generate audio

`voice runtime state` tetap dipakai untuk telemetry cepat, tetapi tidak menjadi source of truth untuk profile/generation history.

### Output model

Voice engine tetap satu jalur utama: `Fish-Speech`.

Mode hanya menentukan tujuan output:

- `standalone`: generate audio lalu simpan + preview
- `attach_avatar`: generate audio lalu simpan + kirim ke sesi LiveTalking aktif

### Avatar attach contract

Attach day-1 memakai kontrak vendor yang memang ada:

- browser preview vendor membuat `sessionid`
- dashboard menyimpan `preview_session_id`
- backend mengirim hasil WAV ke `POST /humanaudio` pada LiveTalking

Ini membuat attach menjadi nyata, bukan sekadar status palsu.

## Data Model

### `voice_profiles`

- `id`
- `name`
- `engine`
- `reference_wav_path`
- `reference_text`
- `language`
- `notes`
- `is_active`
- `created_at`
- `updated_at`

### `voice_lab_state`

Satu row aktif untuk host lokal:

- `id=1`
- `mode`
- `active_profile_id`
- `preview_session_id`
- `selected_avatar_id`
- `draft_text`
- `last_generation_id`
- `updated_at`

### `voice_generations`

- `id`
- `mode`
- `profile_id`
- `source_type`
- `input_text`
- `emotion`
- `speed`
- `status`
- `audio_path`
- `audio_size_bytes`
- `latency_ms`
- `duration_ms`
- `attached_to_avatar`
- `avatar_session_id`
- `created_at`

## Backend API

### Profiles

- `GET /api/voice/profiles`
- `POST /api/voice/profiles`
- `PUT /api/voice/profiles/{id}`
- `DELETE /api/voice/profiles/{id}`
- `POST /api/voice/profiles/{id}/activate`

### Voice Lab State

- `GET /api/voice/lab`
- `PUT /api/voice/lab`

### Generation

- `POST /api/voice/generate`
- `GET /api/voice/generations`
- `GET /api/voice/generations/{id}`
- `GET /api/voice/audio/{id}`

### Validation / attach helpers

- `POST /api/voice/lab/preview-session`

## Frontend UX

Tab `Suara` dipecah menjadi:

- mode switch
- profile manager
- generator console
- result player + history
- telemetry
- attach status

Operator harus selalu tahu:

- Fish hidup atau tidak
- profile aktif yang dipakai
- mode output aktif
- audio terbaru tersimpan atau gagal
- attach benar-benar terkirim atau tertahan

## Error Handling

- generate `standalone` tidak boleh bergantung pada avatar
- generate `attach_avatar` harus fail jelas bila:
  - avatar belum running
  - preview session belum ada
  - LiveTalking reject upload
- audio yang gagal attach tetap disimpan sebagai generation history
- semua aksi menghasilkan operator receipt

## Testing Strategy

### Backend

- store round-trip untuk profile, lab state, generation
- API CRUD profile
- API update/get voice lab state
- generate standalone menghasilkan metadata + audio file
- generate attach mengirim WAV ke endpoint avatar bila session aktif
- attach gagal bila session/avatar tidak siap

### Frontend

- voice panel mode switch
- profile create/activate
- generate standalone
- generate attach
- history/result rendering

### Browser

- tab `Suara` bisa generate audio
- hasil audio muncul sebagai player
- mode attach menampilkan state session attach

