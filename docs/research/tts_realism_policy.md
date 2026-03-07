# TTS Realism Policy

> **Status**: Active (policy-first, no engine rewrite)
> **Date**: 2026-03-07

## Current Stack

| Engine | Role | Quality | Cost |
|--------|------|---------|------|
| Edge TTS | Primary (cloud) | Good | Free |
| Fish Speech | Upgrade path (GPU) | Better | Free (self-hosted) |
| CosyVoice | Future option | Best | Free (self-hosted) |

## Policy Rules

1. **Stability first**: Do not rewrite TTS engine before vertical slice is stable
2. **Edge TTS is acceptable** for initial internal demos
3. **Fish Speech** upgrade only when GPU capacity allows
4. **Voice cloning** requires reference audio (see `docs/specs/audio_asset_spec.md`)
5. **Emotion mapping** is defined in `config.yaml` under `voice.emotion_mapping`

## Quality Targets

| Dimension | Target | Current |
|-----------|--------|---------|
| Naturalness | 7/10 | 6/10 (Edge TTS) |
| Latency | <500ms | ~300ms (Edge TTS) |
| Language | Indonesian + English | Indonesian (Edge TTS) |
