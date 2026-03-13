# LiveTalking Browser Preview Activation Design

**Date:** 2026-03-13

**Goal**

Mengaktifkan `http://localhost:8010/webrtcapi.html` dan `http://localhost:8010/rtcpushapi.html` sebagai jalur preview browser yang benar-benar hidup untuk video avatar + audio, dengan dashboard tetap menjadi source of truth untuk status engine dan langkah operator.

## Problem Statement

Gejala yang terlihat di dashboard saat ini:

- tab Preview menandai target vendor tidak terjangkau
- `http://127.0.0.1:8010/webrtcapi.html` dan `http://127.0.0.1:8010/rtcpushapi.html` tidak aktif
- dashboard bisa menampilkan status avatar menerima perintah jalan, tetapi proses vendor nyata tidak hidup

Root cause yang sudah diverifikasi:

- pada `MOCK_MODE=true`, `LiveTalkingManager.start()` hanya menandai state `running` tanpa menyalakan sidecar vendor
- saat dijalankan real, sidecar `external/livetalking/app.py` crash cepat dengan `ModuleNotFoundError: No module named 'torch._namedtensor_internals'`
- dashboard Preview gagal karena `8010` memang tidak hidup, bukan karena komponen embed browser rusak

## Constraints

- dashboard `videoliveai` tetap menjadi source of truth operasional
- vendor LiveTalking tetap diperlakukan sebagai sidecar media engine
- implementasi harus jujur: tidak boleh melaporkan preview sehat jika proses vendor tidak benar-benar hidup
- target fase ini adalah preview browser operator untuk `TikTok LIVE Studio` desktop capture, bukan otomasi penuh TikTok Studio

## Desired Outcome

Setelah implementasi:

- operator bisa start engine dari dashboard atau API
- sidecar boot stabil di port `8010`
- `webrtcapi.html` dapat dibuka dan melakukan negosiasi WebRTC
- browser menerima track `video` dan `audio`
- `rtcpushapi.html` juga reachable dan aktif sebagai debug surface untuk transport `rtcpush`
- dashboard Preview menampilkan status yang sesuai dengan kondisi runtime nyata

## Architecture

### 1. Sidecar Startup Must Be Real

`LiveTalkingManager` harus berhenti menganggap state `running` sebagai sinyal sukses. Sukses start hanya sah jika:

- subprocess vendor masih hidup setelah startup window
- port `8010` benar-benar membuka listener HTTP
- target debug page dapat merespons

Jika proses mati cepat, API harus mengembalikan error yang menyebut akar gagal startup.

### 2. Environment Boundary Must Be Explicit

Sidecar vendor tidak boleh bergantung diam-diam pada env Python utama jika dependency torch/media stack-nya berbeda atau rusak. Manager harus:

- memilih interpreter yang valid untuk sidecar
- menyimpan log startup ringkas
- menampilkan detail environment/runtime yang dipakai untuk boot vendor

### 3. Transport Surfaces Must Be Honest

`webrtcapi.html` dan `rtcpushapi.html` bukan sekadar link statis. Dashboard harus bisa membedakan tiga keadaan:

- process vendor belum jalan
- process hidup tetapi halaman debug belum reachable
- halaman reachable tetapi sesi media belum dimulai

### 4. Dashboard Role

Dashboard tidak akan menggantikan halaman vendor pada fase ini. Dashboard berperan sebagai:

- controller start/stop engine
- source of truth status
- prober reachability preview
- pemberi instruksi operator untuk membuka vendor page dan mulai sesi media

Vendor page tetap dipakai untuk negosiasi WebRTC / RTC push dan uji media langsung.

## Implementation Scope

### In Scope

- fix startup environment LiveTalking
- hardening `LiveTalkingManager`
- hardening API `/api/engine/livetalking/*`
- validasi browser `webrtcapi.html`
- validasi browser `rtcpushapi.html`
- update dokumentasi operasi lokal Windows/TikTok LIVE Studio

### Out of Scope

- otomatis klik tombol di TikTok LIVE Studio
- ingest komentar TikTok real-time
- production RTMP publish ke TikTok real
- full custom preview page replacement di dashboard

## Risks

- vendor dependency stack berat dan sensitif terhadap versi torch/CUDA
- `rtcpushapi.html` kemungkinan butuh service push target tambahan tergantung jalur vendor
- audio dapat hidup di browser vendor tetapi tetap butuh routing berbeda saat nanti ditangkap oleh TikTok LIVE Studio

## Acceptance Criteria

- `POST /api/engine/livetalking/start` gagal jujur bila startup vendor gagal
- `GET /api/engine/livetalking/debug-targets` menunjukkan target `webrtcapi` reachable saat engine hidup
- `http://localhost:8010/webrtcapi.html` load tanpa console error fatal
- negosiasi WebRTC berhasil dan elemen media menerima track audio/video
- `http://localhost:8010/rtcpushapi.html` reachable pada transport `rtcpush`
- dokumentasi operator menjelaskan langkah tes lokal Windows secara eksplisit
