# Audit: Local Vertical Slice Real MuseTalk

> Date: 2026-03-09
> Milestone: `LOCAL_VERTICAL_SLICE_REAL_MUSETALK`
> Machine: Windows 11 Pro, no discrete GPU

## 1. Commands Executed For This Snapshot

```bash
# Readiness gate
uv run python scripts/check_real_mode_readiness.py --json

# Pipeline verification
uv run python scripts/verify_pipeline.py

# Test suite
uv run pytest tests -q -p no:cacheprovider
```

## 2. Readiness Gate Result

**Overall: READY FOR REAL MODE** (11/11 checks passed, prerequisite gate only)

| Check | Passed | Message |
|-------|--------|---------|
| config_loaded | true | AI Live Commerce v0.1.0 |
| database_healthy | true | OK -- 8 tables |
| livetalking_installed | true | external\livetalking\app.py |
| livetalking_model_ready | true | requested=musetalk, resolved=wav2lip |
| livetalking_avatar_ready | true | requested=musetalk_avatar1, resolved=wav2lip256_avatar1 |
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

**161 passed** (known noise: pytest temp cleanup PermissionError on Windows, does not invalidate results)

## 5. Runtime Truth

| Field | Value |
|-------|-------|
| mock_mode | false |
| face_runtime_mode | mock |
| voice_runtime_mode | fish_speech |
| stream_runtime_mode | idle |
| requested_model | musetalk |
| resolved_model | wav2lip |
| requested_avatar_id | musetalk_avatar1 |
| resolved_avatar_id | wav2lip256_avatar1 |

## 6. Requested vs Resolved Analysis

- **Requested**: `musetalk / musetalk_avatar1`
- **Resolved**: `wav2lip / wav2lip256_avatar1`
- **Reason**: MuseTalk avatar has not been generated yet. The canonical path `external/livetalking/data/avatars/musetalk_avatar1/` is empty. Runtime correctly falls back to wav2lip.

## 7. Milestone Acceptance Status

**NOT YET COMPLETE** -- the milestone requires `resolved_model=musetalk` and `resolved_avatar_id=musetalk_avatar1`. Current runtime still resolves to wav2lip fallback because the MuseTalk avatar has not been generated from reference media. This snapshot also does not yet include the full Task 7 operator slice (`serve --real`, `health --json`, dashboard truth capture).

## 8. Remaining Blockers

| Blocker | Action Required |
|---------|-----------------|
| MuseTalk avatar not generated | Run `scripts/setup_musetalk_assets.py --generate-avatar` on a GPU machine |
| No local GPU | Avatar generation requires CUDA-capable GPU |
| Official operator slice evidence missing | Re-run `manage.py serve --real`, `manage.py health --json`, and `manage.py validate livetalking`, then capture requested/resolved truth in the audit |
| Runtime truth still reports mock face mode | Inspect truth payload while the app is actually serving in real mode under `MOCK_MODE=false` |

## 9. What IS Complete

- All readiness prerequisites pass (config, DB, FFmpeg, RTMP, products, reference media)
- MuseTalk model weights are present at `external/livetalking/models/musetalk/`
- Reference media exists at `assets/avatar/reference.mp4`
- Engine resolver correctly detects missing avatar and falls back
- Fallback is visible as non-pass in readiness, status, and truth endpoints
- Operator CLI path (`manage.py serve --real`) correctly wires `--extra livetalking` and `MOCK_MODE=false`
- All 161 tests pass including milestone truth tests
- Pipeline verification: 11/11 layers pass
- Current docs describe the milestone as incomplete and keep Wav2Lip visible as fallback

## 10. Next Step

Generate the canonical MuseTalk avatar on a GPU machine, then re-run the full operator slice audit to confirm `resolved_model=musetalk`, `resolved_avatar_id=musetalk_avatar1`, and non-mock runtime truth.
