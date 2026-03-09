# Local Audio Vertical Slice — Fish-Speech Acceptance Contract

> Version: 1.0
> Created: 2026-03-09
> Scope: local non-mock voice synthesis with Fish-Speech voice cloning for Indonesian live stream

## 1. Active Voice Path

```
FastAPI -> VoiceRouter -> FishSpeechEngine -> local Fish-Speech API sidecar (127.0.0.1:8080)
```

- Primary engine: **Fish-Speech** via local sidecar API
- Fallback engine: **Edge TTS** (emergency-only, does NOT count as acceptance pass)

## 2. Clone Asset Contract

Canonical voice clone assets:

| Asset | Path | Requirements |
|-------|------|-------------|
| Reference audio | `assets/voice/reference.wav` | 16kHz or 24kHz mono WAV, clean voice, 5-30 seconds |
| Reference transcript | `assets/voice/reference.txt` | Non-empty plain text aligned with reference audio, Indonesian preferred |

Both files must exist for clone acceptance. Missing either file blocks voice readiness.

## 3. Fallback Policy

- Edge TTS remains available for runtime continuity (emergency fallback).
- Any fallback activation must be surfaced in runtime truth as `fallback_active=true`.
- Fallback-active runs are **not** acceptance-pass for this milestone.
- Acceptance requires `voice_engine.resolved_engine=fish_speech` and `voice_engine.fallback_active=false`.

## 4. Runtime Truth Fields (Voice Engine)

The runtime truth snapshot must include `voice_engine` with:

| Field | Type | Description |
|-------|------|-------------|
| `requested_engine` | string | Engine requested by config (e.g. `fish_speech`) |
| `resolved_engine` | string | Engine actually used for last synthesis |
| `fallback_active` | bool | True if fallback was used instead of primary |
| `server_reachable` | bool | Fish-Speech sidecar health check result |
| `reference_ready` | bool | Both clone reference assets exist |
| `last_latency_ms` | float or null | Last synthesis latency |
| `last_error` | string or null | Last synthesis error message |

The `voice_runtime_mode` field is enhanced from a simple string to a derived value:

- `mock` — MOCK_MODE=true
- `fish_speech_local` — primary engine active, no fallback
- `edge_tts_fallback` — fallback active
- `voice_error` — both engines failed
- `unknown` — engine not yet resolved by real synthesis, or unexpected failure

## 5. Readiness Checks (Voice)

These checks are mandatory for local realistic audio acceptance:

| Check | Blocking | Description |
|-------|----------|-------------|
| `voice_reference_wav_ready` | yes | `assets/voice/reference.wav` exists |
| `voice_reference_text_ready` | yes | `assets/voice/reference.txt` exists and is non-empty |
| `fish_speech_server_reachable` | yes | Fish-Speech sidecar is reachable at configured URL |

## 6. Validation Endpoint

`POST /api/validate/voice-local-clone`

Runs one Indonesian synthesis smoke test and records evidence.

Response:

```json
{
  "status": "pass | fail | blocked | error",
  "checks": [...],
  "evidence_id": "...",
  "latency_ms": 1234.5
}
```

## 7. Acceptance Criteria

Milestone passes only if ALL are true:

1. `MOCK_MODE=false` local run uses Fish-Speech sidecar for synthesis.
2. `voice_engine.resolved_engine=fish_speech`.
3. `voice_engine.fallback_active=false` during acceptance validation.
4. Indonesian sample synthesis succeeds with real audio output bytes.
5. Runtime truth and docs report the same state.
6. Validation evidence is recorded and auditable.

## 8. Out of Scope

- GPT-SoVITS / CosyVoice production integration
- Emotion fine-tuning and expressive style training
- Long-session auto-recovery hardening
- Production rollout and live-platform certification

## Related Docs

- [architecture.md](/docs/architecture.md)
- [dashboard_truth_model.md](/docs/specs/dashboard_truth_model.md)
- [task_status.md](/docs/task_status.md)
