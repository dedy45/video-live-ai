"""LLM Test helper — dipanggil dari menu.bat.

Usage:
    python scripts/_llm_test.py [auto|groq|chutes|gemini_local_flash|all]
"""
from __future__ import annotations

import asyncio
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

from src.brain.router import LLMRouter  # noqa: E402
from src.brain.adapters.base import TaskType  # noqa: E402


async def test_provider(router: LLMRouter, provider: str | None) -> None:
    task = TaskType.SELLING_SCRIPT if provider in ("chutes", "gemini_local_pro") else TaskType.CHAT_REPLY
    res = await router.route(
        system_prompt="Kamu adalah AI host live commerce Indonesia yang ramah dan energik.",
        user_prompt="Sapa penonton dengan semangat dan perkenalkan produk skincare terbaru!",
        task_type=task,
        preferred_provider=provider,
    )
    status = "OK  " if res.success else "FAIL"
    latency = f"{round(res.latency_ms, 0):>6}ms"
    name = provider or "auto"
    text = res.text[:80] if res.text else ""
    err = res.error[:80] if res.error else ""
    print(f"  [{status}] {name:<22} {latency}  provider={res.provider}")
    if res.success:
        print(f"          text: {text}")
    else:
        print(f"          error: {err}")
    print()


async def main() -> None:
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"
    router = LLMRouter()

    if mode == "all":
        providers = [
            "gemini_local_flash",
            "gemini_local_pro",
            "groq",
            "chutes",
            "gemini",
            "local",
            "claude",
            "gpt4o",
        ]
        print(f"  Testing {len(providers)} providers...\n")
        for p in providers:
            await test_provider(router, p)
    elif mode == "auto":
        print("  Testing auto-route (best provider)...\n")
        await test_provider(router, None)
    else:
        print(f"  Testing provider: {mode}\n")
        await test_provider(router, mode)


asyncio.run(main())
