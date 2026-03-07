# Avatar Asset Specification

> **Status**: Active
> **Date**: 2026-03-07

## Reference Video Requirements

| Property | Requirement |
|----------|-------------|
| **Duration** | 3-5 minutes minimum |
| **Resolution** | 512x512 minimum, 1024x1024 recommended |
| **Format** | MP4 (H.264) |
| **FPS** | 25-30 fps |
| **Lighting** | Even, front-facing, no harsh shadows |
| **Framing** | Head and shoulders, centered |
| **Background** | Solid color or simple, low-contrast |
| **Expression** | Natural talking, varied expressions |
| **Movement** | Minimal head movement, no hand gestures in frame |
| **Path** | `assets/avatar/reference.mp4` |

## Avatar Data Requirements

| Property | Requirement |
|----------|-------------|
| **Format** | Preprocessed by LiveTalking (`coords.pkl` + frames) |
| **Path** | `external/livetalking/data/avatars/<avatar_id>/` |
| **Naming** | `wav2lip256_avatar1`, `musetalk_avatar1`, etc. |

## Quality Checklist

- [ ] Face clearly visible, no occlusion
- [ ] Consistent lighting throughout video
- [ ] No glasses reflections or heavy makeup
- [ ] Audio synced with lip movement
- [ ] No background noise or music
