# Model Path Policy

> **Status**: Active
> **Date**: 2026-03-07
> **Decision**: Option A — keep all runtime models under vendor directory

## Policy

All runtime model weights and avatar assets live **inside** `external/livetalking/`:

| Resource | Path |
|----------|------|
| Wav2Lip model | `external/livetalking/models/wav2lip.pth` |
| MuseTalk models | `external/livetalking/models/musetalk/` |
| GFPGAN models | `external/livetalking/models/gfpgan/` |
| Wav2Lip avatars | `external/livetalking/data/avatars/wav2lip256_avatar1/` |
| MuseTalk avatars | `external/livetalking/data/avatars/musetalk_avatar1/` |

## Rationale

- LiveTalking expects models in its own directory structure
- No symlinks or copies needed before launch
- Setup scripts download directly to vendor paths
- Simpler for both Windows and Ubuntu

## Verification

All batch scripts (`run_livetalking_*.bat`, `setup_*_model.bat`, `verify_livetalking.bat`)
must check paths under `external/livetalking/`, not under project root `models/`.
