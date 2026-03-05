"""Config + Env Keys Check — dipanggil dari menu.bat."""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Load .env
for line in Path(".env").read_text(encoding="utf-8").splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, _, v = line.partition("=")
    k, v = k.strip(), v.strip()
    if k and v:
        os.environ.setdefault(k, v)

sys.path.insert(0, ".")

try:
    from src.config.loader import load_config
    c = load_config()
    print("  App         :", c.app.name, "v" + c.app.version)
    print("  Env         :", c.app.env)
    print("  Dashboard   :", f"{c.dashboard.host}:{c.dashboard.port}")
    print("  LLM Budget  : $" + str(c.llm_providers.daily_budget_usd))
    print("  Gemini model:", c.llm_providers.gemini.model)
    print("  Claude model:", c.llm_providers.claude.model)
    print("  GPT model   :", c.llm_providers.gpt4o.model)
    print("  Local model :", c.llm_providers.qwen.model)
except Exception as e:
    print("  [WARN] Config load error:", e)

print()
print("  API Keys & URLs:")

keys = [
    "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GROQ_API_KEY",
    "CHUTES_API_TOKEN",
    "CHUTES_API_KEY",
    "LOCAL_LLM_URL",
    "LOCAL_API",
    "LOCAL_LLM_MODEL",
    "LOCAL_GEMINI_URL",
    "LOCAL_GEMINI_API_KEY",
    "MOCK_MODE",
    "CHUTES_MODEL",
]

for k in keys:
    v = os.getenv(k, "")
    status = "SET    " if v else "MISSING"
    display = (v[:28] + "...") if len(v) > 28 else v
    # Mask sensitive keys partially
    if v and any(x in k for x in ["KEY", "TOKEN", "API"]) and len(v) > 8:
        display = v[:6] + "****" + v[-4:]
    print(f"    [{status}] {k:<28} {display}")

print()
print("  litellm:")
try:
    import litellm
    print(f"    [SET    ] litellm                       v{litellm.__version__}")
except ImportError:
    print("    [MISSING] litellm                        run: pip install litellm")
