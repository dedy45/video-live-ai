# Avatar & Suara Recovery Plan

## Status

- Status: `IMPLEMENTED`
- Tanggal verifikasi: `2026-03-11`
- Hasil verifikasi:
  - `npm run test -- src/tests/performer-page.test.ts src/tests/action-receipt.test.ts src/tests/performer-preview-panel.test.ts src/tests/performer-validation-panel.test.ts src/tests/api.test.ts` -> `18 passed`
  - `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "livetalking_start_api_returns_operator_receipt_fields or livetalking_stop_api_returns_operator_receipt_fields or livetalking_debug_targets_reports_reachability"` -> `3 passed`
  - `npm run build` -> `PASS`
  - `npm run test:e2e -- e2e/dashboard.spec.ts` -> `13 passed`

## Summary
Pulihkan `Avatar & Suara` tanpa mengubah sidebar utama: tetap satu menu `#/performer`, tetapi di dalamnya menjadi workspace bertab dengan 6 tab operator.

Tab yang akan ada:
- `Ringkasan`
- `Suara`
- `Avatar`
- `Preview`
- `Validasi`
- `Teknis`

Target utama:
- mengembalikan permukaan detail yang hilang dari versi sebelumnya,
- membuat aksi tombol benar-benar sinkron dengan state UI tanpa perlu `Refresh Truth` manual,
- menambahkan error handling operator-first yang jelas,
- memvalidasi semuanya lagi di browser pada `/dashboard` dan `/dashboard/performer.html`.

## Masalah Yang Sudah Terkonfirmasi
1. `Avatar & Suara` saat ini merangkum terlalu banyak hal ke satu `PerformerPanel`, sementara `VoicePanel` dan `EnginePanel` yang lebih lengkap masih ada tetapi tidak dipakai di halaman utama.
2. `Start Face Engine` reproducibly mengembalikan receipt sukses (`state running`), tetapi kartu `Wajah` dan `Preview` tetap stale sampai operator menekan `Refresh Truth` manual.
3. Link preview vendor di `localhost:8010` ditampilkan sebagai normal walau endpoint benar-benar mati.
4. Copy UI bercampur Indonesia/Inggris dan terlalu teknis untuk operator: `Warm Voice`, `Refresh Truth`, `engine.start`, `Loaded`, dan receipt monospace berbasis action id.
5. Coverage test saat ini lolos karena belum menguji sinkronisasi state pasca-aksi, reachability preview, dan kelengkapan menu di browser.

## Desain Implementasi
### 1. Ubah `PerformerPage` menjadi workspace bertab
- `src/dashboard/frontend/src/pages/PerformerPage.svelte` menjadi shell halaman saja.
- Buat parent stateful baru, misalnya `src/dashboard/frontend/src/components/panels/PerformerWorkspace.svelte`, yang memegang seluruh data, tab aktif, receipt, action state, dan refresh orchestration.
- `PerformerPanel.svelte` tidak lagi menjadi cockpit monolitik; ubah menjadi wrapper ke `PerformerWorkspace` atau hapus setelah referensi dipindah.
- `AvatarPanel.svelte` tidak lagi menjadi alias ke `PerformerPanel`; jadikan wrapper tipis untuk tab Avatar atau hapus jika tidak dipakai.

Tab implementation:
- `Ringkasan`: snapshot operator, CTA utama, status suara/avatar, warning kritis, dan last action.
- `Suara`: refactor dari `VoicePanel.svelte`.
- `Avatar`: refactor dari `EnginePanel.svelte`.
- `Preview`: panel baru untuk embedded preview + fallback.
- `Validasi`: panel baru untuk seluruh validasi avatar/suara.
- `Teknis`: panel baru untuk log engine, path readiness, vendor links, raw truth ringkas.

### 2. Sentralisasi data dan aksi supaya state tidak pecah
- Jangan biarkan `VoicePanel`, `EnginePanel`, dan tab lain melakukan fetch sendiri-sendiri.
- Parent workspace melakukan:
  - bootstrap data,
  - refresh runtime truth,
  - refresh readiness,
  - refresh engine status/config/logs,
  - orchestration seluruh aksi operator.
- Refactor child panel menjadi presentational components yang menerima props + callbacks.
- Gunakan `bootstrapRuntimeSnapshot()` dari `src/dashboard/frontend/src/lib/runtime-client.ts` untuk bootstrap awal agar sejalan dengan source of truth shell yang ada.

### 3. Perbaiki bug tombol dengan action reconciliation, bukan refresh sekali lalu selesai
Tambahkan helper baru, misalnya `src/dashboard/frontend/src/lib/performer-actions.ts`, untuk semua aksi suara/avatar.

Alur standar setiap aksi:
1. Kirim request aksi.
2. Tampilkan receipt `pending` atau `success` awal.
3. Poll `getRuntimeTruth()` dan, jika perlu, `getLiveTalkingStatus()` sampai state target benar-benar cocok.
4. Jika sinkron dalam batas waktu, update receipt ke `confirmed`.
5. Jika tidak sinkron, ubah receipt ke `warning` dengan pesan operator:
   - aksi diterima,
   - status dashboard belum sinkron,
   - langkah berikutnya yang harus dilakukan.
6. Jika request gagal, tampilkan `error` dengan penyebab dan next step.

Default reconciliation:
- interval `500 ms`
- timeout `5 s`
- untuk `start/stop engine`, truth target adalah `face_engine.engine_state`
- untuk aksi suara, truth target memakai field yang relevan (`server_reachable`, `queue_depth`, `last_error`) bila memang berubah; jika tidak ada truth mutation, cukup receipt eksplisit yang menyatakan aksi administratif saja

### 4. Pulihkan menu lengkap memakai panel lama yang memang masih ada
- `VoicePanel.svelte` dijadikan tab `Suara`, tetapi dirombak ke copy operator Indonesia dan menerima props dari parent.
- `EnginePanel.svelte` dijadikan tab `Avatar`, bukan dibiarkan sebagai panel yatim.
- Konten yang harus ada kembali:
  - kontrol start/stop avatar,
  - status model/avatar/runtime,
  - kontrol suara,
  - test speak,
  - validasi terkait,
  - vendor/debug surfaces,
  - log/path readiness.

### 5. Tambahkan tab `Preview` dengan embed + fallback
Buat panel baru, misalnya `src/dashboard/frontend/src/components/panels/PerformerPreviewPanel.svelte`.

Perilaku:
- probe availability target preview/vendor lebih dulu,
- jika reachable: tampilkan embedded preview utama,
- jika tidak reachable: tampilkan fallback card informatif, bukan link mati.

Isi fallback wajib:
- target mana yang gagal,
- waktu pengecekan terakhir,
- error singkat yang bisa dipahami operator,
- tindakan berikutnya,
- tombol `Cek Lagi`,
- tombol `Buka Paksa di Tab Baru` sebagai escape hatch sekunder.

## Perubahan API / Interface / Types
### Backend
Augment, bukan mengganti total, endpoint berikut di `src/dashboard/api.py`:
- `POST /api/engine/livetalking/start`
- `POST /api/engine/livetalking/stop`

Tambahkan field baru agar konsisten dengan aksi suara:
- `status`: `success | blocked | error`
- `action`
- `message`
- `reason_code`
- `details`
- `next_step`
- field lama seperti `state`, `port`, `transport`, dst tetap dipertahankan agar kompatibel

Tambahkan endpoint baru:
- `GET /api/engine/livetalking/debug-targets`

Response shape:
- `targets.webrtcapi.url`
- `targets.webrtcapi.reachable`
- `targets.webrtcapi.http_status`
- `targets.webrtcapi.error`
- pola yang sama untuk `dashboard_vendor` dan `rtcpushapi`
- `checked_at`

Tidak perlu endpoint validasi agregat baru; tab `Validasi` akan memakai endpoint validasi yang sudah ada.

### Frontend types
Di `src/dashboard/frontend/src/lib/types.ts`:
- extend `OperatorActionStatus` menjadi:
  - `success`
  - `blocked`
  - `error`
  - `pending`
  - `warning`
- upgrade `OperatorActionResult` dengan:
  - `reason_code?: string`
  - `details?: string[]`
  - `next_step?: string`
- upgrade `ActionReceipt` dengan:
  - `title: string`
  - `message: string`
  - `status`
  - `timestamp`
  - `details?: string[]`
  - `nextStep?: string`
  - `action?: string` hanya sebagai internal trace, bukan copy utama

Di `src/dashboard/frontend/src/lib/api.ts`:
- tambah typed wrapper `getLiveTalkingDebugTargets()`
- update typing untuk `startLiveTalking()` dan `stopLiveTalking()` sesuai response baru

## Copy dan Error Handling
### Prinsip copy
- Permukaan utama full Bahasa Indonesia operator-first.
- Istilah teknis hanya sebagai detail sekunder.
- Jangan tampilkan raw action id sebagai teks utama.
- Jangan gunakan label generik seperti `Aksi engine wajah selesai`.

Contoh arah copy:
- `Warm Voice` -> `Panaskan Mesin Suara`
- `Refresh Truth` -> `Muat Ulang Status Langsung`
- `Start Face Engine` -> `Jalankan Avatar`
- `Loaded` -> `Siap`
- receipt `engine.start` -> `Avatar menerima perintah jalan`

### Receipt baru
Refactor `src/dashboard/frontend/src/components/common/ActionReceipt.svelte`:
- gaya visual operator, bukan monospace debug
- status badge jelas
- judul + pesan utama + next step
- detail teknis collapsible, bukan selalu tampak
- blocked/warning/error memakai alasan yang spesifik dan tindak lanjut

### Error surfaces yang wajib
- server unreachable
- validation fail
- preview target unreachable
- action accepted but truth not yet synchronized
- action succeeded but dependent system still unavailable
- missing reference asset / missing avatar / missing vendor process

## Tab Validasi
Buat `PerformerValidationPanel.svelte` untuk validasi penuh avatar/suara.

Check yang tampil dan bisa dijalankan dari tab ini:
- `validateLiveTalkingEngine`
- `validateVoiceLocalClone`
- `validateAudioChunkingSmoke`
- `validateRealModeReadiness`
- `validateRuntimeTruth`
- `preview target reachability` via endpoint baru

Tambahan:
- hasil terakhir per check
- timestamp
- status pass/fail/blocked/error
- shortcut ke `Setup & Validasi` untuk check yang sifatnya lintas-sistem di luar avatar/suara

Default yang dipilih:
- tab ini memuat validasi penuh untuk domain avatar/suara saja
- validasi stream dan system-wide tetap canonical di `Setup & Validasi`

## Tab Teknis
Buat `PerformerTechnicalPanel.svelte`.

Isi:
- status engine rinci
- path readiness
- vendor URLs
- log engine
- raw runtime truth ringkas
- freshness / checked-at markers

Tab ini menggantikan collapse bawah yang sekarang terlalu mudah tercampur dengan operasi harian.

## File Yang Perlu Disentuh
Frontend:
- `src/dashboard/frontend/src/pages/PerformerPage.svelte`
- `src/dashboard/frontend/src/components/panels/PerformerPanel.svelte`
- `src/dashboard/frontend/src/components/panels/VoicePanel.svelte`
- `src/dashboard/frontend/src/components/panels/EnginePanel.svelte`
- `src/dashboard/frontend/src/components/panels/AvatarPanel.svelte`
- `src/dashboard/frontend/src/components/common/ActionReceipt.svelte`
- `src/dashboard/frontend/src/lib/api.ts`
- `src/dashboard/frontend/src/lib/types.ts`
- `src/dashboard/frontend/src/lib/runtime-client.ts`
- new `src/dashboard/frontend/src/lib/performer-actions.ts`
- new `src/dashboard/frontend/src/components/panels/PerformerWorkspace.svelte`
- new `src/dashboard/frontend/src/components/panels/PerformerPreviewPanel.svelte`
- new `src/dashboard/frontend/src/components/panels/PerformerValidationPanel.svelte`
- new `src/dashboard/frontend/src/components/panels/PerformerTechnicalPanel.svelte`

Backend:
- `src/dashboard/api.py`
- optional helper file if preview probing is split out from router logic

Tests:
- `src/dashboard/frontend/src/tests/performer-page.test.ts`
- `src/dashboard/frontend/src/tests/performer-panel.test.ts`
- `src/dashboard/frontend/src/tests/voice-panel.test.ts`
- new `src/dashboard/frontend/src/tests/engine-panel.test.ts`
- new `src/dashboard/frontend/src/tests/performer-preview-panel.test.ts`
- new `src/dashboard/frontend/src/tests/performer-validation-panel.test.ts`
- new `src/dashboard/frontend/src/tests/action-receipt.test.ts`
- `src/dashboard/frontend/e2e/dashboard.spec.ts`
- `tests/test_dashboard.py`

## Test Cases dan Scenario
### Unit / component
1. `PerformerPage` merender tab:
   - Ringkasan
   - Suara
   - Avatar
   - Preview
   - Validasi
   - Teknis
2. `ActionReceipt` menampilkan copy operator, next step, dan technical detail terlipat.
3. `VoicePanel` memakai label Indonesia dan tidak menampilkan raw action ids.
4. `EnginePanel` menampilkan pending state lalu confirmed state tanpa refresh manual.
5. `PreviewPanel` men-disable preview utama bila target tidak reachable dan menampilkan fallback message.
6. `ValidationPanel` menjalankan seluruh check avatar/suara dan merender hasil per check.

### Backend
1. `engine start/stop` response mengandung `status`, `message`, `action`, `reason_code`, dan field lama tetap ada.
2. `debug-targets` mengembalikan reachability per vendor URL.
3. response error tetap serializable dan informatif saat probe gagal.

### Browser / E2E
Jalankan dengan server mock:
- `MOCK_MODE=true`
- `DASHBOARD_PORT=8011`
- akses:
  - `/dashboard#/performer`
  - `/dashboard/performer.html`

Skenario wajib:
1. Klik `Jalankan Avatar` -> UI berubah ke pending lalu `Berjalan` tanpa menekan refresh manual.
2. Klik `Hentikan Avatar` -> UI kembali `Berhenti` tanpa refresh manual.
3. Klik `Panaskan Mesin Suara` saat sidecar down -> status `blocked` dengan pesan operator dan langkah berikutnya.
4. Klik `Tes Suara` -> telemetry tampil dan receipt mudah dipahami.
5. Saat `8010` tidak reachable -> tab `Preview` menampilkan fallback card, bukan sekadar link mati.
6. Semua tab di `Avatar & Suara` bisa diakses dari dashboard shell dan dari standalone `performer.html`.
7. Smoke navigation semua surface utama:
   - setup
   - products
   - performer
   - stream
   - live console
   - monitor

## Acceptance Criteria
- `Avatar & Suara` kembali punya menu lengkap di dalam satu halaman, bukan satu cockpit panjang.
- Tidak ada aksi suara/avatar yang membutuhkan `Refresh Truth` manual agar status utama ikut berubah.
- Preview tidak pernah tampil sebagai link “normal” saat target tidak reachable.
- Receipt aksi tidak lagi menampilkan jargon mentah sebagai copy utama.
- Semua label utama operator konsisten dalam Bahasa Indonesia.
- Browser validation lulus untuk dashboard shell dan standalone performer page.

## Assumptions dan Default Yang Dipilih
- Sidebar tetap 6 menu; tidak mengembalikan route `Voice` dan `Face Engine` terpisah.
- Tidak ada persistence tab di localStorage/sessionStorage; tab default selalu `Ringkasan`.
- `Validasi` di halaman ini berarti validasi penuh untuk domain avatar/suara, bukan duplikasi seluruh Setup system-wide.
- Preview embed hanya aktif bila probe availability lolos; fallback card selalu tersedia.
- Validasi browser utama dilakukan di mock mode lokal karena deterministik; real mode hanya tambahan jika sidecar tersedia.
