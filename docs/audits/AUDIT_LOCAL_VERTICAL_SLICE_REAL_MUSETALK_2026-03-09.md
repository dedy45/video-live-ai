# Audit: Local Vertical Slice Real MuseTalk

> Date: 2026-03-09
> Milestone: `LOCAL_VERTICAL_SLICE_REAL_MUSETALK`
> Machine: Windows 11 Pro, local UV environment

## 1. Commands Executed For This Snapshot

```bash
# Prerequisite gate
uv run python scripts/check_real_mode_readiness.py --json

# Pipeline verification
uv run python scripts/verify_pipeline.py

# Test suite
uv run pytest tests -q -p no:cacheprovider

# Asset normalization status
uv run --extra livetalking python scripts/setup_musetalk_assets.py --sync-only

# Official operator slice
uv run python scripts/manage.py serve --real
uv run python scripts/manage.py health --json
POST /api/engine/livetalking/start
POST /api/validate/real-mode-readiness
GET /api/runtime/truth
GET /api/engine/livetalking/status
```

## 2. Readiness Gate Result

**Overall: READY FOR REAL MODE** (11/11 checks passed)

| Check | Passed | Message |
|-------|--------|---------|
| config_loaded | true | AI Live Commerce v0.1.0 |
| database_healthy | true | OK -- 8 tables |
| livetalking_installed | true | external\livetalking\app.py |
| livetalking_model_ready | true | musetalk: external\livetalking\models\musetalk |
| livetalking_avatar_ready | true | musetalk_avatar1: external\livetalking\data\avatars\musetalk_avatar1 |
| ffmpeg_available | true | tools\ffmpeg\bin\ffmpeg.exe |
| rtmp_target_configured | true | TikTok RTMP configured |
| mode_explicit | true | MOCK_MODE=false |
| MOCK_MODE is NOT true | true | MOCK_MODE is false |
| Reference MP4 exists | true | assets\avatar\reference.mp4 |
| Product data source exists | true | Found: products.json |

## 3. Pipeline Verification Result

**11/11 layers passed**

| Layer | Result | Time |
|-------|--------|------|
| config | PASS | 292ms |
| database | PASS | 283ms |
| brain | PASS | 3529ms |
| voice | PASS | 4ms |
| face | PASS | 19ms |
| composition | PASS | 46ms |
| stream | PASS | 3ms |
| chat | PASS | 3ms |
| commerce | PASS | 7ms |
| orchestrator | PASS | 4ms |
| health | PASS | 0ms |

## 4. Test Suite Result

**183 passed** (known noise: pytest temp cleanup PermissionError on Windows, does not invalidate results)

## 5. Asset Contract Result

`uv run --extra livetalking python scripts/setup_musetalk_assets.py --sync-only`

| Field | Value |
|-------|-------|
| Models ready | true |
| Avatar ready | true |
| Reference exists | true |
| Can generate | true |

## 6. Runtime Truth

| Field | Value |
|-------|-------|
| mock_mode | false |
| face_runtime_mode | livetalking_local |
| voice_runtime_mode | fish_speech |
| stream_runtime_mode | idle |
| requested_model | musetalk |
| resolved_model | musetalk |
| requested_avatar_id | musetalk_avatar1 |
| resolved_avatar_id | musetalk_avatar1 |
| fallback_active | false |

## 7. Requested vs Resolved Analysis

- **Requested**: `musetalk / musetalk_avatar1`
- **Resolved**: `musetalk / musetalk_avatar1`
- **Reason**: Canonical MuseTalk model and avatar assets are present, so the official operator slice no longer falls back.

## 8. Operator Slice Evidence

- `uv run python scripts/manage.py health --json` while the app is running shows:
  - `runtime_truth.face_runtime_mode=livetalking_local`
  - `runtime_truth.face_engine.requested_model=musetalk`
  - `runtime_truth.face_engine.resolved_model=musetalk`
  - `runtime_truth.face_engine.fallback_active=false`
- `POST /api/engine/livetalking/start` returns `state=running`, `model=musetalk`, `avatar_id=musetalk_avatar1`
- `POST /api/validate/real-mode-readiness` returns `status=pass`
- The vendor sidecar process is launched as:
  - `python app.py --transport webrtc --model musetalk --avatar_id musetalk_avatar1 --listenport 8010`

## 9. Milestone Acceptance Status

**LOCAL VERIFIED** -- the milestone acceptance fields now match the MuseTalk contract for the local vertical slice.

## 10. Remaining Non-Blockers

| Item | Action Required |
|------|-----------------|
| Health summary alignment completed | Keep `face_pipeline` health in regression checks for non-mock readiness-complete runs |
| Humanization layer not started | Implement the minimum humanization contract on top of the validated MuseTalk slice |
| Real live test not started | Freeze RTMP dry-run and rollback criteria before server rollout |

## 11. What IS Complete

- All readiness prerequisites pass (config, DB, FFmpeg, RTMP, products, reference media)
- MuseTalk model weights are present at `external/livetalking/models/musetalk/`
- Canonical MuseTalk avatar exists at `external/livetalking/data/avatars/musetalk_avatar1/`
- Reference media exists at `assets/avatar/reference.mp4`
- Operator CLI path (`manage.py serve --real`) correctly wires `--extra livetalking` and `MOCK_MODE=false`
- Requested/resolved runtime truth now matches MuseTalk without fallback
- Validation Console passes the real-mode check
- All 183 tests pass including milestone truth tests
- Pipeline verification: 11/11 layers pass
- Current docs describe the milestone as locally verified and keep the remaining non-blockers explicit

## 12. Next Step

Use this validated local MuseTalk slice as the base for Humanization Minimum, then prepare the first short real live test on the Ubuntu target host.
