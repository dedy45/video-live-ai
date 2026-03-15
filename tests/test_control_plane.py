from __future__ import annotations

import importlib
from pathlib import Path
from unittest.mock import patch

import pytest


def _prepare_isolated_dashboard_api(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import src.data.database as database
    import src.dashboard.api as dashboard_api
    import src.orchestrator.show_director as show_director

    db_path = tmp_path / "control-plane.db"
    monkeypatch.setattr(database, "DB_PATH", db_path)
    database.init_database(db_path)
    show_director.reset_show_director()

    return importlib.reload(dashboard_api)


def test_control_plane_store_round_trips_product_affiliate_fields(tmp_path: Path) -> None:
    from src.control_plane.store import ControlPlaneStore

    store = ControlPlaneStore(db_path=tmp_path / "control-plane.db")
    created = store.create_product(
        name="Lip Cream Matte",
        price=89000,
        category="beauty",
        stock=25,
        margin_percent=28.0,
        description="Lip cream transferproof",
        affiliate_links={
            "tiktok": "https://shop.tiktok.test/lip-cream",
            "shopee": "https://shopee.test/lip-cream",
        },
        selling_points=["ringan", "pigmented", "transferproof"],
        commission_rate=12.5,
        objection_handling={"aman?": "pakai sesuai petunjuk"},
        compliance_notes="Hindari klaim medis",
    )

    products = store.list_products()
    assert len(products) == 1
    assert products[0]["id"] == created["id"]
    assert products[0]["affiliate_links"]["tiktok"] == "https://shop.tiktok.test/lip-cream"
    assert products[0]["selling_points"] == ["ringan", "pigmented", "transferproof"]
    assert products[0]["commission_rate"] == 12.5
    assert products[0]["objection_handling"]["aman?"] == "pakai sesuai petunjuk"
    assert products[0]["compliance_notes"] == "Hindari klaim medis"


def test_control_plane_store_manages_tiktok_stream_target_activation(tmp_path: Path) -> None:
    from src.control_plane.store import ControlPlaneStore

    store = ControlPlaneStore(db_path=tmp_path / "control-plane.db")
    first = store.create_stream_target(
        platform="tiktok",
        label="Primary TikTok",
        rtmp_url="rtmp://push.tiktok.test/live/",
        stream_key="abc123",
    )
    second = store.create_stream_target(
        platform="tiktok",
        label="Backup TikTok",
        rtmp_url="rtmp://push.tiktok.test/live/",
        stream_key="def456",
    )

    store.activate_stream_target(first["id"])
    store.activate_stream_target(second["id"])
    targets = store.list_stream_targets()

    first_row = next(target for target in targets if target["id"] == first["id"])
    second_row = next(target for target in targets if target["id"] == second["id"])

    assert first_row["is_active"] is False
    assert second_row["is_active"] is True
    assert second_row["stream_key_masked"].endswith("456")


def test_control_plane_store_enforces_single_active_live_session(tmp_path: Path) -> None:
    from src.control_plane.store import ControlPlaneStore

    store = ControlPlaneStore(db_path=tmp_path / "control-plane.db")
    target = store.create_stream_target(
        platform="tiktok",
        label="Primary TikTok",
        rtmp_url="rtmp://push.tiktok.test/live/",
        stream_key="abc123",
    )
    store.activate_stream_target(target["id"])
    first = store.start_live_session(platform="tiktok", stream_target_id=target["id"])

    with pytest.raises(RuntimeError, match="active live session"):
        store.start_live_session(platform="tiktok", stream_target_id=target["id"])

    assert first["status"] == "active"


def test_control_plane_store_tracks_session_product_pool_focus_and_pause(tmp_path: Path) -> None:
    from src.control_plane.store import ControlPlaneStore

    store = ControlPlaneStore(db_path=tmp_path / "control-plane.db")
    first_product = store.create_product(name="Lip Cream Matte", price=89000)
    second_product = store.create_product(name="Serum Brightening", price=129000)
    target = store.create_stream_target(
        platform="tiktok",
        label="Primary TikTok",
        rtmp_url="rtmp://push.tiktok.test/live/",
        stream_key="abc123",
    )
    store.activate_stream_target(target["id"])
    session = store.start_live_session(platform="tiktok", stream_target_id=target["id"])

    assigned = store.add_session_products(
        session_id=session["id"],
        product_ids=[first_product["id"], second_product["id"]],
    )
    store.set_focus_product(
        session_id=session["id"],
        session_product_id=assigned[1]["id"],
        reason="operator_pin",
    )
    paused = store.pause_rotation(
        session_id=session["id"],
        reason="viewer_question",
        question="Apakah serum ini aman untuk remaja?",
    )
    resumed = store.resume_rotation(session_id=session["id"])
    summary = store.get_active_live_session()

    assert len(assigned) == 2
    assert paused["rotation_paused"] is True
    assert paused["current_mode"] == "SOFT_PAUSED_FOR_QNA"
    assert resumed["rotation_paused"] is False
    assert summary["state"]["current_focus_product_id"] == second_product["id"]
    assert summary["state"]["pending_question"] is None


def test_control_plane_store_manages_voice_profiles_and_lab_state(tmp_path: Path) -> None:
    from src.control_plane.store import ControlPlaneStore

    store = ControlPlaneStore(db_path=tmp_path / "control-plane.db")
    created = store.create_voice_profile(
        name="Sari Fish",
        reference_wav_path="assets/voice/sari.wav",
        reference_text="Halo semuanya, aku Sari.",
        language="id",
        notes="profile utama",
    )
    updated = store.update_voice_profile(
        created["id"],
        name="Sari Fish Pro",
        reference_wav_path="assets/voice/sari-pro.wav",
        reference_text="Halo semuanya, aku Sari Pro.",
        language="id",
        notes="profile utama update",
    )
    activated = store.activate_voice_profile(created["id"])
    lab_state = store.update_voice_lab_state(
        mode="attach_avatar",
        active_profile_id=created["id"],
        preview_session_id="884422",
        selected_avatar_id="wav2lip256_avatar1",
        draft_text="Tes voice lab",
    )
    profiles = store.list_voice_profiles()
    current_state = store.get_voice_lab_state()

    assert created["id"] > 0
    assert updated["name"] == "Sari Fish Pro"
    assert activated["is_active"] is True
    assert len(profiles) == 1
    assert profiles[0]["is_active"] is True
    assert lab_state["mode"] == "attach_avatar"
    assert lab_state["preview_session_id"] == "884422"
    assert current_state["active_profile_id"] == created["id"]


def test_control_plane_store_records_voice_generations(tmp_path: Path) -> None:
    from src.control_plane.store import ControlPlaneStore

    store = ControlPlaneStore(db_path=tmp_path / "control-plane.db")
    profile = store.create_voice_profile(
        name="Sari Fish",
        reference_wav_path="assets/voice/sari.wav",
        reference_text="Halo semuanya, aku Sari.",
        language="id",
        notes="profile utama",
    )
    generation = store.create_voice_generation(
        mode="standalone",
        profile_id=profile["id"],
        source_type="manual_text",
        input_text="Halo operator",
        emotion="friendly",
        speed=1.0,
        status="success",
        audio_path="data/runtime/voice/voice-1.wav",
        audio_size_bytes=4096,
        latency_ms=321.5,
        duration_ms=1500.0,
        attached_to_avatar=False,
        avatar_session_id="",
    )
    history = store.list_voice_generations()
    loaded = store.get_voice_generation(generation["id"])

    assert generation["id"] > 0
    assert history[0]["input_text"] == "Halo operator"
    assert history[0]["profile_name"] == "Sari Fish"
    assert loaded["audio_path"] == "data/runtime/voice/voice-1.wav"
    assert loaded["attached_to_avatar"] is False


def test_control_plane_store_voice_lab_tracks_richer_generator_defaults(tmp_path: Path) -> None:
    from src.control_plane.store import ControlPlaneStore

    store = ControlPlaneStore(db_path=tmp_path / "control-plane.db")
    profile = store.create_voice_profile(
        name="Sari Quick Clone",
        reference_wav_path="assets/voice/sari.wav",
        reference_text="Halo semuanya, aku Sari.",
        language="id",
    )

    updated = store.update_voice_lab_state(
        mode="standalone",
        active_profile_id=profile["id"],
        preview_session_id="",
        selected_avatar_id="wav2lip256_avatar1",
        draft_text="Hello from voice lab",
        last_generation_id=None,
        selected_language="en",
        selected_profile_type="quick_clone",
        selected_revision_id=None,
        selected_style_preset="conversational",
        selected_stability=0.72,
        selected_similarity=0.81,
    )

    assert updated["selected_language"] == "en"
    assert updated["selected_profile_type"] == "quick_clone"
    assert updated["selected_style_preset"] == "conversational"
    assert updated["selected_stability"] == 0.72
    assert updated["selected_similarity"] == 0.81


def test_control_plane_store_voice_generation_exposes_library_metadata(tmp_path: Path) -> None:
    from src.control_plane.store import ControlPlaneStore

    store = ControlPlaneStore(db_path=tmp_path / "control-plane.db")
    profile = store.create_voice_profile(
        name="Sari Quick Clone",
        reference_wav_path="assets/voice/sari.wav",
        reference_text="Halo semuanya, aku Sari.",
        language="id",
    )

    generation = store.create_voice_generation(
        mode="standalone",
        profile_id=profile["id"],
        source_type="manual_text",
        input_text="Hello operator",
        emotion="neutral",
        speed=1.0,
        status="success",
        audio_path="data/runtime/voice/voice-99.wav",
        audio_size_bytes=12345,
        latency_ms=321.0,
        duration_ms=1450.0,
        attached_to_avatar=False,
        avatar_session_id="",
        language="en",
        style_preset="conversational",
        stability=0.61,
        similarity=0.84,
        audio_filename="voice-99.wav",
        download_name="sari-quick-clone-en.wav",
    )

    history = store.list_voice_generations(limit=5)

    assert generation["language"] == "en"
    assert generation["style_preset"] == "conversational"
    assert generation["stability"] == 0.61
    assert generation["similarity"] == 0.84
    assert generation["download_name"] == "sari-quick-clone-en.wav"
    assert history[0]["audio_url"] == f"/api/voice/audio/{generation['id']}"
    assert history[0]["download_url"] == f"/api/voice/audio/{generation['id']}/download"


def test_control_plane_store_training_job_round_trip(tmp_path: Path) -> None:
    from src.control_plane.store import ControlPlaneStore

    store = ControlPlaneStore(db_path=tmp_path / "control-plane.db")
    profile = store.create_voice_profile(
        name="Studio Sari",
        reference_wav_path="assets/voice/sari.wav",
        reference_text="Halo semuanya, aku Sari.",
        language="id",
        profile_type="studio_voice",
        supported_languages=["id"],
        quality_tier="studio",
    )

    job = store.create_voice_training_job(
        profile_id=profile["id"],
        job_type="studio_voice_training",
        status="queued",
        current_stage="queued",
        progress_pct=0.0,
        dataset_path="data/runtime/voice/datasets/studio-sari",
        log_path="data/runtime/voice/training/studio-sari.log",
        meta={"languages": ["id"]},
    )

    jobs = store.list_voice_training_jobs()

    assert job["profile_id"] == profile["id"]
    assert job["status"] == "queued"
    assert jobs[0]["job_type"] == "studio_voice_training"
    assert jobs[0]["profile_name"] == "Studio Sari"


@pytest.mark.asyncio
async def test_dashboard_product_crud_uses_sqlite_store(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    dashboard_api = _prepare_isolated_dashboard_api(tmp_path, monkeypatch)

    created = await dashboard_api.create_product(
        dashboard_api.ProductMutationRequest(
            name="Lip Cream Matte",
            price=89000,
            category="beauty",
            affiliate_links={"tiktok": "https://shop.tiktok.test/lip-cream"},
            selling_points=["ringan", "pigmented"],
            commission_rate=12.5,
            objection_handling={"aman?": "pakai sesuai petunjuk"},
            compliance_notes="Hindari klaim medis",
        )
    )
    updated = await dashboard_api.update_product(
        created["id"],
        dashboard_api.ProductMutationRequest(
            name="Lip Cream Matte 2.0",
            price=99000,
            category="beauty",
            affiliate_links={"tiktok": "https://shop.tiktok.test/lip-cream-2"},
            selling_points=["ringan", "lebih tahan lama"],
            commission_rate=15.0,
            objection_handling={"aman?": "pakai sesuai petunjuk"},
            compliance_notes="Tetap hindari klaim medis",
        ),
    )
    products = await dashboard_api.list_products()
    deleted = await dashboard_api.delete_product(created["id"])
    products_after_delete = await dashboard_api.list_products()

    assert created["id"] > 0
    assert updated["name"] == "Lip Cream Matte 2.0"
    assert any(product["name"] == "Lip Cream Matte 2.0" for product in products)
    assert deleted["status"] == "deleted"
    assert products_after_delete == []


@pytest.mark.asyncio
async def test_dashboard_stream_target_and_session_flow_uses_single_source_of_truth(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dashboard_api = _prepare_isolated_dashboard_api(tmp_path, monkeypatch)

    product = await dashboard_api.create_product(
        dashboard_api.ProductMutationRequest(name="Lip Cream Matte", price=89000)
    )
    target = await dashboard_api.create_stream_target(
        dashboard_api.StreamTargetMutationRequest(
            platform="tiktok",
            label="Primary TikTok",
            rtmp_url="rtmp://push.tiktok.test/live/",
            stream_key="abc123",
        )
    )

    with patch(
        "src.dashboard.api.check_ffmpeg_ready",
        return_value={"available": True, "path": r"C:\tools\ffmpeg\bin\ffmpeg.exe"},
    ):
        validation = await dashboard_api.validate_stream_target(target["id"])

    activated = await dashboard_api.activate_stream_target(target["id"])
    session = await dashboard_api.start_live_session(
        dashboard_api.LiveSessionStartRequest(platform="tiktok")
    )
    assignments = await dashboard_api.add_live_session_products(
        dashboard_api.SessionProductsRequest(product_ids=[product["id"]])
    )
    focus = await dashboard_api.set_live_session_focus(
        dashboard_api.FocusProductRequest(session_product_id=assignments["items"][0]["id"])
    )
    paused = await dashboard_api.pause_live_session(
        dashboard_api.LiveSessionPauseRequest(reason="viewer_question", question="Harga berapa?")
    )
    paused_runtime = await dashboard_api.get_director_runtime()
    resumed = await dashboard_api.resume_live_session()
    resumed_runtime = await dashboard_api.get_director_runtime()
    summary = await dashboard_api.get_live_session()
    status = await dashboard_api.get_status()

    assert validation["status"] == "pass"
    assert activated["target"]["is_active"] is True
    assert session["session"]["status"] == "active"
    assert assignments["count"] == 1
    assert focus["state"]["current_focus_product_id"] == product["id"]
    assert paused["state"]["rotation_paused"] is True
    assert paused_runtime["director"]["state"] == "PAUSED"
    assert resumed["state"]["rotation_paused"] is False
    assert resumed_runtime["director"]["state"] == "SELLING"
    assert summary["session"]["id"] == session["session"]["id"]
    assert status["current_product"]["id"] == product["id"]


@pytest.mark.asyncio
async def test_dashboard_start_live_session_starts_stream_runtime_from_persisted_target(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dashboard_api = _prepare_isolated_dashboard_api(tmp_path, monkeypatch)

    target = await dashboard_api.create_stream_target(
        dashboard_api.StreamTargetMutationRequest(
            platform="tiktok",
            label="Primary TikTok",
            rtmp_url="rtmp://push.tiktok.test/live/",
            stream_key="abc123",
        )
    )
    await dashboard_api.activate_stream_target(target["id"])

    class FakeStreamRuntime:
        def __init__(self) -> None:
            self.started_target: dict[str, str] | None = None

        async def start_target(self, target: dict[str, str]) -> dict[str, str]:
            self.started_target = target
            return {"status": "live", "platform": target["platform"]}

        async def stop_active(self) -> dict[str, str]:
            return {"status": "stopped"}

        def get_snapshot(self) -> dict[str, object]:
            return {
                "stream_running": self.started_target is not None,
                "stream_status": "live" if self.started_target else "idle",
                "platform": self.started_target["platform"] if self.started_target else None,
                "target_label": self.started_target["label"] if self.started_target else None,
                "last_error": "",
            }

    runtime = FakeStreamRuntime()
    monkeypatch.setattr(dashboard_api, "get_stream_runtime_service", lambda: runtime)

    session = await dashboard_api.start_live_session(
        dashboard_api.LiveSessionStartRequest(platform="tiktok")
    )
    summary = await dashboard_api.get_live_session()

    assert runtime.started_target is not None
    assert runtime.started_target["stream_key"] == "abc123"
    assert session["session"]["status"] == "active"
    assert summary["state"]["stream_status"] == "live"


@pytest.mark.asyncio
async def test_dashboard_stop_live_session_moves_director_to_idle(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dashboard_api = _prepare_isolated_dashboard_api(tmp_path, monkeypatch)

    target = await dashboard_api.create_stream_target(
        dashboard_api.StreamTargetMutationRequest(
            platform="tiktok",
            label="Primary TikTok",
            rtmp_url="rtmp://push.tiktok.test/live/",
            stream_key="abc123",
        )
    )
    await dashboard_api.activate_stream_target(target["id"])
    await dashboard_api.start_live_session(
        dashboard_api.LiveSessionStartRequest(platform="tiktok")
    )

    stopped = await dashboard_api.stop_live_session()
    director_runtime = await dashboard_api.get_director_runtime()

    assert stopped["status"] == "stopped"
    assert director_runtime["director"]["state"] == "IDLE"
    assert director_runtime["director"]["stream_running"] is False


@pytest.mark.asyncio
async def test_dashboard_start_live_session_rejects_when_stream_runtime_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from fastapi import HTTPException

    dashboard_api = _prepare_isolated_dashboard_api(tmp_path, monkeypatch)

    target = await dashboard_api.create_stream_target(
        dashboard_api.StreamTargetMutationRequest(
            platform="tiktok",
            label="Primary TikTok",
            rtmp_url="rtmp://push.tiktok.test/live/",
            stream_key="abc123",
        )
    )
    await dashboard_api.activate_stream_target(target["id"])

    class FailingStreamRuntime:
        async def start_target(self, target: dict[str, str]) -> dict[str, str]:
            raise RuntimeError("ffmpeg not found")

        async def stop_active(self) -> dict[str, str]:
            return {"status": "stopped"}

        def get_snapshot(self) -> dict[str, object]:
            return {
                "stream_running": False,
                "stream_status": "error",
                "platform": None,
                "target_label": None,
                "last_error": "ffmpeg not found",
            }

    monkeypatch.setattr(dashboard_api, "get_stream_runtime_service", lambda: FailingStreamRuntime())

    with pytest.raises(HTTPException, match="ffmpeg not found") as exc_info:
        await dashboard_api.start_live_session(
            dashboard_api.LiveSessionStartRequest(platform="tiktok")
        )

    summary = await dashboard_api.get_live_session()

    assert exc_info.value.status_code == 502
    assert summary["session"] is None
