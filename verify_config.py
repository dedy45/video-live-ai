"""Verify current LLM configuration and loaded adapters.

Run this to see which adapters WILL be loaded based on current .env
"""
import os
from pathlib import Path

# Load .env
env_file = Path(".env")
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if key and val and key not in os.environ:
            os.environ[key] = val

def _is_valid_key(key: str) -> bool:
    """Check if API key is valid (not placeholder)."""
    if not key:
        return False
    # Check for common placeholder patterns (case-insensitive)
    placeholders = ["your_", "changeme", "placeholder", "xxx", "yyy"]
    key_lower = key.lower()
    is_placeholder = any(p in key_lower for p in placeholders)
    return not is_placeholder

print("=" * 70)
print("LLM CONFIGURATION VERIFICATION")
print("=" * 70)
print()

# Check each provider
providers = {
    "GEMINI (cloud)": os.getenv("GEMINI_API_KEY", ""),
    "ANTHROPIC (cloud)": os.getenv("ANTHROPIC_API_KEY", ""),
    "OPENAI (cloud)": os.getenv("OPENAI_API_KEY", ""),
    "GROQ (cloud)": os.getenv("GROQ_API_KEY", ""),
    "CHUTES (cloud)": os.getenv("CHUTES_API_KEY", "") or os.getenv("CHUTES_API_TOKEN", ""),
}

# Debug: print actual values
print("DEBUG - Actual .env values:")
for name, key in providers.items():
    print(f"  {name}: '{key[:40] if key else '(empty)'}...'")
print()

print("CLOUD PROVIDERS:")
print("-" * 70)
loaded_cloud = []
for name, key in providers.items():
    is_valid = _is_valid_key(key)
    status = "[LOAD]" if is_valid else "[SKIP]"
    reason = ""
    if not key:
        reason = " (no key in .env)"
    elif not is_valid:
        reason = f" (placeholder: {key[:30]}...)"
    
    print(f"{name:25} {status:10} {reason}")
    if is_valid:
        loaded_cloud.append(name.split()[0].lower())

print()
print("LOCAL PROVIDERS:")
print("-" * 70)

local_api = os.getenv("LOCAL_API", "")
local_gemini = os.getenv("LOCAL_GEMINI_API_KEY", "")

has_local = _is_valid_key(local_api) or _is_valid_key(local_gemini)

if has_local:
    print("[LOAD] LOCAL ADAPTERS WILL LOAD")
    print(f"   LOCAL_API: {local_api[:30] if local_api else '(not set)'}")
    print(f"   LOCAL_GEMINI_API_KEY: {local_gemini[:30] if local_gemini else '(not set)'}")
    print()
    print("   These adapters will be loaded:")
    print("   - gemini_local_flash")
    print("   - gemini_25_flash")
    print("   - gemini_local_pro")
    print("   - claude_local")
    print("   - gpt4o_local")
    loaded_local = 5
else:
    print("[SKIP] LOCAL ADAPTERS SKIPPED")
    print(f"   LOCAL_API: {local_api if local_api else '(commented out or empty)'}")
    print(f"   LOCAL_GEMINI_API_KEY: {local_gemini if local_gemini else '(not set)'}")
    print()
    print("   To enable local adapters, uncomment in .env:")
    print("   LOCAL_API=sk-231d5e6912b44d929ac0b93ba2d2e033")
    loaded_local = 0

print()
print("=" * 70)
print("SUMMARY")
print("=" * 70)
total = len(loaded_cloud) + loaded_local
print(f"Total adapters that will load: {total}")
print(f"  - Cloud: {len(loaded_cloud)}")
print(f"  - Local: {loaded_local}")
print()

if total == 0:
    print("WARNING: No adapters will load!")
    print("   Add at least one valid API key to .env")
elif total < 3:
    print(f"WARNING: Only {total} adapter(s) configured")
    print("   Consider adding more for reliability")
else:
    print("[OK] Good configuration!")

print()
print("Expected dashboard display:")
if total > 0:
    print(f"  Healthy {total}/{total}")
    if loaded_cloud:
        print(f"  Cloud providers: {', '.join(loaded_cloud)}")
    if loaded_local > 0:
        print(f"  Local providers: gemini_local_flash, gemini_25_flash, gemini_local_pro, claude_local, gpt4o_local")
else:
    print("  No providers available")

print()
print("=" * 70)
print("NEXT STEPS")
print("=" * 70)
print("1. If configuration looks correct:")
print("   → Run: quick_restart.bat")
print()
print("2. After restart, verify in dashboard:")
print("   → Open: http://localhost:8001/dashboard/#/monitor")
print()
print("3. Check logs:")
print("   → grep 'adapter_loaded\\|adapter_skipped' tmp-dashboard-8011.log")
print()
print("=" * 70)
