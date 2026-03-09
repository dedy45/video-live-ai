

# 🎯 Analisis Status & Saran Optimal

## Pemahaman Situasi Anda Saat Ini

```
┌────────────────────────────────────────────────────────────────┐
│                    CURRENT REALITY MAP                         │
│                                                                │
│  ████████████████████░░░░░░░░░░  ~60% Complete                │
│                                                                │
│  ✅ SOLID (tidak perlu disentuh lagi):                         │
│  ├── FastAPI control plane                                     │
│  ├── Brain layer (Gemini/Claude routing)                       │
│  ├── Voice orchestration (pipeline ready)                      │
│  ├── Dashboard Svelte (40 tests + 8 browser tests)            │
│  ├── FFmpeg runtime                                            │
│  ├── 143 passing tests                                         │
│  └── 11/11 pipeline layers verified                            │
│                                                                │
│  ⚠️ PARTIAL (perlu penyelesaian):                              │
│  ├── LiveTalking runtime (CPU only, no GPU validated)          │
│  ├── MuseTalk avatar (belum generated)                         │
│  ├── Face pipeline (NotImplementedError on GPU path)           │
│  └── GFPGAN (target only, not implemented)                     │
│                                                                │
│  🔴 BLOCKED / MISSING:                                         │
│  ├── Product data source (real-mode gate blocker)              │
│  ├── Real GPU validation                                       │
│  ├── RTMP to TikTok/Shopee (untested)                         │
│  ├── Voice model decision (Fish/GPT-SoVITS/Cosy)              │
│  ├── 18-24 hour stability                                      │
│  └── Production avatar + voice assets                          │
└────────────────────────────────────────────────────────────────┘
```

---

## 🧭 Prinsip Strategi: "Unblock → Validate → Harden → Launch"

```
Jangan loncat ke optimasi sebelum fondasi production BENAR-BENAR jalan.

Urutan SALAH:  Optimasi suara → Bikin behavior engine → belum bisa stream
Urutan BENAR:  Bisa stream dulu → visual jalan → suara ok → behavior polish
```

---

## 📋 FASE OPTIMAL: 6 Fase Berurutan

### FASE 1: Unblock Real-Mode Gate (3-5 hari)

**Tujuan: `check_real_mode_readiness.py` → PASS**

```
┌──────────────────────────────────────────────────────────────┐
│  FASE 1: UNBLOCK                                             │
│  Prioritas: Menghilangkan semua BLOCKER                      │
│                                                              │
│  Task 1.1: Product Data Source                               │
│  ─────────────────────────────────                           │
│  Ini blocker paling mudah tapi paling menghalangi.           │
│  Anda TIDAK perlu catalog lengkap. Cukup:                    │
│                                                              │
│    products/                                                 │
│    ├── catalog.json          ← 5-10 produk test              │
│    └── images/                                               │
│        ├── product_001.jpg                                   │
│        └── product_002.jpg                                   │
│                                                              │
│  Task 1.2: Voice Model Decision                              │
│  ─────────────────────────────────                           │
│  JANGAN menunda keputusan ini. Pilih SATU:                   │
│                                                              │
│  ┌──────────────┬───────────┬───────────┬──────────────┐    │
│  │ Criteria     │ FishSpeech│ GPT-SoVITS│ CosyVoice    │    │
│  ├──────────────┼───────────┼───────────┼──────────────┤    │
│  │ Indo quality │ ★★★☆     │ ★★★★     │ ★★★☆         │    │
│  │ Latency      │ ★★★★     │ ★★★☆     │ ★★★☆         │    │
│  │ Fine-tune    │ ★★★★     │ ★★★★★    │ ★★★☆         │    │
│  │ VRAM needed  │ ~4GB     │ ~6GB     │ ~4GB          │    │
│  │ Community ID │ ★★★☆     │ ★★★★★    │ ★★☆☆         │    │
│  │ Stability    │ ★★★★     │ ★★★☆     │ ★★★☆         │    │
│  └──────────────┴───────────┴───────────┴──────────────┘    │
│                                                              │
│  REKOMENDASI: GPT-SoVITS untuk Indonesia                     │
│  Alasan: komunitas Indonesia paling banyak,                  │
│  fine-tuning paling mature, kualitas bahasa Indonesia         │
│  paling natural. Latency bisa dioptimasi.                    │
│                                                              │
│  FALLBACK: FishSpeech jika latency jadi masalah              │
│                                                              │
│  Task 1.3: Siapkan Reference Media                           │
│  ─────────────────────────────────                           │
│  Untuk MuseTalk avatar generation nanti:                     │
│  - 1 foto portrait HD (4K, well-lit, front-facing)           │
│  - 1 video reference 10 detik (bicara, ada lip movement)     │
│  - 3 audio reference clips (neutral, excited, soft)          │
│                                                              │
│  BELUM perlu GPU. Cukup siapkan file-nya.                    │
└──────────────────────────────────────────────────────────────┘
```

```python
# products/catalog.json — Minimal viable product data
{
  "catalog_version": "0.1.0",
  "products": [
    {
      "id": "PROD001",
      "name": "Serum Vitamin C Brightening",
      "price": 89000,
      "sale_price": 65000,
      "stock": 150,
      "category": "skincare",
      "description": "Serum vitamin C 20% untuk mencerahkan kulit",
      "key_benefits": [
        "Mencerahkan dalam 7 hari",
        "Tekstur ringan, cepat meresap",
        "Cocok untuk semua jenis kulit"
      ],
      "image": "images/product_001.jpg",
      "shopee_link": "https://shopee.co.id/product/xxx",
      "tiktok_link": "https://tiktok.com/product/xxx"
    },
    {
      "id": "PROD002",
      "name": "Moisturizer Hydra Glow",
      "price": 120000,
      "sale_price": 95000,
      "stock": 200,
      "category": "skincare",
      "description": "Pelembab dengan hyaluronic acid",
      "key_benefits": [
        "Hidrasi 24 jam",
        "Non-comedogenic",
        "Ada SPF 30"
      ],
      "image": "images/product_002.jpg",
      "shopee_link": "https://shopee.co.id/product/yyy",
      "tiktok_link": "https://tiktok.com/product/yyy"
    }
  ]
}
```

```python
# scripts/create_product_source.py
"""
Jalankan ini untuk unblock real-mode gate.
uv run python scripts/create_product_source.py
"""
import json
from pathlib import Path

def create_minimal_product_source():
    products_dir = Path("products")
    products_dir.mkdir(exist_ok=True)
    (products_dir / "images").mkdir(exist_ok=True)
    
    catalog = {
        "catalog_version": "0.1.0",
        "last_updated": "2025-03-09T00:00:00Z",
        "products": [
            {
                "id": f"PROD{i:03d}",
                "name": f"Test Product {i}",
                "price": 50000 + (i * 10000),
                "sale_price": 40000 + (i * 8000),
                "stock": 100,
                "category": "skincare",
                "description": f"Test product {i} for development",
                "key_benefits": [
                    "Benefit 1", "Benefit 2", "Benefit 3"
                ],
                "image": f"images/product_{i:03d}.jpg",
                "shopee_link": "",
                "tiktok_link": ""
            }
            for i in range(1, 6)  # 5 produk test
        ]
    }
    
    catalog_path = products_dir / "catalog.json"
    catalog_path.write_text(json.dumps(catalog, indent=2))
    
    # Create placeholder images
    for i in range(1, 6):
        img_path = products_dir / f"images/product_{i:03d}.jpg"
        if not img_path.exists():
            # Create 1x1 placeholder
            img_path.write_bytes(
                b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01'
                b'\x01\x00\x00\x01\x00\x01\x00\x00'
                b'\xff\xd9'
            )
    
    print(f"✅ Product catalog created: {catalog_path}")
    print(f"   {len(catalog['products'])} products")
    print(f"   Run check_real_mode_readiness.py to verify")

if __name__ == "__main__":
    create_minimal_product_source()
```

---

### FASE 2: GPU Validation & Avatar Generation (1-2 minggu)

**Tujuan: Face pipeline berjalan di GPU, MuseTalk avatar generated**

```
┌──────────────────────────────────────────────────────────────┐
│  FASE 2: GPU VALIDATION                                      │
│                                                              │
│  ⚠️ INI ADALAH FASE PALING KRITIS                           │
│  Banyak hal yang "works in mock" tapi gagal di GPU.          │
│                                                              │
│  GPU Requirement Minimum:                                    │
│  ┌────────────────────────────────────────────┐             │
│  │  Component      │ VRAM Needed │ Concurrent │             │
│  ├────────────────────────────────────────────┤             │
│  │  MuseTalk       │ ~4 GB      │            │             │
│  │  Voice (GPT-S)  │ ~4-6 GB   │            │             │
│  │  GFPGAN         │ ~2 GB      │            │             │
│  │  Total          │ ~10-12 GB  │ ← Minimum  │             │
│  │                 │            │   RTX 3080  │             │
│  │  Recommended    │            │   RTX 4090  │             │
│  └────────────────────────────────────────────┘             │
│                                                              │
│  Jika TIDAK punya GPU 12GB+:                                │
│  → Sewa cloud GPU (RunPod / Vast.ai / Lambda)               │
│  → Atau split: Voice di cloud, Face di local                 │
│                                                              │
│  Task 2.1: Generate MuseTalk Avatar                          │
│  ────────────────────────────────────                        │
│  Input yang sudah disiapkan di Fase 1:                       │
│  - Portrait photo → avatar generation                        │
│  - Reference video → lip sync calibration                    │
│                                                              │
│  Output:                                                     │
│  external/livetalking/data/musetalk_avatar1/                │
│  ├── full_imgs/         ← extracted frames                   │
│  ├── mask/              ← face masks                         │
│  ├── coords.pkl         ← face coordinates                   │
│  └── vid_output/        ← pre-rendered segments              │
│                                                              │
│  Task 2.2: Fix NotImplementedError                           │
│  ────────────────────────────────────                        │
│  src/face/pipeline.py:                                       │
│  - MuseTalk path → implement real GPU inference              │
│  - GFPGAN path → implement (atau defer ke Fase 4)           │
│                                                              │
│  Task 2.3: Latency Benchmark                                │
│  ────────────────────────────────────                        │
│  Measure end-to-end latency:                                 │
│  Chat input → Brain → Voice → Face → Frame output           │
│                                                              │
│  TARGET: < 3 detik end-to-end                                │
│  (ditambah artificial delay 1.5-3s = total 3-6 detik         │
│   yang terasa natural)                                       │
└──────────────────────────────────────────────────────────────┘
```

```python
# scripts/gpu_benchmark.py
"""
Run setelah GPU available.
uv run python scripts/gpu_benchmark.py
"""
import time
import torch

class GPUBenchmark:
    """Benchmark setiap layer untuk latency budget"""
    
    def __init__(self):
        self.results = {}
        
    def check_gpu(self):
        print("=" * 60)
        print("GPU VALIDATION REPORT")
        print("=" * 60)
        
        if not torch.cuda.is_available():
            print("❌ CUDA not available!")
            print("   Options:")
            print("   1. Install CUDA toolkit")
            print("   2. Use cloud GPU (RunPod/Vast.ai)")
            print("   3. Split architecture (voice=cloud, face=local)")
            return False
        
        gpu = torch.cuda.get_device_properties(0)
        vram_gb = gpu.total_mem / (1024**3)
        
        print(f"✅ GPU: {gpu.name}")
        print(f"   VRAM: {vram_gb:.1f} GB")
        
        if vram_gb < 8:
            print(f"   ⚠️ VRAM < 8GB — akan perlu model splitting")
            print(f"   Rekomendasi: sequential loading, bukan concurrent")
        elif vram_gb < 12:
            print(f"   ⚠️ VRAM < 12GB — tight, perlu memory management")
        else:
            print(f"   ✅ VRAM cukup untuk concurrent loading")
        
        return True
    
    def benchmark_layer(self, name: str, fn, iterations: int = 10):
        """Benchmark satu layer"""
        # Warmup
        fn()
        torch.cuda.synchronize()
        
        times = []
        for _ in range(iterations):
            start = time.perf_counter()
            fn()
            torch.cuda.synchronize()
            elapsed = time.perf_counter() - start
            times.append(elapsed)
        
        avg = sum(times) / len(times)
        p95 = sorted(times)[int(len(times) * 0.95)]
        
        self.results[name] = {
            "avg_ms": avg * 1000,
            "p95_ms": p95 * 1000,
            "status": "✅" if avg < 0.5 else "⚠️" if avg < 1.0 else "❌"
        }
        
        print(f"  {name}:")
        print(f"    avg: {avg*1000:.0f}ms | p95: {p95*1000:.0f}ms")
    
    def print_latency_budget(self):
        """
        Show total pipeline latency vs budget
        """
        print("\n" + "=" * 60)
        print("LATENCY BUDGET")
        print("=" * 60)
        
        total_avg = sum(r["avg_ms"] for r in self.results.values())
        total_p95 = sum(r["p95_ms"] for r in self.results.values())
        
        print(f"\n  Pipeline total (avg): {total_avg:.0f}ms")
        print(f"  Pipeline total (p95): {total_p95:.0f}ms")
        print(f"  + Artificial human delay: 1500-3000ms")
        print(f"  = Perceived response time: "
              f"{total_avg + 1500:.0f} - {total_avg + 3000:.0f}ms")
        
        target = 3000  # 3 seconds pipeline target
        if total_avg < target:
            print(f"\n  ✅ Within {target}ms budget "
                  f"({target - total_avg:.0f}ms headroom)")
        else:
            print(f"\n  ❌ Over budget by {total_avg - target:.0f}ms")
            print(f"     Optimizations needed:")
            
            # Find bottleneck
            bottleneck = max(
                self.results.items(), key=lambda x: x[1]["avg_ms"]
            )
            print(f"     Bottleneck: {bottleneck[0]} "
                  f"({bottleneck[1]['avg_ms']:.0f}ms)")
```

### VRAM Management Strategy

```python
# src/core/vram_manager.py
"""
Untuk GPU < 12GB, model harus bergantian di-load.
Ini CRITICAL untuk stability jangka panjang.
"""

class VRAMManager:
    """
    Strategy: Sequential Loading
    
    Saat Brain generates text:
      → Voice model loaded, Face model offloaded
    
    Saat Voice generates audio:
      → Face model loading in background
    
    Saat Face generates frames:
      → Voice model offloaded, Brain ready (CPU/API)
    """
    
    def __init__(self, total_vram_gb: float):
        self.total_vram = total_vram_gb
        self.loaded_models = {}
        self.model_sizes = {
            "musetalk": 4.0,    # GB
            "gpt_sovits": 4.5,  # GB  
            "fish_speech": 3.5, # GB
            "gfpgan": 1.5,      # GB
        }
    
    def can_load(self, model_name: str) -> bool:
        current_usage = sum(
            self.model_sizes[m] for m in self.loaded_models
        )
        needed = self.model_sizes.get(model_name, 0)
        return (current_usage + needed) <= (self.total_vram * 0.85)
    
    def load_model(self, model_name: str):
        if not self.can_load(model_name):
            # Offload least recently used
            lru_model = min(
                self.loaded_models, 
                key=lambda m: self.loaded_models[m]["last_used"]
            )
            self.offload_model(lru_model)
        
        # Load to GPU
        self.loaded_models[model_name] = {
            "loaded_at": time.time(),
            "last_used": time.time()
        }
    
    def offload_model(self, model_name: str):
        if model_name in self.loaded_models:
            # Move to CPU / delete from VRAM
            del self.loaded_models[model_name]
            torch.cuda.empty_cache()
            
    def get_optimal_pipeline_order(self) -> list[str]:
        """
        Untuk GPU kecil, tentukan urutan optimal:
        Brain (API, no GPU) → Voice (GPU) → Face (GPU)
        
        Voice dan Face TIDAK concurrent di GPU < 12GB.
        """
        if self.total_vram >= 12:
            return ["concurrent"]  # Load semua
        elif self.total_vram >= 8:
            return ["voice_then_face"]  # Sequential
        else:
            return ["voice_then_face_with_offload"]  # Aggressive offload
```

---

### FASE 3: End-to-End Stream Test (1 minggu)

**Tujuan: Stream 30 menit ke test RTMP target tanpa crash**

```
┌──────────────────────────────────────────────────────────────┐
│  FASE 3: FIRST REAL STREAM                                   │
│                                                              │
│  Ini pertama kalinya semua layer berjalan bersama.           │
│  PASTI akan ada masalah. Itu normal.                         │
│                                                              │
│  Step 3.1: Local RTMP Test                                   │
│  ─────────────────────────                                   │
│  Jangan langsung ke TikTok. Test local dulu:                 │
│                                                              │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐              │
│  │ Pipeline  │───▶│ RTMP     │───▶│ VLC /    │              │
│  │ Output    │    │ (nginx)  │    │ OBS      │              │
│  └──────────┘    └──────────┘    │ (viewer)  │              │
│                                   └──────────┘              │
│                                                              │
│  Step 3.2: Stability Checklist                               │
│  ┌─────────────────────────────────────────────┐            │
│  │  ☐ Stream berjalan 30 menit tanpa crash     │            │
│  │  ☐ Audio-video sync maintained              │            │
│  │  ☐ Lip sync visually acceptable             │            │
│  │  ☐ No VRAM leak (memory stable)             │            │
│  │  ☐ FPS consistent (≥24 fps)                 │            │
│  │  ☐ Audio latency < 500ms                    │            │
│  │  ☐ Recovery dari temporary error             │            │
│  └─────────────────────────────────────────────┘            │
│                                                              │
│  Step 3.3: 30-Minute Burn Test                               │
│  Record metrics setiap 1 menit:                              │
│  - VRAM usage                                                │
│  - CPU usage                                                 │
│  - FPS output                                                │
│  - Audio-video sync offset                                   │
│  - Error count                                               │
│                                                              │
│  PASS CRITERIA:                                              │
│  - Zero crash                                                │
│  - VRAM tidak naik terus (leak)                              │
│  - FPS > 20 sustained                                        │
│  - A/V sync < 200ms drift                                    │
└──────────────────────────────────────────────────────────────┘
```

```python
# scripts/stream_burn_test.py
"""
30-minute burn test with metrics collection.
uv run python scripts/stream_burn_test.py --duration 1800
"""

class BurnTest:
    def __init__(self, duration_seconds: int = 1800):
        self.duration = duration_seconds
        self.metrics_log = []
        
    async def run(self):
        print("🔥 BURN TEST STARTED")
        print(f"   Duration: {self.duration // 60} minutes")
        print(f"   Collecting metrics every 10 seconds")
        print("=" * 60)
        
        start = time.time()
        
        # Start the full pipeline
        pipeline = await self.start_pipeline()
        
        while (time.time() - start) < self.duration:
            await asyncio.sleep(10)
            
            metrics = self.collect_metrics(pipeline)
            self.metrics_log.append(metrics)
            
            elapsed = time.time() - start
            self.print_status(elapsed, metrics)
            
            # Check for problems
            alerts = self.check_health(metrics)
            for alert in alerts:
                print(f"   ⚠️ {alert}")
        
        # Final report
        self.print_final_report()
    
    def collect_metrics(self, pipeline) -> dict:
        return {
            "timestamp": time.time(),
            "vram_used_mb": torch.cuda.memory_allocated() / 1e6,
            "vram_reserved_mb": torch.cuda.memory_reserved() / 1e6,
            "cpu_percent": psutil.cpu_percent(),
            "ram_used_mb": psutil.Process().memory_info().rss / 1e6,
            "fps": pipeline.get_current_fps(),
            "av_sync_ms": pipeline.get_av_sync_offset(),
            "errors_last_10s": pipeline.get_error_count(last_n_seconds=10),
            "frames_dropped": pipeline.get_dropped_frames(),
        }
    
    def check_health(self, metrics: dict) -> list[str]:
        alerts = []
        
        if metrics["vram_used_mb"] > metrics.get("prev_vram", 0) * 1.1:
            alerts.append("VRAM increasing — possible memory leak")
        
        if metrics["fps"] < 20:
            alerts.append(f"FPS dropped to {metrics['fps']}")
        
        if abs(metrics["av_sync_ms"]) > 200:
            alerts.append(f"A/V sync drift: {metrics['av_sync_ms']}ms")
        
        if metrics["errors_last_10s"] > 0:
            alerts.append(f"{metrics['errors_last_10s']} errors in last 10s")
        
        return alerts
    
    def print_final_report(self):
        print("\n" + "=" * 60)
        print("BURN TEST FINAL REPORT")
        print("=" * 60)
        
        vram_values = [m["vram_used_mb"] for m in self.metrics_log]
        fps_values = [m["fps"] for m in self.metrics_log]
        sync_values = [abs(m["av_sync_ms"]) for m in self.metrics_log]
        
        vram_trend = vram_values[-1] - vram_values[0]
        
        checks = {
            "No crash": True,  # If we got here
            f"VRAM stable (drift: {vram_trend:+.0f}MB)": abs(vram_trend) < 500,
            f"FPS avg {sum(fps_values)/len(fps_values):.1f}": 
                min(fps_values) >= 20,
            f"A/V sync max {max(sync_values):.0f}ms": 
                max(sync_values) < 200,
            f"Total errors: {sum(m['errors_last_10s'] for m in self.metrics_log)}":
                sum(m['errors_last_10s'] for m in self.metrics_log) < 5,
        }
        
        all_pass = True
        for check, passed in checks.items():
            icon = "✅" if passed else "❌"
            print(f"  {icon} {check}")
            if not passed:
                all_pass = False
        
        print()
        if all_pass:
            print("  🎉 BURN TEST PASSED — Ready for Fase 4")
        else:
            print("  ⛔ BURN TEST FAILED — Fix issues before proceeding")
```

---

### FASE 4: Humanization Layer (2 minggu)

**Tujuan: Penonton tidak curiga ini AI**

```
┌──────────────────────────────────────────────────────────────┐
│  FASE 4: HUMANIZATION                                        │
│                                                              │
│  Ini adalah fase dari saran saya sebelumnya.                │
│  TAPI hanya dimulai SETELAH Fase 3 PASS.                    │
│                                                              │
│  Prioritas implementasi (dari yang paling impactful):        │
│                                                              │
│  Priority 1: Timing (1-2 hari)                               │
│  ┌─────────────────────────────────────────────┐            │
│  │  ☐ Response delay 1.5-5 detik               │            │
│  │  ☐ Speech pauses (mid-sentence)              │            │
│  │  ☐ Selective chat answering (30%)            │            │
│  │  ☐ Filler words ("hmm", "eh", "nah")        │            │
│  └─────────────────────────────────────────────┘            │
│                                                              │
│  Priority 2: Voice (3-5 hari)                                │
│  ┌─────────────────────────────────────────────┐            │
│  │  ☐ Fine-tune voice model (3 jam data Indo)   │            │
│  │  ☐ Add breath sounds                         │            │
│  │  ☐ Add room tone                             │            │
│  │  ☐ Prosody variation (excited/calm/tired)    │            │
│  └─────────────────────────────────────────────┘            │
│                                                              │
│  Priority 3: Face (3-5 hari)                                 │
│  ┌─────────────────────────────────────────────┐            │
│  │  ☐ Natural blink (3-4 detik interval)        │            │
│  │  ☐ Head micro-motion (Perlin noise)          │            │
│  │  ☐ Eye movement variation                    │            │
│  │  ☐ GFPGAN post-processing (partial, 0.6)    │            │
│  └─────────────────────────────────────────────┘            │
│                                                              │
│  Priority 4: Behavior (3-5 hari)                             │
│  ┌─────────────────────────────────────────────┐            │
│  │  ☐ Idle actions (minum, benerin rambut)      │            │
│  │  ☐ Stream state machine                      │            │
│  │  ☐ Gift/order reactions                      │            │
│  │  ☐ System prompt "Sari" personality          │            │
│  └─────────────────────────────────────────────┘            │
│                                                              │
│  Priority 5: Environment (1-2 hari)                          │
│  ┌─────────────────────────────────────────────┐            │
│  │  ☐ Camera imperfection filter                │            │
│  │  ☐ Real room background (bukan green screen) │            │
│  │  ☐ Stream quality = medium (bukan too clean) │            │
│  └─────────────────────────────────────────────┘            │
└──────────────────────────────────────────────────────────────┘
```

---

### FASE 5: Blind Test & Iteration (1 minggu)

**Tujuan: 5 dari 5 orang tidak bisa bedakan AI vs manusia**

```
┌──────────────────────────────────────────────────────────────┐
│  FASE 5: BLIND TEST PROTOCOL                                 │
│                                                              │
│  Metodologi:                                                 │
│                                                              │
│  1. Rekam 2 video 5-menit:                                   │
│     Video A: AI livestream anda                              │
│     Video B: Host manusia asli (rekam teman/talent)          │
│                                                              │
│  2. Tunjukkan ke 10 orang (yang biasa nonton live TikTok)    │
│     Tanya: "Mana yang AI?"                                   │
│                                                              │
│  3. Scoring:                                                  │
│     ┌────────────────────────────────────────┐               │
│     │  Correct identification  │  Action     │               │
│     ├────────────────────────────────────────┤               │
│     │  > 7/10 detect AI       │  FAIL       │               │
│     │  5-7/10 detect AI       │  Iterate    │               │
│     │  < 5/10 detect AI       │  PASS       │               │
│     │  < 3/10 detect AI       │  🎉 LAUNCH  │               │
│     └────────────────────────────────────────┘               │
│                                                              │
│  4. Untuk setiap orang yang detect:                          │
│     Tanya: "Kenapa kamu pikir itu AI?"                      │
│     → Jawaban ini = bugfix priority list                    │
│                                                              │
│  Typical feedback & fixes:                                   │
│  ┌────────────────────────────────────────────┐             │
│  │  Feedback            │  Fix                │             │
│  ├────────────────────────────────────────────┤             │
│  │  "Matanya aneh"      │  Blink + eye motion │             │
│  │  "Suaranya robotic"  │  Voice fine-tuning  │             │
│  │  "Terlalu sempurna"  │  Add imperfections  │             │
│  │  "Jawabnya template" │  Better prompting   │             │
│  │  "Ga pernah diem"    │  Add idle behavior  │             │
│  │  "Gerakannya kaku"   │  Head motion + idle │             │
│  └────────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────────┘
```

---

### FASE 6: Production Launch & Long-Running Stability (2 minggu)

```
┌──────────────────────────────────────────────────────────────┐
│  FASE 6: PRODUCTION                                          │
│                                                              │
│  Step 6.1: 2-Hour Test Stream (TikTok, small audience)       │
│  ────────────────────────────────────────────                │
│  - Akun baru / akun test                                     │
│  - Malam hari (audience lebih sedikit)                       │
│  - Monitor: VRAM, FPS, error rate, chat responses            │
│  - Record everything untuk post-analysis                     │
│                                                              │
│  Step 6.2: Recovery & Watchdog                               │
│  ────────────────────────────────────────────                │
│  Untuk 18-24 jam stability:                                  │
│                                                              │
│  ┌────────────┐   ┌────────────┐   ┌────────────┐          │
│  │  Pipeline   │   │  Watchdog  │   │  Recovery  │          │
│  │  Process    │◀─▶│  (checks   │──▶│  Manager   │          │
│  │            │   │   every    │   │            │          │
│  │            │   │   30 sec)  │   │  ├─ restart│          │
│  │            │   │            │   │  ├─ reconnect        │
│  │            │   │  ├─ FPS    │   │  ├─ reload model     │
│  │            │   │  ├─ VRAM   │   │  └─ alert operator   │
│  │            │   │  ├─ A/V    │   │            │          │
│  │            │   │  └─ Errors │   │            │          │
│  └────────────┘   └────────────┘   └────────────┘          │
│                                                              │
│  Step 6.3: Gradual Scale-Up                                  │
│  ────────────────────────────────────────────                │
│  Week 1: 2 jam/hari, monitor ketat                           │
│  Week 2: 4 jam/hari, reduce monitoring                       │
│  Week 3: 8 jam/hari, automated monitoring only               │
│  Week 4+: Full schedule                                      │
│                                                              │
│  Step 6.4: Shopee Integration                                │
│  ────────────────────────────────────────────                │
│  - TikTok dulu (lebih lenient, API lebih mudah)              │
│  - Shopee setelah TikTok stable                              │
│  - Shopee butuh product link auto-pin                        │
│  - Shopee chat format berbeda dari TikTok                    │
└──────────────────────────────────────────────────────────────┘
```

```python
# src/core/watchdog.py

class StreamWatchdog:
    """
    Monitor stream health dan auto-recover.
    WAJIB untuk long-running streams.
    """
    
    def __init__(self, pipeline, max_restart_attempts: int = 3):
        self.pipeline = pipeline
        self.max_restarts = max_restart_attempts
        self.restart_count = 0
        self.check_interval = 30  # seconds
        
    async def run(self):
        while True:
            await asyncio.sleep(self.check_interval)
            
            health = self.check_health()
            
            if health["status"] == "HEALTHY":
                self.restart_count = 0  # Reset counter
                continue
            
            elif health["status"] == "DEGRADED":
                await self.handle_degraded(health)
                
            elif health["status"] == "CRITICAL":
                await self.handle_critical(health)
    
    def check_health(self) -> dict:
        checks = {
            "fps": self.pipeline.get_current_fps(),
            "vram_mb": torch.cuda.memory_allocated() / 1e6,
            "vram_max_mb": torch.cuda.get_device_properties(0).total_mem / 1e6,
            "av_sync_ms": self.pipeline.get_av_sync_offset(),
            "rtmp_connected": self.pipeline.is_rtmp_connected(),
            "last_frame_age_ms": self.pipeline.get_last_frame_age(),
            "error_rate": self.pipeline.get_error_rate(window=60),
        }
        
        # Determine status
        if not checks["rtmp_connected"]:
            return {"status": "CRITICAL", "reason": "RTMP disconnected", **checks}
        
        if checks["last_frame_age_ms"] > 5000:
            return {"status": "CRITICAL", "reason": "Pipeline frozen", **checks}
        
        if checks["vram_mb"] > checks["vram_max_mb"] * 0.95:
            return {"status": "CRITICAL", "reason": "VRAM nearly full", **checks}
        
        if checks["fps"] < 15:
            return {"status": "DEGRADED", "reason": "Low FPS", **checks}
        
        if abs(checks["av_sync_ms"]) > 500:
            return {"status": "DEGRADED", "reason": "A/V sync drift", **checks}
        
        return {"status": "HEALTHY", **checks}
    
    async def handle_degraded(self, health: dict):
        """Try soft fixes first"""
        reason = health["reason"]
        
        if reason == "Low FPS":
            # Reduce quality temporarily
            self.pipeline.set_quality("low")
            await asyncio.sleep(10)
            
            if self.pipeline.get_current_fps() >= 20:
                # Gradually restore quality
                await asyncio.sleep(30)
                self.pipeline.set_quality("medium")
        
        elif reason == "A/V sync drift":
            # Reset sync
            self.pipeline.resync_av()
    
    async def handle_critical(self, health: dict):
        """Restart components or full pipeline"""
        if self.restart_count >= self.max_restarts:
            # Alert operator — auto-recovery failed
            await self.alert_operator(
                f"❌ Pipeline failed after {self.max_restarts} restarts. "
                f"Reason: {health['reason']}. Manual intervention needed."
            )
            return
        
        self.restart_count += 1
        reason = health["reason"]
        
        if reason == "RTMP disconnected":
            # Just reconnect RTMP
            await self.pipeline.reconnect_rtmp()
            
            # Play "technical difficulty" while reconnecting
            await self.pipeline.play_holding_pattern(
                audio="maaf ya kak, bentar ada gangguan teknis dikit",
                duration=10
            )
        
        elif reason == "Pipeline frozen":
            # Full restart
            await self.pipeline.restart()
            
        elif reason == "VRAM nearly full":
            # Emergency VRAM cleanup
            torch.cuda.empty_cache()
            gc.collect()
            
            # If still full, restart with offloading
            if torch.cuda.memory_allocated() / 1e6 > health["vram_max_mb"] * 0.9:
                await self.pipeline.restart(mode="memory_saving")
```

---

## 📊 TIMELINE KESELURUHAN

```
┌──────────────────────────────────────────────────────────────┐
│                    OPTIMAL TIMELINE                          │
│                                                              │
│  Week  1-2:  FASE 1 — Unblock (product data, voice decision)│
│  Week  3-4:  FASE 2 — GPU Validation + Avatar Generation    │
│  Week  5:    FASE 3 — End-to-End Stream Test (30 min)        │
│  Week  6-7:  FASE 4 — Humanization Layer                     │
│  Week  8:    FASE 5 — Blind Test & Iteration                 │
│  Week  9-10: FASE 6 — Production Launch                      │
│                                                              │
│  Total: ~10 minggu untuk production-ready                    │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │          DEPENDENCY GRAPH                           │    │
│  │                                                     │    │
│  │  Fase 1 ──▶ Fase 2 ──▶ Fase 3 ──┐                 │    │
│  │                                   │                 │    │
│  │                                   ▼                 │    │
│  │                              Fase 4 ──▶ Fase 5     │    │
│  │                                           │         │    │
│  │                                           ▼         │    │
│  │                                      Fase 6         │    │
│  │                                                     │    │
│  │  ⚠️ Fase 4 TIDAK BOLEH dimulai sebelum Fase 3 PASS │    │
│  │  ⚠️ Fase 6 TIDAK BOLEH dimulai sebelum Fase 5 PASS │    │
│  └─────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────┘
```

---

## 🎯 SARAN PALING PENTING

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  3 ATURAN YANG TIDAK BOLEH DILANGGAR:                        │
│                                                              │
│  1. JANGAN optimize sebelum bisa stream                      │
│     ────────────────────────────────────                     │
│     Anda punya 143 test passing. Bagus.                      │
│     Tapi kalau belum bisa stream 30 menit tanpa crash,       │
│     semua humanization layer sia-sia.                        │
│     → Fase 1-3 dulu. Titik.                                 │
│                                                              │
│  2. JANGAN concurrent semua hal                              │
│     ────────────────────────────────────                     │
│     "Hati-hati dan teliti" berarti SEQUENTIAL.               │
│     Selesaikan satu fase, validasi, baru lanjut.             │
│     Jangan kerjakan voice + face + behavior sekaligus.       │
│                                                              │
│  3. JANGAN skip blind test (Fase 5)                          │
│     ────────────────────────────────────                     │
│     Anda TIDAK BISA menilai sendiri apakah terlihat natural. │
│     Developer bias = "looks good to me" padahal obvious AI.  │
│     10 orang random HARUS menilai.                           │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

```
┌──────────────────────────────────────────────────────────────┐
│                                                              │
│  BESOK ANDA HARUS:                                           │
│                                                              │
│  1. ☐ Jalankan scripts/create_product_source.py              │
│  2. ☐ Jalankan check_real_mode_readiness.py → harus PASS     │
│  3. ☐ Putuskan: GPT-SoVITS atau FishSpeech                  │
│  4. ☐ Siapkan 1 foto portrait HD untuk avatar                │
│  5. ☐ Cek ketersediaan GPU (lokal atau cloud)                │
│                                                              │
│  5 task ini = 1 hari kerja.                                  │
│  Setelah ini, Fase 1 selesai.                                │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```