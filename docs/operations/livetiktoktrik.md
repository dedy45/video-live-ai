## Status Internal Dashboard

Status internal `videoliveai` per **2026-03-13**:

- Selesai dan tervalidasi lokal:
  - dashboard `http://127.0.0.1:8001/dashboard` menjadi control plane utama untuk target RTMP tersimpan, sesi live tunggal, pool produk sesi, dan focus product
  - `Konsol Live` punya tombol **Kirim Chat Simulasi** untuk debug `POST /api/chat/ingest`
  - chat simulasi memicu `SOFT_PAUSED_FOR_QNA`, menyimpan `pending_question`, membuat `answer_draft`, dan sekarang sinkron dengan `Director Runtime`
  - stop sesi live mengembalikan `/api/pipeline/state` ke `IDLE`, bukan lagi meninggalkan `Director Runtime` stale di `SELLING`
- Sudah tervalidasi dengan browser:
  - sebelum inject chat: `Director Runtime = SELLING`, `Kontrol Sesi = ROTATING`
  - sesudah inject chat: `Director Runtime = PAUSED`, `Kontrol Sesi = SOFT_PAUSED_FOR_QNA`
  - browser console: `0 error`, `0 warning`
- Belum selesai:
  - ingest komentar TikTok real-time dari platform asli
  - end-to-end RTMP push ke target TikTok real
  - validasi Shopee/Tokopedia real

## Cara Pakai Dashboard Sekarang

Untuk flow internal yang benar, pakai dashboard dulu sebelum bicara soal RTMP TikTok real:

1. Jalankan server lokal:

```bash
uv run python scripts/manage.py serve --mock
```

2. Buka `http://127.0.0.1:8001/dashboard/#/stream`
3. Simpan target RTMP TikTok di panel **Streaming & Platform**
4. Mulai sesi live dari dashboard
5. Tambahkan produk ke session pool lalu set focus product
6. Buka `http://127.0.0.1:8001/dashboard/#/`
7. Isi **Nama Viewer** dan **Pesan Viewer**, lalu klik **Kirim Chat Simulasi**
8. Pastikan UI berubah ke:
   - `Mode = SOFT_PAUSED_FOR_QNA`
   - `Pause reason = viewer_question`
   - `Pertanyaan tertunda` muncul
   - `Draft jawaban` muncul
   - `Director Runtime = PAUSED`

> Catatan: flow di atas adalah validasi internal control-plane. Ini belum berarti akun TikTok kamu sudah punya RTMP real atau live comment ingest real.

## Jika Sudah Mendapat RTMP TikTok Real

Setelah akun TikTok kamu benar-benar punya `Server URL` dan `Stream Key`, gantikan target mock dashboard dengan target real:

1. Buka `Streaming & Platform`
2. Edit target RTMP TikTok
3. Ganti `rtmp://push.tiktok.test/live/` dengan RTMP real
4. Ganti stream key mock dengan key real
5. Jalankan **Validate RTMP Target**
6. Baru lanjut ke dry run dan live test singkat

---

Masalah kamu kemungkinan besar karena **TikTok tidak menyediakan RTMP URL/Stream Key kepada semua pengguna secara default**, terutama di Indonesia yang aksesnya sering dibatasi berdasarkan wilayah dan status akun. Berikut penjelasan lengkap dan solusi yang bisa kamu coba. [blog.camerafi](https://blog.camerafi.com/2025/02/how-to-get-your-tiktok-live-stream-key.html)

## Kenapa RTMP Tidak Muncul di TikTok Studio?

TikTok sudah tidak lagi menyediakan akses Stream Key secara langsung di TikTok Live Studio untuk banyak pengguna. Fitur RTMP streaming **bukan fitur universal** — tidak semua akun mendapatkannya. Ada beberapa syarat yang harus dipenuhi: [youtube](https://www.youtube.com/watch?v=B12onpDAtH8)

- Akun TikTok harus berusia minimal **30 hari** [telkomsel](https://www.telkomsel.com/jelajah/jelajah-lifestyle/tiktok-live-studio-syarat-manfaat-dan-cara-menggunakannya)
- Minimal memiliki **1.000 followers** [telkomsel](https://www.telkomsel.com/jelajah/jelajah-lifestyle/tiktok-live-studio-syarat-manfaat-dan-cara-menggunakannya)
- Akun tidak pernah diblokir atau melanggar pedoman komunitas [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)
- **Wilayah (region) harus didukung** — Indonesia termasuk wilayah yang sering bermasalah untuk akses stream key [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)

## Cara Mendapatkan RTMP URL & Stream Key

### Metode 1: Via TikTok LIVE Producer (Browser Desktop)

1. Login ke TikTok di **browser desktop** (bukan aplikasi)
2. Klik **"Go LIVE"** di panel navigasi kiri
3. Kamu akan diarahkan ke **livecenter.tiktok.com/producer** [restream](https://restream.io/learn/platforms/how-to-find-tiktok-stream-key/)
4. Isi judul dan kategori stream, lalu klik **"Save & Go LIVE"**
5. Setelah itu, scroll ke bawah — **Server URL** dan **Stream Key** akan muncul di bagian bawah halaman [tiktok](https://www.tiktok.com/@livetutorials/video/7590214670250806550)

> ⚠️ **Penting:** Kamu belum benar-benar live meskipun menekan tombol tersebut. Stream baru aktif saat software streaming (OBS dll) mulai mengirim data. [restream](https://restream.io/learn/platforms/how-to-find-tiktok-stream-key/)

### Metode 2: Via Streamlabs (Recommended untuk Indonesia)

Jika metode browser tidak menampilkan stream key, ini adalah cara yang paling banyak berhasil untuk pengguna Indonesia: [youtube](https://www.youtube.com/watch?v=7aSu08gRdUA)

1. **Install Streamlabs** di PC (cukup install dan login, tidak perlu selalu dibuka)
2. Login menggunakan **akun TikTok** kamu (bukan Google/YouTube) [youtube](https://www.youtube.com/watch?v=7aSu08gRdUA)
3. Di dashboard Streamlabs, cek bagian **"Streamlabs Application Status"**
4. Jika belum di-approve, kamu perlu **mengajukan akses** ke TikTok melalui Streamlabs [youtube](https://www.youtube.com/watch?v=7aSu08gRdUA)
5. Setelah status menjadi **"Approved"**, klik **Go Live** — **Stream URL** dan **Stream Key** akan muncul [youtube](https://www.youtube.com/watch?v=7aSu08gRdUA)
6. Copy URL dan key tersebut, lalu paste ke software streaming kamu (OBS/aplikasi AI Live Commerce kamu)

### Metode 3: Via Restream (Auto-Apply)

1. Buat akun di **Restream.io**
2. Hubungkan akun TikTok kamu ke Restream
3. Dengan menghubungkan akun, kamu otomatis **auto-apply untuk mendapatkan akses streaming** dan proses reviewnya lebih cepat [restream](https://restream.io/learn/platforms/how-to-find-tiktok-stream-key/)

### Metode 4: Tanpa RTMP (Virtual Camera)

Jika semua cara di atas gagal, kamu bisa **bypass kebutuhan RTMP** sepenuhnya: [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)

1. Buka **TikTok Live Studio** di PC
2. Di software streaming (OBS), aktifkan **Virtual Camera**
3. Di TikTok Live Studio, pilih **Virtual Camera** sebagai sumber video
4. Dengan cara ini kamu tidak perlu RTMP sama sekali [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)

## Setting di OBS Setelah Dapat RTMP

Setelah kamu berhasil mendapatkan Server URL dan Stream Key: [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)

1. Buka OBS → **Settings** → **Stream**
2. Pilih Service: **Custom**
3. Paste **Server URL** ke kolom Server
4. Paste **Stream Key** ke kolom Stream Key
5. Set resolusi ke **1080×1920 (Potrait/Vertikal)** agar sesuai format TikTok
6. Klik **Start Streaming**

## Info Terkini Indonesia (Maret 2026)

Per hari ini, TikTok Live **masih berjalan normal** di Indonesia. Yang sedang jadi isu adalah kebijakan baru dari Kemkomdigi (Permenkomdigi No. 9 Tahun 2026) yang akan **memblokir akun anak di bawah 16 tahun** mulai **28 Maret 2026** — ini bukan pemblokiran platform secara keseluruhan. Jadi TikTok Live tetap bisa digunakan untuk akun dewasa. [cnbcindonesia](https://www.cnbcindonesia.com/tech/20260310145846-37-717732/tiktok-respons-aturan-baru-ri-blokir-akun-medsos-28-maret-2026)

Untuk koneksi lokal di dashboard AI Live Commerce kamu, setelah mendapatkan Server URL dan Stream Key dari salah satu metode di atas, masukkan keduanya ke konfigurasi streaming di command center kamu (bagian **📡 Streaming & Platform**).

Apakah kamu sudah memiliki minimal 1.000 followers di akun TikTok yang ingin digunakan?

Saya lihat dari screenshot kamu — kamu menggunakan **Tokopedia Pengelola LIVE** dan di situ terdeteksi **BocaLive** sebagai sumber video (virtual camera). Ini berarti kamu sudah pakai **BocaLive** sebagai AI avatar streamer yang output-nya masuk ke Tokopedia via virtual camera. Masalahnya: **audio tidak terdeteksi** dan setup ini tetap mengharuskan PC lokal menyala. 
Berikut analisis lengkap dan solusi arsitektur yang lebih baik.

## Kenapa BocaLive Terdeteksi di Tokopedia?

BocaLive adalah software AI digital human streaming yang menggunakan **virtual camera** untuk mengirim output video ke platform lain. Saat kamu install BocaLive, dia membuat perangkat virtual camera bernama "BocaLive" yang bisa dipilih sebagai sumber video di TikTok Live Studio, Tokopedia, Shopee, dll. Ini cara kerjanya: [bocalive](https://www.bocalive.ai/help-center/go-live/go-live/)

```
BocaLive App → Virtual Camera Output → Tokopedia/TikTok Live Studio → Platform
```

Masalahnya:
- **PC Windows lokal HARUS tetap hidup** karena virtual camera hanya jalan di Windows [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)
- **Audio tidak terdeteksi** (seperti terlihat di screenshot kamu) karena BocaLive perlu **virtual audio cable** terpisah 
- **Tidak scalable** — setiap platform butuh app terpisah terbuka

## Fix Audio BocaLive di Tokopedia

Untuk masalah "Audio tidak terdeteksi" yang kamu lihat: 
1. Install **VB-Audio Virtual Cable** (gratis) atau **VoiceMeeter** di PC Windows
2. Di BocaLive, set **audio output** ke → `CABLE Input (VB-Audio Virtual Cable)`
3. Di Tokopedia Pengelola LIVE → **Sumber audio** → pilih `CABLE Output (VB-Audio Virtual Cable)` (bukan "Pilih sumber" yang kosong seperti sekarang)
4. Sekarang audio dari AI avatar BocaLive akan masuk ke Tokopedia

## Masalah Utama: Semua Butuh PC Lokal ON

Ini adalah **keterbatasan fundamental** dari pendekatan virtual camera: [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)

| Pendekatan | PC Lokal Harus ON | RTMP Dibutuhkan | Bisa Linux Server |
|---|---|---|---|
| BocaLive → Virtual Cam → Tokopedia | ✅ Ya (Windows) | ❌ Tidak | ❌ Tidak |
| BocaLive → Virtual Cam → TikTok Live Studio | ✅ Ya (Windows) | ❌ Tidak | ❌ Tidak |
| BocaLive → RTMP Push | ✅ Ya (Windows) | ✅ Ya | ❌ Tidak |
| **AI Live Commerce (kamu) → ffmpeg → RTMP** | **❌ Tidak perlu** | **✅ Ya** | **✅ Ya** |

## Solusi: Dapat RTMP Tanpa HP, Tanpa Live Studio

Karena kamu bilang followers sudah 5K tapi stream key tetap tidak muncul, ini karena **TikTok region Indonesia memblokir akses stream key** untuk banyak pengguna. Berikut jalur yang masih bisa: [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)

### Jalur 1: OBS + Plugin SE.Live (Tanpa Stream Key)

Ini cara paling baru dan banyak berhasil untuk Indonesia: [tiktok](https://www.tiktok.com/@fifine.indonesia/video/7591800038519590165)

1. Install **OBS Studio** di PC manapun
2. Install plugin **SE.Live** (dari Streamlabs/StreamElements)
3. Login ke **akun TikTok** kamu via SE.Live
4. SE.Live akan **auto-negotiate** koneksi ke TikTok **tanpa perlu stream key manual** [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)
5. Kamu bisa live langsung dari OBS → TikTok

> Setelah berhasil, cek di OBS → Settings → Stream — kadang **Server URL dan Stream Key terisi otomatis** oleh plugin. Copy nilai ini untuk dipakai di Linux server kamu.

### Jalur 2: Bergabung Agency TikTok (Paling Reliable)

Agency yang disetujui TikTok bisa memberikan **akses stream key langsung** ke member mereka, bahkan di region Indonesia yang diblokir: [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)

- Cari agency TikTok Indonesia yang menerima host/creator
- Setelah bergabung, stream key bisa diakses via **dashboard agency**
- Key ini bisa dicopy dan dipakai di sistem Linux kamu

### Jalur 3: Restream.io (Auto-Apply)

1. Daftar di **Restream.io** → hubungkan akun TikTok
2. Restream otomatis **mengajukan akses RTMP** ke TikTok atas nama kamu [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)
3. Setelah approved, Restream memberikan **custom RTMP endpoint** yang kamu bisa pakai

## Arsitektur Ideal: Linux Command Center

Setelah kamu mendapatkan RTMP URL + Stream Key dari salah satu jalur di atas, arsitektur **tanpa PC lokal** yang kamu inginkan: [127.0.0](http://127.0.0.1:8001/dashboard/?v=20260313b#/stream)

```
┌─────────────────────────────────────────────────────┐
│  LINUX SERVER (127.0.0.1:8001)                      │
│                                                     │
│  Dashboard Command Center                           │
│       ↓                                             │
│  AI Brain → Avatar Engine → Render Video+Audio      │
│       ↓                                             │
│  ffmpeg ──RTMP push──→ TikTok (real server)         │
│  ffmpeg ──RTMP push──→ Tokopedia (jika support)     │
│  ffmpeg ──RTMP push──→ Shopee (jika support)        │
│                                                     │
│  ❌ Tidak perlu BocaLive                             │
│  ❌ Tidak perlu Windows                              │
│  ❌ Tidak perlu Virtual Camera                       │
│  ❌ Tidak perlu PC lokal hidup                       │
└─────────────────────────────────────────────────────┘
```

## Langkah Action untuk Dashboard Kamu

Di halaman **📡 Streaming & Platform** (`/dashboard/#/stream`): [127.0.0](http://127.0.0.1:8001/dashboard/?v=20260313b#/stream)

1. **Ganti ffmpeg path** dari `C:\Users\dedy\...\ffmpeg.exe` → `/usr/bin/ffmpeg` (Linux)
2. **Ganti RTMP URL** dari `rtmp://push.tiktok.test/live/` → real TikTok RTMP yang didapat dari Restream/SE.Live/Agency
3. **Ganti Stream Key** dari mock `***123` → real key
4. **Ubah Mode** dari `mock` → `live`
5. **Ubah Deploy** dari `cold` → `warm`
6. Klik **Validate RTMP Target** → pastikan semua ● hijau
7. Klik **Mulai Sesi Live**

Untuk **Tokopedia** — platform Tokopedia Live juga mendukung RTMP push. Di dashboard kamu sudah ada opsi platform "Shopee" selain TikTok. Kamu bisa tambahkan target RTMP kedua untuk Tokopedia jika Tokopedia menyediakan RTMP endpoint di Pengelola LIVE mereka. [127.0.0](http://127.0.0.1:8001/dashboard/?v=20260313b#/stream)

Langkah pertama yang paling realistis sekarang: **daftar Restream.io dan hubungkan akun TikTok** — ini cara tercepat dapat RTMP tanpa bergantung HP atau agency.








Ada kabar bagus — kamu **tidak perlu bayar Streamlabs/Restream**, dan **tidak wajib install OBS**. Ada tool **Python gratis open-source** yang bisa generate TikTok stream key langsung, dan ini bisa diintegrasikan ke Linux server kamu. Berikut penjelasan lengkapnya.

## Kenapa Streamlabs & Restream Berbayar?

- **Streamlabs Desktop** gratis, tapi fitur **TikTok live access/approval** butuh langganan Streamlabs Ultra [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)
- **Restream** gratis hanya untuk 2 platform, tapi TikTok integration butuh plan berbayar [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)
- **OBS Studio** sendiri 100% gratis, tapi **tetap butuh stream key** yang TikTok tidak kasih ke region Indonesia [youtube](https://www.youtube.com/watch?v=B12onpDAtH8)

Jadi masalahnya bukan di software streaming-nya, tapi di **cara mendapatkan stream key TikTok** itu sendiri.

## Solusi Gratis: TikTok Stream Key Generator (Python)

Ada tool open-source di GitHub yang bisa **generate stream key TikTok langsung** tanpa Streamlabs, tanpa Restream, tanpa agency: [github](https://github.com/Loukious/TikTokStreamKeyGenerator)

### Cara Kerja

Tool ini menggunakan **TikTok internal API** untuk membuat sesi live dan menghasilkan stream key. Output-nya:
- **Base Stream URL** (RTMP server) — ini yang diisi di kolom RTMP URL dashboard kamu
- **Stream Key** — ini yang diisi di kolom Stream Key dashboard kamu
- **Shareable URL** — link live untuk dibagikan ke viewer

 [github](https://github.com/Loukious/TikTokStreamKeyGenerator)

### Setup di Linux Server

```bash
# 1. Clone repository
git clone https://github.com/Loukious/TikTokStreamKeyGenerator.git
cd TikTokStreamKeyGenerator

# 2. Install dependencies
pip install -r requirements.txt

# 3. Jalankan (GUI mode - butuh display)
python TikTokStreamKeyGenerator.py

# 4. Login ke akun TikTok via browser yang muncul
# 5. Set judul stream & kategori
# 6. Klik "Go Live" → Stream URL + Key muncul
```


### Alternatif: Streamlabs-based Generator (Juga Gratis)

Ada versi kedua yang menggunakan Streamlabs API tapi **tanpa perlu bayar Streamlabs Ultra**: [github](https://github.com/Loukious/StreamLabsTikTokStreamKeyGenerator)

```bash
git clone https://github.com/Loukious/StreamLabsTikTokStreamKeyGenerator.git
cd StreamLabsTikTokStreamKeyGenerator
pip install -r requirements.txt
python main.py
```


> ⚠️ **Catatan**: Tool ini butuh login TikTok sekali untuk mendapatkan token. Setelah itu, token bisa di-save dan di-reuse. [github](https://github.com/Loukious/StreamLabsTikTokStreamKeyGenerator)

## Arsitektur Lengkap di Linux Server (Tanpa OBS, Tanpa Bayar)

Berikut cara **semua berjalan di Linux server** via dashboard kamu: [127.0.0](http://127.0.0.1:8001/dashboard/?v=20260313b#/stream)

```
┌──────────────────────────────────────────────────────┐
│  LINUX SERVER (127.0.0.1:8001)                       │
│                                                      │
│  ┌─ Step 1: Generate Key ──────────────────────┐     │
│  │ TikTokStreamKeyGenerator (Python)           │     │
│  │   → Output: RTMP URL + Stream Key           │     │
│  │   → Auto-save ke config dashboard           │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  ┌─ Step 2: Dashboard Control ─────────────────┐     │
│  │ Command Center (:8001/#/stream)             │     │
│  │   → RTMP URL: rtmp://push-rtmp-*.tiktok...  │     │
│  │   → Stream Key: [auto-generated]            │     │
│  │   → Platform: TikTok                        │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  ┌─ Step 3: Stream via ffmpeg ─────────────────┐     │
│  │ AI Brain → Avatar Render → ffmpeg           │     │
│  │   → RTMP push ke TikTok server              │     │
│  └─────────────────────────────────────────────┘     │
│                                                      │
│  ❌ Tidak perlu OBS                                   │
│  ❌ Tidak perlu Streamlabs (berbayar)                 │
│  ❌ Tidak perlu Restream (berbayar)                   │
│  ❌ Tidak perlu BocaLive                              │
│  ❌ Tidak perlu Windows                               │
└──────────────────────────────────────────────────────┘
```

## Integrasi ke Dashboard Kamu

Yang perlu kamu tambahkan di backend Command Center: [127.0.0](http://127.0.0.1:8001/dashboard/?v=20260313b#/stream)

### 1. Auto Key Generator Module

Buat script wrapper yang bisa dipanggil dari dashboard:

```python
# /opt/ai-live-commerce/tools/tiktok_key_gen.py
# Wrapper untuk TikTokStreamKeyGenerator
# Dipanggil oleh dashboard saat "Mulai Sesi Live" diklik

import subprocess, json

def generate_tiktok_key(title="AI Live Commerce", category="shopping"):
    """Generate fresh TikTok RTMP URL + Stream Key"""
    # Panggil TikTokStreamKeyGenerator headless
    result = subprocess.run(
        ["python", "/opt/TikTokStreamKeyGenerator/generate.py",
         "--title", title, "--category", category],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    return {
        "rtmp_url": data["base_stream_url"],
        "stream_key": data["stream_key"],
        "share_url": data["shareable_url"]
    }
```

### 2. Update Dashboard Config

Di halaman **📡 Streaming & Platform**, update field ini: [127.0.0](http://127.0.0.1:8001/dashboard/?v=20260313b#/stream)

| Field | Dari (Mock) | Ke (Production) |
|---|---|---|
| **RTMP URL** | `rtmp://push.tiktok.test/live/` | Auto-fill dari key generator |
| **Stream Key** | `***123` | Auto-fill dari key generator |
| **ffmpeg path** | `C:\Users\dedy\...\ffmpeg.exe` | `/usr/bin/ffmpeg` |

### 3. Flow Saat Klik "Mulai Sesi Live"

1. Dashboard panggil `tiktok_key_gen.py` → dapat RTMP URL + Key fresh
2. Auto-fill ke RTMP Configuration
3. Validate RTMP Target → pastikan ● hijau semua
4. Start ffmpeg pipeline → push avatar stream ke TikTok
5. Dashboard monitor via Stream Posture → `idle` → `selling`

## Penting: Limitasi Stream Key TikTok

- Stream key **expired per sesi** — setiap kali live baru, harus generate key baru [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)
- Inilah kenapa integrasi **auto key generator** di backend sangat penting
- Tool GitHub di atas menghandle ini dengan **session token** yang di-cache [github](https://github.com/Loukious/TikTokStreamKeyGenerator)
- Pastikan akun TikTok tetap login (cookie/session disimpan di server)

## Apakah OBS Wajib?

**Tidak.** OBS hanya dibutuhkan kalau kamu streaming manual dari PC. Karena kamu punya sistem AI Live Commerce dengan ffmpeg, kamu **cukup pakai ffmpeg saja**. ffmpeg bisa push RTMP langsung ke TikTok server sama seperti OBS, tanpa GUI, tanpa Windows. [blog.tikfinity](https://blog.tikfinity.com/id/how-to-get-your-tiktok-stream-key-in-2025/)

```bash
# ffmpeg push (ini yang dashboard kamu jalankan di background)
ffmpeg -re -i /tmp/avatar_stream.mp4 \
  -c:v libx264 -preset veryfast -b:v 2500k \
  -vf "scale=1080:1920" \
  -c:a aac -ar 44100 -b:a 128k \
  -f flv "rtmp://REAL_URL/live/REAL_KEY"
```

Langkah pertama sekarang: **clone TikTokStreamKeyGenerator di server Linux**, coba login dengan akun TikTok kamu (yang sudah 5K followers), dan lihat apakah stream key berhasil di-generate.


Jadi akun kamu yang satunya **500 followers** dan hasilnya **"Not Approved"** saat coba generate key. Ini karena TikTok **minimal butuh 1.000 followers** untuk unlock fitur LIVE. Berikut semua alternatif selain tool Loukious dan cara mengatasi masalah 500 followers. [eskimo](https://www.eskimo.travel/en/blog/how-to-go-live-on-tiktok)

## Kenapa 500 Followers Ditolak?

TikTok secara resmi mensyaratkan **minimum 1.000 followers** untuk membuka fitur LIVE di semua region. Akun dengan 500 followers **belum memenuhi syarat**, sehingga: [tiktokstats](https://tiktokstats.com/articles/tiktok-live-content-monetization-requirements-2026-guide)

- Tool **StreamLabsTikTokStreamKeyGenerator** gagal karena TikTok API menolak request "Go Live" [github](https://github.com/Loukious/TikTokStreamKeyGenerator)
- **livecenter.tiktok.com** juga tidak akan muncul
- Opsi **"Cast to PC"** di app HP tidak tersedia [oscal](https://www.oscal.hk/blog/app/how-do/get-tiktok-rtmp-key)

## Cara Live TikTok dengan Kurang dari 1.000 Followers

Ada beberapa metode yang dilaporkan berhasil di 2026: [youtube](https://www.youtube.com/watch?v=202BKjm9kM0)

### Metode 1: Request Live Access via TikTok Support

1. Buka TikTok → **Profil** → **Menu (≡)** → **Settings and Privacy**
2. Pilih **Report a Problem** → **LIVE** → **I can't start a LIVE**
3. Tulis pesan: *"I am a content creator and would like to request LIVE access for my account for business/commerce purposes"*
4. Beberapa akun dilaporkan mendapat akses dalam **3–7 hari** meskipun di bawah 1K [agorapulse](https://www.agorapulse.com/blog/tiktok/how-to-go-live-on-tiktok-and-also-what-to-avoid-doing/)

### Metode 2: Tingkatkan Engagement (Paling Cepat)

TikTok kadang membuka akses LIVE untuk akun di bawah 1K jika memiliki **engagement tinggi**: [youtube](https://www.youtube.com/watch?v=zqf-JWScBWk)

- Upload **3–5 video per hari** selama seminggu
- Pastikan interaksi aktif: like, komentar, share dari orang lain [youtube](https://www.youtube.com/watch?v=zqf-JWScBWk)
- Gunakan hashtag trending Indonesia
- Dari 500 → 1.000 followers bisa dicapai dalam **1–2 minggu** dengan konten konsisten

### Metode 3: Gabung Agency TikTok (Instan)

Agency resmi TikTok bisa **bypass syarat 1.000 followers** dan langsung memberikan akses LIVE + stream key: [tiktok](https://www.tiktok.com/discover/tutorial-ambil-stream-key-di-tiktok-2026)

- Cari **"TikTok MCN agency Indonesia"** di Google
- Beberapa agency gratis untuk bergabung (mereka ambil commission dari gifts)
- Setelah join, stream key bisa didapat dari **dashboard agency** [tiktok](https://www.tiktok.com/discover/tutorial-ambil-stream-key-di-tiktok-2026)

### Metode 4: Restream Free Trial (Auto-Apply)

Restream punya **free tier** yang bisa digunakan untuk apply TikTok LIVE access: [youtube](https://www.youtube.com/watch?v=202BKjm9kM0)

1. Daftar **Restream.io** (gratis)
2. Hubungkan akun TikTok
3. Restream otomatis **mengajukan akses LIVE** ke TikTok
4. Ini kadang berhasil bahkan untuk akun di bawah 1K karena Restream adalah **partner resmi TikTok** [youtube](https://www.youtube.com/watch?v=202BKjm9kM0)
5. Setelah approved, kamu tidak harus streaming via Restream — cukup ambil keynya

## Alternatif Tool Selain Loukious

| Tool | Cara Kerja | Gratis | Butuh 1K? |
|---|---|---|---|
| **TikTokStreamKeyGenerator** (Loukious)  [github](https://github.com/Loukious/TikTokStreamKeyGenerator) | Python + Chrome, login TikTok, generate key | ✅ | ✅ Ya |
| **StreamLabsTikTokStreamKeyGenerator** (Loukious)  [github](https://github.com/Loukious/TikTokStreamKeyGenerator) | Via Streamlabs API, lebih stabil | ✅ | ✅ Ya |
| **Aitum Vertical**  [tiktok](https://www.tiktok.com/@livetutorials/video/7590214670250806550) | OBS plugin, auto-connect TikTok | ✅ | ✅ Ya |
| **Castr**  [castr](https://castr.com/blog/how-to-get-a-tiktok-stream-key/) | Cloud RTMP relay, auto-generate key | ❌ Berbayar | ✅ Ya |
| **TikTok Live Producer** (browser)  [oscal](https://www.oscal.hk/blog/app/how-do/get-tiktok-rtmp-key) | livecenter.tiktok.com | ✅ | ✅ Ya |
| **Agency Dashboard**  [tiktok](https://www.tiktok.com/discover/tutorial-ambil-stream-key-di-tiktok-2026) | Via MCN partner | ✅ | ❌ Bisa bypass |
| **Restream Free**  [youtube](https://www.youtube.com/watch?v=202BKjm9kM0) | Auto-apply access | ✅ (trial) | ❌ Kadang bypass |

> **Semua tool tetap butuh akun yang sudah punya akses LIVE dari TikTok.** Tool hanya membantu **extract stream key** — bukan bypass syarat followers. [github](https://github.com/Loukious/TikTokStreamKeyGenerator)

## Strategi Terbaik untuk Situasi Kamu

Kamu punya **2 akun**: satu 5K followers, satu 500 followers.

### Untuk akun 5K (harusnya sudah bisa):

Akun 5K seharusnya sudah memenuhi syarat. Jika stream key masih tidak bisa di-generate, kemungkinan:
- **Region Indonesia di-restrict** — coba gunakan tool Loukious dengan opsi **"Region Priority"** set ke region lain (misal Singapore/US) [github](https://github.com/Loukious/TikTokStreamKeyGenerator)
- Akun pernah **kena pelanggaran** community guidelines [oscal](https://www.oscal.hk/blog/app/how-do/get-tiktok-rtmp-key)
- Belum pernah login ke **TikTok LIVE Studio** sebelumnya — coba login sekali dulu di desktop `tiktok.com` → klik "Go LIVE" [oscal](https://www.oscal.hk/blog/app/how-do/get-tiktok-rtmp-key)

### Untuk akun 500 (belum bisa):

1. **Prioritas utama**: naikkan ke 1.000 followers dulu (paling realistis)
2. **Jalan pintas**: gabung agency TikTok Indonesia — bisa unlock akses LIVE instan [tiktok](https://www.tiktok.com/discover/tutorial-ambil-stream-key-di-tiktok-2026)
3. **Coba Restream free**: kadang bisa bypass untuk akun aktif [youtube](https://www.youtube.com/watch?v=202BKjm9kM0)

## Integrasi ke Dashboard Linux

Setelah **salah satu akun** berhasil generate key, flow di dashboard kamu: [127.0.0](http://127.0.0.1:8001/dashboard/?v=20260313b#/stream)

```
┌─ Akun TikTok (5K followers) ─────────────────────┐
│                                                    │
│  Tool generate key (Loukious/Aitum/Agency)         │
│       ↓                                            │
│  Output: RTMP URL + Stream Key                     │
│       ↓                                            │
│  Dashboard (:8001/#/stream)                        │
│  → Paste RTMP URL + Key                            │
│  → ffmpeg push dari Linux                          │
│  → LIVE!                                           │
└────────────────────────────────────────────────────┘
```

Fokuskan dulu di **akun 5K** — itu yang paling dekat bisa digunakan. Coba jalankan tool Loukious dengan akun tersebut, dan pastikan kamu sudah pernah login ke `tiktok.com` di browser desktop dan klik "Go LIVE" minimal sekali sebelumnya. [oscal](https://www.oscal.hk/blog/app/how-do/get-tiktok-rtmp-key)


Oke, saya paham situasinya sekarang. Kamu ingin tahu bagaimana **metode Virtual Camera** bekerja untuk **bypass kebutuhan stream key** — dan apakah bisa diintegrasikan ke sistem AI Live Commerce kamu. Berikut penjelasan lengkap semua opsi.

## Cara Virtual Camera Bekerja (Tanpa RTMP)

Alur virtual camera sangat sederhana: [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)

```
Software Apapun (OBS/BocaLive/AI kamu)
    ↓ Virtual Camera output
TikTok Live Studio (desktop app)
    ↓ Langsung konek ke TikTok server (internal)
Penonton TikTok
```

**Keunggulannya**: Tidak butuh RTMP URL, tidak butuh Stream Key, tidak butuh approval khusus. TikTok Live Studio yang handle koneksi ke server TikTok secara internal — kamu cukup "menyuapi" video lewat virtual camera. [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)

## Syarat Virtual Camera di TikTok Live Studio

Meskipun tidak butuh stream key, tetap ada syarat: [tiktok](https://www.tiktok.com/discover/obs-virtual-camera-tidak-muncul-di-tiktok-studio)

- Akun TikTok tetap butuh **minimal 1.000 followers** untuk bisa Go LIVE [tiktok](https://www.tiktok.com/discover/obs-virtual-camera-tidak-muncul-di-tiktok-studio)
- Harus install **TikTok Live Studio** (Windows/Mac only, **tidak ada Linux**) [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)
- Harus pernah live **minimal 25 menit** dulu dari TikTok Live Studio sebelum virtual camera muncul sebagai opsi [tiktok](https://www.tiktok.com/discover/obs-virtual-camera-tidak-muncul-di-tiktok-studio)
- PC Windows/Mac **harus tetap menyala** selama live berlangsung

## 3 Cara Implementasi Virtual Camera

### Opsi A: BocaLive → TikTok Live Studio (Cara Kamu Sekarang)

Ini yang kamu sudah coba di Tokopedia. Untuk TikTok: [ppl-ai-file-upload.s3.amazonaws](https://ppl-ai-file-upload.s3.amazonaws.com/web/direct-files/attachments/images/167324671/bc6f4c8f-46d3-422a-9bf3-b521d22f3a16/image.jpg)

1. Buka **BocaLive** → set AI avatar & konten
2. BocaLive otomatis register sebagai **virtual camera** di sistem
3. Buka **TikTok Live Studio** → pilih kamera: **"BocaLive"**
4. Pilih audio: **VB-Audio Virtual Cable** (untuk fix audio tidak terdeteksi)
5. Klik **Go Live** → selesai, live tanpa RTMP [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)

**Kekurangan**: BocaLive berbayar ($58/bulan), dan kamu sudah punya AI avatar engine sendiri di dashboard. [videototext](https://www.videototext.io/ru/blog/top-6-obs-alternatives-for-enhanced-live-streaming)

### Opsi B: OBS Virtual Camera → TikTok Live Studio (GRATIS)

Ini cara **paling populer dan gratis** di Indonesia: [tiktok](https://www.tiktok.com/@streamhacks.id/video/7479268837607640326)

1. Buka **OBS Studio** (gratis) → setup scene dengan avatar/konten kamu
2. Klik **"Start Virtual Camera"** di OBS [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)
3. Buka **TikTok Live Studio** → pilih kamera: **"OBS Virtual Camera"** [tiktok](https://www.tiktok.com/@anggi.setya/video/7506491511635201287)
4. Audio: pilih **"OBS Audio"** atau virtual cable
5. Klik **Go Live** [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)

### Opsi C: AI Live Commerce → OBS → TikTok Live Studio

Ini cara **mengintegrasikan dashboard kamu** dengan virtual camera: [youtube](https://www.youtube.com/watch?v=5kZIeQd9LAk)

```
Dashboard Linux (:8001)
    ↓ render avatar video
    ↓ output ke local RTMP server (nginx-rtmp di Linux)
         ↓
OBS (di Windows) ← ambil dari Media Source RTMP lokal
    ↓ Start Virtual Camera
TikTok Live Studio ← pilih "OBS Virtual Camera"
    ↓ Go Live
TikTok
```

## Perbandingan Semua Metode

| | RTMP Direct | Virtual Camera | Streamlabs Plugin OBS |
|---|---|---|---|
| **Butuh Stream Key** | ✅ Ya | ❌ Tidak | ❌ Tidak  [youtube](https://www.youtube.com/watch?v=mdzYJbqaBbM) |
| **Butuh Windows PC ON** | ❌ Tidak | ✅ Ya | ✅ Ya |
| **Bisa Full Linux** | ✅ Ya | ❌ Tidak | ❌ Tidak |
| **Butuh 1K Followers** | ✅ Ya | ✅ Ya | ✅ Ya |
| **Biaya** | Gratis | Gratis (OBS) / $58/bln (BocaLive) | Gratis  [youtube](https://www.youtube.com/watch?v=kTFFsWVzF9U) |
| **Kompleksitas** | Rendah | Sedang | Rendah |
| **Cocok untuk AI Automation** | ✅ Ideal | ⚠️ Semi-manual | ⚠️ Semi-manual |

## Opsi Terbaik: Streamlabs Plugin di OBS (Gratis, Tanpa Stream Key)

Ini **discovery baru** yang sangat relevan — kamu bisa live di TikTok dari OBS **tanpa stream key sama sekali**, dan **gratis** untuk TikTok: [youtube](https://www.youtube.com/watch?v=mdzYJbqaBbM)

1. **Install OBS Studio** (gratis, ada di Windows/Mac/Linux)
2. **Install Plugin Streamlabs untuk OBS** — bukan Streamlabs Desktop yang berbayar, tapi **plugin OBS yang gratis** [youtube](https://www.youtube.com/watch?v=mdzYJbqaBbM)
3. Login ke akun TikTok via plugin
4. Setup scene di OBS (bisa ambil feed dari Linux server kamu via RTMP lokal)
5. Klik **Start Streaming** → plugin langsung konek ke TikTok **tanpa perlu stream key manual** [youtube](https://www.youtube.com/watch?v=kTFFsWVzF9U)
6. Untuk TikTok, ini **gratis** karena Streamlabs resmi partner TikTok [youtube](https://www.youtube.com/watch?v=kTFFsWVzF9U)
7. Bahkan bisa **multistream** ke YouTube + TikTok sekaligus secara gratis [youtube](https://www.youtube.com/watch?v=kTFFsWVzF9U)

### Integrasi dengan Dashboard Linux Kamu

```
┌─────────────────────────────────────┐
│ LINUX SERVER                        │
│ Dashboard (:8001) → AI Avatar       │
│    ↓ render video+audio             │
│ nginx-rtmp (:1935) ← local stream   │
└──────────────┬──────────────────────┘
               │ RTMP lokal (LAN)
┌──────────────▼──────────────────────┐
│ PC WINDOWS (bisa low-spec)          │
│ OBS Studio                          │
│  └─ Media Source: rtmp://LINUX:1935 │
│  └─ Plugin Streamlabs (TikTok)      │
│  └─ Start Streaming → TikTok LIVE   │
└─────────────────────────────────────┘
```

Dengan cara ini:
- **Linux server tetap jadi otak** — semua AI processing di sana [127.0.0](http://127.0.0.1:8001/dashboard/?v=20260313b#/stream)
- **PC Windows cuma jadi relay** — tinggal buka OBS, minimal resource
- **Tidak perlu stream key** [youtube](https://www.youtube.com/watch?v=mdzYJbqaBbM)
- **Tidak perlu bayar** apapun [youtube](https://www.youtube.com/watch?v=kTFFsWVzF9U)
- Dashboard kamu tetap menjadi **single control center**

## Rekomendasi Berdasarkan Situasi Kamu

Karena akun 5K followers kamu **tidak bisa dapat stream key** (region Indonesia di-block), dan kamu **tidak mau bayar**:

1. **Sekarang (quickest win)**: Install OBS + Plugin Streamlabs di PC Windows → login TikTok → live langsung, gratis, tanpa stream key [youtube](https://www.youtube.com/watch?v=kTFFsWVzF9U)
2. **Jangka pendek**: Setup nginx-rtmp di Linux server → OBS di Windows ambil feed dari Linux → relay ke TikTok via Streamlabs plugin
3. **Jangka panjang**: Explore TikTok API partnership atau agency untuk dapat RTMP direct — agar bisa full Linux tanpa Windows sama sekali

Mau saya buatkan panduan langkah-langkah detail untuk install plugin Streamlabs di OBS?


Tidak, bukan hanya Streamlabs dan Restream. Ada **banyak penyedia lain** yang bisa generate stream key TikTok, bahkan ada yang **gratis**. Dan untuk pertanyaan kedua — **ya, virtual camera di Ubuntu Linux bisa** menggunakan `v4l2loopback`. Berikut penjelasan lengkapnya.

## Semua Penyedia Stream Key TikTok

Berikut daftar lengkap semua cara mendapatkan RTMP stream key TikTok, dari gratis sampai berbayar: [tiktok](https://www.tiktok.com/@livetutorials/video/7590214670250806550)

| Penyedia | Gratis? | Cara Kerja | Cocok Linux? |
|---|---|---|---|
| **Aitum Vertical + Aitum Multistream** | ✅ Gratis | Plugin OBS, auto-generate key, best vertical workflow | ✅ OBS Linux  [tiktok](https://www.tiktok.com/@livetutorials/video/7590214670250806550) |
| **TokTutorials.com** | ✅ Gratis | Web-based, generate free stream key langsung | ✅ Browser saja  [youtube](https://www.youtube.com/watch?v=i22C2wfj54o) |
| **Loukious Generator (GitHub)** | ✅ Gratis | Python script, generate via TikTok API | ✅ Python Linux  [github](https://github.com/Loukious/TikTokStreamKeyGenerator) |
| **Agency TikTok** | ✅ Gratis | Gabung agency, key dari dashboard agency | ✅ Copy key saja  [tiktok](https://www.tiktok.com/discover/tutorial-ambil-stream-key-di-tiktok-2026) |
| **Restream** | ⚠️ Free tier ada | Auto-apply, expedited review | ✅ Browser/API  [restream](https://restream.io/learn/platforms/how-to-find-tiktok-stream-key/) |
| **Streamlabs** | ⚠️ Free tier ada | Plugin OBS, login TikTok | ⚠️ Windows/Mac only |
| **Meld Studio** | ❌ Berbayar | Desktop app, auto-connect TikTok | ❌ Windows/Mac  [tiktok](https://www.tiktok.com/@livetutorials/video/7590214670250806550) |
| **Castr** | ❌ Berbayar | Cloud RTMP relay | ✅ Cloud-based |
| **PRISM Live Studio** | ✅ Gratis | Mobile + desktop, multi-platform | ❌ Windows/Mac/Mobile  [riverside](https://riverside.com/blog/best-restream-alternatives) |

### Yang Paling Menjanjikan: Aitum (Gratis + Linux)

**Aitum Vertical** adalah plugin OBS yang dirancang khusus untuk **vertical streaming ke TikTok**: [youtube](https://www.youtube.com/watch?v=3HQ-mZ36G2M)

1. Install OBS Studio di Linux: `sudo apt install obs-studio`
2. Install plugin **Aitum Vertical** dari [aitum.tv/products/vertical](https://aitum.tv/products/vertical)
3. Install **Aitum Multistream** untuk auto-generate stream key [youtube](https://www.youtube.com/watch?v=3HQ-mZ36G2M)
4. Login akun TikTok → key otomatis di-generate
5. **100% gratis**, bahkan untuk multi-platform streaming [tiktok](https://www.tiktok.com/@livetutorials/video/7590214670250806550)

### TokTutorials.com (Free Stream Key Generator)

Ini yang paling simple — **web-based, gratis**: [youtube](https://www.youtube.com/watch?v=i22C2wfj54o)

1. Kunjungi **toktutorials.com/stream-key**
2. Login akun TikTok
3. Stream key langsung muncul
4. Copy dan paste ke dashboard kamu

## Virtual Camera di Ubuntu Linux: BISA!

Linux punya **v4l2loopback** — kernel module yang membuat **virtual webcam device** persis seperti BocaLive di Windows. [stackoverflow](https://stackoverflow.com/questions/68433415/using-v4l2loopback-virtual-cam-with-google-chrome-or-chromium-on-linux-while-hav)

### Cara Kerja v4l2loopback

```
AI Avatar Engine (dashboard kamu)
    ↓ render video
ffmpeg → menulis ke /dev/video42 (virtual camera)
    ↓
Aplikasi apapun "melihat" /dev/video42 sebagai webcam asli
    ↓
TikTok Live Studio / OBS / Browser → pakai sebagai kamera
```


### Setup v4l2loopback di Ubuntu

```bash
# 1. Install v4l2loopback
sudo apt update
sudo apt install v4l2loopback-dkms v4l2loopback-utils

# 2. Load kernel module (buat virtual camera di /dev/video42)
sudo modprobe v4l2loopback \
  exclusive_caps=1 \
  video_nr=42 \
  card_label="AI Live Commerce Cam"

# 3. Verifikasi
v4l2-ctl --list-devices
# Output: "AI Live Commerce Cam" → /dev/video42
```


### Feed Video dari AI Avatar ke Virtual Camera

```bash
# ffmpeg menulis output avatar ke virtual camera
ffmpeg -re \
  -i /tmp/avatar_stream.mp4 \
  -vcodec rawvideo -pix_fmt yuv420p \
  -f v4l2 /dev/video42
```


Sekarang `/dev/video42` adalah "webcam" yang menampilkan AI avatar kamu. Aplikasi apapun yang buka webcam akan melihat avatar.

### Auto-load Saat Boot

```bash
# Tambahkan ke /etc/modules-load.d/
echo "v4l2loopback" | sudo tee /etc/modules-load.d/v4l2loopback.conf

# Tambahkan opsi
echo 'options v4l2loopback exclusive_caps=1 video_nr=42 card_label="AI Live Commerce Cam"' | \
  sudo tee /etc/modprobe.d/v4l2loopback.conf
```


## Arsitektur Lengkap: Full Ubuntu, Tanpa Windows

```
┌──────────────────────────────────────────────────────┐
│  UBUNTU SERVER                                       │
│                                                      │
│  Dashboard (:8001/#/stream)  ← kontrol terpusat      │
│       ↓                                              │
│  AI Brain → Avatar Engine → render video+audio       │
│       ↓                                              │
│  ┌─ JALUR A: RTMP Direct (jika punya key) ────────┐ │
│  │ ffmpeg → RTMP push → TikTok server              │ │
│  │ (paling ideal, tanpa app tambahan)              │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ JALUR B: Virtual Camera (tanpa key) ──────────┐ │
│  │ ffmpeg → /dev/video42 (v4l2loopback)            │ │
│  │     ↓                                           │ │
│  │ OBS Studio (Linux) → Aitum plugin → TikTok      │ │
│  │ (plugin handle koneksi, tanpa stream key)       │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ❌ Tidak perlu Windows                               │
│  ❌ Tidak perlu BocaLive ($58/bln)                    │
│  ❌ Tidak perlu Streamlabs/Restream berbayar          │
└──────────────────────────────────────────────────────┘
```

## Rekomendasi: Urutan Coba

1. **Pertama** — Coba **TokTutorials.com/stream-key** (gratis, web-based, cukup login TikTok) → kalau dapat key, langsung pakai ffmpeg RTMP push dari Linux [youtube](https://www.youtube.com/watch?v=i22C2wfj54o)
2. **Kedua** — Install **OBS Studio + Aitum Vertical** di Ubuntu → plugin auto-generate key, gratis [tiktok](https://www.tiktok.com/@livetutorials/video/7590214670250806550)
3. **Ketiga** — Setup **v4l2loopback** + OBS di Ubuntu → virtual camera sebagai fallback jika semua gagal [teknocerdas](https://teknocerdas.com/serba-serbi/membuat-webcam-palsu-pada-ubuntu-dengan-v4l2loopback/)
4. **Terakhir** — Gabung **agency TikTok** untuk bypass semua limitasi region Indonesia [tiktok](https://www.tiktok.com/discover/tutorial-ambil-stream-key-di-tiktok-2026)

Untuk **integrasi ke dashboard kamu**, update field di `#/stream`: [127.0.0](http://127.0.0.1:8001/dashboard/?v=20260313b#/stream)
- **ffmpeg path**: `/usr/bin/ffmpeg`
- **RTMP URL**: dari key yang didapat (TokTutorials/Aitum/Agency)
- **Mode**: ubah dari `mock` ke `live`

Mau saya buatkan script lengkap untuk setup v4l2loopback + OBS + Aitum di Ubuntu?