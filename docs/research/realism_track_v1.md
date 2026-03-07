# Face Realism Track v1

> **Status**: Active
> **Date**: 2026-03-07

## Recommendation

| Track | Model | Phase | Purpose |
|-------|-------|-------|---------|
| **Baseline** | Wav2Lip | Now | Operational validation, low VRAM |
| **Upgrade** | MuseTalk | When GPU + assets ready | Better quality, higher VRAM |

## Why Wav2Lip First

- Lower VRAM requirement (~4GB vs ~8GB)
- Simpler avatar preparation
- Faster iteration for operational validation
- Already working with existing avatars

## Upgrade Path to MuseTalk

Prerequisites before upgrading:
1. RTX 3080 Ti or better (8GB+ VRAM)
2. MuseTalk model weights downloaded
3. MuseTalk avatar data prepared
4. Test in mock mode first, then real GPU

## What We Are NOT Doing

- ER-NeRF (requires long training, complex setup)
- FaceFusion (different paradigm)
- Body-double hybrid (out of scope)
