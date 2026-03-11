# Groq + Gemini Only Setup

## Perubahan yang Dilakukan

### 1. .env Configuration
```env
# Hanya Groq + Gemini yang aktif
GROQ_API_KEY=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
GEMINI_API_KEY=AIzaSyBrMFGk9OneX4kSKpxOlA07Ea-zd55wNF0

# Provider lain di-comment
#ANTHROPIC_API_KEY=...
#OPENAI_API_KEY=...
#LOCAL_API=...
```

### 2. Router Priority (router.py)
```python
# Semua task type prioritas: Groq → Gemini
DEFAULT_ROUTING = {
    TaskType.CHAT_REPLY:     ["groq", "gemini"],
    TaskType.SELLING_SCRIPT: ["groq", "gemini"],
    TaskType.HUMOR:          ["groq", "gemini"],
    # ... semua task type sama
}
```

### 3. Current Provider Tracking
- Router sekarang track provider yang sedang aktif
- Dashboard menampilkan "Active: groq" (bukan "unknown")
- Update otomatis setiap kali ada request berhasil

### 4. Frontend Update
- Menampilkan `current_provider` dari API
- Default ke "groq" jika belum ada request
- Chip list menampilkan hanya provider yang ter-load

## Cara Apply

### Option 1: One-Click (Recommended)
```bash
APPLY_GROQ_GEMINI_ONLY.bat
```

Script ini akan:
1. ✓ Clean Windows env vars
2. ✓ Stop old server
3. ✓ Clear caches
4. ✓ Rebuild frontend
5. ✓ Start new server
6. ✓ Verify configuration

### Option 2: Manual Steps

1. Clean Windows environment variables:
```bash
clean_env_vars.bat
```

2. Restart server:
```bash
quick_restart.bat
```

3. Verify:
```bash
python verify_config.py
```

## Expected Result

### Dashboard Display
```
Active: groq
Healthy: 2/2

● groq     groq/llama-3.3-70b-versatile
● gemini   gemini/gemini-2.0-flash
```

### Performance
- Brain Health API: < 100ms (was 20,000ms)
- Dashboard load: ~2 seconds (was 30+ seconds)
- Only 2 adapters loaded (was 11)

### Logs
```bash
grep "adapter_loaded" tmp-dashboard-8011.log
```

Expected output:
```json
{"event": "adapter_loaded", "provider": "groq", "model": "llama-3.3-70b-versatile"}
{"event": "adapter_loaded", "provider": "gemini", "model": "gemini-2.0-flash"}
{"event": "adapters_build_complete", "total_loaded": 2, "providers": ["groq", "gemini"]}
{"event": "routing_table_built", "providers_per_task": 2, "chain": ["groq", "gemini"]}
{"event": "router_initialized", "default_provider": "groq"}
```

## Verification

### 1. Check Configuration
```bash
python verify_config.py
```

Should show:
```
Total adapters that will load: 2
  - Cloud: 2 (groq, gemini)
  - Local: 0
```

### 2. Test Dashboard
Open: http://localhost:8001/dashboard/#/monitor

Check:
- [ ] "Active" shows "groq" (not "unknown")
- [ ] "Healthy" shows "2/2"
- [ ] Only 2 chips displayed (groq, gemini)
- [ ] Page loads in ~2 seconds

### 3. Test Brain
Click "Test Brain" button

Expected:
```
✓ groq/llama-3.3-70b-versatile — 250ms
```

### 4. Check Logs
```bash
# See which adapters loaded
grep "adapter_loaded\|adapter_skipped" tmp-dashboard-8011.log

# See routing table
grep "routing_table_built" tmp-dashboard-8011.log

# See current provider
grep "route_success" tmp-dashboard-8011.log | tail -5
```

## Troubleshooting

### "Active" still shows "unknown"
**Cause:** No request has been made yet

**Solution:** Click "Test Brain" button to trigger a request

### ANTHROPIC still appears in dashboard
**Cause:** Windows environment variable override

**Solution:**
```bash
# Check Windows env var
echo %ANTHROPIC_API_KEY%

# If not empty, clean it
clean_env_vars.bat

# Then restart
quick_restart.bat
```

### Dashboard still slow
**Cause:** Old server still running or cache not cleared

**Solution:**
```bash
# Kill all Python processes
taskkill /F /IM python.exe

# Run full fix
APPLY_GROQ_GEMINI_ONLY.bat
```

### Groq fails, Gemini not used
**Cause:** Fallback chain not working

**Solution:** Check logs:
```bash
grep "route_success\|provider_failed" tmp-dashboard-8011.log | tail -10
```

Should show fallback to gemini if groq fails.

## Benefits

### Performance
- ✅ 200× faster health checks (100ms vs 20,000ms)
- ✅ 15× faster dashboard load (2s vs 30s)
- ✅ 5× fewer adapters to manage (2 vs 11)

### Cost
- ✅ Groq: $0.59/M input, $0.79/M output (cheapest)
- ✅ Gemini: $0.075/M input, $0.30/M output (backup)
- ✅ No local server needed (simpler setup)

### Reliability
- ✅ Groq: Ultra-fast (250ms avg)
- ✅ Gemini: Reliable backup
- ✅ Automatic fallback if Groq fails
- ✅ No "unknown" provider confusion

## Files Modified

1. `.env` - Cleaned up, only Groq + Gemini
2. `src/brain/router.py` - Simplified routing, added current_provider tracking
3. `src/dashboard/api.py` - Added current_provider to brain health response
4. `src/dashboard/frontend/src/components/panels/MonitorPanel.svelte` - Display current provider

## Rollback

To restore previous configuration:

1. Uncomment providers in `.env`:
```env
ANTHROPIC_API_KEY=your_key_here
OPENAI_API_KEY=your_key_here
LOCAL_API=sk-231d5e6912b44d929ac0b93ba2d2e033
```

2. Restart:
```bash
quick_restart.bat
```

3. Verify:
```bash
python verify_config.py
```
