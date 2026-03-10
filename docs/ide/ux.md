# ANALISIS MENYELURUH DASHBOARD AI LIVE COMMERCE — COMMAND CENTER
### Hasil Scan: 8 Tab UI + 50+ API Endpoints + 4 Raw API Responses

***

## PERUBAHAN DARI VERSI SEBELUMNYA

Dashboard telah **berevolusi signifikan** — menu berubah dari 9 tab menjadi 8 tab dengan struktur lebih baik:

| Sebelumnya | Sekarang | Status |
|---|---|---|
| Overview | **Overview** (dengan Operations Cockpit baru) | Jauh lebih baik |
| Readiness | Digabung ke **Validation** | Sudah ter-render |
| Engine | Dipecah jadi **Voice** + **Face Engine** | Lebih fokus |
| Preview | Dihapus (link pindah ke Face Engine) | Tepat |
| Stream | **Stream** | Sama |
| Commerce | **Commerce** | Sama |
| Monitor | **Monitor** (sekarang load!) | Diperbaiki |
| Diagnostics | **Diagnostics** | Masih BROKEN |
| Validation | **Validation** (gabung Readiness) | Jauh lebih baik |

***

## ANALISIS PER TAB — FAKTA, BUKAN OPINI

### 1. OVERVIEW — Operations Cockpit [127.0.0](http://127.0.0.1:8181/dashboard/)

**Apa yang ada:**
- Ops Summary: 6 card (Overall Status `cold`, Deployment `cold`, Restart Count `0`, Incident Severity `none`, Voice/Face/Stream, Resource Pressure)
- **Operations Cockpit** (BARU): System Posture `IDLE` + Operator Alert `NORMAL`
- **Live Snapshot**: Viewers `0`, Uptime `30m`, Budget `$5.00`, Current Product `Skincare Glow Set Premium`
- Voice/Face/Stream status panel
- Resource Pressure: CPU/RAM/Disk semua `0%`
- **Operator Focus** (BARU): Next Check, Watch Item, Recommended Path

**Apa yang sudah BAIK dan tidak perlu diubah:**
- Operator Focus dengan "Recommended Path: Overview → Voice → Face Engine → Stream → Validation" adalah **guidance UX yang cerdas** — ini membantu operator non-teknis
- System Posture + Operator Alert memberi ringkasan cepat tanpa harus baca detail
- Current Product sudah muncul di overview

**Apa yang OPTIMAL untuk ditambahkan (bukan maximal):**

1. **Warna semantik pada System Posture** — `IDLE` seharusnya abu-abu/netral, bukan biru yang sama dengan semua card lain. Ketika `LIVE` nanti harus hijau, `ERROR` merah. Ini zero-cost tapi high-impact untuk scanning cepat oleh operator
2. **Operator Alert `NORMAL` menipu** — teks di bawahnya bilang "Voice unknown · Face livetalking_stopped" — ini BUKAN normal. Alert seharusnya `WARNING` (kuning) karena 2 dari 3 subsistem tidak aktif. Logic backend perlu dikoreksi
3. **Budget `$5.00` butuh konteks minimal** — tambahkan teks kecil "LLM API budget" di bawahnya agar operator tahu ini bukan budget iklan/produk. Brain config menunjukkan ini daily_budget_usd untuk multi-LLM routing [127.0.0](http://127.0.0.1:8001/api/brain/config)

***

### 2. VOICE — Voice Control Center

**Apa yang ada:**
- Voice Runtime `unknown` (Requested fish_speech, Resolved unknown)
- Fallback State `OFF` (Reference ready yes, Sidecar down)
- Voice Status: Queue Depth `0`, Chunk Size `n/a`, Last Latency `n/a ms`, P50/P95 `n/a`
- Operator Controls: 4 tombol (Warmup Voice, Clear Queue, Restart Voice, Refresh Truth)
- Voice Testing: Load Reference `ready`, Run Clone Smoke + Chunking Check → "manual via Validation"
- Diagnostics: Deployment `cold`, Time to First Audio `n/a ms`, Last Error `none`

**Sudah BAIK:**
- Panel terstruktur rapi — status, kontrol, testing, diagnostics dalam satu halaman
- Link ke Validation untuk smoke test menghindari duplikasi UI
- Fallback State terekspos — ini penting untuk reliability

**OPTIMAL untuk ditambahkan:**

1. **Tombol "Test Speak" inline** — cukup satu input teks + tombol play. Operator harus bisa cek suara tanpa harus buka tab lain. API `/api/brain/test` sudah ada di backend. Ini fitur paling kritis yang belum ada — bagaimana operator tahu suara berfungsi jika tidak bisa test? [127.0.0](http://127.0.0.1:8001/api/brain/config)
2. **Sidecar status lebih jelas** — "Sidecar down" di bawah Fallback State terlalu tersembunyi. Ini seharusnya WARNING badge sendiri karena artinya Fish-Speech server tidak jalan (sesuai readiness check: fish_speech_server_reachable = WARNING) [127.0.0](http://127.0.0.1:8001/api/readiness)
3. **Voice engine selector** — saat ini hanya menampilkan `fish_speech` tanpa opsi ganti. Jika hanya ada satu engine, tampilkan sebagai info saja. Jika ada rencana multi-engine, tambahkan dropdown

***

### 3. FACE ENGINE — Face Engine Control Center

**Apa yang ada:**
- Engine State `STOPPED` (Runtime livetalking_stopped, PID -)
- Face Model `musetalk` (Avatar musetalk_avatar1)
- Controls: Start (hijau) + Stop (kuning olive)
- Transport/Uptime: Port `8010`, Transport `webrtc`, Uptime `0s`
- Model/Avatar Resolution: Requested = Resolved (musetalk / musetalk_avatar1)
- Path Readiness: app.py `Found`, Models `Found`, Avatar `Found`
- Vendor Debug Links: Vendor Dashboard, WebRTC Preview, RTC Push

**Sudah BAIK:**
- Path Readiness check mencegah error karena file hilang
- Start/Stop buttons jelas dengan warna berbeda
- Tombol Refresh + Validate di header

**OPTIMAL untuk ditambahkan:**

1. **Embedded preview kecil (thumbnail WebRTC)** — BUKAN full iframe, cukup 320x240 thumbnail yang menampilkan frame terakhir dari avatar. Ini menggantikan tab Preview yang sudah dihapus. Tanpa ini, operator harus klik "WebRTC Preview" dan buka tab baru — memecah workflow
2. **GPU/VRAM usage di panel ini** — diagnostik API menunjukkan GPU adalah NVIDIA GeForce GTX 1650. GTX 1650 hanya punya **4GB VRAM** — ini sangat terbatas untuk musetalk. Tampilkan VRAM usage real-time di sebelah Transport/Uptime agar operator tahu kapan mendekati limit [127.0.0](http://127.0.0.1:8001/diagnostic/)
3. **Avatar selector** — jika hanya ada 1 avatar, ini tidak urgent. Tapi jika sudah ada beberapa avatar assets, tambahkan dropdown sederhana. Model/Avatar Resolution sudah menunjukkan requested vs resolved, tinggal buat writable
4. **Inference FPS indicator** — satu angka "FPS: 24" saat engine running. Ini menunjukkan apakah avatar berjalan mulus atau lag

***

### 4. STREAM — Stream Control Center

**Apa yang ada:**
- Stream Posture `idle` (Runtime idle, Pipeline unknown)
- Emergency State `CLEAR`
- Live Controls: Start Stream (hijau), Stop Stream (olive), Emergency Stop (merah)
- RTMP Validation: tombol "Validate RTMP Target"
- Pipeline State Machine: 4 tombol IDLE / WARMING / LIVE / COOLDOWN

**Sudah BAIK:**
- Emergency Stop terpisah jelas (merah)
- Pipeline state machine concept sudah benar

**Masalah KRITIS dan OPTIMAL untuk diperbaiki:**

1. **TIDAK ADA INPUT RTMP URL / STREAM KEY** — ini masalah terbesar di seluruh dashboard. Readiness API menunjukkan `rtmp_target_configured: TikTok RTMP configured`, artinya config di-hardcode di file backend. Operator HARUS bisa mengubah RTMP target dari UI tanpa edit file config. Minimal: satu text input untuk RTMP URL + satu untuk Stream Key + tombol Save. Ini non-negotiable untuk production [127.0.0](http://127.0.0.1:8001/api/readiness)
2. **Pipeline state buttons tidak ada highlight aktif** — keempat tombol (IDLE/WARMING/LIVE/COOLDOWN) tampil identik. Tidak ada indikasi mana state yang sedang aktif. Tambahkan border/glow pada state aktif
3. **Tidak ada stream health metrics saat live** — ketika streaming aktif, operator butuh: bitrate (kbps), frame drops, duration timer. Cukup 3 angka ini, tidak perlu graph
4. **Tidak ada multi-target RTMP** — goal adalah TikTok DAN Shopee. Saat ini hanya satu RTMP target. Optimal: tambahkan tab/toggle "Target 1: TikTok" / "Target 2: Shopee" dengan masing-masing stream key sendiri. Implementasi ffmpeg bisa split output ke 2 RTMP URL

***

### 5. VALIDATION — Readiness + Validation Gate Center

**Apa yang ada:**
- **Readiness section** (BARU — dulu broken): menampilkan 13 checks, status `DEGRADED`
  - 12x OK: config_loaded, database_healthy, livetalking_installed, avatar_reference_video/audio, livetalking_model_ready, livetalking_avatar_ready, ffmpeg_available, rtmp_target_configured, mode_explicit, voice_reference_wav_ready, voice_reference_text_ready
  - 1x WARNING: `fish_speech_server_reachable` — Fish-Speech not reachable at http://127.0.0.1:9880
- **Validation Gate Center**: 3 categories
  - Core Truth and Readiness: Runtime Truth, Real-Mode Readiness, Mock Stack
  - Voice and Media Checks: Voice Local Clone, Audio Chunking Smoke, LiveTalking Engine
  - Stream and Long-Run Checks: RTMP Target, Stream Dry Run, Resource Budget, Soak Sanity
- **Recent Validation History**: timestamps, PASS/FAIL/BLOCKED status

**Sudah BAIK — ini tab terbaik di dashboard:**
- Readiness check per-item dengan pesan detail dan path
- Kategorisasi validation checks logis
- History dengan timestamp
- WARNING fish_speech jelas menunjukkan masalah

**OPTIMAL untuk ditambahkan:**

1. **Tombol "Run All Checks"** — saat ini harus klik 10x "Run Check" satu per satu. Satu tombol di atas yang menjalankan semua sekaligus
2. **Link hasil Readiness ke Operator Alert di Overview** — status DEGRADED di sini seharusnya membuat Operator Alert di Overview menampilkan WARNING, bukan NORMAL. Ini inkonsistensi logic
3. **Detail error saat FAIL** — di Recent Validation History, entri FAIL tidak menunjukkan KENAPA fail. Tambahkan expandable row/tooltip dengan error message
4. **Auto-run readiness saat tab dibuka** — saat ini readiness check perlu trigger manual (tombol Refresh). Sebaiknya auto-run setiap kali tab dibuka, atau setiap 60 detik

***

### 6. MONITOR — Operations Monitor

**Apa yang ada:**
- Incidents: "No open incidents"
- **Component Health** (BARU — dulu tidak load): face_pipeline `healthy`, database `healthy`, gpu `healthy`, config `healthy`, livetalking `idle` (kuning), analytics `healthy`
- **Resource Pressure**: CPU `0%`, RAM `0%`, Disk `0%`, **VRAM `n/a`** (BARU)
- **Recent Incidents**: "No recent incidents"
- **Recent Chat**: "No recent chat activity"

**Sudah BAIK:**
- Component health dengan dot indicator (hijau/kuning) sudah ada
- VRAM ditambahkan di Resource Pressure
- Recent Chat panel sudah ada (menunggu data)

**OPTIMAL untuk ditambahkan:**

1. **VRAM harus menampilkan angka, bukan `n/a`** — diagnostik API menunjukkan GPU GTX 1650 terdeteksi dan healthy. VRAM seharusnya menampilkan usage/total (misal "1.2/4.0 GB"). Ini kritis karena GTX 1650 terbatas [127.0.0](http://127.0.0.1:8001/diagnostic/)
2. **Recent Chat perlu lebih dari passive display** — saat live, chat penonton akan masuk. Panel ini sebaiknya menampilkan sender + message + timestamp. API `/api/chat/recent` sudah siap (sekarang return `[]` karena belum live) [127.0.0](http://127.0.0.1:8001/api/chat/recent)
3. **Network throughput** — satu angka upload bandwidth. Kritis untuk stream quality. Cukup "Upload: X Mbps"
4. **Component list belum lengkap** — diagnostik API menunjukkan 15 komponen (config, face_pipeline, database, gpu, livetalking, analytics, brain, voice, face, composition, stream, chat, commerce, orchestrator), tapi Monitor hanya tampilkan 6. Tampilkan semua, atau minimal tambahkan `brain`, `voice`, `stream` [127.0.0](http://127.0.0.1:8001/diagnostic/)

***

### 7. COMMERCE — Paling Minimalis

**Apa yang ada:**
- Revenue Summary: `Rp 0`
- Products (10): 10 produk dengan nama + harga + tombol "Switch"

**Masalah:** Tab ini paling tertinggal dibanding kemajuan tab lain.

**OPTIMAL untuk ditambahkan (bertahap):**

**Tahap 1 — Immediate (supaya Commerce berfungsi minimal):**
1. **Active product highlight** — Overview sudah menunjukkan "Current Product: Skincare Glow Set Premium", tapi di Commerce list tidak ada indikasi mana yang aktif. Tambahkan background warna berbeda atau badge "ACTIVE" pada produk yang sedang di-pin
2. **Revenue breakdown minimal** — API revenue hanya return `{"total": 0.0}`. Di panel Revenue Summary, tambahkan: Total Orders, Average Order Value, selain total revenue. Ini butuh perubahan backend juga [127.0.0](http://127.0.0.1:8001/api/analytics/revenue)
3. **Gambar produk thumbnail** — teks-only listing sulit untuk scanning cepat. Cukup 40x40 pixel thumbnail di sebelah kiri nama

**Tahap 2 — Saat sudah live production:**
4. **Order feed real-time** — notifikasi masuk saat ada pembelian
5. **Product queue/urutan** — drag-and-drop atau tombol up/down untuk mengatur urutan presentasi
6. **Stok per produk** — informasi sisa stok mencegah overselling

***

### 8. DIAGNOSTICS — MASIH BROKEN

**Apa yang ada:** "Loading diagnostics..." — tidak pernah selesai render.

**Padahal backend sangat kaya data** — API `/diagnostic/` mengembalikan data lengkap: 15 komponen dengan status, latency, system info (Windows 11, Python 3.12.12, NVIDIA GTX 1650, 8 database tables). [127.0.0](http://127.0.0.1:8001/diagnostic/)

**OPTIMAL fix:**
1. **Perbaiki Svelte component** — ini bug frontend, bukan backend. Fetch ke `/diagnostic/` kemungkinan gagal parse response atau ada error di component

# ANALISIS ULANG: KONTEKS AFFILIATE PRODUCT — Produk Berganti-Ganti

## FAKTA KRITIS: Apa yang Berubah dengan Model Affiliate

Konteks **affiliate** mengubah segalanya karena:

1. **Produk bukan milik Anda** — Anda tidak kontrol stok, harga bisa berubah sewaktu-waktu, dan komisi bervariasi per produk
2. **Produk berganti-ganti** — katalog tidak statis, produk bisa masuk/keluar kapan saja berdasarkan campaign affiliate
3. **AI harus tahu konteks produk yang sedang ditampilkan** — selling script, product QA, dan chat reply harus relevan dengan produk AKTIF saat itu
4. **Link affiliate harus ter-track** — tanpa tracking link, live streaming tidak menghasilkan komisi

***

## DATA MODEL PRODUK SAAT INI — TERLALU MINIM UNTUK AFFILIATE

Dari API `/api/products`, setiap produk hanya punya: [127.0.0](http://127.0.0.1:8001/api/products)

```
{
  "id": 1,
  "name": "Skincare Glow Set Premium",
  "price": 149000.0,
  "price_formatted": "Rp 149,000",
  "category": "beauty",
  "is_active": true
}
```

**Yang TIDAK ADA tapi WAJIB untuk affiliate:**

| Field yang Hilang | Kenapa Wajib |
|---|---|
| `affiliate_link` | Tanpa ini = 0 komisi. Ini raison d'être affiliate |
| `commission_rate` / `commission_amount` | Operator perlu prioritaskan produk komisi tinggi |
| `platform` (tiktok/shopee) | Produk affiliate beda link per platform |
| `description` / `selling_points` | AI Brain butuh ini untuk generate selling script — saat ini brain config punya task `selling_script` dan `product_qa` [127.0.0](http://127.0.0.1:8001/api/brain/stats) tapi TIDAK ADA data produk yang bisa dijadikan konteks |
| `image_url` | Thumbnail untuk identifikasi cepat saat switching produk |
| `expiry_date` / `campaign_end` | Link affiliate punya masa berlaku |
| `stock_status` | Affiliate tetap perlu tahu apakah merchant masih punya stok |
| `original_price` (sebelum diskon) | Untuk menunjukkan potongan harga ke penonton |

Ini masalah fundamental — **seluruh data model produk harus diperluas** di backend Python sebelum UI bisa menjadi fungsional untuk affiliate.

***

## ANALISIS PER TAB — DAMPAK KONTEKS AFFILIATE

### 1. COMMERCE TAB — Butuh Transformasi Total

**Kondisi saat ini:** Revenue Summary `Rp 0` + daftar 10 produk dengan tombol Switch. Semua produk `is_active: true` — tidak ada pembedaan mana yang sedang ditampilkan vs antrian. [127.0.0](http://127.0.0.1:8181/dashboard/)

**Masalah spesifik affiliate:**

**A. Tidak ada konsep "Product Queue" vs "Active Showcase"**

Dalam affiliate live, workflow operator adalah:
1. Siapkan antrian 10-20 produk untuk sesi 2 jam
2. Setiap 5-10 menit, SWITCH ke produk berikutnya
3. AI avatar harus langsung bicara tentang produk baru
4. Link affiliate produk aktif harus ter-pin di platform

Saat ini tombol "Switch" ada tapi:
- **Tidak terlihat produk mana yang SEDANG aktif** — API status menunjukkan `current_product: {id:1, name: "Skincare Glow Set Premium"}` tapi di Commerce list SEMUA produk tampil identik tanpa highlight [127.0.0](http://127.0.0.1:8001/api/status)
- **Tidak ada urutan/queue** — operator tidak bisa mengatur "berikutnya produk X, setelah itu Y"
- **Tidak ada timer per produk** — berapa lama sudah membahas produk ini? Kapan harus switch?

**B. Revenue Summary tidak bermakna untuk affiliate**

`Rp 0` tanpa konteks. Untuk affiliate, yang relevan adalah:
- **Estimated commission**, bukan total revenue — karena Anda dapat persentase, bukan full price
- **Click count per affiliate link** — berapa orang klik link dari live
- **Conversion rate** — dari klik ke pembelian

**Saran OPTIMAL untuk Commerce:**

```
┌─────────────────────────────────────────────────────┐
│  COMMERCE - Affiliate Dashboard                      │
│                                                      │
│  ┌──────────────┐  ┌─────────────────────────────┐  │
│  │ NOW SHOWING  │  │ PRODUCT QUEUE               │  │
│  │ ┌──────────┐ │  │                             │  │
│  │ │ [image]  │ │  │  2. Kaos Oversize    05:00  │  │
│  │ │ Skincare │ │  │  3. Earbuds Pro ANC  05:00  │  │
│  │ │ Glow Set │ │  │  4. Tas Selempang    05:00  │  │
│  │ │ Rp149,000│ │  │  5. Madu Hutan       05:00  │  │
│  │ │ ━━━━━━━━ │ │  │  ...                        │  │
│  │ │Rp199,000 │ │  │                             │  │
│  │ │(diskon25%)│ │  │  [+ Add Product]            │  │
│  │ └──────────┘ │  │  [▶ Auto-rotate: OFF]       │  │
│  │ Timer: 3:42  │  │                             │  │
│  │ Commission:  │  │                             │  │
│  │   8% = ~Rp12K│  │                             │  │
│  │              │  │                             │  │
│  │ [NEXT ▶]    │  └─────────────────────────────┘  │
│  └──────────────┘                                    │
│                                                      │
│  ┌─────────────────────────────────────────────────┐ │
│  │ SESSION STATS                                    │ │
│  │ Products Shown: 1/10  │  Est. Commission: Rp 0  │ │
│  │ Total Switches: 0     │  Session Time: 00:03:42  │ │
│  └─────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────┘
```

Implementasi minimal yang dibutuhkan:
1. **Highlight produk aktif** di list — cukup beda warna background + badge "ACTIVE"
2. **Durasi timer per produk** — mulai hitung saat Switch ditekan
3. **Queue ordering** — tombol panah atas/bawah untuk reorder, atau drag-drop
4. **Auto-rotate toggle** — switch produk otomatis setiap X menit (kritis untuk affiliate agar semua produk dapat exposure)

***

### 2. OVERVIEW — Current Product Perlu Enrichment

Di Live Snapshot, `Current Product: Skincare Glow Set Premium` sudah muncul. Tapi untuk affiliate: [127.0.0](http://127.0.0.1:8001/dashboard/)

**Saran optimal:**
- Tambahkan **commission rate** di sebelah nama produk: "Skincare Glow Set Premium (8%)"
- Tambahkan **time on product** di bawahnya: "Showing for 3m 42s"
- Jangan ubah layout lain — Overview sudah cukup informatif

***

### 3. AI BRAIN — Masalah Terbesar yang Tidak Terlihat di UI

Brain config menunjukkan task routing yang canggih: [127.0.0](http://127.0.0.1:8001/api/brain/stats)
- `selling_script` → routed ke claude_local, gemini_local_pro, gpt4o_local, chutes, groq, gemini
- `product_qa` → routed ke gemini_local_pro, claude_local, gpt4o_local, chutes, groq, gemini
- `chat_reply`, `humor`, `emotion_detect`, `filler`, `safety_check`

**Masalah KRITIS untuk affiliate:**

AI Brain HARUS tahu detail produk yang sedang aktif agar bisa generate selling script yang akurat. Saat ini:
- Product data hanya `name` + `price` + `category` — AI tidak punya informasi **apa keunggulan produk, bahan, ukuran, target audience**
- Saat produk di-switch, apakah brain context ikut berubah? Tidak ada mekanisme yang terlihat

**Saran optimal — "Product Context Feed":**

Tambahkan field di setiap produk:
```python
{
  "selling_points": ["Kandungan Niacinamide 5%", "Sudah BPOM", "Rating 4.9/5"],
  "target_audience": "Wanita 18-35, kulit berminyak",  
  "ai_prompt_hint": "Fokus pada hasil glowing dalam 7 hari"
}
```

Saat Switch ditekan, backend harus:
1. Update `current_product` di status
2. **Inject product context ke brain prompt** — sehingga selling_script dan product_qa langsung relevan
3. AI avatar otomatis mulai membahas produk baru

Ini bisa di-expose di UI Commerce sebagai **textarea "AI Talking Points"** di bawah setiap produk — operator bisa edit sebelum live.

***

### 4. STREAM TAB — Multi-Platform Affiliate Link Problem

Untuk affiliate, satu produk bisa punya **link berbeda di TikTok vs Shopee**:
- TikTok Affiliate: `https://vt.tiktok.com/ZSxxxxxxx/`
- Shopee Affiliate: `https://shp.ee/xxxxxxx`

Saat ini Stream tab tidak punya konsep multi-platform. [127.0.0](http://127.0.0.1:8001/dashboard/)

**Saran optimal (bukan maximal):**

Jangan bangun multi-RTMP dulu. Sebagai langkah pertama:
1. Tambahkan **dropdown "Target Platform"** di Stream tab: TikTok / Shopee
2. Saat dipilih, RTMP URL otomatis terisi dari config
3. **Di Commerce, tampilkan affiliate link sesuai platform aktif** — jika streaming ke TikTok, tampilkan TikTok affiliate link

Multi-RTMP simulcast bisa jadi phase 2 nanti.

***

### 5. VOICE TAB — Tidak Perlu Banyak Perubahan untuk Affiliate

Voice tab sudah cukup baik. Satu hal yang relevan untuk affiliate:

**Saran optimal:**
- **Voice persona per category** — produk beauty mungkin butuh nada lembut, produk electronics lebih energik. Ini bisa berupa preset: "Gentle", "Energetic", "Professional". Tapi ini PHASE 3, bukan prioritas sekarang.

***

### 6. FACE ENGINE — Tidak Perlu Perubahan untuk Affiliate

Musetalk + musetalk_avatar1 sudah fungsional. Affiliate tidak mengubah kebutuhan face engine.

***

## PRIORITAS IMPLEMENTASI — TEROPTIMAL (Bukan Maximal)

### PHASE 1: "Bisa Live Affiliate" (1-2 minggu)

Fokus: **Commerce + Product Data Model + Stream Input**

| No | Task | Effort | Impact |
|---|---|---|---|
| 1 | **Perluas product model**: tambah `affiliate_link`, `commission_rate`, `description`, `selling_points`, `image_url`, `platform` | Backend: sedang | Tanpa ini, affiliate = 0 |
| 2 | **Active product highlight** di Commerce list | Frontend: kecil | Operator tahu produk mana aktif |
| 3 | **RTMP URL input field** di Stream tab | Frontend: kecil | Tanpa ini, tidak bisa live |
| 4 | **Product context injection ke Brain** saat Switch | Backend: sedang | AI bicara relevan |
| 5 | **Fix Diagnostics tab** (frontend bug) | Frontend: kecil | 1 dari 8 tab broken |
| 6 | **Fix Operator Alert logic** — DEGRADED ≠ NORMAL | Backend: kecil | Mencegah false confidence |

### PHASE 2: "Live Affiliate yang Efisien" (2-4 minggu)

| No | Task | Effort | Impact |
|---|---|---|---|
| 7 | **Product queue** dengan ordering | Frontend+Backend: sedang | Workflow terstruktur |
| 8 | **Per-product timer** + auto-rotate | Frontend: sedang | Equal exposure untuk semua produk |
| 9 | **Embedded face preview** di Face Engine tab | Frontend: sedang | Tidak perlu buka tab baru |
| 10 | **Commission tracker** di Commerce | Backend+Frontend: sedang | Tahu estimasi pendapatan |
| 11 | **AI Talking Points textarea** per produk | Frontend: kecil | Operator kontrol apa yang AI katakan |
| 12 | **Platform selector** (TikTok/Shopee) di Stream | Frontend: kecil | Persiapan multi-platform |

### PHASE 3: "Scaling" (setelah live berjalan stabil)

| No | Task |
|---|---|
| 13 | Multi-RTMP simulcast (TikTok + Shopee bersamaan) |
| 14 | Shopee/TikTok API integration untuk auto-sync produk affiliate |
| 15 | Real-time order feed + conversion tracking |
| 16 | Auto-import produk dari TikTok Shop / Shopee Affiliate dashboard |
| 17 | Voice persona presets per kategori produk |
| 18 | Authentication untuk remote access |

***

## SATU HAL YANG PALING KRITIS

Jika hanya boleh pilih **SATU** hal untuk dikerjakan terlebih dahulu, itu adalah:

> **Perluas data model produk di backend Python** — tambahkan minimal `affiliate_link`, `selling_points`, dan `commission_rate`.

Alasannya: Seluruh ekosistem bergantung pada ini. UI Commerce tidak bisa menampilkan info yang berguna tanpa data. AI Brain tidak bisa generate selling script tanpa konteks produk. Affiliate tracking tidak bisa berjalan tanpa link. Dan pergantian produk yang Anda butuhkan hanya bermakna jika setiap produk membawa konteksnya sendiri — bukan hanya nama dan harga.

Semua perbaikan UI di atas akan menjadi kosmetik belaka jika fondasi data produk tidak diperkaya terlebih dahulu.