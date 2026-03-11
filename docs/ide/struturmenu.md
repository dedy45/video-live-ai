## Audit UX Lengkap: 7 Menu Dashboard — Masalah & Restruktur

### MASALAH UTAMA: Tata Letak Membingungkan

Setelah memeriksa seluruh 7 menu, berikut masalah inti kenapa membingungkan:

***

### AUDIT PER MENU

**1. Konsol Live** [127.0.0](http://127.0.0.1:8181/dashboard/#/)
- **Masalah:** Terlalu banyak section placeholder ("akan datang di fase berikutnya") — Panduan Skrip, Aksi Berikutnya, Aksi Cepat semua inactive. Halaman terasa kosong dan tidak actionable
- **Masalah:** "Ringkasan Operasional" di bawah menampilkan 6 card kecil yang informasinya overlap dengan status bar di atas (Deploy, Face, Voice, Stream sudah ada di top bar)
- **Masalah:** Tidak jelas ini "home" atau "control room" — tidak ada tombol utama yang jelas

**2. Produk** [127.0.0](http://127.0.0.1:8181/dashboard/#/products)
- **Masalah:** Layout 2-column (Produk Aktif kiri vs Antrian kanan) membuang space besar — Produk Aktif area kiri setengah page kosong (tidak ada link affiliate, poin penjualan kosong, komisi 0%)
- **Masalah:** Tidak ada cara edit produk langsung, tidak ada tombol tambah produk
- **Masalah:** Setiap produk di antrian hanya "Ganti" — tidak ada info apa yang akan terjadi setelah ganti

**3. Performer** [127.0.0](http://127.0.0.1:8181/dashboard/#/performer)
- **Masalah TERBESAR:** Halaman ini **terlalu panjang dan campur aduk**. Scroll 3 viewport penuh. Berisi: Cockpit Performer, Kontrol Utama, Kesiapan Produksi, Launchpad Preview, Runtime Suara, Engine State, Status Fallback, Face Model, Status Suara, Kontrol Operator, Transport/Uptime, Model/Avatar Resolution, Path Readiness, Pengujian Suara, Tes Suara Inline, Vendor Debug Links, Engine Logs, Preview & Debug
- **Masalah:** Mixing antara **operator controls** (Start/Stop, Warm Voice) dan **developer debug** (Engine Logs, Path Readiness, Vendor Debug Links) di satu halaman
- **Masalah:** Operator harian tidak perlu lihat engine logs dan path readiness — itu untuk developer

**4. Streaming** [127.0.0](http://127.0.0.1:8181/dashboard/#/stream)
- **Masalah:** RTMP Configuration di-hide (tombol "Show") — padahal ini info paling penting di halaman ini
- **Masalah:** Pipeline State Machine (IDLE/WARMING/LIVE/COOLDOWN) ditampilkan sebagai 4 tombol biasa — seharusnya visual stepper/timeline yang menunjukkan state saat ini
- **Masalah:** Tidak ada tempat input stream key baru, tidak ada platform selector

**5. Validasi** [127.0.0](http://127.0.0.1:8181/dashboard/#/validation)
- **Relatif baik.** 13 readiness checks jelas dengan OK/WARNING. Validation Gate Center dengan Run Check per kategori sudah terstruktur
- **Masalah minor:** History di bawah tidak punya filter/search

**6. Monitor** [127.0.0](http://127.0.0.1:8181/dashboard/#/monitor)
- **Masalah:** Terlalu minimalis — 4 card (Component Health, Resource Pressure, Recent Incidents, Recent Chat) dengan data minimal/kosong
- **Masalah:** Component Health sebelumnya menampilkan data, sekarang "No component health data" — tidak konsisten
- **Masalah:** Tidak ada grafik/chart — hanya angka statis. Untuk monitoring 12 jam, perlu trend line

**7. Diagnostik** [127.0.0](http://127.0.0.1:8181/dashboard/#/diagnostics)
- **Masalah:** Halaman kosong — "Loading diagnostics..." dan tidak pernah load. Non-functional

***

### MASALAH STRUKTURAL GLOBAL

| Masalah | Dampak |
|---------|--------|
| **Tidak ada workflow sequence** — menu di sidebar tidak mencerminkan urutan operasi live | Operator bingung mulai dari mana |
| **Duplikasi informasi** — status bar atas, Konsol Live, Monitor, Performer semua tampilkan status yang sama | Membingungkan mana source of truth |
| **Developer debug campur operator controls** — Performer paling parah | Operator ketakutan lihat engine logs |
| **Placeholder "akan datang" terlalu banyak** — Konsol Live, Performer Preview | Dashboard terasa belum jadi |
| **Tidak ada visual hierarchy** — semua card size sama, tidak ada yang menonjol | Tidak tahu mana yang urgent |

***

### SARAN RESTRUKTUR: SIDEBAR BERDASARKAN WORKFLOW

Ubah urutan sidebar mengikuti **alur operasional live streaming**, bukan urutan teknis:

```
SEBELUM (sekarang):          SESUDAH (saran):
──────────────────           ──────────────────
1. Konsol Live               ━━ PERSIAPAN ━━
2. Produk                    1. 🔧 Setup
3. Performer                    (gabung: Validasi + Diagnostik)
4. Streaming                 2. 📦 Produk
5. Validasi                  3. 🎭 Avatar & Suara
6. Monitor                      (Performer, dipangkas)
7. Diagnostik                
                             ━━ OPERASI ━━
                             4. 📡 Streaming
                                (RTMP + Platform config)
                             5. 📺 Konsol Live
                                (command center saat live)
                             
                             ━━ PENGAWASAN ━━
                             6. 📊 Monitor
                                (gabung: Monitor + resource)
```

**Dari 7 menu → 6 menu**, tapi setiap menu lebih fokus dan mengikuti alur.

***

### DETAIL RESTRUKTUR PER MENU

#### Menu 1: 🔧 SETUP (Gabung Validasi + Diagnostik)

**Kenapa digabung:** Validasi dan Diagnostik keduanya soal "apakah sistem siap" — operator tidak perlu 2 halaman terpisah untuk ini. Diagnostik saat ini bahkan non-functional.

```
┌── SETUP ─────────────────────────────────────────────┐
│                                                       │
│  SYSTEM READINESS          [Run All Checks] [Refresh] │
│  ┌──────────────────────────────────────────────────┐ │
│  │ ● Config        OK   │ ● Database    OK          │ │
│  │ ● LiveTalking   OK   │ ● Avatar      OK          │ │
│  │ ● Models        OK   │ ● FFmpeg      OK          │ │
│  │ ● RTMP Target   OK   │ ● Voice Ref   OK          │ │
│  │ ○ Fish-Speech   WARN │ ● Mode        OK          │ │
│  └──────────────────────────────────────────────────┘ │
│                                                       │
│  Overall: DEGRADED — Fix: start Fish-Speech sidecar   │
│                                                       │
│  ENVIRONMENT                                          │
│  Host: DESKTOP-N1GGHD7 | Role: local_lab             │
│  GPU: GTX 1650 (4GB) | CUDA: OK                      │
│  Deploy Mode: cold | Origin: real_local               │
│                                                       │
│  ─── Validation Gates (collapsible) ───               │
│  [▶ Core Truth]  [▶ Real-Mode]  [▶ Voice]            │
│  [▶ Stream]  [▶ Resource]  [▶ Soak]                  │
│                                                       │
│  ─── Recent Check History ───                         │
│  (compact table)                                      │
└───────────────────────────────────────────────────────┘
```

**Prinsip:** Satu layar, operator langsung tahu sistem siap atau tidak. Detail check bisa di-expand kalau perlu.

***

#### Menu 2: 📦 PRODUK (Upgrade)

```
┌── PRODUK ────────────────────────────────────────────┐
│                                                       │
│  PRODUK AKTIF                          [Ganti ▼]     │
│  ┌────────────────────────────────────────────────┐  │
│  │  Kaos Oversize Premium Cotton                   │  │
│  │  Rp 89,000 | Komisi: 12% | Kategori: FASHION   │  │
│  │  Link TikTok: https://...  [Copy]               │  │
│  │  Link Shopee: https://...  [Copy]               │  │
│  │  Poin: "Bahan adem, oversize trendy, size S-XL" │  │
│  └────────────────────────────────────────────────┘  │
│                                                       │
│  ANTRIAN ROTASI              Timer: 12:45 tersisa     │
│  ┌──┬────────────────────┬────────┬──────┬────────┐  │
│  │# │ Nama               │ Harga  │Komisi│        │  │
│  ├──┼────────────────────┼────────┼──────┼────────┤  │
│  │1 │ Skincare Glow Set  │149,000 │ 15%  │[Aktif] │  │
│  │2 │ Wireless Earbuds   │249,000 │ 10%  │[Skip]  │  │
│  │3 │ Tas Selempang      │ 69,000 │  8%  │        │  │
│  └──┴────────────────────┴────────┴──────┴────────┘  │
│                                                       │
│  [+ Tambah Produk]  [Import CSV]  [Atur Rotasi]      │
└───────────────────────────────────────────────────────┘
```

**Perbaikan dari sekarang:**
- Produk Aktif area kiri yang kosong → dijadikan card penuh dengan SEMUA info (link affiliate, komisi, poin penjualan)
- Antrian jadi tabel compact, bukan list card besar-besar
- Timer rotasi otomatis
- Tombol tambah/import produk

***

#### Menu 3: 🎭 AVATAR & SUARA (Performer Dipangkas)

**Masalah sekarang:** Performer page 3 viewport panjang. Pangkas jadi 2 section bersih.

```
┌── AVATAR & SUARA ────────────────────────────────────┐
│                                                       │
│  ┌─ SUARA ──────────────┐ ┌─ WAJAH ────────────────┐│
│  │ Engine: fish_speech   │ │ Model: musetalk         ││
│  │ Status: ● READY / ○   │ │ Avatar: musetalk_avatar1││
│  │ Latency: 450ms        │ │ FPS: 25 | GPU: loaded   ││
│  │ Fallback: edge_tts    │ │ Status: ● RUNNING       ││
│  │                        │ │                          ││
│  │ [Warm Voice] [Test]   │ │ [Start] [Stop]           ││
│  └────────────────────────┘ └──────────────────────────┘│
│                                                       │
│  PREVIEW                                              │
│  ┌────────────────────────────────────────────────┐  │
│  │         (WebRTC preview embed)                  │  │
│  │         atau: [Open Preview Window]             │  │
│  └────────────────────────────────────────────────┘  │
│                                                       │
│  ─── Detail Teknis (collapsed by default) ──▶        │
│  (Engine logs, Path readiness, Vendor debug —         │
│   HIDDEN kecuali developer klik expand)               │
└───────────────────────────────────────────────────────┘
```

**Prinsip:** Operator lihat 2 card (Suara + Wajah) + Preview. Selesai. Detail teknis di-collapse, hanya developer yang buka.

***

#### Menu 4: 📡 STREAMING (Upgrade)

```
┌── STREAMING ─────────────────────────────────────────┐
│                                                       │
│  PIPELINE    ○ IDLE → ○ WARMING → ○ LIVE → ○ COOL   │
│              ▲ kamu di sini                           │
│                                                       │
│  ┌─ PLATFORM TARGET ────────────────────────────────┐│
│  │  Platform: TikTok ▼                               ││
│  │  RTMP URL:  rtmp://push.tiktok.com/... [Paste]    ││
│  │  Stream Key: ************************** [Paste]   ││
│  │  Key Age: 5 menit lalu | Status: ● Valid          ││
│  │                                                    ││
│  │  💡 Ambil key: HP → TikTok app → LIVE → Cast to PC││
│  └───────────────────────────────────────────────────┘│
│                                                       │
│  ┌─ KONTROL ──────────┐  ┌─ STREAM HEALTH ─────────┐│
│  │                      │  │ Bitrate: — kbps          ││
│  │  [▶ START STREAM]    │  │ Frame drop: 0%           ││
│  │  [■ STOP STREAM]     │  │ Uptime: —                ││
│  │  [⚠ EMERGENCY STOP]  │  │ Reconnects: 0            ││
│  └──────────────────────┘  └──────────────────────────┘│
│                                                       │
│  [Validate RTMP] [Dry Run]                            │
└───────────────────────────────────────────────────────┘
```

**Perbaikan:**
- RTMP Config **terbuka by default**, bukan di-hide
- Pipeline State Machine jadi visual stepper horizontal, bukan 4 tombol flat
- Tempat paste stream key jelas dan prominent
- Stream Health visible saat live

***

#### Menu 5: 📺 KONSOL LIVE (Redesign Total)

Ini menu yang paling sering dilihat saat live. Harus jadi **command center sesungguhnya**.

```
┌── KONSOL LIVE ───────────────────────────────────────┐
│                                                       │
│  ● LIVE 2h 15m    TikTok    142 viewers               │
│                                                       │
│  ┌─ PRODUK AKTIF ──────┐ ┌─ AVATAR ──────────────┐  │
│  │ Kaos Oversize Cotton │ │  [Preview thumbnail]   │  │
│  │ Rp 
## Lanjutan: Restruktur Menu 5, 6 + Ringkasan Final

***

### Menu 5: 📺 KONSOL LIVE (Redesign Total)

Menu ini paling sering dilihat saat live. Harus jadi **command center sesungguhnya**, bukan halaman placeholder.

```
┌── KONSOL LIVE ───────────────────────────────────────┐
│                                                       │
│  ● LIVE 2h 15m    TikTok    142 viewers               │
│                                                       │
│  ┌─ PRODUK AKTIF ──────┐ ┌─ AVATAR STATUS ─────────┐│
│  │ Kaos Oversize Cotton │ │  Suara: ● ready          ││
│  │ Rp 89,000 | 12%     │ │  Wajah: ● running        ││
│  │ Link: [Copy]         │ │  Stream: ● live          ││
│  │ Sisa rotasi: 8:45   │ │  Latency: 420ms          ││
│  │                      │ │                           ││
│  │ [Ganti Produk ▼]    │ │  [Preview Window]         ││
│  └──────────────────────┘ └───────────────────────────┘│
│                                                       │
│  ┌─ SKRIP PANDUAN ─────────────────────────────────┐ │
│  │ "Hai kak, ini Kaos Oversize yang lagi hits      │ │
│  │  banget! Bahannya cotton premium, adem banget.  │ │
│  │  Size ada dari S sampai XL. Harga cuma 89 ribu  │ │
│  │  kak, langsung cek keranjang kuning ya!"        │ │
│  │                                        [Refresh]│ │
│  └──────────────────────────────────────────────────┘ │
│                                                       │
│  ┌─ AKSI CEPAT ────────────────────────────────────┐ │
│  │ [▶ Ganti Produk]  [🔊 Tes Suara]  [📌 Pin Link]│ │
│  │ [⏸ Pause Avatar]  [⚠ Emergency Stop]            │ │
│  └──────────────────────────────────────────────────┘ │
│                                                       │
│  ┌─ RINGKASAN ─────────┐ ┌─ LOG AKTIVITAS ─────────┐│
│  │ Uptime: 2h 15m       │ │ 10:45 Ganti → Earbuds   ││
│  │ Produk ditampilkan: 5│ │ 10:30 Voice restart      ││
│  │ Restart: 0           │ │ 10:15 Ganti → Kaos       ││
│  │ Insiden: 0           │ │ 10:00 Stream started      ││
│  └──────────────────────┘ └───────────────────────────┘│
└───────────────────────────────────────────────────────┘
```

**Perbaikan dari sekarang:**
- "Panduan Skrip" yang saat ini placeholder → harus terisi dari LLM brain berdasarkan produk aktif
- "Aksi Cepat" yang saat ini disabled → harus fungsional dengan tombol warna berbeda per severity
- "Status Operator" yang hanya "COLD" → ganti jadi indikator visual pipeline (icon warna)
- Tambah: timer rotasi produk, log aktivitas sesi, viewer count
- Hapus: "Ringkasan Operasional" 6 card di bawah — itu duplikasi, pindah ke Monitor

***

### Menu 6: 📊 MONITOR (Upgrade)

```
┌── MONITOR ───────────────────────────────────────────┐
│                                                       │
│  RESOURCE PRESSURE           Refresh: realtime (WS)   │
│  ┌────────────────────────────────────────────────┐  │
│  │  CPU  [████████░░░░░░░░] 45%                    │  │
│  │  RAM  [██████░░░░░░░░░░] 38%                    │  │
│  │  VRAM [████████████░░░░] 72%  ⚠ >70%            │  │
│  │  Disk [██░░░░░░░░░░░░░░] 12%                    │  │
│  └────────────────────────────────────────────────┘  │
│                                                       │
│  COMPONENT HEALTH                                     │
│  ┌──────────────┬──────────┬──────────┬────────────┐ │
│  │ FastAPI  ●   │ Database ●│ GPU  ●   │ Config  ●  │ │
│  │ LiveTalk ●   │ Voice  ○  │ Stream ○ │ Brain  ●   │ │
│  └──────────────┴──────────┴──────────┴────────────┘ │
│                                                       │
│  LLM BRAIN                                            │
│  Active: groq (llama-3.3-70b) | 10/11 adapters failed │
│  [Test Brain]                                         │
│                                                       │
│  INCIDENTS                        [Clear Resolved]    │
│  (timeline list — auto-populated)                     │
│                                                       │
│  ALERT CONFIG                                         │
│  Telegram: @user [Test] | Threshold VRAM: 80%         │
└───────────────────────────────────────────────────────┘
```

**Perbaikan:**
- Resource pressure pakai **progress bar visual**, bukan hanya angka "0%"
- LLM Brain Health dari Diagnostik **pindah ke sini** — karena ini monitoring, bukan diagnostic terpisah
- Tambah alert configuration (Telegram threshold)
- VRAM warning otomatis kalau >70%

***

### DIAGNOSTIK: DIGABUNG / DIHAPUS SEBAGAI MENU TERPISAH

Diagnostik saat ini berisi LLM Brain Health + Adapters + Operator Actions (Test Brain, Validate Mock, API Docs, System Diagnostic). [127.0.0](http://127.0.0.1:8181/dashboard/#/diagnostics)

**Saran:** 
- **LLM Brain Health & Adapters** → pindah ke **Monitor** (section "LLM Brain")
- **Test Brain, API Docs** → pindah ke **Setup** (bagian developer tools, collapsed)
- **Hapus Diagnostik sebagai menu terpisah** — kontennya tersebar ke menu yang lebih relevan

***

### RINGKASAN: SIDEBAR BARU

```
SEBELUM (7 menu, urutan bingung):     SESUDAH (6 menu, urutan workflow):
─────────────────────────────          ─────────────────────────────────
1. Konsol Live                         ━━ PERSIAPAN ━━
2. Produk                              1. 🔧 Setup & Validasi
3. Performer                              (gabung Validasi + Diagnostik)
4. Streaming                           2. 📦 Produk & Penawaran
5. Validasi                            3. 🎭 Avatar & Suara
6. Monitor                                (Performer, dipangkas bersih)
7. Diagnostik                          
                                       ━━ OPERASI ━━
                                       4. 📡 Streaming & Platform
                                          (RTMP config + stream key)
                                       5. 📺 Konsol Live
                                          (command center utama)
                                       
                                       ━━ PENGAWASAN ━━
                                       6. 📊 Monitor & Insiden
                                          (resource + brain + alerts)
```

**Kenapa urutan ini:**
- Operator baru buka dashboard → **Setup**: apakah sistem siap?
- Siap → **Produk**: set produk yang mau dijual hari ini
- Produk ready → **Avatar & Suara**: pastikan avatar & voice running
- Semua ready → **Streaming**: paste stream key, start stream
- Live → **Konsol Live**: ini jadi "home" selama live (produk rotasi, skrip, quick actions)
- Sepanjang live → **Monitor**: pantau resource, insiden, LLM brain

***

### PRINSIP UI YANG HARUS DITERAPKAN

| Prinsip | Implementasi |
|---------|-------------|
| **Operator vs Developer** | Setiap halaman punya mode default (operator: bersih) dan expandable section (developer: detail teknis). Engine logs, path readiness, vendor debug → collapsed by default |
| **No duplicate info** | Status bar atas = single source. Jangan ulangi di body halaman. Kalau perlu detail lebih → klik status bar item |
| **Visual hierarchy** | Tombol action utama (Start Stream, Emergency Stop) harus BESAR dan BERWARNA. Info secondary pakai text kecil |
| **No dead placeholder** | Hapus semua "akan datang di fase berikutnya". Kalau belum ada → jangan tampilkan section itu sama sekali |
| **Mobile-friendly** | 6 menu lebih baik dari 7 di layar HP. Card layout harus responsive stack vertical |
| **Color coding** | Hijau = ready/running. Kuning = warning/degraded. Merah = error/stopped. Abu = idle/unknown. Konsisten di semua halaman |
| **Workflow numbering** | Sidebar bisa pakai section header (PERSIAPAN / OPERASI / PENGAWASAN) supaya operator tahu fase mana |

***

### PRIORITAS IMPLEMENTASI

| Urutan | Perubahan | Effort |
|--------|-----------|--------|
| 1 | Pangkas Performer → Avatar & Suara (hide debug section) | Kecil — CSS collapse + reorganize |
| 2 | Gabung Diagnostik ke Monitor + Setup | Sedang — pindah component |
| 3 | Redesign Konsol Live (skrip + aksi cepat fungsional) | Sedang — butuh backend endpoint |
| 4 | Streaming: buka RTMP config default + stream key input | Kecil — CSS + form field |
| 5 | Reorder sidebar + section headers | Kecil — routing change |
| 6 | Produk: tambah link affiliate + rotasi timer | Sedang — database + UI |
| 7 | Monitor: progress bar + VRAM chart + alert config | Sedang — chart library + backend |

Ini semua bisa dikerjakan **tanpa rewrite** — hanya reorganisasi komponen Svelte yang sudah ada, plus beberapa komponen baru. Struktur backend FastAPI tidak perlu berubah, hanya frontend layout.