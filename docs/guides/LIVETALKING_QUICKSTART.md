# LiveTalking Integration Quick Start

> Last verified: 2026-03-07
> Scope: current integration boundary between `videoliveai` and `external/livetalking`

## What This Guide Is For

Use this guide to validate the current internal-live setup without confusing:

- target architecture
- vendor capabilities
- mock-mode checks
- unfinished production GPU paths

## Runtime Truth Today

### Active in the current vendor copy

- MuseTalk runtime
- Wav2Lip runtime
- Ultralight runtime
- WebRTC / rtcpush / virtualcam output
- vendor debug pages under `localhost:8010`

### Not safe to assume active today

- ER-NeRF runtime in the vendor app
- built-in GFPGAN in the vendor runtime
- unified production bridge from FastAPI to LiveTalking

## Official Validation Path

```bash
uv sync --extra dev
uv run pytest tests -q -p no:cacheprovider
uv run python scripts/verify_pipeline.py
MOCK_MODE=true uv run python -m src.main
```

Expected result on the current snapshot:

- `89 passed`
- `11/11 layers PASS`

## Entry Points

| Path | Purpose |
|------|---------|
| `uv run python -m src.main` | Main FastAPI app |
| `external/livetalking/app.py` | Vendor engine entrypoint |
| `http://localhost:8000/dashboard` | Main operator dashboard |
| `http://localhost:8010/*.html` | Vendor debug pages only |

## Model Guidance

### Recommended default

- **MuseTalk** for the main realtime face path if GPU budget is sufficient

### Acceptable fallback

- **Wav2Lip** for compatibility and lower GPU demand

### Low-resource option

- **Ultralight** when you need a lighter runtime path

### Backlog / target, not default runtime assumptions

- **ER-NeRF**
- **GFPGAN**

Those still belong to the target stack, not the guaranteed current implementation.

## Voice Layer Boundary

LiveTalking is the face/output sidecar.  
Voice generation belongs to `videoliveai`.

Treat these separately:

- `FishSpeech`, `Edge-TTS`, `GPT-SoVITS`, `CosyVoice` = voice layer
- `MuseTalk`, `Wav2Lip`, `Ultralight` = face/runtime layer

## Reference Assets

For real production validation you still need:

- reference face/video assets under `assets/avatar/`
- reference voice assets under `assets/voice/`
- real GPU environment for vendor runtime checks

## Common Pitfalls

- Do not treat `localhost:8010` vendor pages as the main dashboard.
- Do not assume every item in project README is already active in vendor runtime.
- Do not use `conda` commands as the source-of-truth workflow.
- Do not treat mock-mode pass as proof of production live readiness.

## Related Docs

- [README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/README.md)
- [architecture.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/architecture.md)
- [task_status.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/task_status.md)
- [MODEL_COMPARISON.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/MODEL_COMPARISON.md)

## Resources

- LiveTalking Repo: https://github.com/lipku/LiveTalking
- MuseTalk: https://github.com/TMElyralab/MuseTalk
- ER-NeRF: https://github.com/Fictionarry/ER-NeRF
- GFPGAN: https://github.com/TencentARC/GFPGAN
