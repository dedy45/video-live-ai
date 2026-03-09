# Fish-Speech Local Real Audio Design

**Status:** Approved design for immediate execution  
**Date:** 2026-03-09  
**Audience:** coding agent, operator, reviewer  
**Scope:** local non-mock audio vertical slice with local voice cloning for Indonesian live stream

---

## 1. Problem Statement

`videoliveai` already has a stable local face path (`LiveTalking + MuseTalk`), but the voice path is not yet realistic for live stream:

- `FishSpeechEngine` exists, but production inference still raises `NotImplementedError`
- runtime truth reports `fish_speech` too optimistically without proving local clone inference is active
- readiness gates are focused on face/stream and do not yet enforce local voice clone readiness
- current fallback behavior (`Edge TTS`) is useful for continuity, but must not be counted as acceptance for realistic local audio

Without a strict local voice contract, realism claims for live stream remain incomplete.

---

## 2. Non-Negotiable Goals

1. **Local-only acceptance path**: final pass must run with local Fish-Speech inference (`MOCK_MODE=false`, no cloud dependency as acceptance evidence).
2. **Voice cloning required**: synthesis must use real local reference assets and clone-style conditioning.
3. **Indonesia-first quality**: acceptance text and checks must include Indonesian utterances.
4. **Live-stream realism discipline**: keep latency, continuity, and fallback visibility explicit.
5. **Workspace alignment**: preserve current architecture (`FastAPI control plane`, `UV`, `/dashboard` truth model, operator CLI via `scripts/manage.py`).

---

## 3. Rejected Shortcuts

The following are explicitly out of acceptance:

- counting `Edge TTS` as final pass for local realistic audio
- claiming success from mock-mode or synthetic test doubles
- claiming `fish_speech` active from config string only
- skipping clone asset validation (reference audio/transcript quality)
- adding cloud-only TTS paths into critical acceptance path

---

## 4. Architecture Options

### Option A: In-process Fish-Speech Python integration

- **Pros:** fewer processes, lower local orchestration complexity.
- **Cons:** tighter dependency coupling, harder isolation/debugging, harder parity with upstream Fish-Speech server behavior.

### Option B (Recommended): Local Fish-Speech sidecar API

- `videoliveai` remains control plane.
- `FishSpeechEngine` calls local Fish-Speech API (`127.0.0.1:<port>`) via client adapter.
- **Pros:** clean process boundary, operationally similar to LiveTalking sidecar, easier health/readiness checks and rollout.
- **Cons:** extra process management and endpoint contract handling.

### Option C: Cloud TTS primary + local fallback

- **Rejected for this milestone** because it violates local-realistic acceptance requirements.

**Decision:** adopt **Option B**.

---

## 5. Chosen Design

### Active Audio Path

`FastAPI -> VoiceRouter -> FishSpeechEngine -> local Fish-Speech API sidecar`

### Fallback Policy

- `Edge TTS` remains emergency fallback for runtime continuity.
- Any fallback activation must be surfaced in runtime truth and validation.
- Fallback-active runs are **not** acceptance-pass for this milestone.

### Runtime Truth Extension

Current truth must be upgraded from single string to explicit requested/resolved voice state.

Required truth fields:

- `voice_runtime_mode` (e.g., `fish_speech_local`, `edge_tts_fallback`, `voice_error`, `mock`)
- `voice_engine.requested_engine`
- `voice_engine.resolved_engine`
- `voice_engine.fallback_active`
- `voice_engine.server_reachable`
- `voice_engine.reference_ready`
- `voice_engine.last_latency_ms`
- `voice_engine.last_error`

---

## 6. Local Asset Contract (Voice Clone)

Canonical local assets:

- `assets/voice/reference.wav` (16k or 24k mono WAV, clean voice)
- `assets/voice/reference.txt` (transcript aligned with reference sample, Indonesian preferred)

Validation rules:

- both files must exist for clone acceptance
- transcript must be non-empty, plain text
- reference audio must pass minimal format checks (WAV, duration window per spec)

---

## 7. Readiness and Validation Contract

The following checks become mandatory for local realistic audio acceptance:

1. Fish-Speech sidecar endpoint reachable.
2. Voice clone reference assets ready.
3. Local non-mock synthesis succeeds with Indonesian sample text.
4. Resolved engine remains `fish_speech` (no fallback active).
5. Latency is recorded and compared against budget (warn/fail thresholds defined in implementation).

Recommended new endpoint:

- `POST /api/validate/voice-local-clone`

Expected output:

- `status`: `pass` | `fail` | `blocked` | `error`
- `checks`: explicit pass/fail list
- `evidence_id`: validation history linkage

---

## 8. Testing Strategy

### Unit

- Fish-Speech API client request/response contract.
- Engine behavior on success, timeout, and invalid response.
- Voice router fallback path and fallback visibility state updates.

### Integration (local)

- readiness check includes voice clone prerequisites.
- runtime truth reflects requested/resolved voice engine.
- validation endpoint runs synthesis smoke and records evidence.

### Regression

- existing dashboard truth and readiness tests remain green.
- no silent downgrade to `edge_tts` in acceptance evidence.

---

## 9. Acceptance Criteria

Milestone passes only if all are true:

1. `MOCK_MODE=false` local run uses Fish-Speech sidecar for synthesis.
2. `voice_engine.resolved_engine=fish_speech`.
3. `voice_engine.fallback_active=false` during acceptance validation.
4. Indonesian sample synthesis succeeds with real audio output bytes.
5. Runtime truth and docs report the same state.
6. Validation evidence is recorded and auditable.

---

## 10. Out of Scope for This Milestone

- GPT-SoVITS/CosyVoice production integration
- emotion fine-tuning and expressive style training
- long-session auto-recovery hardening
- production rollout and live-platform certification

---

## 11. Execution Order

1. Freeze audio acceptance truth and contracts.
2. Implement Fish-Speech local adapter and engine integration.
3. Add runtime truth + readiness + validation gates.
4. Add TDD coverage and regression checks.
5. Run local non-mock evidence capture and sync source-of-truth docs.

---

## 12. External References

- Fish-Speech official repository: https://github.com/fishaudio/fish-speech
- Fish-Speech API/inference start command (official docs): https://speech.fish.audio/inference/

