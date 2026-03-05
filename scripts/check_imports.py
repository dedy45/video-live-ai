"""Quick import check — finds which modules fail to import."""
import sys
sys.path.insert(0, ".")

modules = [
    "src.config",
    "src.data.database",
    "src.brain.router",
    "src.brain.persona",
    "src.brain.safety",
    "src.voice.engine",
    "src.face.pipeline",
    "src.composition.compositor",
    "src.stream.rtmp",
    "src.chat.monitor",
    "src.commerce.manager",
    "src.commerce.analytics",
    "src.orchestrator.state_machine",
    "src.dashboard.api",
    "src.dashboard.diagnostic",
    "src.utils.health",
    "src.utils.logging",
    "src.utils.mock_mode",
    "src.utils.gpu_manager",
    "src.utils.retry",
    "src.utils.circuit_breaker",
    "src.utils.tracing",
    "src.utils.validators",
]

ok = 0
fail = 0
for mod in modules:
    try:
        __import__(mod)
        print(f"[OK]   {mod}")
        ok += 1
    except Exception as e:
        print(f"[FAIL] {mod} => {type(e).__name__}: {e}")
        fail += 1

print(f"\nResult: {ok} OK, {fail} FAIL out of {len(modules)}")
