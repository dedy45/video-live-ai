# LLM Provider Configuration Guide

## Overview

Router sekarang **hanya load adapter yang punya API key valid** di `.env`. Ini membuat:
- ✅ Startup lebih cepat
- ✅ Health check lebih cepat
- ✅ Dashboard hanya tampilkan provider yang terpakai
- ✅ Tidak ada error dari provider yang tidak dikonfigurasi

## How It Works

### 1. Auto-Detection
Router membaca `.env` dan hanya load adapter yang punya API key:

```python
# Valid key - akan di-load
GEMINI_API_KEY=AIzaSyBrMFGk9OneX4kSKpxOlA07Ea-zd55wNF0

# Placeholder - akan di-skip
ANTHROPIC_API_KEY=your_anthropic_key_here
OPENAI_API_KEY=your_openai_key_here
```

### 2. Placeholder Detection
Router otomatis skip key yang mengandung:
- `your_`
- `changeme`
- `placeholder`
- `xxx`, `yyy`
- Empty string

### 3. Dynamic Routing Table
Routing table dibangun berdasarkan adapter yang ter-load:

```python
# Jika hanya Gemini + Groq + Chutes yang ter-load:
routing[TaskType.CHAT_REPLY] = ["groq", "chutes", "gemini"]
# Claude dan GPT-4o otomatis di-skip karena tidak ter-load
```

## Configuration Examples

### Minimal Setup (Cloud Only - No Local)
```env
# .env
GEMINI_API_KEY=AIzaSyBrMFGk9OneX4kSKpxOlA07Ea-zd55wNF0
GROQ_API_KEY=gsk_xxx
CHUTES_API_KEY=cpk_xxx

# Comment out or remove local keys
# LOCAL_API=sk-xxx
# LOCAL_GEMINI_API_KEY=sk-xxx
```
**Result:** Only cloud adapters (gemini, groq, chutes) - 3 total

### Local Only Setup (Free)
```env
# .env
LOCAL_API=sk-231d5e6912b44d929ac0b93ba2d2e033
LOCAL_GEMINI_URL=http://127.0.0.1:8091/v1
```
**Result:** Only local adapters (gemini_local_*, claude_local, gpt4o_local) - 5 total

### Budget Setup (Cloud + Local)
```env
# .env
GEMINI_API_KEY=AIzaSyBrMFGk9OneX4kSKpxOlA07Ea-zd55wNF0
GROQ_API_KEY=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
LOCAL_API=sk-231d5e6912b44d929ac0b93ba2d2e033
```
**Result:** Gemini + Groq + local adapters (8 total)

### Full Setup (All Providers)
```env
# .env
GEMINI_API_KEY=AIzaSyBrMFGk9OneX4kSKpxOlA07Ea-zd55wNF0
ANTHROPIC_API_KEY=sk-ant-api03-xxx
OPENAI_API_KEY=sk-proj-xxx
GROQ_API_KEY=gsk_xxx
CHUTES_API_KEY=cpk_xxx
LOCAL_API=sk-231d5e6912b44d929ac0b93ba2d2e033
```
**Result:** All 11 adapters loaded

## Current Configuration

Based on your `.env` (after disabling local):

### ✅ Loaded Adapters (3)
1. **gemini** - Google Gemini 2.0 Flash (cloud)
2. **groq** - Groq Llama 3.3 70B (cloud, fast)
3. **chutes** - Chutes.ai MiniMax M2.5 (cloud)

### ❌ Skipped Adapters (8)
1. **claude** - No valid ANTHROPIC_API_KEY
2. **gpt4o** - No valid OPENAI_API_KEY
3. **gemini_local_flash** - LOCAL_API commented out
4. **gemini_25_flash** - LOCAL_API commented out
5. **gemini_local_pro** - LOCAL_API commented out
6. **claude_local** - LOCAL_API commented out
7. **gpt4o_local** - LOCAL_API commented out
8. **local** - LOCAL_API commented out

**Total:** 3 adapters (cloud only)

## Adding New Providers

### Step 1: Get API Key
Sign up for provider and get API key:
- Anthropic Claude: https://console.anthropic.com/
- OpenAI GPT: https://platform.openai.com/api-keys

### Step 2: Add to .env
```env
# Add your key
ANTHROPIC_API_KEY=sk-ant-api03-your-actual-key-here
OPENAI_API_KEY=sk-proj-your-actual-key-here
```

### Step 3: Restart Server
```bash
quick_restart.bat
```

### Step 4: Verify
Check dashboard - new providers should appear:
```
http://localhost:8001/dashboard/#/monitor
```

Or check logs:
```bash
grep "adapter_loaded" tmp-dashboard-8011.log
```

## Removing Providers

### Option 1: Comment Out API Key (Recommended)
```env
# Comment out to disable
#LOCAL_API=sk-231d5e6912b44d929ac0b93ba2d2e033
#ANTHROPIC_API_KEY=sk-ant-xxx
```

### Option 2: Remove Line Completely
```env
# Just delete the line
# (no ANTHROPIC_API_KEY line at all)
```

### Option 3: Use Placeholder
```env
# Replace with placeholder
ANTHROPIC_API_KEY=your_anthropic_key_here
```

**Important for Local Adapters:**
To disable ALL local adapters (gemini_local_*, claude_local, gpt4o_local), you must:
```env
# Comment out BOTH:
#LOCAL_API=sk-xxx
#LOCAL_GEMINI_API_KEY=sk-xxx
```

If either is set, local adapters will load.

Then restart server:
```bash
quick_restart.bat
```

## Routing Priority

Router prioritizes providers in this order:

### 1. Chat Replies (Speed Priority)
```
groq → gemini_local_flash → gemini_25_flash → gpt4o_local → 
claude_local → chutes → local → gemini
```

### 2. Selling Scripts (Quality Priority)
```
claude_local → gemini_local_pro → gpt4o_local → chutes → 
groq → gemini → claude → gpt4o
```

### 3. Product QA (Accuracy Priority)
```
gemini_local_pro → claude_local → gpt4o_local → chutes → 
groq → gemini → claude → gpt4o
```

### 4. Safety Check (Accuracy Priority)
```
claude_local → gemini_local_pro → gpt4o_local → groq → 
gemini → claude → gpt4o
```

**Note:** Only loaded adapters are included in routing table.

## Cost Optimization

### Free Tier (No API Costs)
Use only local adapters:
```env
LOCAL_API=sk-231d5e6912b44d929ac0b93ba2d2e033
LOCAL_GEMINI_URL=http://127.0.0.1:8091/v1
```

### Budget Tier ($1-5/day)
Add Groq (cheapest cloud):
```env
GROQ_API_KEY=gsk_xxx
LOCAL_API=sk-xxx
```

### Production Tier ($5-20/day)
Add Gemini + Groq:
```env
GEMINI_API_KEY=AIza_xxx
GROQ_API_KEY=gsk_xxx
LOCAL_API=sk-xxx
```

### Enterprise Tier (Unlimited)
Add all providers for maximum reliability:
```env
GEMINI_API_KEY=AIza_xxx
ANTHROPIC_API_KEY=sk-ant_xxx
OPENAI_API_KEY=sk-proj_xxx
GROQ_API_KEY=gsk_xxx
CHUTES_API_KEY=cpk_xxx
LOCAL_API=sk-xxx
```

## Troubleshooting

### Provider Not Showing in Dashboard

**Check 1:** API key valid?
```bash
grep "PROVIDER_API_KEY" .env
```

**Check 2:** Check logs
```bash
grep "adapter_loaded\|adapter_skipped" tmp-dashboard-8011.log
```

**Check 3:** Restart server
```bash
quick_restart.bat
```

### Provider Shows But Fails

**Symptom:** Provider appears in dashboard but requests fail

**Cause:** API key invalid or expired

**Solution:**
1. Test key manually
2. Check provider dashboard for quota/billing
3. Update key in `.env`
4. Restart server

### Too Many Providers

**Symptom:** Dashboard cluttered with unused providers

**Solution:** Remove unused API keys from `.env`:
```env
# Comment out unused providers
# ANTHROPIC_API_KEY=sk-ant-xxx
# OPENAI_API_KEY=sk-proj-xxx
```

## Logs

### Startup Logs
```bash
# See which adapters loaded
grep "adapter_loaded" tmp-dashboard-8011.log

# See which adapters skipped
grep "adapter_skipped" tmp-dashboard-8011.log

# See routing table
grep "routing_table_built" tmp-dashboard-8011.log
```

### Example Output
```json
{"event": "adapter_loaded", "provider": "gemini", "model": "gemini-2.0-flash"}
{"event": "adapter_loaded", "provider": "groq", "model": "llama-3.3-70b-versatile"}
{"event": "adapter_loaded", "provider": "chutes", "model": "MiniMaxAI/MiniMax-M2.5-TEE"}
{"event": "adapter_skipped", "provider": "claude", "reason": "no_valid_api_key"}
{"event": "adapter_skipped", "provider": "gpt4o", "reason": "no_valid_api_key"}
{"event": "adapters_build_complete", "total_loaded": 8, "providers": ["gemini", "groq", "chutes", ...]}
{"event": "routing_table_built", "tasks": 7, "avg_providers_per_task": 5.2}
```

## Best Practices

1. **Start Small:** Begin with free/local adapters, add cloud as needed
2. **Monitor Costs:** Check `/api/brain/stats` for daily spend
3. **Test New Providers:** Use "Test Brain" button in dashboard
4. **Keep Backups:** Always have 2+ providers configured for reliability
5. **Update Keys:** Rotate API keys periodically for security

## Related Files

- `.env` - Configuration file
- `src/brain/router.py` - Router implementation
- `src/brain/adapters/` - Adapter implementations
- `docs/fixes/2026-03-12-monitor-bottleneck-fix.md` - Performance fix details
