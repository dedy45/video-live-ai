"""Pipeline Verification CLI — verify every layer works correctly.

Usage:
    python scripts/verify_pipeline.py           # Verify all layers
    python scripts/verify_pipeline.py --layer brain   # Verify one layer
    python scripts/verify_pipeline.py --verbose       # Detailed output

Covers Checkpoints 3, 6, 10, 13 from tasks.md.
"""

from __future__ import annotations

import asyncio
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path

# Ensure project root on path
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("MOCK_MODE", "true")


@dataclass
class VerifyResult:
    layer: str
    passed: bool
    message: str
    duration_ms: float
    details: list[str]


class PipelineVerifier:
    """Runs verification checks on each system layer."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.results: list[VerifyResult] = []

    async def verify_all(self) -> list[VerifyResult]:
        """Run all layer verifications in sequence."""
        checks = [
            ("config", self._verify_config),
            ("database", self._verify_database),
            ("brain", self._verify_brain),
            ("voice", self._verify_voice),
            ("face", self._verify_face),
            ("composition", self._verify_composition),
            ("stream", self._verify_stream),
            ("chat", self._verify_chat),
            ("commerce", self._verify_commerce),
            ("orchestrator", self._verify_orchestrator),
            ("health", self._verify_health),
        ]
        for name, check_fn in checks:
            result = await self._run_check(name, check_fn)
            self.results.append(result)
        return self.results

    async def verify_one(self, layer: str) -> VerifyResult:
        """Verify a single layer."""
        checks = {
            "config": self._verify_config,
            "database": self._verify_database,
            "brain": self._verify_brain,
            "voice": self._verify_voice,
            "face": self._verify_face,
            "composition": self._verify_composition,
            "stream": self._verify_stream,
            "chat": self._verify_chat,
            "commerce": self._verify_commerce,
            "orchestrator": self._verify_orchestrator,
            "health": self._verify_health,
        }
        fn = checks.get(layer)
        if not fn:
            return VerifyResult(layer, False, f"Unknown layer: {layer}", 0, [])
        return await self._run_check(layer, fn)

    async def _run_check(self, name: str, fn) -> VerifyResult:
        start = time.time()
        try:
            details = await fn()
            elapsed = (time.time() - start) * 1000
            return VerifyResult(name, True, "PASS", elapsed, details)
        except Exception as e:
            elapsed = (time.time() - start) * 1000
            return VerifyResult(name, False, f"FAIL: {e}", elapsed, [str(e)])

    # ── Individual layer checks ──────────────────────────────────

    async def _verify_config(self) -> list[str]:
        from src.config import get_config, get_env, is_mock_mode
        details = []
        config = get_config()
        details.append(f"App: {config.app.name} v{config.app.version}")
        details.append(f"Mock Mode: {is_mock_mode()}")
        details.append(f"LLM budget: ${config.llm_providers.daily_budget_usd}/day")
        env = get_env()
        details.append(f"Dashboard: {env.dashboard_host}:{env.dashboard_port}")
        return details

    async def _verify_database(self) -> list[str]:
        from src.data.database import check_database_health, init_database
        details = []
        init_database()
        health = check_database_health()
        assert health["healthy"], f"Database unhealthy: {health['message']}"
        details.append(f"Status: {health['message']}")
        details.append(f"Tables: {health['tables']}")
        return details

    async def _verify_brain(self) -> list[str]:
        from src.brain.adapters.base import TaskType
        from src.brain.router import LLMRouter
        from src.brain.persona import PersonaEngine
        from src.brain.safety import SafetyFilter
        details = []

        # Router
        router = LLMRouter()
        response = await router.route("Test system", "Halo!", task_type=TaskType.CHAT_REPLY)
        assert response.success, f"Router failed: {response.error}"
        details.append(f"Router: {response.provider}/{response.model} → {len(response.text)} chars")

        # Health check all adapters
        health = await router.health_check_all()
        for name, ok in health.items():
            details.append(f"  Adapter {name}: {'✓' if ok else '✗'}")

        # Persona
        persona = PersonaEngine()
        prompt = persona.build_system_prompt(state="SELLING", product_context="Test Product")
        assert len(prompt) > 50, "Persona prompt too short"
        details.append(f"Persona prompt: {len(prompt)} chars")

        # Safety
        safety = SafetyFilter()
        result = safety.check("Ini teks aman untuk dijual")
        assert result.safe, "Safe text flagged incorrectly"
        details.append(f"Safety: passed (incidents={safety.incident_count})")

        return details

    async def _verify_voice(self) -> list[str]:
        from src.voice.engine import VoiceRouter
        details = []
        router = VoiceRouter()
        result = await router.synthesize("Halo semuanya!", emotion="happy", trace_id="verify-voice")
        assert len(result.audio_data) > 0, "No audio data returned"
        details.append(f"Audio: {len(result.audio_data)} bytes, {result.duration_ms:.0f}ms")
        details.append(f"Cache size: {router.cache.size}")
        return details

    async def _verify_face(self) -> list[str]:
        from src.face.pipeline import AvatarPipeline
        details = []
        pipeline = AvatarPipeline()
        frames = []
        async for frame in pipeline.render(b"fake_audio", 100.0, trace_id="verify-face"):
            frames.append(frame)
        assert len(frames) >= 1, "No frames rendered"
        details.append(f"Frames: {len(frames)}, size: {frames[0].width}x{frames[0].height}")
        return details

    async def _verify_composition(self) -> list[str]:
        from src.composition.compositor import FFmpegCompositor
        details = []
        comp = FFmpegCompositor()
        fg = comp.build_filter_graph(
            background_path="assets/backgrounds/room.png",
            product_image_path="assets/products/item.png",
            price_text="Rp 99.000",
            cta_text="Checkout Sekarang!",
        )
        assert len(fg) > 0, "Empty filter graph"
        details.append(f"Filter graph: {len(fg)} chars")
        health = await comp.health_check()
        details.append(f"FFmpeg available: {health}")
        return details

    async def _verify_stream(self) -> list[str]:
        from src.stream.rtmp import RTMPStreamer, StreamStatus
        details = []
        streamer = RTMPStreamer(platform="tiktok")
        started = await streamer.start()
        assert started, "Stream failed to start"
        health = streamer.get_health()
        assert health.status == StreamStatus.LIVE, f"Not live: {health.status}"
        details.append(f"Status: {health.status.value}")
        await streamer.stop()
        details.append("Stop: OK")
        return details

    async def _verify_chat(self) -> list[str]:
        from src.chat.monitor import ChatMonitor, TikTokConnector, ShopeeConnector, IntentDetector
        details = []

        # Intent detection
        detector = IntentDetector()
        p, intent = detector.detect("Mau beli kak!")
        details.append(f"Intent 'Mau beli kak!' → {intent} (P{p.value})")

        p2, intent2 = detector.detect("Harga berapa?")
        details.append(f"Intent 'Harga berapa?' → {intent2} (P{p2.value})")

        # Monitor registration
        monitor = ChatMonitor()
        monitor.register_connector(TikTokConnector())
        monitor.register_connector(ShopeeConnector())
        details.append(f"Connectors: {list(monitor.connectors.keys())}")

        return details

    async def _verify_commerce(self) -> list[str]:
        from src.commerce.manager import Product, ProductManager, ScriptEngine, AffiliateTracker
        details = []

        pm = ProductManager()
        pm.add_product(Product(name="Lipstik Magic", price=89000, features=["Tahan 24jam"]))
        pm.add_product(Product(name="Serum Wajah", price=150000, features=["Vitamin C"]))
        current = pm.get_current_product()
        assert current is not None
        details.append(f"Products: {len(pm.get_all_active())}, current: {current.name}")

        pm.rotate_next()
        details.append(f"After rotate: {pm.get_current_product().name}")

        se = ScriptEngine()
        script = se.parse_script_response(1, "1. HOOK: Test\n7. CTA: Beli sekarang!")
        details.append(f"Script parsed: {len(script.phases)} phases")

        tracker = AffiliateTracker()
        from src.commerce.manager import AffiliateEvent
        tracker.track_event(AffiliateEvent("tiktok", 1, "purchase", 5000))
        summary = tracker.get_daily_summary()
        details.append(f"Affiliate: {summary['purchases']} purchases, Rp {summary['total_commission']}")

        return details

    async def _verify_orchestrator(self) -> list[str]:
        from src.orchestrator.state_machine import Orchestrator, SystemState
        details = []
        orch = Orchestrator()
        status = orch.get_status()
        details.append(f"State: {status['state']}")
        details.append(f"LLM providers: {len(status['llm_stats']) - 1}")  # -1 for _summary
        details.append(f"Safety incidents: {status['safety_incidents']}")
        return details

    async def _verify_health(self) -> list[str]:
        from src.utils.health import get_health_manager, HealthStatus
        details = []
        hm = get_health_manager()

        # Register a test check
        async def test_check() -> HealthStatus:
            return HealthStatus(name="test", healthy=True, status="healthy", message="OK")

        hm.register("verify_test", test_check)
        results = await hm.check_all()
        for r in results:
            details.append(f"  {r.name}: {r.status} ({r.latency_ms:.1f}ms)")
        details.append(f"Overall: {hm.overall_status}")
        return details

    def print_report(self) -> None:
        """Print formatted verification report."""
        use_unicode = _stdout_supports("✅❌🎉⚠️→─")
        pass_icon = "✅" if use_unicode else "[PASS]"
        fail_icon = "❌" if use_unicode else "[FAIL]"
        detail_prefix = "→" if use_unicode else "->"
        divider = "─" * 60 if use_unicode else "-" * 60
        title = (
            "  AI Live Commerce — Pipeline Verification Report"
            if use_unicode
            else "  AI Live Commerce - Pipeline Verification Report"
        )

        print("\n" + "=" * 60)
        print(title)
        print("=" * 60 + "\n")

        passed = sum(1 for r in self.results if r.passed)
        total = len(self.results)

        for r in self.results:
            icon = pass_icon if r.passed else fail_icon
            print(f"  {icon} {r.layer:<15} {r.message:<30} ({r.duration_ms:.0f}ms)")
            if self.verbose:
                for d in r.details:
                    print(f"     {detail_prefix} {d}")
                print()

        print(f"\n{divider}")
        print(f"  Result: {passed}/{total} layers passed")

        if passed == total:
            if use_unicode:
                print("  🎉 ALL LAYERS VERIFIED SUCCESSFULLY")
            else:
                print("  ALL LAYERS VERIFIED SUCCESSFULLY")
        else:
            failed = [r.layer for r in self.results if not r.passed]
            if use_unicode:
                print(f"  ⚠️  Failed layers: {', '.join(failed)}")
            else:
                print(f"  WARNING Failed layers: {', '.join(failed)}")

        print("=" * 60 + "\n")


def _stdout_supports(text: str) -> bool:
    """Return True when the active stdout encoding can render the given text."""
    encoding = sys.stdout.encoding or "utf-8"
    try:
        text.encode(encoding)
    except UnicodeEncodeError:
        return False
    return True


async def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Verify AI Live Commerce pipeline")
    parser.add_argument("--layer", type=str, help="Verify a specific layer")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show details")
    args = parser.parse_args()

    verifier = PipelineVerifier(verbose=args.verbose)

    if args.layer:
        result = await verifier.verify_one(args.layer)
        verifier.results = [result]
    else:
        await verifier.verify_all()

    verifier.print_report()
    sys.exit(0 if all(r.passed for r in verifier.results) else 1)


if __name__ == "__main__":
    asyncio.run(main())
