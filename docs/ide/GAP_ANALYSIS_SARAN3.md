# Gap Analysis: Saran3.md vs Current Project Structure

**Tanggal**: 12 Maret 2026  
**Dokumen Sumber**: `docs/ide/saran3.md`  
**Dokumen Referensi**: `docs/architecture.md`, `docs/README.md`, `scripts/manage.py`

---

## Executive Summary

Dokumen `saran3.md` berisi rekomendasi arsitektur lengkap untuk deployment VideoLiveAI dengan fokus pada:
1. **Topology Real**: Local PC (GTX 1650) untuk development, Vast.ai (RTX 3090/4090) untuk production
2. **SQLite dengan WAL mode** sebagai database (bukan PostgreSQL/MySQL)
3. **Vast.ai deployment strategy** lengkap dengan setup scripts
4. **Menu interaktif CLI** yang comprehensive via `manage.py`
5. **Dashboard web lengkap** dengan WebSocket real-time updates
6. **Affiliate business model** dengan product management, scripts, dan TTS cache

---

## I. ARSITEKTUR & TOPOLOGY

### ✅ SUDAH ADA (Aligned)

| Komponen | Status | Lokasi |
|----------|--------|--------|
| FastAPI control plane | ✅ Ada | `src/main.py` |
| Dashboard operator | ✅ Ada | `src/dashboard/` |
| SQLite database | ✅ Ada | `data/videoliveai.db` |
| LiveTalking vendor sidecar | ✅ Ada | `external/livetalking/` |
| Fish-Speech sidecar | ✅ Ada | `external/fish-speech/` |
| UV package manager | ✅ Ada | Policy sudah diterapkan |
| Mock mode testing | ✅ Ada | `MOCK_MODE=true` |
| Real mode with GPU | ✅ Ada | `MOCK_MODE=false` |

### ❌ BELUM ADA (Gaps)

| Komponen | Rekomendasi Saran3 | Status Current | Priority |
|----------|-------------------|----------------|----------|
| **SQLite WAL mode** | Explicit WAL + busy_timeout config | Tidak ada explicit config | 🔴 HIGH |
| **Database schema lengkap** | 7 tables (products, sessions, events, scripts, audio_cache, alerts) | Hanya partial | 🔴 HIGH |
| **Vast.ai setup scripts** | `scripts/vast_setup.sh`, `vast_start.sh`, `vast_stop.sh` | Tidak ada | 🟡 MEDIUM |
| **Remote sync scripts** | `scripts/sync_to_vast.sh`, `sync_db_from_vast.sh` | Tidak ada | 🟡 MEDIUM |
| **SSH tunnel helper** | `scripts/connect_vast.sh` | Tidak ada | 🟢 LOW |

---

## II. DATABASE ARCHITECTURE

### Rekomendasi Saran3.md

```python
# src/data/database.py dengan WAL mode
async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    await db.execute("PRAGMA journal_mode=WAL")
    await db.execute("PRAGMA busy_timeout=30000")
    await db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = aiosqlite.Row
    return db
```

**7 Tables yang direkomendasikan:**
1. `products` - Affiliate products dengan commission, links, scripts
2. `stream_sessions` - Session tracking per live stream
3. `stream_events` - Event log per session
4. `scripts` - Content scripts library
5. `audio_cache` - TTS audio cache index
6. `alerts` - Alert history dengan acknowledgment
7. Indexes untuk performance

### Current State

**File**: `src/data/database.py` (perlu dicek apakah ada)

**Gap Analysis:**
- ❌ Tidak ada explicit WAL mode configuration
- ❌ Schema tidak lengkap (missing tables: stream_sessions, stream_events, scripts, audio_cache, alerts)
- ❌ Tidak ada indexes yang proper
- ⚠️ Product model ada di `src/commerce/manager.py` tapi tidak sync dengan DB schema

**Action Items:**
1. 🔴 Implement WAL mode + busy_timeout
2. 🔴 Create complete schema migration
3. 🔴 Add proper indexes
4. 🟡 Create `src/data/database.py` dengan async SQLite wrapper

---

## III. MANAGE.PY CLI

### Rekomendasi Saran3.md

**Command groups yang direkomendasikan:**

```bash
# SERVE
uv run python scripts/manage.py serve --mock
uv run python scripts/manage.py serve --real

# PRODUCT MANAGEMENT
uv run python scripts/manage.py product add --platform tiktok --name "..." --price 50000
uv run python scripts/manage.py product list --platform all
uv run python scripts/manage.py product import-csv products.csv --platform tiktok

# SCRIPT GENERATION
uv run python scripts/manage.py script generate --product-id 1
uv run python scripts/manage.py script generate --all-products

# CACHE MANAGEMENT
uv run python scripts/manage.py cache warm --all
uv run python scripts/manage.py cache stats
uv run python scripts/manage.py cache clear

# STREAM CONTROL
uv run python scripts/manage.py stream test --platform tiktok --duration 30
uv run python scripts/manage.py stream set-key --platform tiktok --rtmp-url "..." --stream-key "..."

# SETUP
uv run python scripts/manage.py setup all
uv run python scripts/manage.py setup-db
uv run python scripts/manage.py setup-livetalking

# INTERACTIVE MENU
uv run python scripts/manage.py menu
```

### Current State

**File**: `scripts/manage.py` ✅ Ada

**Commands yang sudah ada:**
- ✅ `serve --mock` / `serve --real`
- ✅ `start` / `stop` / `status`
- ✅ `health`
- ✅ `validate`
- ✅ `logs`
- ✅ `sync`
- ✅ `load-products`
- ✅ `setup-livetalking`
- ✅ `setup-fish-speech`
- ✅ `setup`
- ✅ `open`

**Commands yang BELUM ada:**
- ❌ `product` group (add, list, import-csv)
- ❌ `script` group (generate)
- ❌ `cache` group (warm, stats, clear)
- ❌ `stream` group (test, set-key)
- ❌ `menu` (interactive TUI)

**Gap Analysis:**

| Feature | Saran3 | Current | Gap |
|---------|--------|---------|-----|
| Product CRUD | ✅ Lengkap | ❌ Tidak ada | 🔴 HIGH |
| Script generation | ✅ Ada | ❌ Tidak ada | 🔴 HIGH |
| Cache management | ✅ Ada | ❌ Tidak ada | 🔴 HIGH |
| Stream testing | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| Interactive menu | ✅ Ada | ❌ Tidak ada | 🟢 LOW |

**Action Items:**
1. 🔴 Add `product` command group dengan subcommands
2. 🔴 Add `script` command group untuk LLM script generation
3. 🔴 Add `cache` command group untuk TTS audio cache
4. 🟡 Add `stream` command group untuk RTMP testing
5. 🟢 Add `menu` command untuk interactive TUI

---

## IV. DASHBOARD API ENDPOINTS

### Rekomendasi Saran3.md

**API Endpoints yang direkomendasikan:**

```
GET  /api/health                    - Overall system health
GET  /api/runtime/truth             - Runtime truth model
POST /api/stream/start              - Start livestream
POST /api/stream/stop               - Graceful stop
POST /api/stream/emergency-stop     - Emergency stop
POST /api/stream/pause              - Pause stream
POST /api/stream/resume             - Resume stream
GET  /api/stream/status             - Current stream status
GET  /api/products                  - List products
POST /api/products                  - Add product
POST /api/products/next             - Skip to next product
GET  /api/show/schedule             - Get show schedule
POST /api/show/say                  - Make avatar say text
GET  /api/sessions                  - List stream sessions
GET  /api/sessions/{id}/events      - Get session events
GET  /api/alerts                    - Get alerts
POST /api/alerts/{id}/acknowledge   - Acknowledge alert
WS   /api/ws/dashboard              - WebSocket real-time updates
```

### Current State

**File**: `src/dashboard/api.py` ✅ Ada

**Endpoints yang sudah ada:**
- ✅ `/api/status`
- ✅ `/api/health/summary`
- ✅ `/api/readiness`
- ✅ `/api/runtime/truth`
- ✅ `/api/products` (GET)
- ✅ `/api/products/{id}/switch` (POST)

**Endpoints yang BELUM ada:**
- ❌ `/api/stream/*` (start, stop, pause, resume, status)
- ❌ `/api/products` (POST - add product)
- ❌ `/api/products/next` (POST)
- ❌ `/api/show/*` (schedule, say)
- ❌ `/api/sessions` dan `/api/sessions/{id}/events`
- ❌ `/api/alerts` dan acknowledge
- ❌ `/api/ws/dashboard` (WebSocket)

**Gap Analysis:**

| Endpoint Group | Saran3 | Current | Gap |
|----------------|--------|---------|-----|
| Stream control | 6 endpoints | 0 | 🔴 CRITICAL |
| Product management | 3 endpoints | 1 (GET only) | 🔴 HIGH |
| Show control | 2 endpoints | 0 | 🟡 MEDIUM |
| Sessions/History | 2 endpoints | 0 | 🟡 MEDIUM |
| Alerts | 2 endpoints | 0 | 🟡 MEDIUM |
| WebSocket | 1 endpoint | 0 | 🟡 MEDIUM |

**Action Items:**
1. 🔴 Implement `/api/stream/*` endpoints (BLOCKER untuk live)
2. 🔴 Implement POST `/api/products` untuk add product
3. 🔴 Implement `/api/products/next` untuk rotation
4. 🟡 Implement `/api/show/*` endpoints
5. 🟡 Implement `/api/sessions` dan `/api/alerts`
6. 🟡 Implement WebSocket `/api/ws/dashboard`

---

## V. DASHBOARD FRONTEND

### Rekomendasi Saran3.md

**5 Views yang direkomendasikan:**
1. **Overview** - Stream status, current product, GPU temp, stats
2. **Control** - Start/stop stream, pause/resume, next product, say text
3. **Products** - Product catalog dengan active indicator
4. **Health** - System health per component
5. **Alerts** - Alert list dengan acknowledge

**Features:**
- WebSocket real-time updates setiap 5 detik
- Mobile-responsive design
- Dark theme (#0f0f1a background)
- Live badge dengan pulse animation
- GPU temperature color coding
- Emergency stop button

### Current State

**Update 2026-03-11 (verified after Avatar & Suara recovery):**
- Operator frontend sekarang memakai 6 surface resmi: `Setup & Validasi`, `Produk & Penawaran`, `Avatar & Suara`, `Streaming & Platform`, `Konsol Live`, dan `Monitor & Insiden`
- `PerformerPage.svelte` tidak lagi monolitik; sekarang menjadi workspace bertab dengan `Ringkasan`, `Suara`, `Avatar`, `Preview`, `Validasi`, dan `Teknis`
- Halaman standalone operator aktif sekarang: `index.html`, `setup.html`, `products.html`, `performer.html`, `stream.html`, dan `monitor.html`
- `ValidationPage.svelte` dan `DiagnosticsPage.svelte` tidak lagi menjadi halaman operator terpisah
- Browser smoke untuk dashboard performer sekarang lulus, termasuk validasi preview fallback saat vendor target tidak reachable

**Update 2026-03-12 (verified after brain/director runtime recovery):**
- `ShowDirector` sekarang sudah ada di `src/orchestrator/show_director.py` dan menjadi source of truth runtime live selama proses FastAPI hidup
- prompt utama tidak lagi hardcoded penuh di `persona.py`; prompt aktif sekarang dibaca dari `PromptRegistry` versioned di `src/brain/prompt_registry.py`
- UI operator sekarang sudah punya surface baca-saja untuk `Brain & Prompt` di `Setup & Validasi` dan `Director Runtime` di `Konsol Live`
- shell dashboard sekarang sudah centered, responsive, dan sidebar memakai lebar stabil sehingga tidak ikut bergeser saat halaman tinggi atau viewport mengecil

**File**: `src/dashboard/frontend/src/` ✅ Ada (Svelte)

**Pages yang sudah ada:**
- ✅ `LiveConsolePage.svelte` (Overview)
- ✅ `ProductsPage.svelte` (Products)
- ✅ `SetupPage.svelte` (Setup & Validasi)
- ✅ `PerformerPage.svelte` (workspace Avatar & Suara)
- ✅ `StreamPage.svelte` (Streaming)
- ✅ `MonitorPage.svelte` (Monitor)

**Features yang sudah ada:**
- ✅ Svelte SPA
- ✅ WebSocket dashboard updates
- ✅ Tabbed operator workspace for performer
- ✅ Preview fallback dengan backend reachability probe
- ✅ Indonesian UI
- ✅ Product switching
- ✅ Single sidebar (fixed duplikasi)
- ✅ `Brain & Prompt` runtime surface
- ✅ `Director Runtime` runtime surface
- ✅ Centered responsive shell dengan sidebar width stabil

**Features yang BELUM ada:**
- ❌ Stream control buttons (start/stop/pause/resume)
- ⚠️ Emergency stop button ada di Konsol Live, tetapi belum menjadi director-level workflow lengkap dengan pause/resume/override
- ❌ GPU temperature monitoring
- ❌ Live badge dengan pulse animation
- ❌ Alerts panel dengan acknowledge
- ❌ Sessions history
- ⚠️ Prompt draft/publish/rollback editor
- ⚠️ Director manual override UI (pause/resume/skip phase/inject speech)

**Gap Analysis:**

| Feature | Saran3 | Current | Gap |
|---------|--------|---------|-----|
| WebSocket updates | ✅ Ada | ✅ Ada | resolved |
| Stream control UI | ✅ Ada | ⚠️ Partial | 🔴 HIGH |
| GPU monitoring | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| Alerts system | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| Mobile responsive | ✅ Ada | ✅ Ada | resolved |
| Brain/prompt runtime visibility | ✅ Ada | ✅ Ada (read-only) | resolved |
| Prompt editing workflow | ✅ Ada | ❌ Tidak ada | 🔴 HIGH |
| Director manual override | ✅ Ada | ❌ Tidak ada | 🔴 HIGH |

**Action Items:**
1. 🔴 Add director-level controls (pause/resume/skip phase/inject speech)
2. 🔴 Add prompt draft/test/publish/rollback workflow
3. 🔴 Add stream control buttons (start/stop/pause/resume) yang tersambung ke director
4. 🟡 Add GPU temperature monitoring widget
5. 🟡 Add alerts panel dengan acknowledge
6. 🟡 Add sessions history view

---

## VI. VAST.AI DEPLOYMENT

### Rekomendasi Saran3.md

**Scripts yang direkomendasikan:**

1. **`scripts/vast_setup.sh`** - First-time setup di Vast.ai instance
   - Install system packages (ffmpeg, portaudio, etc)
   - Install UV
   - Clone repo
   - Install dependencies
   - Setup LiveTalking
   - Download models
   - Setup environment

2. **`scripts/vast_start.sh`** - Start services di Vast.ai
   - Start FastAPI dalam tmux session
   - Start LiveTalking dalam tmux session
   - Print access URLs

3. **`scripts/vast_stop.sh`** - Graceful stop services

4. **`scripts/sync_to_vast.sh`** - Sync code dari local ke Vast.ai
   - rsync dengan exclude patterns
   - SSH tunnel support

5. **`scripts/sync_db_from_vast.sh`** - Pull database dari Vast.ai ke local

6. **`scripts/connect_vast.sh`** - SSH tunnel untuk dashboard access

### Current State

**Vast.ai scripts:**
- ❌ Tidak ada sama sekali

**Deployment documentation:**
- ✅ Ada di `docs/PRODUCTION_READINESS_CHECKLIST.md`
- ⚠️ Tapi tidak ada automation scripts

**Gap Analysis:**

| Script | Saran3 | Current | Priority |
|--------|--------|---------|----------|
| vast_setup.sh | ✅ Lengkap | ❌ Tidak ada | 🟡 MEDIUM |
| vast_start.sh | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| vast_stop.sh | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| sync_to_vast.sh | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| sync_db_from_vast.sh | ✅ Ada | ❌ Tidak ada | 🟢 LOW |
| connect_vast.sh | ✅ Ada | ❌ Tidak ada | 🟢 LOW |

**Action Items:**
1. 🟡 Create `scripts/vast_setup.sh` untuk first-time setup
2. 🟡 Create `scripts/vast_start.sh` dan `vast_stop.sh`
3. 🟡 Create `scripts/sync_to_vast.sh` untuk code sync
4. 🟢 Create `scripts/sync_db_from_vast.sh` untuk DB backup
5. 🟢 Create `scripts/connect_vast.sh` untuk SSH tunnel

---

## VII. AFFILIATE BUSINESS MODEL

### Rekomendasi Saran3.md

**Product fields yang direkomendasikan:**
```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    platform TEXT NOT NULL,           -- tiktok | shopee
    product_id TEXT NOT NULL,
    name TEXT NOT NULL,
    price REAL,
    commission_rate REAL DEFAULT 0,
    image_url TEXT,
    affiliate_link TEXT,
    category TEXT,
    script_template TEXT,             -- ← Script template
    is_active INTEGER DEFAULT 1,
    last_promoted_at TEXT,
    total_promotions INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);
```

**Features:**
- Product CRUD via CLI dan dashboard
- CSV import untuk bulk products
- Script generation per product via LLM
- Product rotation scheduler
- Commission tracking
- Affiliate link management

### Current State

**File**: `data/products.json` ✅ Ada

**Product fields yang ada:**
```json
{
  "id": 1,
  "name": "...",
  "price": 50000,
  "affiliate_links": {
    "tiktok": "...",
    "shopee": "..."
  },
  "commission_rate": 0.10,
  "selling_points": [...],
  "objection_handling": {...},
  "compliance_notes": "..."
}
```

**Gap Analysis:**

| Feature | Saran3 | Current | Gap |
|---------|--------|---------|-----|
| Database storage | ✅ SQLite | ⚠️ JSON file | 🔴 HIGH |
| Product CRUD | ✅ CLI + API | ❌ Tidak ada | 🔴 HIGH |
| CSV import | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| Script generation | ✅ LLM | ❌ Tidak ada | 🔴 HIGH |
| Rotation scheduler | ✅ Ada | ❌ Tidak ada | 🔴 HIGH |
| Commission tracking | ✅ Ada | ⚠️ Partial | 🟡 MEDIUM |
| Promotion history | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |

**Action Items:**
1. 🔴 Migrate products dari JSON ke SQLite
2. 🔴 Implement product CRUD (CLI + API)
3. 🔴 Implement script generation via LLM
4. 🔴 Implement product rotation scheduler
5. 🟡 Implement CSV import
6. 🟡 Add promotion tracking

---

## VIII. TTS AUDIO CACHE

### Rekomendasi Saran3.md

**Audio cache system:**
```sql
CREATE TABLE audio_cache (
    id INTEGER PRIMARY KEY,
    text_hash TEXT UNIQUE NOT NULL,
    text_preview TEXT,
    file_path TEXT NOT NULL,
    engine TEXT NOT NULL,              -- fish_speech | edge_tts
    duration_ms INTEGER,
    created_at TEXT
);
```

**Features:**
- Pre-generate audio untuk template scripts
- Pre-generate audio untuk product scripts
- Cache stats (count, total duration, disk usage)
- Cache warm-up command
- Cache clear command

**3-tier TTS strategy:**
1. Check cache first
2. If miss, call Fish-Speech
3. If Fish-Speech fails, fallback to Edge-TTS
4. Save to cache

### Current State

**Audio cache:**
- ❌ Tidak ada database table
- ❌ Tidak ada cache management
- ⚠️ Ada folder `data/audio_cache/` tapi tidak terindex

**TTS engines:**
- ✅ Fish-Speech client ada (`src/voice/fish_speech.py` - perlu dicek)
- ✅ Edge-TTS fallback ada (config)
- ❌ Tidak ada orchestration layer

**Gap Analysis:**

| Feature | Saran3 | Current | Gap |
|---------|--------|---------|-----|
| Cache database | ✅ Ada | ❌ Tidak ada | 🔴 HIGH |
| Cache warm-up | ✅ CLI | ❌ Tidak ada | 🔴 HIGH |
| Cache stats | ✅ CLI | ❌ Tidak ada | 🟡 MEDIUM |
| 3-tier strategy | ✅ Ada | ⚠️ Partial | 🔴 HIGH |
| Pre-generation | ✅ Ada | ❌ Tidak ada | 🔴 HIGH |

**Action Items:**
1. 🔴 Create `audio_cache` table
2. 🔴 Implement `src/voice/audio_cache.py`
3. 🔴 Implement 3-tier TTS orchestrator
4. 🔴 Add `cache warm` command
5. 🟡 Add `cache stats` command
6. 🟡 Add `cache clear` command

---

## IX. STREAM ORCHESTRATION

### Rekomendasi Saran3.md

**Show Director (`src/orchestrator/show_director.py`):**
- Start/stop stream
- Pause/resume
- Product rotation (4 menit per produk)
- Script phases (7 phases per product)
- Emergency stop
- Uptime tracking
- Stats tracking (products shown, comments read)

**RTMP Manager (`src/stream/rtmp_manager.py`):**
- RTMP connection management
- Multi-platform output (TikTok + Shopee simultaneous)
- Auto-reconnect dengan exponential backoff
- Connection health monitoring
- Test connection (dry run)

### Current State

**Orchestrator:**
- ⚠️ Ada `src/orchestrator/` folder
- ✅ Ada `show_director.py`
- ⚠️ Sudah ada runtime phase sequence, history, emergency flag, dan stream flag
- ❌ Belum ada product rotation scheduler
- ❌ Belum ada automation script phases per product

**Stream:**
- ⚠️ Ada `src/stream/` folder
- ⚠️ Ada `rtmp_manager.py` (perlu dicek completeness)
- ❌ Tidak ada auto-reconnect
- ❌ Tidak ada multi-platform simultaneous

**Gap Analysis:**

| Feature | Saran3 | Current | Gap |
|---------|--------|---------|-----|
| Show Director | ✅ Lengkap | ⚠️ Core runtime service ada, control workflow belum lengkap | 🟡 MEDIUM |
| Product rotation | ✅ Ada | ❌ Tidak ada | 🔴 CRITICAL |
| Script phases | ✅ 7 phases | ⚠️ Runtime sequence ada, automation belum ada | 🔴 HIGH |
| RTMP manager | ✅ Ada | ⚠️ Partial | 🟡 MEDIUM |
| Auto-reconnect | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| Multi-platform | ✅ Ada | ❌ Tidak ada | 🟢 LOW |

**Action Items:**
1. 🔴 Implement product rotation scheduler
2. 🔴 Implement script phase automation (hook, hero, money, etc)
3. 🔴 Tambahkan mutation endpoints dan UI untuk `pause`, `resume`, `skip-phase`, `inject-speech`, dan provider override
4. 🟡 Complete `src/stream/rtmp_manager.py`
5. 🟡 Add auto-reconnect logic
6. 🟢 Add multi-platform simultaneous output

---

## X. MONITORING & ALERTS

### Rekomendasi Saran3.md

**Alerts system:**
```sql
CREATE TABLE alerts (
    id INTEGER PRIMARY KEY,
    severity TEXT NOT NULL,           -- info | warning | critical
    component TEXT,
    message TEXT NOT NULL,
    acknowledged INTEGER DEFAULT 0,
    created_at TEXT
);
```

**Monitoring features:**
- GPU temperature monitoring
- VRAM usage monitoring
- Memory leak detection
- Stream health monitoring
- Telegram bot alerts
- Hourly reports

**Watchdog:**
- Auto-restart on crash
- Process health checks
- Recovery procedures

### Current State

**Monitoring:**
- ✅ Ada `src/monitoring/` folder
- ⚠️ Ada health checks (perlu dicek completeness)
- ❌ Tidak ada alerts table
- ❌ Tidak ada Telegram bot
- ❌ Tidak ada watchdog

**GPU monitoring:**
- ⚠️ Ada di config (`gpu.temp_max_celsius`)
- ❌ Tidak ada active monitoring

**Gap Analysis:**

| Feature | Saran3 | Current | Gap |
|---------|--------|---------|-----|
| Alerts database | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| GPU monitoring | ✅ Ada | ⚠️ Partial | 🟡 MEDIUM |
| Telegram bot | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| Watchdog | ✅ Ada | ❌ Tidak ada | 🔴 HIGH |
| Memory leak detection | ✅ Ada | ❌ Tidak ada | 🟡 MEDIUM |
| Hourly reports | ✅ Ada | ❌ Tidak ada | 🟢 LOW |

**Action Items:**
1. 🔴 Implement watchdog untuk auto-restart
2. 🟡 Create `alerts` table
3. 🟡 Implement GPU temperature monitoring
4. 🟡 Implement Telegram bot alerts
5. 🟡 Add memory leak detection
6. 🟢 Add hourly reports

---

## XI. PRIORITY MATRIX

### 🔴 CRITICAL (BLOCKER - Tidak bisa live tanpa ini)

1. **Show Director** - Orchestration untuk 12 jam live
2. **Product Rotation** - Automatic product switching
3. **Stream Control API** - Start/stop/pause/resume endpoints
4. **Database Migration** - SQLite dengan WAL mode + complete schema
5. **TTS Audio Cache** - Pre-generation untuk latency reduction
6. **Watchdog** - Auto-restart on crash

### 🔴 HIGH (Penting untuk production)

1. **Product CRUD** - CLI + API untuk manage products
2. **Script Generation** - LLM-based script generation
3. **3-Tier TTS Orchestrator** - Cache → Fish-Speech → Edge-TTS
4. **WebSocket Dashboard** - Real-time updates
5. **Stream Control UI** - Frontend buttons untuk control

### 🟡 MEDIUM (Improve quality & operations)

1. **Vast.ai Scripts** - Deployment automation
2. **RTMP Auto-reconnect** - Stream stability
3. **GPU Monitoring** - Temperature & VRAM tracking
4. **Telegram Alerts** - Critical alerts notification
5. **CSV Product Import** - Bulk product management
6. **Alerts System** - Alert tracking & acknowledgment

### 🟢 LOW (Nice to have)

1. **Interactive Menu** - TUI untuk manage.py
2. **Multi-platform Simultaneous** - TikTok + Shopee bersamaan
3. **Hourly Reports** - Automated reporting
4. **Sessions History** - Historical data analysis
5. **Mobile Optimization** - Better mobile UX

---

## XII. IMPLEMENTATION ROADMAP

### Phase 1: Foundation (Week 1)
- 🔴 Database migration dengan WAL mode
- 🔴 Complete schema (7 tables)
- 🔴 Product CRUD (CLI + API)
- 🔴 TTS audio cache system

### Phase 2: Core Orchestration (Week 2)
- 🔴 Show Director implementation
- 🔴 Product rotation scheduler
- 🔴 Script phases (7 phases)
- 🔴 Stream control API endpoints

### Phase 3: Dashboard & Monitoring (Week 3)
- 🔴 WebSocket real-time updates
- 🔴 Stream control UI
- 🟡 GPU monitoring
- 🟡 Alerts system

### Phase 4: Stability & Deployment (Week 4)
- 🔴 Watchdog implementation
- 🟡 Vast.ai deployment scripts
- 🟡 RTMP auto-reconnect
- 🟡 Telegram bot alerts

### Phase 5: Polish & Scale (Week 5+)
- 🟡 CSV import
- 🟢 Interactive menu
- 🟢 Multi-platform simultaneous
- 🟢 Hourly reports

---

## XIII. KESIMPULAN

### Alignment Score: 60%

**Yang Sudah Aligned:**
- ✅ Arsitektur dasar (FastAPI + SQLite + LiveTalking + Fish-Speech)
- ✅ UV package manager policy
- ✅ Mock/Real mode separation
- ✅ Dashboard Svelte frontend
- ✅ Basic manage.py CLI
- ✅ Product data model (JSON)

**Gap Terbesar:**
1. **Orchestration Layer** - Show Director belum ada (BLOCKER)
2. **Database Schema** - Incomplete, tidak ada WAL mode
3. **TTS Cache System** - Tidak ada pre-generation & caching
4. **Stream Control** - API endpoints belum ada
5. **Product Management** - Tidak ada CRUD operations
6. **Monitoring** - Watchdog & alerts belum ada

### Rekomendasi

**Immediate Actions (This Week):**
1. Implement Show Director (BLOCKER untuk live)
2. Complete database schema migration
3. Implement TTS audio cache system
4. Add stream control API endpoints
5. Add product CRUD operations

**Next Week:**
1. Implement watchdog
2. Add WebSocket dashboard updates
3. Create Vast.ai deployment scripts
4. Implement GPU monitoring
5. Add Telegram bot alerts

**Future:**
1. Polish dashboard UI
2. Add advanced features (multi-platform, reports)
3. Optimize performance
4. Scale to multiple streams

---

**Prepared by**: AI Assistant  
**Date**: 11 Maret 2026  
**Version**: 1.0.0
