"""Test script untuk debug LLM Router initialization."""
import sys
import os
from pathlib import Path

# Add src to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Load environment
from src.config import load_env, load_config
load_env()

print("=" * 60)
print("Testing LLM Router Initialization")
print("=" * 60)

# Check environment variables
print("\n1. Checking Environment Variables:")
env_vars = [
    "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY", 
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "CHUTES_API_KEY",
    "LOCAL_LLM_URL",
    "LOCAL_API",
]

for var in env_vars:
    val = os.getenv(var, "")
    if val:
        # Mask the key for security
        masked = val[:8] + "..." + val[-4:] if len(val) > 12 else "***"
        print(f"   ✓ {var}: {masked}")
    else:
        print(f"   ✗ {var}: NOT SET")

# Try to load config
print("\n2. Loading Config:")
try:
    config = load_config()
    print(f"   ✓ Config loaded: {config.app.name} v{config.app.version}")
except Exception as e:
    print(f"   ✗ Config load failed: {e}")
    sys.exit(1)

# Try to initialize router
print("\n3. Initializing LLM Router:")
try:
    from src.brain.router import LLMRouter
    router = LLMRouter()
    print(f"   ✓ Router initialized successfully")
    print(f"   ✓ Adapters: {list(router.adapters.keys())}")
    
    # Check adapter availability
    print("\n4. Checking Adapter Availability:")
    for name, adapter in router.adapters.items():
        status = "✓ Available" if adapter.is_available else "✗ Unavailable"
        print(f"   {status}: {name}")
        if hasattr(adapter, '_api_base'):
            print(f"      API Base: {adapter._api_base}")
        if hasattr(adapter, '_litellm_model'):
            print(f"      Model: {adapter._litellm_model}")
    
    print("\n5. Routing Table:")
    for task_type, providers in router.routing_table.items():
        print(f"   {task_type.value}: {' → '.join(providers)}")
    
    print("\n" + "=" * 60)
    print("✓ All checks passed! Router is working correctly.")
    print("=" * 60)
    
except Exception as e:
    print(f"   ✗ Router initialization failed: {e}")
    import traceback
    print("\nFull traceback:")
    traceback.print_exc()
    sys.exit(1)
