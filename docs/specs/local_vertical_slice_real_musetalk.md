# Milestone: LOCAL_VERTICAL_SLICE_REAL_MUSETALK

> Status: ACTIVE
> Date: 2026-03-09
> Scope: local UV environment, real non-mock vertical slice

## Milestone Name

`LOCAL_VERTICAL_SLICE_REAL_MUSETALK`

## Active Path

The only acceptable primary face runtime path for this milestone:

```
FastAPI -> dashboard/operator flow -> LiveTalking sidecar -> MuseTalk
```

## Fallback Rule

- `Wav2Lip` may remain in the repository for emergency/dev fallback
- `Wav2Lip` must NOT be counted as a pass for this milestone
- If runtime truth resolves to `wav2lip`, the milestone is NOT complete

## Acceptance Truth Fields

The system is only considered locally real and MuseTalk-active if ALL of the following are true:

| Field | Required Value |
|-------|---------------|
| `mock_mode` | `false` |
| `requested_model` | `musetalk` |
| `resolved_model` | `musetalk` |
| `requested_avatar_id` | `musetalk_avatar1` |
| `resolved_avatar_id` | `musetalk_avatar1` |
| vendor sidecar port | reachable |
| dashboard truth surfaces | reflect same values |

Any silent or automatic downgrade to `wav2lip` must remain visible as a failure to complete this milestone.

## Required Evidence

1. `uv run python scripts/check_real_mode_readiness.py --json` returns `is_ready: true`
2. `uv run python scripts/manage.py health --json` shows `musetalk` as resolved runtime
3. `/api/runtime/truth` returns `resolved_model=musetalk`
4. `/api/engine/livetalking/status` shows `resolved_model=musetalk`
5. Real local product data passes the readiness gate
6. Canonical `musetalk_avatar1` exists in `external/livetalking/data/avatars/musetalk_avatar1/`
7. One local audit with fresh evidence saved

## Out of Scope

- Voice redesign
- GFPGAN
- ER-NeRF
- Blind test
- Long-run stability
- Production launch work
- Humanization (Phase 2 of this track)

## Source of Truth

- This spec
- `docs/architecture.md`
- `docs/task_status.md`
- `docs/workflow.md`
