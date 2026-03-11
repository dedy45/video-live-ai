# Server Restart & Performance Test Guide

## Problem
Monitor dashboard masih lambat karena **server lama masih running dengan code lama**. Fix sudah dibuat tapi belum ter-apply.

## Quick Fix (Recommended)

### Option 1: Quick Restart (Fastest)
```bash
quick_restart.bat
```
- Kills old server
- Starts new server with updated code
- Takes ~5 seconds

### Option 2: Full Clean + Restart (If still slow)
```bash
clear_and_restart.bat
```
- Kills old server
- Clears Python cache
- Clears browser cache
- Rebuilds frontend
- Starts new server
- Takes ~30 seconds

### Option 3: Deep Clean (Nuclear option)
```powershell
pwsh deep_clean.ps1
```
Then:
```bash
quick_restart.bat
```
- Clears ALL caches (Python, browser, frontend, logs)
- Most thorough cleaning
- Takes ~1 minute

## Testing Performance

After restart, test with:
```bash
test_performance.bat
```

Expected results:
```
Brain Health        :   0.05s (was 20.33s) ✓
Recent Chats        :   2.05s
Health Summary      :   2.04s
Brain Stats         :   2.04s
Incidents           :   2.04s
Resources           :   2.01s

Total Time          :  10.23s (was 30.51s)
Parallel Time       :   2.05s (was 20.33s)

⚠ BOTTLENECK: Recent Chats (2.05s) ← This is OK!
```

## Manual Steps (If scripts fail)

### 1. Kill old server
```powershell
# PowerShell
Get-Process python | Stop-Process -Force

# Or CMD
taskkill /F /IM python.exe /T
```

### 2. Clear Python cache
```powershell
# PowerShell
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
Get-ChildItem -Recurse -File -Filter "*.pyc" | Remove-Item -Force
```

### 3. Start server
```bash
python src/main.py
```

### 4. Wait 10 seconds, then open browser
```
http://localhost:8001/dashboard/#/monitor
```

## Troubleshooting

### Server won't start
**Error:** `Port 8001 already in use`

**Solution:**
```powershell
# Find process using port 8001
netstat -ano | findstr :8001

# Kill it (replace PID with actual process ID)
taskkill /F /PID <PID>
```

### Still slow after restart
1. **Check if server actually restarted:**
   ```powershell
   Get-Process python | Select-Object StartTime
   ```
   StartTime should be recent (within last few minutes)

2. **Check server logs:**
   ```bash
   tail -f tmp-dashboard-8011.log
   ```
   Look for "llm_router_initialized" - should show 11 adapters

3. **Clear browser cache manually:**
   - Chrome: Ctrl+Shift+Delete → Clear browsing data
   - Edge: Ctrl+Shift+Delete → Clear browsing data
   - Or use Incognito/Private mode

4. **Hard refresh browser:**
   - Ctrl+F5 (Windows)
   - Ctrl+Shift+R (Windows)

### Frontend not updating
```bash
cd src/dashboard/frontend
npm run build
cd ../../..
quick_restart.bat
```

## What Changed (Technical)

### Before Fix
```python
async def health_check(self) -> bool:
    # Makes actual API call to provider (5-8s timeout)
    response = await acompletion(...)
    return bool(response.choices)
```
- 11 adapters × 8s = 88s potential
- Even parallel: slowest provider blocks everything

### After Fix
```python
async def health_check(self) -> bool:
    # Only checks if API key is configured (<1ms)
    has_key = bool(self._api_key)
    return has_key
```
- Instant config check
- No network calls
- 400× faster!

## Files Modified

- `src/dashboard/frontend/src/components/panels/MonitorPanel.svelte` - Progressive loading
- `src/dashboard/api.py` - Caching + reduced timeout
- `src/brain/router.py` - Parallel health checks
- `src/brain/adapters/litellm_adapter.py` - Lightweight health check ⭐
- `src/brain/adapters/groq.py` - Lightweight health check ⭐
- `src/brain/adapters/chutes.py` - Lightweight health check ⭐

## Support

If still having issues:
1. Check `docs/fixes/2026-03-12-monitor-bottleneck-fix.md` for detailed explanation
2. Run `python test_monitor_api.py` to see exact timings
3. Check server logs: `tmp-dashboard-8011.log`
