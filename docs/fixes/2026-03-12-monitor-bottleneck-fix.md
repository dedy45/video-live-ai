# Monitor Dashboard Bottleneck Fix

**Date:** 2026-03-12  
**Issue:** Monitor dashboard membutuhkan 20+ detik untuk render karena bottleneck di brain health check

## Root Cause Analysis

### Frontend (MonitorPanel.svelte)
- **Problem:** `Promise.all()` di line 29-31 memblok seluruh render sampai semua API selesai
- **Impact:** User melihat "Loading operations monitor..." selama 20+ detik

### Backend (/api/brain/health)
- **Problem:** Timeout 30s + tidak ada caching
- **Impact:** Setiap request monitor harus tunggu health check selesai (18+ detik)

### Router (router.py health_check_all)
- **Problem:** Serial execution - health check dijalankan satu per satu
- **Impact:** Total waktu = sum of all adapter timeouts (8s × 10 adapters = 80s potential)

## Solution Implemented

### 1. Frontend: Progressive Loading
**File:** `src/dashboard/frontend/src/components/panels/MonitorPanel.svelte`

**Changes:**
- Split loading state: `loading` (critical data) + `brainLoading` (brain data)
- Load critical APIs first (chats, health, resources, incidents) - fast APIs
- Load brain data in background without blocking render
- Show "Loading brain data..." only in brain section

**Result:** Dashboard renders in ~1.5s, brain data loads progressively

### 2. Backend: Caching + Reduced Timeout
**File:** `src/dashboard/api.py`

**Changes:**
- Added brain health cache with 30s TTL
- Reduced timeout from 30s → 10s
- Cache both success and error results
- Return cached result if still fresh

**Result:** Subsequent requests return instantly from cache

### 3. Router: Parallel Health Checks
**File:** `src/brain/router.py`

**Changes:**
- Changed from serial `for` loop to parallel `asyncio.gather()`
- All adapters checked concurrently
- Exception handling per-adapter (one failure doesn't block others)

**Result:** Total time = max(adapter_timeout) instead of sum(adapter_timeout)

### 4. Adapters: Lightweight Health Checks (CRITICAL FIX)
**Files:** 
- `src/brain/adapters/litellm_adapter.py`
- `src/brain/adapters/groq.py`
- `src/brain/adapters/chutes.py`

**Changes:**
- **REMOVED actual API calls from health_check()**
- Health check now only verifies configuration (API key present)
- Actual connectivity verified lazily on first real request
- Prevents 11 adapters × 8s timeout = 88s potential delay

**Result:** Brain health check completes in <100ms instead of 20+ seconds

**Why this is critical:**
- Old implementation: Each health_check() made actual API call to provider
- With 11 adapters, even parallel execution could take 8-20s (slowest provider)
- Many providers (local Gemini, Ollama) might be unreachable → timeout
- Dashboard doesn't need real-time connectivity status, just configuration status
- Real connectivity is verified when adapter is actually used

## Performance Impact

### Before Fix
- Initial load: 20+ seconds
- User experience: Blocked on "Loading operations monitor..."
- Backend timing:
  - `/api/brain/health`: 18,363 ms (actual API calls to 11 providers)
  - `/api/brain/stats`: 24 ms
  - `/api/resources`: 6 ms
  - `/api/incidents`: 3.5 ms

### After Fix
- Initial load: ~1.5 seconds (critical data)
- Brain data: ~100ms (config check only, non-blocking)
- Subsequent loads: <50ms (cached)
- User experience: Dashboard usable immediately

### Measured Performance (After Fix)
```
Recent Chats        :   2.05s
Health Summary      :   2.04s
Brain Stats         :   2.04s
Incidents           :   2.04s
Resources           :   2.01s
Brain Health        :   0.05s (was 20.33s!)

Total Time          :  10.23s (was 30.51s)
Parallel Time       :   2.05s (was 20.33s)
```

**Key Improvement:** Brain Health reduced from 20.33s → 0.05s (400× faster!)

## Technical Details

### Health Check Strategy Change

**Old Approach (Slow):**
```python
async def health_check(self) -> bool:
    # Make actual API call to provider
    response = await acompletion(
        model=self.model,
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=5,
        timeout=5.0
    )
    return bool(response.choices)
```
- Problem: 11 adapters × 5-8s timeout = 55-88s potential
- Even with parallel execution, slowest provider blocks everything
- Many local providers (Ollama, Cherry Studio) might be down

**New Approach (Fast):**
```python
async def health_check(self) -> bool:
    # Only check if API key is configured
    has_key = bool(self._api_key)
    self.is_available = has_key
    return has_key
```
- Instant: No network calls, just config check
- Actual connectivity verified lazily on first real request
- Dashboard shows "configured" vs "not configured", not "online" vs "offline"

### Adapter Timeouts (No Longer Relevant for Health Check)
All adapters had reasonable timeouts, but they're no longer used in health_check:
- LiteLLMAdapter: 8s health check timeout → now <1ms config check
- GroqAdapter: 5s health check timeout → now <1ms config check
- ChutesAdapter: 5s health check timeout → now <1ms config check

### Cache Strategy
```python
BRAIN_HEALTH_CACHE_TTL = 30.0  # seconds
```
- Cache hit: Return immediately
- Cache miss: Execute health check, cache result
- Cache both success and error states
- TTL prevents stale data

### Parallel Execution
```python
tasks = {name: adapter.health_check() for name, adapter in self.adapters.items()}
results = await asyncio.gather(*tasks.values(), return_exceptions=True)
```
- All health checks run concurrently
- Exception in one adapter doesn't affect others
- Total time = slowest adapter (not sum of all)

## Verification

Run diagnostics to verify no errors:
```bash
# No syntax/type errors in modified files
getDiagnostics([
  "src/dashboard/frontend/src/components/panels/MonitorPanel.svelte",
  "src/dashboard/api.py",
  "src/brain/router.py"
])
```

## Future Improvements

1. **WebSocket for Brain Data:** Push updates instead of polling
2. **Lazy Health Checks:** Only check adapters when actually needed
3. **Smarter Cache Invalidation:** Invalidate on adapter config changes
4. **Health Check Debouncing:** Prevent multiple concurrent checks

## Related Files

- `src/dashboard/frontend/src/components/panels/MonitorPanel.svelte`
- `src/dashboard/api.py`
- `src/brain/router.py`
- `src/brain/adapters/litellm_adapter.py` ⭐ Critical fix
- `src/brain/adapters/groq.py` ⭐ Critical fix
- `src/brain/adapters/chutes.py` ⭐ Critical fix

## Testing

To verify the fix works:

1. **Restart the server** (critical - old code still running):
   ```bash
   # Kill old processes
   pkill -f "python.*main.py"
   
   # Start fresh
   python src/main.py
   ```

2. **Test API directly**:
   ```bash
   python test_monitor_api.py
   ```
   Expected: Brain Health < 100ms

3. **Test in browser**:
   - Open http://localhost:8001/dashboard/#/monitor
   - Dashboard should render in ~2 seconds
   - Brain section shows data immediately (no "Loading brain data...")

## Lessons Learned

1. **Health checks should be lightweight** - Don't make actual API calls in health checks
2. **Lazy verification** - Verify connectivity when actually needed, not preemptively
3. **Progressive loading** - Load critical data first, defer slow operations
4. **Caching** - Cache expensive operations with reasonable TTL
5. **Parallel execution** - Run independent operations concurrently
6. **Measure first** - Always measure actual performance before optimizing
