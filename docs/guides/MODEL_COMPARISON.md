# LiveTalking Runtime Model Comparison

> Last audited: 2026-03-07
> Basis: local vendor copy in `external/livetalking`

## What This Document Compares

This is a runtime comparison for the vendor face engine only.  
It does not compare voice systems such as `GPT-SoVITS` or `CosyVoice`, because those belong to the voice layer.

## Runtime Status Matrix

| Model / Feature | Vendor docs claim | Runtime status today | Notes |
|-----------------|-------------------|----------------------|-------|
| MuseTalk | Yes | `ACTIVE` | Primary recommended path |
| Wav2Lip | Yes | `ACTIVE` | Legacy fallback |
| Ultralight | Yes | `ACTIVE` | Low-resource option |
| ER-NeRF | Yes | `INACTIVE` | Branch is advertised but commented out in current app runtime |
| GFPGAN | Implied in project docs | `NOT FOUND IN VENDOR RUNTIME` | Treat as project-layer target, not vendor fact |

## Practical Recommendation

### Use MuseTalk if

- you want the best current face path in this repo
- GPU budget is strong enough
- you are optimizing for the internal-live target

### Use Wav2Lip if

- you need compatibility
- you need easier fallback on lower GPU budget
- you are debugging basic vendor flow

### Use Ultralight if

- you need a lighter runtime path
- you are testing low-resource scenarios

### Do not choose ER-NeRF as the default path yet

It is still part of the target architecture discussion, but not something that should be assumed active in the current vendor app.

## Performance Hints

Based on the current vendor README:

| Path | GPU guidance |
|------|--------------|
| Wav2Lip | RTX 3060 or higher is typically enough |
| MuseTalk | RTX 3080 Ti or higher is the safer assumption |
| ER-NeRF | Treat as high-end / R&D only for now |

## Architecture Boundary

- `MuseTalk`, `Wav2Lip`, `Ultralight` = face runtime choices
- `GPT-SoVITS`, `CosyVoice`, `FishSpeech`, `Edge-TTS` = voice layer choices

Do not mix these two decision layers into one model comparison.

## Internal-Live Default Decision

For the current `videoliveai` direction:

1. Default face runtime: `MuseTalk`
2. Fallback face runtime: `Wav2Lip`
3. Low-resource fallback: `Ultralight`
4. Backlog / R&D: `ER-NeRF`, `GFPGAN`

## Related Docs

- [LIVETALKING_QUICKSTART.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/LIVETALKING_QUICKSTART.md)
- [architecture.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/architecture.md)
- [task_status.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/task_status.md)
