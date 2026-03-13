# Panduan Akses LiveTalking Web

> Status: Debug guide  
> Scope: `videoliveai/external/livetalking/web`  
> Audience: Operator internal dan developer

## Tujuan Dokumen

Folder `external/livetalking/web` berisi halaman web bawaan vendor LiveTalking.  
Halaman-halaman ini **bukan dashboard utama proyek**. Fungsinya adalah:

- debug engine vendor
- test preview WebRTC
- test pengiriman text langsung ke engine
- isolasi masalah apakah error ada di vendor engine atau di `videoliveai`

Dashboard utama tetap:

```text
http://localhost:8001/dashboard
```

Debug pages vendor biasanya berada di:

```text
http://localhost:8010/
```

## Aturan Pakai

- Gunakan `/dashboard` untuk operasional normal
- Gunakan halaman di `localhost:8010` hanya untuk debug
- Jangan jadikan halaman vendor sebagai source of truth sistem
- Jangan tambah logic operator utama ke dalam halaman vendor

## Peta Halaman Vendor

| File | Akses | Fungsi |
|------|-------|--------|
| `dashboard.html` | `http://localhost:8010/dashboard.html` | Panel interaksi vendor LiveTalking |
| `webrtcapi.html` | `http://localhost:8010/webrtcapi.html` | Test WebRTC + kirim text ke avatar |
| `webrtcapi-custom.html` | `http://localhost:8010/webrtcapi-custom.html` | Variasi test WebRTC custom |
| `webrtcapi-asr.html` | `http://localhost:8010/webrtcapi-asr.html` | Test WebRTC dengan alur ASR |
| `webrtc.html` | `http://localhost:8010/webrtc.html` | Preview WebRTC dasar |
| `webrtcchat.html` | `http://localhost:8010/webrtcchat.html` | Test chat dengan WebRTC |
| `rtcpushapi.html` | `http://localhost:8010/rtcpushapi.html` | Test push mode berbasis RTC |
| `rtcpushapi-asr.html` | `http://localhost:8010/rtcpushapi-asr.html` | Test RTC push + ASR |
| `rtcpushchat.html` | `http://localhost:8010/rtcpushchat.html` | Test chat pada mode RTC push |
| `rtcpush.html` | `http://localhost:8010/rtcpush.html` | Preview dasar mode RTC push |
| `chat.html` | `http://localhost:8010/chat.html` | Uji alur chat vendor |
| `echo.html` | `http://localhost:8010/echo.html` | Uji halaman echo sederhana |
| `echoapi.html` | `http://localhost:8010/echoapi.html` | Uji endpoint echo API |
| `asr/index.html` | `http://localhost:8010/asr/index.html` | Halaman pengujian speech recognition |

## Terjemahan Fungsi Halaman Penting

### `dashboard.html`

Judul asli:

```text
livetalking数字人交互平台
```

Makna Bahasa Indonesia:

```text
Platform Interaksi Avatar Digital LiveTalking
```

Peran:
- halaman debug vendor yang paling lengkap
- cocok untuk melihat apakah engine vendor hidup
- bukan dashboard operator proyek

### `webrtcapi.html`

Fungsi:
- membuka preview audio/video avatar
- klik `Start`
- isi text
- kirim ke engine agar avatar berbicara

Ini adalah halaman paling penting untuk memastikan:
- WebRTC preview bekerja
- engine menerima input text
- avatar bisa merespons secara langsung

### `rtcpushapi.html`

Fungsi:
- menguji mode push output vendor
- berguna saat memeriksa jalur transport selain preview biasa

### `asr/index.html`

Judul asli:

```text
语音识别
```

Terjemahan Bahasa Indonesia:

```text
Pengenalan Suara
```

Fungsi:
- test speech recognition vendor
- bukan bagian dashboard utama proyek

## Urutan Debug yang Disarankan

Jika engine tidak jelas bermasalah di mana, urutan debug paling aman:

1. Buka `http://localhost:8001/dashboard`
2. Cek readiness dan health di dashboard utama
3. Jika engine dicurigai bermasalah, buka:

```text
http://localhost:8010/webrtcapi.html
```

4. Klik `Start`
5. Masukkan text pendek, misalnya:

```text
Halo, ini test avatar.
```

6. Jika vendor page berhasil tapi dashboard utama gagal:
   - masalah ada di bridge/control plane `videoliveai`
7. Jika vendor page juga gagal:
   - masalah ada di engine, model, port, dependency, atau asset

## Mana yang Dipakai Untuk Apa

| Kebutuhan | Halaman yang dipakai |
|-----------|----------------------|
| Operasional normal | `/dashboard` |
| Validasi sistem menyeluruh | `/dashboard` + `/diagnostic` |
| Test engine vendor langsung | `webrtcapi.html` |
| Test preview vendor dasar | `webrtc.html` |
| Test speech recognition vendor | `asr/index.html` |

## Catatan Penting

- Banyak teks di halaman vendor masih bahasa China atau generik
- Itu normal karena halaman tersebut berasal dari repo vendor
- Untuk fase internal sekarang, lebih aman **tidak menerjemahkan file vendor satu per satu**
- Yang diterjemahkan dan dijadikan pegangan operator adalah **panduan aksesnya**, bukan vendor code

## Rekomendasi Praktis

- Simpan halaman vendor apa adanya untuk memudahkan update upstream
- Letakkan semua logika operator dan validasi sistem di dashboard proyek sendiri
- Gunakan panduan ini sebagai jembatan Bahasa Indonesia untuk tim internal
