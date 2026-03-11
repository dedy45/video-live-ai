
## I. ARSITEKTUR YANG SEBENARNYA DIBUTUHKAN

### Topology Real

```
┌──────────────────────────────┐
│     LOCAL PC (GTX 1650)      │
│     ════════════════════     │
│  • Code development          │
│  • Script validation         │
│  • Mock mode testing         │
│  • Dashboard development     │
│  • SQLite database           │
│  • Git repository            │
│                              │
│  uv run python manage.py     │
│     serve --mock             │
└──────────────┬───────────────┘
               │ 
               │  git push / rsync / scp
               │  SSH tunnel for dashboard
               ▼
┌──────────────────────────────┐
│     VAST.AI INSTANCE         │
│     (RTX 3090 / RTX 4090)    │
│     ════════════════════     │
│  • LiveTalking + MuseTalk    │
│  • Fish-Speech TTS           │
│  • LLM Brain (API calls)     │
│  • RTMP output → TikTok      │
│  • RTMP output → Shopee      │
│  • FastAPI + Dashboard       │
│  • SQLite database (copy)    │
│                              │
│  uv run python manage.py     │
│     serve --real             │
└──────────────┬───────────────┘
               │
               │  RTMP push
               ▼
┌──────────────────────────────┐
│  TikTok Live / Shopee Live   │
└──────────────────────────────┘

MONITORING:
  Local PC browser → https://vast-ip:8000/dashboard
  HP browser → https://vast-ip:8000/dashboard
  Telegram bot → alerts & quick commands
```

### SQLite — Tetap Pakai, Tapi Harus Benar

```python
# src/data/database.py — SQLite dengan WAL mode

import aiosqlite
import os

DB_PATH = os.getenv("VIDEOLIVEAI_DB", "data/videoliveai.db")

async def get_db():
    db = await aiosqlite.connect(DB_PATH)
    # WAL mode = bisa read sambil write, jauh lebih stabil
    await db.execute("PRAGMA journal_mode=WAL")
    # Timeout 30 detik kalau ada lock
    await db.execute("PRAGMA busy_timeout=30000")
    # Foreign keys on
    await db.execute("PRAGMA foreign_keys=ON")
    db.row_factory = aiosqlite.Row
    return db

async def init_db():
    """Initialize database schema"""
    db = await get_db()
    
    await db.executescript("""
    
    -- Products untuk affiliate
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        product_id TEXT NOT NULL,
        name TEXT NOT NULL,
        price REAL,
        commission_rate REAL DEFAULT 0,
        image_url TEXT,
        affiliate_link TEXT,
        category TEXT,
        script_template TEXT,
        is_active INTEGER DEFAULT 1,
        last_promoted_at TEXT,
        total_promotions INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(platform, product_id)
    );

    -- Stream sessions
    CREATE TABLE IF NOT EXISTS stream_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform TEXT NOT NULL,
        started_at TEXT NOT NULL,
        ended_at TEXT,
        status TEXT DEFAULT 'running',
        total_viewers_peak INTEGER DEFAULT 0,
        total_comments INTEGER DEFAULT 0,
        total_products_shown INTEGER DEFAULT 0,
        health_events INTEGER DEFAULT 0,
        notes TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- Stream events log
    CREATE TABLE IF NOT EXISTS stream_events (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id INTEGER REFERENCES stream_sessions(id),
        event_type TEXT NOT NULL,
        event_data TEXT,  -- JSON string
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- Content scripts
    CREATE TABLE IF NOT EXISTS scripts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category TEXT NOT NULL,
        script_type TEXT NOT NULL,
        content TEXT NOT NULL,
        language TEXT DEFAULT 'id',
        duration_estimate INTEGER,
        usage_count INTEGER DEFAULT 0,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- TTS audio cache index
    CREATE TABLE IF NOT EXISTS audio_cache (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        text_hash TEXT UNIQUE NOT NULL,
        text_preview TEXT,
        file_path TEXT NOT NULL,
        engine TEXT NOT NULL,
        duration_ms INTEGER,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- Alerts history
    CREATE TABLE IF NOT EXISTS alerts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        severity TEXT NOT NULL,
        component TEXT,
        message TEXT NOT NULL,
        acknowledged INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    );

    -- CREATE INDEXES
    CREATE INDEX IF NOT EXISTS idx_products_platform 
        ON products(platform, is_active);
    CREATE INDEX IF NOT EXISTS idx_sessions_status 
        ON stream_sessions(status);
    CREATE INDEX IF NOT EXISTS idx_events_session 
        ON stream_events(session_id, created_at);
    CREATE INDEX IF NOT EXISTS idx_audio_cache_hash 
        ON audio_cache(text_hash);
    CREATE INDEX IF NOT EXISTS idx_alerts_severity 
        ON alerts(severity, acknowledged);
    
    """)
    
    await db.commit()
    await db.close()
```

**Kenapa SQLite cukup untuk case ini:**
```
✅ Single server write (Vast.ai instance)
✅ Dashboard read-only dari remote (WAL mode handles ini)
✅ Tidak ada concurrent write dari banyak server
✅ Zero maintenance — file-based, backup = copy file
✅ Cukup cepat untuk volume data livestream
✅ Portable — bisa copy DB file dari local ke Vast.ai
```

---

## II. VAST.AI DEPLOYMENT STRATEGY

### 2.1 Vast.ai Instance Selection

```yaml
RECOMMENDED INSTANCE:
  GPU: RTX 3090 (24GB VRAM) — sweet spot price/performance
  Alternative: RTX 4090 (24GB VRAM) — faster tapi lebih mahal
  Budget option: RTX 3080 (10GB VRAM) — minimum viable
  
  vCPU: 8+ cores
  RAM: 32GB+
  Disk: 100GB+ (models + data + logs)
  
  Docker image: nvidia/cuda:12.1-devel-ubuntu22.04
  
  PRICING ESTIMATE (per March 2025):
    RTX 3090: ~$0.20-0.40/hr
    12 jam/hari × 30 hari = 360 jam/bulan
    Cost: $72-144/bulan (~Rp 1.1-2.2 juta)
    
    RTX 4090: ~$0.35-0.70/hr
    Cost: $126-252/bulan (~Rp 2-4 juta)

VAST.AI SEARCH FILTER:
  - GPU: RTX 3090
  - VRAM: ≥ 24GB
  - RAM: ≥ 32GB
  - Disk: ≥ 100GB
  - Upload speed: ≥ 100 Mbps (KRITIS untuk RTMP)
  - Reliability: ≥ 95%
  - Region: Asia (lower latency ke TikTok/Shopee servers)
```

### 2.2 Vast.ai Setup Script

```bash
#!/bin/bash
# scripts/vast_setup.sh
# Jalankan ini pertama kali di Vast.ai instance

set -e

echo "═══════════════════════════════════════"
echo "  VideoLiveAI Vast.ai Setup"
echo "═══════════════════════════════════════"

# ---- System packages ----
apt-get update && apt-get install -y \
    git curl wget htop tmux \
    ffmpeg libsndfile1 portaudio19-dev \
    libgl1-mesa-glx libglib2.0-0 \
    supervisor

# ---- UV package manager ----
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# ---- Clone repository ----
cd /workspace
if [ ! -d "videoliveai" ]; then
    git clone YOUR_REPO_URL videoliveai
fi
cd videoliveai

# ---- Install dependencies ----
uv sync --extra dev --extra livetalking

# ---- Setup LiveTalking ----
uv run python scripts/manage.py setup-livetalking

# ---- Download models (kalau belum ada) ----
# Models di-cache di /workspace supaya persist antar restart
MODELS_CACHE="/workspace/model_cache"
mkdir -p $MODELS_CACHE

if [ ! -d "$MODELS_CACHE/musetalk" ]; then
    echo "Downloading MuseTalk models..."
    uv run python scripts/manage.py download-models --target $MODELS_CACHE
fi

# Symlink models ke tempat yang expected
ln -sf $MODELS_CACHE/musetalk external/livetalking/models/musetalk

# ---- Setup environment ----
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  EDIT .env FILE SEBELUM LANJUT!"
    echo "    nano .env"
    echo ""
fi

# ---- Verify GPU ----
echo ""
echo "GPU Status:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
echo ""

# ---- Verify CUDA ----
python -c "import torch; print(f'CUDA available: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name(0)}')"

echo ""
echo "═══════════════════════════════════════"
echo "  Setup complete!"
echo "  "
echo "  Next steps:"
echo "  1. Edit .env"
echo "  2. uv run python scripts/manage.py serve --mock  (test)"
echo "  3. uv run python scripts/manage.py serve --real  (production)"
echo "═══════════════════════════════════════"
```

### 2.3 Vast.ai Start/Stop Scripts

```bash
#!/bin/bash
# scripts/vast_start.sh
# Start semua services di Vast.ai

cd /workspace/videoliveai

# Start dalam tmux sessions supaya tidak mati kalau SSH putus
tmux new-session -d -s main "uv run python scripts/manage.py serve --real 2>&1 | tee logs/main.log"
tmux new-session -d -s livetalking "cd external/livetalking && uv run python app.py 2>&1 | tee /workspace/videoliveai/logs/livetalking.log"

echo "Services started in tmux sessions:"
echo "  tmux attach -t main        → FastAPI + Dashboard"
echo "  tmux attach -t livetalking  → LiveTalking engine"
echo ""
echo "Dashboard: http://$(hostname -I | awk '{print $1}'):8000/dashboard"
```

```bash
#!/bin/bash
# scripts/vast_stop.sh
# Graceful stop

echo "Stopping services..."
tmux send-keys -t main C-c
tmux send-keys -t livetalking C-c
sleep 5
tmux kill-session -t main 2>/dev/null
tmux kill-session -t livetalking 2>/dev/null
echo "All services stopped."
```

### 2.4 Remote Dashboard Access dari Local

```bash
# OPTION 1: Direct access (jika Vast.ai port 8000 exposed)
# Browser: http://VAST_IP:8000/dashboard

# OPTION 2: SSH tunnel (lebih aman)
ssh -L 8000:localhost:8000 -L 8010:localhost:8010 root@VAST_IP -p VAST_SSH_PORT

# Lalu buka di browser lokal:
# http://localhost:8000/dashboard     → Operator dashboard
# http://localhost:8010               → LiveTalking debug (kalau perlu)

# OPTION 3: Script otomatis
#!/bin/bash
# scripts/connect_vast.sh
VAST_IP="xxx.xxx.xxx.xxx"
VAST_PORT="xxxxx"  # SSH port dari Vast.ai

echo "Connecting to Vast.ai instance..."
echo "Dashboard will be at: http://localhost:8000/dashboard"
echo "Press Ctrl+C to disconnect"

ssh -N \
    -L 8000:localhost:8000 \
    -L 8010:localhost:8010 \
    root@$VAST_IP -p $VAST_PORT
```

### 2.5 File Sync Local ↔ Vast.ai

```bash
#!/bin/bash
# scripts/sync_to_vast.sh
# Sync code changes dari local ke Vast.ai

VAST_IP="xxx.xxx.xxx.xxx"
VAST_PORT="xxxxx"
REMOTE_PATH="/workspace/videoliveai"

echo "Syncing to Vast.ai..."

rsync -avz --progress \
    --exclude '.git' \
    --exclude '__pycache__' \
    --exclude 'node_modules' \
    --exclude '.venv' \
    --exclude 'external/livetalking/models' \
    --exclude 'logs' \
    --exclude '*.db' \
    --exclude 'data/audio_cache' \
    -e "ssh -p $VAST_PORT" \
    ./ root@$VAST_IP:$REMOTE_PATH/

echo "Sync complete!"
echo "SSH: ssh root@$VAST_IP -p $VAST_PORT"
```

```bash
#!/bin/bash
# scripts/sync_db_from_vast.sh
# Pull database dari Vast.ai ke local (untuk review/backup)

VAST_IP="xxx.xxx.xxx.xxx"
VAST_PORT="xxxxx"

echo "Pulling database from Vast.ai..."

scp -P $VAST_PORT \
    root@$VAST_IP:/workspace/videoliveai/data/videoliveai.db \
    ./data/videoliveai_vast_backup_$(date +%Y%m%d_%H%M).db

echo "Database backup saved!"
```

---

## III. MENU INTERAKTIF — YANG BENAR-BENAR DIBUTUHKAN

### 3.1 manage.py CLI — Hub Utama

```python
# scripts/manage.py — Interactive menu system

import click
import asyncio
import os
import sys

@click.group()
def cli():
    """VideoLiveAI Management CLI"""
    pass

# ═══════════════════════════════════════
#  SERVE COMMANDS
# ═══════════════════════════════════════

@cli.command()
@click.option('--mock', is_flag=True, help='Mock mode (no GPU needed)')
@click.option('--real', is_flag=True, help='Real mode (GPU + LiveTalking)')
@click.option('--host', default='0.0.0.0', help='Bind host')
@click.option('--port', default=8000, help='Bind port')
def serve(mock, real, host, port):
    """Start FastAPI server"""
    if mock:
        os.environ['VIDEOLIVEAI_MODE'] = 'mock'
        click.echo("🔧 Starting in MOCK mode (no GPU required)")
    elif real:
        os.environ['VIDEOLIVEAI_MODE'] = 'real'
        click.echo("🚀 Starting in REAL mode (GPU + LiveTalking)")
    else:
        click.echo("❌ Specify --mock or --real")
        return
    
    import uvicorn
    uvicorn.run("src.main:app", host=host, port=port, reload=mock)

# ═══════════════════════════════════════
#  SETUP COMMANDS
# ═══════════════════════════════════════

@cli.command()
@click.option('--skip-models', is_flag=True)
def setup_livetalking(skip_models):
    """Setup LiveTalking vendor engine"""
    click.echo("Setting up LiveTalking...")
    # ... existing setup logic

@cli.command()
def setup_db():
    """Initialize/migrate database"""
    asyncio.run(_setup_db())

async def _setup_db():
    from src.data.database import init_db
    await init_db()
    click.echo("✅ Database initialized")

@cli.command()
def setup_all():
    """Complete first-time setup"""
    click.echo("═══ VideoLiveAI Complete Setup ═══")
    
    steps = [
        ("Database", "setup-db"),
        ("LiveTalking", "setup-livetalking"),
        ("Verify Pipeline", "verify"),
        ("Warm Cache", "cache-warm"),
    ]
    
    for name, cmd in steps:
        click.echo(f"\n▶ {name}...")
        os.system(f"uv run python scripts/manage.py {cmd}")
    
    click.echo("\n✅ Setup complete!")

# ═══════════════════════════════════════
#  PRODUCT COMMANDS (Affiliate)
# ═══════════════════════════════════════

@cli.group()
def product():
    """Manage affiliate products"""
    pass

@product.command('add')
@click.option('--platform', type=click.Choice(['tiktok', 'shopee']), required=True)
@click.option('--name', required=True)
@click.option('--price', type=float, required=True)
@click.option('--commission', type=float, default=0)
@click.option('--link', required=True)
@click.option('--category', default='general')
def product_add(platform, name, price, commission, link, category):
    """Add a product to catalog"""
    asyncio.run(_product_add(platform, name, price, commission, link, category))

async def _product_add(platform, name, price, commission, link, category):
    from src.data.database import get_db
    db = await get_db()
    await db.execute(
        """INSERT INTO products (platform, product_id, name, price, 
           commission_rate, affiliate_link, category) 
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (platform, f"manual_{int(time.time())}", name, price, 
         commission, link, category)
    )
    await db.commit()
    await db.close()
    click.echo(f"✅ Added: {name} ({platform}) - Rp {price:,.0f}")

@product.command('list')
@click.option('--platform', type=click.Choice(['tiktok', 'shopee', 'all']), default='all')
def product_list(platform):
    """List all products"""
    asyncio.run(_product_list(platform))

async def _product_list(platform):
    from src.data.database import get_db
    db = await get_db()
    
    if platform == 'all':
        rows = await db.execute("SELECT * FROM products WHERE is_active=1")
    else:
        rows = await db.execute(
            "SELECT * FROM products WHERE is_active=1 AND platform=?", 
            (platform,)
        )
    
    products = await rows.fetchall()
    await db.close()
    
    if not products:
        click.echo("No products found.")
        return
    
    click.echo(f"\n{'ID':>4} {'Platform':>8} {'Name':<40} {'Price':>12} {'Commission':>10}")
    click.echo("─" * 80)
    for p in products:
        click.echo(
            f"{p['id']:>4} {p['platform']:>8} {p['name'][:40]:<40} "
            f"Rp {p['price']:>10,.0f} {p['commission_rate']:>9.1f}%"
        )

@product.command('import-csv')
@click.argument('filepath')
@click.option('--platform', type=click.Choice(['tiktok', 'shopee']), required=True)
def product_import_csv(filepath, platform):
    """Import products from CSV file"""
    asyncio.run(_product_import_csv(filepath, platform))

async def _product_import_csv(filepath, platform):
    import csv
    from src.data.database import get_db
    
    db = await get_db()
    count = 0
    
    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            await db.execute(
                """INSERT OR REPLACE INTO products 
                   (platform, product_id, name, price, commission_rate, 
                    affiliate_link, category)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (platform, row.get('product_id', f"csv_{count}"),
                 row['name'], float(row['price']),
                 float(row.get('commission', 0)),
                 row.get('link', ''), row.get('category', 'general'))
            )
            count += 1
    
    await db.commit()
    await db.close()
    click.echo(f"✅ Imported {count} products from {filepath}")

# ═══════════════════════════════════════
#  SCRIPT/CONTENT COMMANDS
# ═══════════════════════════════════════

@cli.group()
def script():
    """Manage content scripts"""
    pass

@script.command('generate')
@click.option('--product-id', type=int, help='Generate for specific product')
@click.option('--all-products', is_flag=True, help='Generate for all products')
@click.option('--type', 'script_type', 
              type=click.Choice(['opening', 'closing', 'filler', 'cta', 'product']),
              default='product')
def script_generate(product_id, all_products, script_type):
    """Generate scripts using LLM"""
    asyncio.run(_script_generate(product_id, all_products, script_type))

async def _script_generate(product_id, all_products, script_type):
    from src.brain.script_generator import ScriptGenerator
    gen = ScriptGenerator()
    
    if all_products:
        from src.data.database import get_db
        db = await get_db()
        rows = await db.execute("SELECT * FROM products WHERE is_active=1")
        products = await rows.fetchall()
        await db.close()
        
        click.echo(f"Generating scripts for {len(products)} products...")
        for p in products:
            click.echo(f"  ▶ {p['name'][:50]}...")
            await gen.generate_and_save(p, script_type)
        click.echo(f"✅ Generated {len(products)} scripts")
    elif product_id:
        click.echo(f"Generating script for product {product_id}...")
        await gen.generate_and_save_by_id(product_id, script_type)
        click.echo("✅ Script generated")

# ═══════════════════════════════════════
#  CACHE COMMANDS
# ═══════════════════════════════════════

@cli.group()
def cache():
    """Manage TTS audio cache"""
    pass

@cache.command('warm')
@click.option('--templates-only', is_flag=True, help='Only warm template scripts')
@click.option('--all', 'warm_all', is_flag=True, help='Warm all including product scripts')
def cache_warm(templates_only, warm_all):
    """Pre-generate TTS audio cache"""
    asyncio.run(_cache_warm(templates_only, warm_all))

async def _cache_warm(templates_only, warm_all):
    from src.voice.audio_cache import AudioCache
    cache = AudioCache()
    
    if templates_only or not warm_all:
        click.echo("Warming template scripts...")
        count = await cache.warm_templates()
        click.echo(f"✅ Warmed {count} template audio clips")
    
    if warm_all:
        click.echo("Warming all product scripts...")
        count = await cache.warm_product_scripts()
        click.echo(f"✅ Warmed {count} product audio clips")

@cache.command('stats')
def cache_stats():
    """Show cache statistics"""
    asyncio.run(_cache_stats())

async def _cache_stats():
    from src.data.database import get_db
    db = await get_db()
    
    row = await db.execute("SELECT COUNT(*) as cnt, SUM(duration_ms) as total_ms FROM audio_cache")
    stats = await row.fetchone()
    await db.close()
    
    total_seconds = (stats['total_ms'] or 0) / 1000
    click.echo(f"\nAudio Cache Stats:")
    click.echo(f"  Clips: {stats['cnt']}")
    click.echo(f"  Total duration: {total_seconds/60:.1f} minutes")
    
    # Disk usage
    cache_dir = "data/audio_cache"
    if os.path.exists(cache_dir):
        size = sum(
            os.path.getsize(os.path.join(cache_dir, f)) 
            for f in os.listdir(cache_dir)
        )
        click.echo(f"  Disk usage: {size / (1024**2):.1f} MB")

@cache.command('clear')
@click.confirmation_option(prompt='Delete all cached audio?')
def cache_clear():
    """Clear all cached audio"""
    asyncio.run(_cache_clear())

async def _cache_clear():
    from src.data.database import get_db
    import shutil
    
    db = await get_db()
    await db.execute("DELETE FROM audio_cache")
    await db.commit()
    await db.close()
    
    cache_dir = "data/audio_cache"
    if os.path.exists(cache_dir):
        shutil.rmtree(cache_dir)
        os.makedirs(cache_dir)
    
    click.echo("✅ Cache cleared")

# ═══════════════════════════════════════
#  STREAM COMMANDS
# ═══════════════════════════════════════

@cli.group()
def stream():
    """Stream management"""
    pass

@stream.command('test')
@click.option('--platform', type=click.Choice(['tiktok', 'shopee']), required=True)
@click.option('--duration', default=30, help='Test duration in seconds')
def stream_test(platform, duration):
    """Test RTMP connection (dry run)"""
    asyncio.run(_stream_test(platform, duration))

async def _stream_test(platform, duration):
    from src.stream.rtmp_manager import RTMPManager
    
    mgr = RTMPManager()
    click.echo(f"Testing {platform} RTMP connection for {duration}s...")
    
    result = await mgr.test_connection(platform, duration)
    
    if result.success:
        click.echo(f"✅ Connection OK")
        click.echo(f"   Bitrate: {result.bitrate}kbps")
        click.echo(f"   Dropped frames: {result.dropped_frames}")
        click.echo(f"   Latency: {result.latency_ms}ms")
    else:
        click.echo(f"❌ Connection FAILED: {result.error}")

@stream.command('set-key')
@click.option('--platform', type=click.Choice(['tiktok', 'shopee']), required=True)
@click.option('--rtmp-url', required=True, help='RTMP server URL')
@click.option('--stream-key', required=True, help='Stream key')
def stream_set_key(platform, rtmp_url, stream_key):
    """Set RTMP stream key for platform"""
    # Store in .env or encrypted config
    env_key = f"{platform.upper()}_RTMP_URL"
    env_val = f"{rtmp_url}/{stream_key}"
    
    # Update .env
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    found = False
    for i, line in enumerate(lines):
        if line.startswith(f"{env_key}="):
            lines[i] = f"{env_key}={env_val}\n"
            found = True
            break
    
    if not found:
        lines.append(f"{env_key}={env_val}\n")
    
    with open('.env', 'w') as f:
        f.writelines(lines)
    
    click.echo(f"✅ {platform} stream key saved")

# ═══════════════════════════════════════
#  VERIFY / DIAGNOSTIC COMMANDS
# ═══════════════════════════════════════

@cli.command()
@click.option('--verbose', '-v', is_flag=True)
def verify(verbose):
    """Verify entire pipeline readiness"""
    asyncio.run(_verify(verbose))

async def _verify(verbose):
    checks = []
    
    # 1. Database
    try:
        from src.data.database import get_db
        db = await get_db()
        await db.execute("SELECT 1")
        await db.close()
        checks.append(("Database (SQLite)", True, "OK"))
    except Exception as e:
        checks.append(("Database (SQLite)", False, str(e)))
    
    # 2. GPU
    try:
        import torch
        if torch.cuda.is_available():
            name = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_mem / (1024**3)
            checks.append(("GPU", True, f"{name} ({mem:.0f}GB)"))
        else:
            checks.append(("GPU", False, "CUDA not available"))
    except Exception as e:
        checks.append(("GPU", False, str(e)))
    
    # 3. LiveTalking
    try:
        import httpx
        async with httpx.AsyncClient() as client:
            r = await client.get("http://localhost:8010/health", timeout=5)
            if r.status_code == 200:
                checks.append(("LiveTalking", True, "Running"))
            else:
                checks.append(("LiveTalking", False, f"HTTP {r.status_code}"))
    except Exception:
        checks.append(("LiveTalking", False, "Not reachable"))
    
    # 4. Fish-Speech
    try:
        from src.voice.fish_speech import FishSpeechEngine
        engine = FishSpeechEngine()
        available = await engine.check_health()
        checks.append(("Fish-Speech", available, "Ready" if available else "Not available"))
    except Exception as e:
        checks.append(("Fish-Speech", False, str(e)))
    
    # 5. Edge-TTS fallback
    try:
        import edge_tts
        checks.append(("Edge-TTS (fallback)", True, "Available"))
    except ImportError:
        checks.append(("Edge-TTS (fallback)", False, "Not installed"))
    
    # 6. FFmpeg
    try:
        result = os.popen("ffmpeg -version 2>&1 | head -1").read().strip()
        checks.append(("FFmpeg", True, result[:60]))
    except:
        checks.append(("FFmpeg", False, "Not found"))
    
    # 7. LLM
    try:
        from src.brain.llm_router import LLMRouter
        router = LLMRouter()
        available = await router.check_health()
        checks.append(("LLM Router", available, "Ready" if available else "Check API key"))
    except Exception as e:
        checks.append(("LLM Router", False, str(e)))
    
    # 8. Voice reference
    ref_wav = "assets/voice/reference.wav"
    ref_txt = "assets/voice/reference.txt"
    checks.append(("Voice reference.wav", os.path.exists(ref_wav), 
                    "Found" if os.path.exists(ref_wav) else "MISSING"))
    checks.append(("Voice reference.txt", os.path.exists(ref_txt),
                    "Found" if os.path.exists(ref_txt) else "MISSING"))
    
    # 9. Products
    try:
        from src.data.database import get_db
        db = await get_db()
        row = await db.execute("SELECT COUNT(*) as cnt FROM products WHERE is_active=1")
        count = (await row.fetchone())['cnt']
        await db.close()
        checks.append(("Products in catalog", count > 0, f"{count} products"))
    except:
        checks.append(("Products in catalog", False, "Cannot query"))
    
    # 10. RTMP keys
    tiktok_key = os.getenv("TIKTOK_RTMP_URL", "")
    shopee_key = os.getenv("SHOPEE_RTMP_URL", "")
    checks.append(("TikTok RTMP key", bool(tiktok_key), 
                    "Configured" if tiktok_key else "NOT SET"))
    checks.append(("Shopee RTMP key", bool(shopee_key),
                    "Configured" if shopee_key else "NOT SET"))
    
    # Print results
    click.echo("\n═══ Pipeline Verification ═══\n")
    
    passed = 0
    failed = 0
    for name, ok, detail in checks:
        icon = "✅" if ok else "❌"
        click.echo(f"  {icon} {name:<30} {detail}")
        if ok:
            passed += 1
        else:
            failed += 1
    
    click.echo(f"\n{'─' * 50}")
    click.echo(f"  Passed: {passed}  Failed: {failed}  Total: {passed + failed}")
    
    if failed == 0:
        click.echo("\n  🎉 ALL CHECKS PASSED — Ready for live!")
    else:
        click.echo(f"\n  ⚠️  {failed} check(s) failed — fix before going live")

# ═══════════════════════════════════════
#  HEALTH COMMAND (quick check)
# ═══════════════════════════════════════

@cli.command()
def health():
    """Quick health check"""
    asyncio.run(_health())

async def _health():
    import httpx
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get("http://localhost:8000/api/health", timeout=5)
            data = r.json()
            
            click.echo(f"\n{'Component':<25} {'Status':<12} {'Detail'}")
            click.echo("─" * 60)
            for comp, info in data.get('components', {}).items():
                status = info.get('status', 'unknown')
                icon = "🟢" if status == 'healthy' else "🔴" if status == 'error' else "🟡"
                click.echo(f"  {icon} {comp:<23} {status:<12} {info.get('detail', '')}")
    except Exception as e:
        click.echo(f"❌ Cannot reach FastAPI: {e}")
        click.echo("   Is the server running? (uv run python scripts/manage.py serve --mock)")

# ═══════════════════════════════════════
#  INTERACTIVE MENU (untuk yang males ketik command)
# ═══════════════════════════════════════

@cli.command()
def menu():
    """Interactive menu (TUI)"""
    while True:
        click.clear()
        click.echo("╔══════════════════════════════════════╗")
        click.echo("║      VideoLiveAI Control Panel       ║")
        click.echo("╠══════════════════════════════════════╣")
        click.echo("║                                      ║")
        click.echo("║  1. Start Server (Mock)              ║")
        click.echo("║  2. Start Server (Real/Production)   ║")
        click.echo("║  3. Verify Pipeline                  ║")
        click.echo("║  4. Health Check                     ║")
        click.echo("║                                      ║")
        click.echo("║  --- Products ---                    ║")
        click.echo("║  5. List Products                    ║")
        click.echo("║  6. Add Product                      ║")
        click.echo("║  7. Import Products (CSV)            ║")
        click.echo("║  8. Generate Scripts for Products    ║")
        click.echo("║                                      ║")
        click.echo("║  --- Cache ---                       ║")
        click.echo("║  9. Warm TTS Cache                   ║")
        click.echo("║  10. Cache Stats                     ║")
        click.echo("║                                      ║")
        click.echo("║  --- Stream ---                      ║")
        click.echo("║  11. Test RTMP Connection            ║")
        click.echo("║  12. Set Stream Key                  ║")
        click.echo("║                                      ║")
        click.echo("║  --- Setup ---                       ║")
        click.echo("║  13. Complete Setup (first time)     ║")
        click.echo("║  14. Setup Database                  ║")
        click.echo("║  15. Setup LiveTalking               ║")
        click.echo("║                                      ║")
        click.echo("║  0. Exit                             ║")
        click.echo("║                                      ║")
        click.echo("╚══════════════════════════════════════╝")
        
        choice = click.prompt("\nSelect", type=int)
        
        commands = {
            1: "serve --mock",
            2: "serve --real",
            3: "verify -v",
            4: "health",
            5: "product list",
            6: None,  # Interactive
            7: None,  # Interactive
            8: "script generate --all-products",
            9: "cache warm --all",
            10: "cache stats",
            11: None,  # Interactive
            12: None,  # Interactive
            13: "setup-all",
            14: "setup-db",
            15: "setup-livetalking",
            0: None,
        }
        
        if choice == 0:
            click.echo("Bye!")
            break
        elif choice == 6:
            # Interactive product add
            platform = click.prompt("Platform", type=click.Choice(['tiktok', 'shopee']))
            name = click.prompt("Product name")
            price = click.prompt("Price (Rp)", type=float)
            commission = click.prompt("Commission %", type=float, default=0)
            link = click.prompt("Affiliate link")
            category = click.prompt("Category", default="general")
            os.system(
                f'uv run python scripts/manage.py product add '
                f'--platform {platform} --name "{name}" --price {price} '
                f'--commission {commission} --link "{link}" --category {category}'
            )
            click.pause()
        elif choice == 7:
            filepath = click.prompt("CSV file path")
            platform = click.prompt("Platform", type=click.Choice(['tiktok', 'shopee']))
            os.system(f'uv run python scripts/manage.py product import-csv {filepath} --platform {platform}')
            click.pause()
        elif choice == 11:
            platform = click.prompt("Platform", type=click.Choice(['tiktok', 'shopee']))
            duration = click.prompt("Duration (seconds)", type=int, default=30)
            os.system(f'uv run python scripts/manage.py stream test --platform {platform} --duration {duration}')
            click.pause()
        elif choice == 12:
            platform = click.prompt("Platform", type=click.Choice(['tiktok', 'shopee']))
            rtmp_url = click.prompt("RTMP URL")
            stream_key = click.prompt("Stream Key")
            os.system(
                f'uv run python scripts/manage.py stream set-key '
                f'--platform {platform} --rtmp-url "{rtmp_url}" --stream-key "{stream_key}"'
            )
            click.pause()
        elif choice in commands and commands[choice]:
            os.system(f"uv run python scripts/manage.py {commands[choice]}")
            if choice not in (1, 2):  # Don't pause for server commands
                click.pause()

if __name__ == '__main__':
    cli()
```

---

## IV. DASHBOARD — MENU INTERAKTIF WEB YANG LENGKAP

### 4.1 Dashboard API Endpoints (Lengkap untuk Operator)

```python
# src/dashboard/api.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import json

router = APIRouter(prefix="/api")

# ═══════ HEALTH ═══════

@router.get("/health")
async def health():
    """Overall system health"""
    from src.reliability.health_manager import HealthManager
    return await HealthManager().get_full_report()

@router.get("/runtime/truth")
async def runtime_truth():
    """Truth model — apa yang sedang aktif, mock atau real"""
    return {
        "mode": os.getenv("VIDEOLIVEAI_MODE", "unknown"),
        "gpu_available": torch.cuda.is_available() if 'torch' in sys.modules else False,
        "livetalking_running": await check_livetalking(),
        "tts_engine": await get_active_tts_engine(),
        "llm_provider": await get_active_llm_provider(),
        "database": "sqlite",
        "host_type": detect_host_type(),  # "local", "vast.ai", "other"
    }

# ═══════ STREAM CONTROL ═══════

@router.post("/stream/start")
async def stream_start(config: StreamStartConfig):
    """
    Start livestream
    Body: { platform: "tiktok"|"shopee"|"both", dry_run: false }
    """
    from src.orchestrator.show_director import ShowDirector
    director = ShowDirector()
    
    session = await director.start_show(
        platform=config.platform,
        dry_run=config.dry_run
    )
    
    return {"status": "started", "session_id": session.id}

@router.post("/stream/stop")
async def stream_stop():
    """Graceful stop — finish current segment, then stop"""
    from src.orchestrator.show_director import ShowDirector
    await ShowDirector().graceful_stop()
    return {"status": "stopping"}

@router.post("/stream/emergency-stop")
async def stream_emergency_stop():
    """EMERGENCY — stop everything immediately"""
    from src.orchestrator.show_director import ShowDirector
    await ShowDirector().emergency_stop()
    return {"status": "emergency_stopped"}

@router.post("/stream/pause")
async def stream_pause():
    """Pause — play filler content"""
    from src.orchestrator.show_director import ShowDirector
    await ShowDirector().pause()
    return {"status": "paused"}

@router.post("/stream/resume")
async def stream_resume():
    """Resume from pause"""
    from src.orchestrator.show_director import ShowDirector
    await ShowDirector().resume()
    return {"status": "resumed"}

@router.get("/stream/status")
async def stream_status():
    """Current stream status"""
    from src.stream.rtmp_manager import RTMPManager
    from src.orchestrator.show_director import ShowDirector
    
    director = ShowDirector()
    rtmp = RTMPManager()
    
    return {
        "is_live": director.is_running,
        "platform": director.current_platform,
        "uptime_seconds": director.uptime_seconds,
        "uptime_formatted": director.uptime_formatted,
        "current_segment": director.current_segment_info,
        "current_product": director.current_product_info,
        "next_product": director.next_product_info,
        "products_shown": director.products_shown_count,
        "comments_read": director.comments_read_count,
        "rtmp_health": await rtmp.get_health(),
        "gpu_temp": await get_gpu_temp(),
    }

# ═══════ PRODUCTS ═══════

@router.get("/products")
async def products_list(platform: str = "all", active_only: bool = True):
    """List products"""
    from src.data.database import get_db
    db = await get_db()
    
    query = "SELECT * FROM products WHERE 1=1"
    params = []
    
    if active_only:
        query += " AND is_active=1"
    if platform != "all":
        query += " AND platform=?"
        params.append(platform)
    
    query += " ORDER BY category, name"
    
    rows = await db.execute(query, params)
    products = [dict(r) for r in await rows.fetchall()]
    await db.close()
    
    return {"products": products, "total": len(products)}

@router.post("/products")
async def products_add(product: ProductCreate):
    """Add product"""
    from src.data.database import get_db
    db = await get_db()
    
    cursor = await db.execute(
        """INSERT INTO products (platform, product_id, name, price, 
           commission_rate, affiliate_link, image_url, category)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (product.platform, product.product_id or f"manual_{int(time.time())}",
         product.name, product.price, product.commission_rate,
         product.affiliate_link, product.image_url, product.category)
    )
    await db.commit()
    product_id = cursor.lastrowid
    await db.close()
    
    return {"id": product_id, "status": "created"}

@router.post("/products/next")
async def products_next():
    """Skip to next product in rotation"""
    from src.orchestrator.show_director import ShowDirector
    await ShowDirector().skip_to_next_product()
    return {"status": "skipped"}

# ═══════ SHOW CONTROL ═══════

@router.get("/show/schedule")
async def show_schedule():
    """Get today's show schedule"""
    from src.orchestrator.show_director import ShowDirector
    return await ShowDirector().get_schedule()

@router.post("/show/say")
async def show_say(request: SayRequest):
    """
    Make avatar say something immediately
    Body: { text: "Halo semuanya!" }
    """
    from src.orchestrator.show_director import ShowDirector
    await ShowDirector().inject_speech(request.text)
    return {"status": "queued"}

# ═══════ SESSIONS & HISTORY ═══════

@router.get("/sessions")
async def sessions_list(limit: int = 20):
    """List recent stream sessions"""
    from src.data.database import get_db
    db = await get_db()
    rows = await db.execute(
        "SELECT * FROM stream_sessions ORDER BY started_at DESC LIMIT ?",
        (limit,)
    )
    sessions = [dict(r) for r in await rows.fetchall()]
    await db.close()
    return {"sessions": sessions}

@router.get("/sessions/{session_id}/events")
async def session_events(session_id: int, limit: int = 100):
    """Get events for a session"""
    from src.data.database import get_db
    db = await get_db()
    rows = await db.execute(
        "SELECT * FROM stream_events WHERE session_id=? ORDER BY created_at DESC LIMIT ?",
        (session_id, limit)
    )
    events = [dict(r) for r in await rows.fetchall()]
    await db.close()
    return {"events": events}

# ═══════ ALERTS ═══════

@router.get("/alerts")
async def alerts_list(unacknowledged_only: bool = False, limit: int = 50):
    """Get alerts"""
    from src.data.database import get_db
    db = await get_db()
    
    query = "SELECT * FROM alerts"
    if unacknowledged_only:
        query += " WHERE acknowledged=0"
    query += " ORDER BY created_at DESC LIMIT ?"
    
    rows = await db.execute(query, (limit,))
    alerts = [dict(r) for r in await rows.fetchall()]
    await db.close()
    return {"alerts": alerts}

@router.post("/alerts/{alert_id}/acknowledge")
async def alert_acknowledge(alert_id: int):
    """Acknowledge an alert"""
    from src.data.database import get_db
    db = await get_db()
    await db.execute("UPDATE alerts SET acknowledged=1 WHERE id=?", (alert_id,))
    await db.commit()
    await db.close()
    return {"status": "acknowledged"}

# ═══════ WEBSOCKET (real-time updates) ═══════

class ConnectionManager:
    def __init__(self):
        self.active: list[WebSocket] = []
    
    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.append(ws)
    
    def disconnect(self, ws: WebSocket):
        self.active.remove(ws)
    
    async def broadcast(self, message: dict):
        for ws in self.active:
            try:
                await ws.send_json(message)
            except:
                pass

ws_manager = ConnectionManager()

@router.websocket("/ws/dashboard")
async def ws_dashboard(websocket: WebSocket):
    await ws_manager.connect(websocket)
    try:
        while True:
            # Send periodic updates
            status = await stream_status()
            await websocket.send_json({
                "type": "stream_status",
                "payload": status
            })
            
            health = await health()
            await websocket.send_json({
                "type": "health_update", 
                "payload": health
            })
            
            await asyncio.sleep(5)  # Update setiap 5 detik
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
```

### 4.2 Dashboard Frontend — Svelte (Mobile-First)

```svelte
<!-- src/dashboard/frontend/src/routes/+page.svelte -->
<script>
  import { onMount, onDestroy } from 'svelte';
  
  // ═══ State ═══
  let streamStatus = {};
  let healthData = {};
  let alerts = [];
  let products = [];
  let ws = null;
  let connected = false;
  let currentView = 'overview'; // overview, products, stream, health, alerts
  
  // ═══ API helper ═══
  const API = window.location.origin + '/api';
  
  async function api(method, path, body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(`${API}${path}`, opts);
    return res.json();
  }
  
  // ═══ WebSocket ═══
  function connectWS() {
    const wsUrl = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/ws/dashboard`;
    ws = new WebSocket(wsUrl);
    
    ws.onopen = () => { connected = true; };
    ws.onclose = () => { 
      connected = false;
      // Auto-reconnect after 3 seconds
      setTimeout(connectWS, 3000);
    };
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'stream_status') streamStatus = data.payload;
      if (data.type === 'health_update') healthData = data.payload;
      if (data.type === 'alert') alerts = [data.payload, ...alerts].slice(0, 100);
    };
  }
  
  // ═══ Actions ═══
  async function startStream(platform) {
    await api('POST', '/stream/start', { platform, dry_run: false });
  }
  async function stopStream() {
    await api('POST', '/stream/stop');
  }
  async function emergencyStop() {
    if (confirm('🚨 EMERGENCY STOP — Are you sure?')) {
      await api('POST', '/stream/emergency-stop');
    }
  }
  async function pauseStream() { await api('POST', '/stream/pause'); }
  async function resumeStream() { await api('POST', '/stream/resume'); }
  async function nextProduct() { await api('POST', '/products/next'); }
  async function sayText() {
    const text = prompt('Ketik yang mau diucapkan avatar:');
    if (text) await api('POST', '/show/say', { text });
  }
  
  async function loadProducts() {
    const res = await api('GET', '/products');
    products = res.products;
  }
  
  onMount(() => {
    connectWS();
    loadProducts();
  });
  
  onDestroy(() => {
    if (ws) ws.close();
  });
  
  // ═══ Helpers ═══
  function formatUptime(seconds) {
    if (!seconds) return '--:--:--';
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h.toString().padStart(2,'0')}:${m.toString().padStart(2,'0')}:${s.toString().padStart(2,'0')}`;
  }
  
  function tempColor(temp) {
    if (!temp) return '#888';
    if (temp < 65) return '#4CAF50';
    if (temp < 75) return '#FF9800';
    if (temp < 85) return '#f44336';
    return '#b71c1c';
  }
</script>

<!-- ═══════════════════════════ -->
<!--         TOP BAR            -->
<!-- ═══════════════════════════ -->
<header class="topbar">
  <div class="logo">🎬 VLA</div>
  
  <div class="live-badge" class:active={streamStatus.is_live}>
    {streamStatus.is_live ? '🔴 LIVE' : '⚫ OFF'}
  </div>
  
  <div class="uptime">{formatUptime(streamStatus.uptime_seconds)}</div>
  
  <div class="gpu-temp" style="color: {tempColor(healthData?.gpu?.temperature)}">
    🌡 {healthData?.gpu?.temperature ?? '--'}°C
  </div>
  
  <div class="connection" class:ok={connected}>
    {connected ? '🟢' : '🔴'}
  </div>
</header>

<!-- ═══════════════════════════ -->
<!--      NAVIGATION            -->
<!-- ═══════════════════════════ -->
<nav class="nav">
  <button class:active={currentView === 'overview'} on:click={() => currentView = 'overview'}>
    📊 Overview
  </button>
  <button class:active={currentView === 'control'} on:click={() => currentView = 'control'}>
    🎮 Control
  </button>
  <button class:active={currentView === 'products'} on:click={() => currentView = 'products'}>
    📦 Products
  </button>
  <button class:active={currentView === 'health'} on:click={() => currentView = 'health'}>
    💚 Health
  </button>
  <button class:active={currentView === 'alerts'} on:click={() => currentView = 'alerts'}>
    🔔 Alerts {#if alerts.filter(a => !a.acknowledged).length > 0}
      <span class="badge">{alerts.filter(a => !a.acknowledged).length}</span>
    {/if}
  </button>
</nav>

<!-- ═══════════════════════════ -->
<!--      MAIN CONTENT          -->
<!-- ═══════════════════════════ -->
<main>

{#if currentView === 'overview'}
  <!-- OVERVIEW -->
  <div class="grid">
    <div class="card">
      <h3>Stream</h3>
      <div class="big-number">
        {streamStatus.is_live ? 'LIVE' : 'OFFLINE'}
      </div>
      <div class="sub">
        Platform: {streamStatus.platform ?? '-'}<br>
        Uptime: {formatUptime(streamStatus.uptime_seconds)}
      </div>
    </div>
    
    <div class="card">
      <h3>Current Product</h3>
      <div class="product-name">
        {streamStatus.current_product?.name ?? 'None'}
      </div>
      <div class="sub">
        {#if streamStatus.next_product}
          Next: {streamStatus.next_product.name}
        {/if}
      </div>
    </div>
    
    <div class="card">
      <h3>GPU</h3>
      <div class="big-number" style="color: {tempColor(healthData?.gpu?.temperature)}">
        {healthData?.gpu?.temperature ?? '--'}°C
      </div>
      <div class="sub">
        VRAM: {healthData?.gpu?.memory_pct ?? '--'}%<br>
        Util: {healthData?.gpu?.gpu_utilization_pct ?? '--'}%
      </div>
    </div>
    
    <div class="card">
      <h3>Stats</h3>
      <div class="stats-list">
        <div>Products shown: {streamStatus.products_shown ?? 0}</div>
        <div>Comments read: {streamStatus.comments_read ?? 0}</div>
      </div>
    </div>
  </div>

{:else if currentView === 'control'}
  <!-- CONTROL PANEL -->
  <div class="control-panel">
    <h2>🎮 Stream Control</h2>
    
    <div class="control-group">
      <h3>Start Stream</h3>
      <div class="button-row">
        <button class="btn primary" on:click={() => startStream('tiktok')} 
                disabled={streamStatus.is_live}>
          🎵 Start TikTok
        </button>
        <button class="btn primary" on:click={() => startStream('shopee')}
                disabled={streamStatus.is_live}>
          🛒 Start Shopee
        </button>
        <button class="btn primary" on:click={() => startStream('both')}
                disabled={streamStatus.is_live}>
          📡 Start Both
        </button>
      </div>
    </div>
    
    <div class="control-group">
      <h3>During Stream</h3>
      <div class="button-row">
        <button class="btn" on:click={pauseStream} disabled={!streamStatus.is_live}>
          ⏸ Pause
        </button>
        <button class="btn" on:click={resumeStream} disabled={!streamStatus.is_live}>
          ▶️ Resume
        </button>
        <button class="btn" on:click={nextProduct} disabled={!streamStatus.is_live}>
          ⏭ Next Product
        </button>
        <button class="btn" on:click={sayText} disabled={!streamStatus.is_live}>
          💬 Say Text
        </button>
      </div>
    </div>
    
    <div class="control-group">
      <h3>Stop Stream</h3>
      <div class="button-row">
        <button class="btn warning" on:click={stopStream} disabled={!streamStatus.is_live}>
          🛑 Graceful Stop
        </button>
        <button class="btn danger" on:click={emergencyStop}>
          🚨 EMERGENCY STOP
        </button>
      </div>
    </div>

    <div class="control-group">
      <h3>Current Segment</h3>
      <div class="segment-info">
        <pre>{JSON.stringify(streamStatus.current_segment, null, 2)}</pre>
      </div>
    </div>
  </div>

{:else if currentView === 'products'}
  <!-- PRODUCTS -->
  <div class="products-panel">
    <h2>📦 Product Catalog ({products.length})</h2>
    <button class="btn" on:click={loadProducts}>🔄 Refresh</button>
    
    <div class="product-list">
      {#each products as product}
        <div class="product-item" class:active={streamStatus.current_product?.id === product.id}>
          <div class="product-info">
            <strong>{product.name}</strong>
            <span class="platform-badge">{product.platform}</span>
          </div>
          <div class="product-price">Rp {product.price?.toLocaleString()}</div>
          <div class="product-commission">{product.commission_rate}% commission</div>
          <div class="product-stats">
            Shown {product.total_promotions}x
            {#if product.last_promoted_at}
              | Last: {new Date(product.last_promoted_at).toLocaleString()}
            {/if}
          </div>
        </div>
      {/each}
    </div>
  </div>

{:else if currentView === 'health'}
  <!-- HEALTH -->
  <div class="health-panel">
    <h2>💚 System Health</h2>
    
    {#if healthData?.components}
      {#each Object.entries(healthData.components) as [name, info]}
        <div class="health-item" class:ok={info.status === 'healthy'} 
             class:warn={info.severity === 'warning'}
             class:crit={info.severity === 'critical'}>
          <div class="health-name">{name}</div>
          <div class="health-status">{info.status}</div>
          {#if info.metrics}
            <div class="health-metrics">
              {#each Object.entries(info.metrics) as [k, v]}
                <span>{k}: {v}</span>
              {/each}
            </div>
          {/if}
          {#if info.issues?.length}
            <div class="health-issues">
              {#each info.issues as issue}
                <div class="issue">⚠️ {issue}</div>
              {/each}
            </div>
          {/if}
        </div>
      {/each}
    {:else}
      <p>No health data yet...</p>
    {/if}
  </div>

{:else if currentView === 'alerts'}
  <!-- ALERTS -->
  <div class="alerts-panel">
    <h2>🔔 Alerts</h2>
    
    {#each alerts as alert}
      <div class="alert-item" class:critical={alert.severity === 'critical'}
           class:warning={alert.severity === 'warning'}
           class:acknowledged={alert.acknowledged}>
        <div class="alert-time">
          {new Date(alert.created_at).toLocaleTimeString()}
        </div>
        <div class="alert-message">{alert.message}</div>
        <div class="alert-component">{alert.component}</div>
        {#if !alert.acknowledged}
          <button class="btn-sm" on:click={() => acknowledgeAlert(alert.id)}>
            ✓ Ack
          </button>
        {/if}
      </div>
    {/each}
  </div>
{/if}

</main>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, system-ui, sans-serif;
    background: #0f0f1a;
    color: #e0e0e0;
  }
  
  .topbar {
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.5rem 1rem;
    background: #1a1a2e;
    border-bottom: 1px solid #333;
    position: sticky;
    top: 0;
    z-index: 100;
  }
  
  .live-badge {
    padding: 0.25rem 0.75rem;
    border-radius: 1rem;
    font-weight: bold;
    font-size: 0.85rem;
    background: #333;
  }
  .live-badge.active {
    background: #c62828;
    animation: pulse 2s infinite;
  }
  
  @keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
  }
  
  .nav {
    display: flex;
    gap: 0;
    background: #16213e;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }
  .nav button {
    flex: 1;
    padding: 0.75rem 0.5rem;
    border: none;
    background: transparent;
    color: #888;
    cursor: pointer;
    white-space: nowrap;
    font-size: 0.85rem;
    border-bottom: 2px solid transparent;
  }
  .nav button.active {
    color: #e94560;
    border-bottom-color: #e94560;
  }
  .badge {
    background: #e94560;
    color: white;
    border-radius: 50%;
    padding: 0.1rem 0.4rem;
    font-size: 0.7rem;
    margin-left: 0.25rem;
  }
  
  main { padding: 1rem; max-width: 1200px; margin: 0 auto; }
  
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1rem;
  }
  
  .card {
    background: #1a1a2e;
    border-radius: 0.5rem;
    padding: 1rem;
    border: 1px solid #333;
  }
  .card h3 { margin: 0 0 0.5rem; color: #888; font-size: 0.85rem; }
  .big-number { font-size: 2rem; font-weight: bold; }
  .sub { color: #666; font-size: 0.85rem; margin-top: 0.5rem; }
  
  .btn {
    padding: 0.5rem 1rem;
    border: 1px solid #444;
    background: #2a2a3e;
    color: #e0e0e0;
    border-radius: 0.25rem;
    cursor: pointer;
    font-size: 0.9rem;
  }
  .btn:hover { background: #3a3a4e; }
  .btn:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn.primary { background: #1565c0; border-color: #1565c0; }
  .btn.warning { background: #e65100; border-color: #e65100; }
  .btn.danger { background: #b71c1c; border-color: #b71c1c; }
  
  .button-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 0.5rem; }
  .control-group { margin-bottom: 1.5rem; }
  
  .product-item {
    padding: 0.75rem;
    border: 1px solid #333;
    border-radius: 0.25rem;
    margin-bottom: 0.5rem;
    background: #1a1a2e;
  }
  .product-item.active { border-color: #e94560; background: #2a1a2e; }
  
  .health-item {
    padding: 0.75rem;
    margin-bottom: 0.5rem;
    border-radius: 0.25rem;
    border-left: 3px solid #4CAF50;
    background: #1a1a2e;
  }
  .health-item.warn { border-left-color: #FF9800; }
  .health-item.crit { border-left-color: #f44336; }
  
  .alert-item {
    padding: 0.5rem;
    margin-bottom: 0.5rem;
    border-radius: 0.25rem;
    background: #1a1a2e;
    display: flex;
    gap: 1rem;
    align-items: center;
  }
  .alert-item.critical { border-left: 3px solid #f44336; }
  .alert-item.warning { border-left: 3px solid #FF9800; }
  
  /* MOBILE RESPONSIVE */
  @media (max-width: 600px) {
    .topbar { font-size: 0.8rem; gap: 0.5rem; }
    .grid { grid-template-columns: 1fr; }
    .big-number { font-size: 1.5rem; }
    .button-row { flex-direction: column; }
    .btn { width: 100%; text-align: center; }
  }
</style>
```

---

## V. FLOW LENGKAP: DARI DEVELOPMENT SAMPAI LIVE

### Step-by-Step

```
═══════════════════════════════════════════════════════
 STAGE 1: LOCAL DEVELOPMENT (GTX 1650)
═══════════════════════════════════════════════════════

1. Clone repo
   git clone <repo> && cd videoliveai

2. Install dependencies
   uv sync --extra dev

3. Setup database
   uv run python scripts/manage.py setup-db

4. Run interactive menu
   uv run python scripts/manage.py menu

5. Start mock server (no GPU needed)
   uv run python scripts/manage.py serve --mock

6. Open dashboard
   http://localhost:8000/dashboard

7. Add test products via CLI atau dashboard
   uv run python scripts/manage.py product add \
     --platform tiktok --name "Test Product" \
     --price 50000 --commission 10 --link "https://..."

8. Generate scripts
   uv run python scripts/manage.py script generate --all-products

9. Verify pipeline (mock)
   uv run python scripts/manage.py verify -v

10. Test real mode (with GPU)
    uv run python scripts/manage.py serve --real
    → Verify MuseTalk works
    → Verify Fish-Speech works
    → Verify lip sync output

═══════════════════════════════════════════════════════
 STAGE 2: VAST.AI DEPLOYMENT
═══════════════════════════════════════════════════════

11. Rent Vast.ai instance (RTX 3090)

12. SSH into instance
    ssh root@VAST_IP -p VAST_PORT

13. Run setup script
    bash scripts/vast_setup.sh

14. Copy .env dan configure
    scp -P PORT .env root@VAST_IP:/workspace/videoliveai/.env
    # Edit: RTMP keys, API keys, Telegram token

15. Copy products database
    scp -P PORT data/videoliveai.db root@VAST_IP:/workspace/videoliveai/data/

16. Warm TTS cache on GPU server
    uv run python scripts/manage.py cache warm --all
    → Ini jauh lebih cepat di RTX 3090

17. Verify pipeline (real, on Vast.ai)
    uv run python scripts/manage.py verify -v
    → Semua harus ✅

18. Start services
    bash scripts/vast_start.sh

═══════════════════════════════════════════════════════
 STAGE 3: REMOTE DASHBOARD ACCESS
═══════════════════════════════════════════════════════

19. Dari PC lokal, buka SSH tunnel
    bash scripts/connect_vast.sh

20. Buka dashboard
    http://localhost:8000/dashboard

21. Atau langsung (jika port exposed di Vast.ai)
    http://VAST_IP:8000/dashboard

22. Dari HP
    Buka browser → http://VAST_IP:8000/dashboard
    → Mobile responsive

═══════════════════════════════════════════════════════
 STAGE 4: TEST STREAM
═══════════════════════════════════════════════════════

23. Set stream key via dashboard atau CLI
    Dashboard → Control → Set Stream Key
    Atau: uv run python scripts/manage.py stream set-key \
          --platform tiktok --rtmp-url "rtmp://..." --stream-key "xxx"

24. Test RTMP connection (dry run)
    uv run python scripts/manage.py stream test --platform tiktok

25. Start test stream (1 jam)
    Dashboard → Control → Start TikTok → monitor

26. Watch for:
    - GPU temperature stays < 80°C
    - No memory growth > 200MB/hour
    - Audio plays smoothly
    - Avatar moves naturally
    - Product cards show correctly
    - RTMP connection stable

═══════════════════════════════════════════════════════
 STAGE 5: PRODUCTION LIVE
═══════════════════════════════════════════════════════

27. Extend test to 4 hours → monitor
28. Extend to 8 hours → monitor
29. Go 12 hours → production!

30. Setup Telegram bot for alerts
31. Setup scheduled hourly reports

═══════════════════════════════════════════════════════
 STAGE 6: DAILY OPERATIONS
═══════════════════════════════════════════════════════

32. Update products regularly
33. Refresh scripts
34. Monitor revenue
35. Review health logs
36. Backup database weekly
```

---

## VI. MINIMUM VIABLE COMPONENTS — BUILD ORDER

```
Yang HARUS ada sebelum bisa live (MVP):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

PRIORITY 1 (BLOCKER — tanpa ini tidak bisa live):
┌────────────────────────────────────────────────┐
│ 1. TTS latency fix (chunking + cache)         │  ← PERTAMA
│ 2. Show director (content loop 12 jam)        │
│ 3. Product rotation system                     │
│ 4. RTMP output pipeline                       │
│ 5. Watchdog (auto-restart kalau crash)        │
│ 6. Dashboard stream control (start/stop/next) │
└────────────────────────────────────────────────┘

PRIORITY 2 (PENTING — bisa live tapi fragile tanpa ini):
┌────────────────────────────────────────────────┐
│ 7. GPU thermal monitoring                     │
│ 8. Stream auto-reconnect                      │
│ 9. Telegram alerts (critical only)            │
│ 10. Memory leak detection                     │
│ 11. Audio cache warm-up system                │
└────────────────────────────────────────────────┘

PRIORITY 3 (IMPROVE — bikin lebih baik):
┌────────────────────────────────────────────────┐
│ 12. Comment interaction system                │
│ 13. Product card overlay                      │
│ 14. Humanization layer (audio)                │
│ 15. Humanization layer (visual)               │
│ 16. Hourly reports                            │
└────────────────────────────────────────────────┘

PRIORITY 4 (SCALE — kalau sudah stabil):
┌────────────────────────────────────────────────┐
│ 17. Multi-platform simultaneous               │
│ 18. Team shift management                     │
│ 19. Revenue tracking                          │
│ 20. Content effectiveness scoring             │
└────────────────────────────────────────────────┘
```

---

## VII. .ENV TEMPLATE LENGKAP

```bash
# .env.example — Copy to .env and fill in

# ═══ MODE ═══
VIDEOLIVEAI_MODE=mock  # mock | real

# ═══ DATABASE ═══
VIDEOLIVEAI_DB=data/videoliveai.db

# ═══ PLATFORM RTMP ═══
TIKTOK_RTMP_URL=
# Format: rtmp://push.tiktokcdn.com/live/STREAM_KEY
SHOPEE_RTMP_URL=
# Format: rtmp://livestream.shopee.co.id/live/STREAM_KEY

# ═══ LLM ═══
LLM_PROVIDER=openai  # openai | anthropic | deepseek | local
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini  # model yang murah tapi cukup bagus untuk script
LLM_FALLBACK_MODEL=gpt-3.5-turbo

# ═══ TTS ═══
TTS_PRIMARY=fish_speech  # fish_speech | edge_tts
FISH_SPEECH_URL=http://localhost:8080  # atau internal docker URL
FISH_SPEECH_REFERENCE_WAV=assets/voice/reference.wav
FISH_SPEECH_REFERENCE_TXT=assets/voice/reference.txt
TTS_FALLBACK=edge_tts
EDGE_TTS_VOICE=id-ID-ArdiNeural  # Indonesian voice

# ═══ LIVETALKING ═══
LIVETALKING_URL=http://localhost:8010
LIVETALKING_AVATAR=musetalk_avatar1
LIVETALKING_ENGINE=musetalk  # musetalk | wav2lip

# ═══ TELEGRAM MONITORING ═══
TELEGRAM_BOT_TOKEN=
TELEGRAM_ALLOWED_USERS=  # comma-separated user IDs
# Get your user ID: message @userinfobot on Telegram

# ═══ STREAM SETTINGS ═══
STREAM_RESOLUTION=1080x1920  # Portrait
STREAM_FPS=30
STREAM_VIDEO_BITRATE=2500k
STREAM_AUDIO_BITRATE=128k
STREAM_PRODUCTS_PER_HOUR=6
STREAM_DEFAULT_DURATION_HOURS=12

# ═══ VAST.AI (for deployment) ═══
VAST_AI_API_KEY=
VAST_INSTANCE_ID=
```

---

## VIII. STRUKTUR DIREKTORI FINAL

```
videoliveai/
├── src/
│   ├── main.py                          # FastAPI entry point
│   ├── brain/
│   │   ├── __init__.py
│   │   ├── llm_router.py               # LiteLLM routing
│   │   ├── persona.py                   # Avatar persona definition
│   │   ├── safety.py                    # Content safety filter
│   │   └── script_generator.py          # Generate scripts for products
│   ├── voice/
│   │   ├── __init__.py
│   │   ├── tts_orchestrator.py          # 3-tier TTS (cache→fish→edge)
│   │   ├── fish_speech.py               # Fish-Speech client
│   │   ├── edge_tts.py                  # Edge-TTS fallback
│   │   ├── audio_cache.py               # Audio cache management
│   │   └── humanizer.py                 # Audio humanization
│   ├── face/
│   │   ├── __init__.py
│   │   ├── pipeline.py
│   │   ├── livetalking_adapter.py       # Bridge ke LiveTalking
│   │   ├── livetalking_manager.py       # Process management
│   │   └── humanizer.py                 # Visual humanization
│   ├── stream/
│   │   ├── __init__.py
│   │   ├── rtmp_manager.py              # RTMP connection management
│   │   ├── multi_platform.py            # Multi-output FFmpeg
│   │   └── reconnect.py                 # Auto-reconnect
│   ├── affiliate/
│   │   ├── __init__.py
│   │   ├── product_manager.py           # Product CRUD
│   │   ├── rotation.py                  # Product rotation scheduler
│   │   └── script_templates.py          # Template scripts per category
│   ├── orchestrator/
│   │   ├── __init__.py
│   │   └── show_director.py             # Main show loop controller
│   ├── interaction/
│   │   ├── __init__.py
│   │   ├── comment_reader.py            # Read platform comments
│   │   ├── tiktok_listener.py           # TikTok comment WebSocket
│   │   └── response_generator.py        # Auto-response to comments
│   ├── reliability/
│   │   ├── __init__.py
│   │   ├── watchdog.py                  # Main supervisor
│   │   ├── gpu_monitor.py               # GPU temp/memory
│   │   ├── memory_monitor.py            # System memory
│   │   ├── stream_monitor.py            # RTMP health
│   │   ├── process_resurrector.py       # Auto-restart LiveTalking
│   │   └── health_manager.py            # Consolidated health
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── telegram_bot.py              # Telegram alerts & commands
│   │   └── scheduled_reports.py         # Periodic reports
│   ├── dashboard/
│   │   ├── api.py                       # Dashboard REST + WebSocket API
│   │   ├── diagnostic.py                # Diagnostic endpoints
│   │   └── frontend/
│   │       ├── src/                     # Svelte source
│   │       ├── dist/                    # Built static files
│   │       ├── package.json
│   │       └── vite.config.js
│   ├── data/
│   │   ├── database.py                  # SQLite + WAL
│   │   └── migrations/                  # Schema migrations
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py                  # Pydantic settings
│   │   └── platform_config.py           # TikTok/Shopee specifics
│   └── utils/
│       ├── __init__.py
│       └── helpers.py
├── scripts/
│   ├── manage.py                        # CLI + interactive menu
│   ├── vast_setup.sh                    # Vast.ai first-time setup
│   ├── vast_start.sh                    # Start on Vast.ai
│   ├── vast_stop.sh                     # Stop on Vast.ai
│   ├── connect_vast.sh                  # SSH tunnel from local
│   ├── sync_to_vast.sh                  # Rsync code to Vast.ai
│   ├── sync_db_from_vast.sh             # Pull DB backup
│   ├── verify_pipeline.py               # Pipeline verification
│   └── backup.sh                        # Backup script
├── assets/
│   ├── voice/
│   │   ├── reference.wav                # Voice clone reference
│   │   └── reference.txt                # Reference transcript
│   ├── fonts/                           # For overlays
│   └── templates/                       # Script templates
├── data/
│   ├── videoliveai.db                   # SQLite database
│   └── audio_cache/                     # Cached TTS audio files
├── logs/                                # Runtime logs
├── tests/
├── docs/
├── external/
│   └── livetalking/                     # Vendor sidecar
├── config/
├── .env.example
├── .env                                 # (gitignored)
└── pyproject.toml
```

---

## IX. CRITICAL PATH — APA YANG HARUS DIKERJAKAN MINGGU INI

```
MINGGU INI — 3 hal saja:
━━━━━━━━━━━━━━━━━━━━━━━

1. TTS CHUNKING + CACHE SYSTEM
   ├── Implement ChunkedFishSpeech
   ├── Implement AudioCache with SQLite index
   ├── Implement 3-tier TTS orchestrator
   ├── Test: single chunk < 5 detik di GTX 1650
   └── Test: cached response < 100ms

2. PRODUCT SYSTEM (SQLite-based)
   ├── Database schema (products table)
   ├── CLI commands (add, list, import-csv)
   ├── Product rotation algorithm
   └── Basic script generation per product

3. SHOW DIRECTOR (skeleton)
   ├── Main loop: product → filler → product → interaction
   ├── Timer-based segment switching
   ├── Integration point untuk TTS + LiveTalking
   └── Start/stop dari dashboard API

BARU setelah itu:
→ Vast.ai deployment
→ Real RTMP test
→ Watchdog layer
→ Telegram monitoring
```

**Ini adalah arsitektur yang PRACTICAL untuk builder, bukan enterprise blueprint. Build → Test → Deploy → Iterate.**