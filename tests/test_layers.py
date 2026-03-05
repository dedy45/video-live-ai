"""Tests for Layers 2-7 and Orchestrator — Mock Mode."""

from __future__ import annotations

import os

import pytest

os.environ["MOCK_MODE"] = "true"


# === Layer 2: Voice ===

@pytest.mark.asyncio
async def test_voice_router_mock() -> None:
    """VoiceRouter should return audio in Mock Mode."""
    from src.voice.engine import VoiceRouter

    router = VoiceRouter()
    result = await router.synthesize("Halo semua!", emotion="happy", trace_id="test-voice-001")
    assert len(result.audio_data) > 0
    assert result.sample_rate == 24000
    assert result.emotion == "happy"


@pytest.mark.asyncio
async def test_audio_cache() -> None:
    """AudioCache should cache and retrieve audio by content hash."""
    from src.voice.engine import AudioResult, AudioCache

    cache = AudioCache()
    audio = AudioResult(audio_data=b"test", duration_ms=100.0, text="test text", emotion="neutral")
    cache.put(audio)
    cached = cache.get("test text", "neutral")
    assert cached is not None
    assert cached.cached is True


# === Layer 3: Face ===

@pytest.mark.asyncio
async def test_avatar_pipeline_mock() -> None:
    """AvatarPipeline should yield frames in Mock Mode."""
    from src.face.pipeline import AvatarPipeline

    pipeline = AvatarPipeline()
    frames = []
    async for frame in pipeline.render(b"fake", 100.0, trace_id="test-face-001"):
        frames.append(frame)
    assert len(frames) >= 1
    assert frames[0].width == 512


def test_temporal_smoother() -> None:
    """TemporalSmoother should process frames without error."""
    import numpy as np
    from src.face.pipeline import TemporalSmoother, VideoFrame

    smoother = TemporalSmoother(window_size=3)
    for i in range(5):
        frame = VideoFrame(pixels=np.random.randint(0, 255, (64, 64, 3), dtype=np.uint8), timestamp_ms=float(i * 33))
        result = smoother.smooth(frame)
        assert result.pixels.shape == (64, 64, 3)


def test_identity_controller() -> None:
    """IdentityController should track reset intervals."""
    from src.face.pipeline import IdentityController

    ctrl = IdentityController(reset_interval_min=0)  # Immediate reset for test
    assert ctrl.needs_reset()
    ctrl.mark_reset()


# === Layer 5: Stream ===

@pytest.mark.asyncio
async def test_rtmp_streamer_mock_start() -> None:
    """RTMPStreamer should start in Mock Mode."""
    from src.stream.rtmp import RTMPStreamer, StreamStatus

    streamer = RTMPStreamer(platform="tiktok")
    result = await streamer.start()
    assert result is True
    health = streamer.get_health()
    assert health.status == StreamStatus.LIVE
    await streamer.stop()


# === Layer 6: Chat ===

def test_intent_detector_purchase() -> None:
    """IntentDetector should detect purchase intent."""
    from src.chat.monitor import IntentDetector, EventPriority

    detector = IntentDetector()
    priority, intent = detector.detect("Mau beli kak!")
    assert priority == EventPriority.P1_PURCHASE
    assert intent == "purchase"


def test_intent_detector_question() -> None:
    """IntentDetector should detect questions."""
    from src.chat.monitor import IntentDetector, EventPriority

    detector = IntentDetector()
    priority, intent = detector.detect("Harga berapa kak?")
    assert priority == EventPriority.P2_QUESTION
    assert intent == "question"


@pytest.mark.asyncio
async def test_priority_queue() -> None:
    """PriorityEventQueue should return highest priority first."""
    from src.chat.monitor import ChatEvent, EventPriority, PriorityEventQueue

    queue = PriorityEventQueue()
    await queue.put(ChatEvent("test", "u1", "general", EventPriority.P4_GENERAL))
    await queue.put(ChatEvent("test", "u2", "beli!", EventPriority.P1_PURCHASE))
    await queue.put(ChatEvent("test", "u3", "harga?", EventPriority.P2_QUESTION))

    first = await queue.get()
    assert first.priority == EventPriority.P1_PURCHASE
    assert first.username == "u2"


@pytest.mark.asyncio
async def test_chat_monitor_registers_connectors() -> None:
    """ChatMonitor should register and start connectors."""
    from src.chat.monitor import ChatMonitor, TikTokConnector

    monitor = ChatMonitor()
    connector = TikTokConnector()
    monitor.register_connector(connector)
    assert "tiktok" in monitor.connectors


# === Layer 7: Commerce ===

def test_product_manager_rotation() -> None:
    """ProductManager should rotate products."""
    from src.commerce.manager import Product, ProductManager

    pm = ProductManager()
    pm.add_product(Product(name="Lipstik", price=99000))
    pm.add_product(Product(name="Moisturizer", price=150000))

    current = pm.get_current_product()
    assert current is not None
    assert current.name == "Lipstik"

    pm.rotate_next()
    assert pm.get_current_product().name == "Moisturizer"


def test_script_engine_parse() -> None:
    """ScriptEngine should parse 7-phase script from LLM text."""
    from src.commerce.manager import ScriptEngine

    engine = ScriptEngine()
    llm_text = """
    1. HOOK: Hai kak, produk terbaru nih!
    2. PROBLEM: Kulit kering bikin gak pede
    3. SOLUTION: Moisturizer ini solusinya
    4. FEATURES: SPF 50, lightweight, tahan 12 jam
    5. SOCIAL PROOF: Sudah 5000 terjual!
    6. URGENCY: Stok tinggal 10!
    7. CTA: Checkout sekarang kak!
    """
    script = engine.parse_script_response(1, llm_text)
    assert script.hook != ""
    assert script.cta != ""
    assert "Checkout" in script.cta


def test_affiliate_tracker() -> None:
    """AffiliateTracker should track events and compute summary."""
    from src.commerce.manager import AffiliateEvent, AffiliateTracker

    tracker = AffiliateTracker()
    tracker.track_event(AffiliateEvent("tiktok", 1, "click"))
    tracker.track_event(AffiliateEvent("tiktok", 1, "purchase", 5000))

    summary = tracker.get_daily_summary()
    assert summary["clicks"] == 1
    assert summary["purchases"] == 1
    assert summary["total_commission"] == 5000


# === Orchestrator ===

def test_orchestrator_status() -> None:
    """Orchestrator should provide status report."""
    from src.orchestrator.state_machine import Orchestrator, SystemState

    orch = Orchestrator()
    status = orch.get_status()
    assert status["state"] == SystemState.IDLE.value
    assert "llm_stats" in status
    assert "safety_incidents" in status
