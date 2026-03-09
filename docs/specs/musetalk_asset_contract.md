# MuseTalk Asset Contract

> Date: 2026-03-09
> Scope: canonical paths and readiness requirements for MuseTalk activation

## Canonical Paths

| Asset | Path | Required |
|-------|------|----------|
| MuseTalk model weights | `external/livetalking/models/musetalk/` | Yes — must contain model files |
| MuseTalk avatar data | `external/livetalking/data/avatars/musetalk_avatar1/` | Yes — must contain generated avatar |
| Reference video | `assets/avatar/reference.mp4` | Yes — needed for avatar generation |
| Reference audio | `assets/avatar/reference.wav` | Optional — for voice cloning |

## Readiness Contract

Asset setup is considered **ready** only when ALL of the following are true:

1. `external/livetalking/models/musetalk/` exists and is non-empty
2. `external/livetalking/data/avatars/musetalk_avatar1/` exists and is non-empty
3. `assets/avatar/reference.mp4` exists

Asset setup must report **not ready** when any of the above is missing, with an explicit message identifying which asset is absent.

## Generation Flow

```
assets/avatar/reference.mp4
  -> LiveTalking MuseTalk avatar generator
  -> external/livetalking/data/avatars/musetalk_avatar1/
```

## Legacy Path Normalization

The sync function handles these legacy locations:

- `models/musetalk/` -> `external/livetalking/models/musetalk/`
- `data/avatars/musetalk_avatar1/` -> `external/livetalking/data/avatars/musetalk_avatar1/`
- `external/livetalking/musetalk/data/avatars/musetalk_avatar1/` -> `external/livetalking/data/avatars/musetalk_avatar1/`

## Rules

- Partial folders must NOT count as success
- Reports must tell the operator exactly which asset is missing
- Silent success on missing assets is a bug
