"""Run dashboard server with detailed debug logging."""
import sys
import os
from pathlib import Path

# Add src to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set debug logging
os.environ["LOG_LEVEL"] = "DEBUG"

print("=" * 60)
print("Starting Dashboard Server with Debug Logging")
print("=" * 60)

# Check .env file
env_file = Path(".env")
if env_file.exists():
    print(f"✓ .env file found: {env_file.absolute()}")
else:
    print(f"✗ .env file NOT found at: {env_file.absolute()}")
    sys.exit(1)

# Load environment first
print("\nLoading environment...")
from src.config import load_env, load_config
env = load_env()
print(f"✓ Environment loaded")

# Load config
print("\nLoading config...")
config = load_config()
print(f"✓ Config loaded: {config.app.name} v{config.app.version}")

# Create app
print("\nCreating FastAPI app...")
from src.main import create_app
app = create_app()
print(f"✓ App created with {len(app.routes)} routes")

# Check if LLM Router was initialized
print("\nChecking LLM Router...")
from src.dashboard.api import get_llm_router
router = get_llm_router()
if router:
    print(f"✓ LLM Router initialized with {len(router.adapters)} adapters")
    print(f"  Adapters: {list(router.adapters.keys())}")
else:
    print("✗ LLM Router NOT initialized - check logs above")

# Start server
print("\n" + "=" * 60)
print(f"Starting server on {config.dashboard.host}:{config.dashboard.port}")
print("=" * 60)
print("\nPress Ctrl+C to stop\n")

import uvicorn
uvicorn.run(
    app,
    host=config.dashboard.host,
    port=config.dashboard.port,
    log_level="debug",
)
