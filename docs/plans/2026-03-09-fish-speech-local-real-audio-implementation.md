# Fish-Speech Local Real Audio Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Deliver a local non-mock audio slice that uses Fish-Speech voice cloning for Indonesian live stream, with truthful runtime reporting, validation gates, and test evidence.

> **Review status (2026-03-10):** Tasks 1-8 are now implemented and locally verified for direct non-mock testing. Current remaining issue is performance realism: the local Fish-Speech smoke path completes with `resolved_engine=fish_speech` and `fallback_active=false`, but observed latency on the current GTX 1650 setup remains around `31-40s`.

**Architecture:** Keep `videoliveai` as the control plane and add Fish-Speech as a local sidecar API integration for voice synthesis. Extend VoiceRouter runtime truth from config-only signaling to requested/resolved engine state with fallback visibility. Enforce acceptance through readiness checks and a dedicated validation endpoint.

**Tech Stack:** Python 3.12, FastAPI, UV, httpx, pytest, pytest-asyncio, local Fish-Speech API sidecar, existing dashboard truth/readiness/validation flow.

---

## 0. Why This Plan Exists

Current voice path is not acceptance-grade for realistic local live stream:

- `FishSpeechEngine._run_inference` is not implemented.
- Runtime truth can claim `fish_speech` without proving local synthesis.
- Voice clone assets and local Fish-Speech reachability are not hard-gated in readiness.
- Fallback (`edge_tts`) is available but not explicitly treated as non-acceptance for this milestone.

This plan closes those gaps without changing the established control-plane architecture.

---

## 1. Hard Constraints

### Local Realism Rule

- Acceptance run must be `MOCK_MODE=false`.
- Acceptance must use local Fish-Speech synthesis, not cloud-only TTS.

### Clone Rule

- Acceptance requires valid local clone assets:
  - `assets/voice/reference.wav`
  - `assets/voice/reference.txt`

### Truth Rule

- Runtime truth must expose requested/resolved voice engine and fallback state.
- If fallback is active during acceptance, milestone is not complete.

### Scope Rule

Do not include in this milestone:

- GPT-SoVITS/CosyVoice integration
- voice emotion model retraining
- production rollout hardening

---

## 2. End State

This implementation is complete only if:

1. Local Fish-Speech sidecar is reachable from the app.
2. `FishSpeechEngine` performs real non-mock synthesis via local API.
3. Runtime truth shows requested/resolved voice engine with fallback visibility.
4. Readiness + validation include voice clone checks.
5. Tests cover success/failure/fallback paths and pass.
6. Local audit evidence records an Indonesian synthesis pass with fallback inactive.

---

## 3. Execution Strategy

Implement in six blocks:

1. `Freeze Voice Contract`
2. `Implement Fish-Speech Client + Engine`
3. `Expose Voice Runtime Truth`
4. `Add Readiness/Validation Gates`
5. `Wire Operator CLI + Scripts`
6. `Verify, Audit, and Sync Docs`

---

## 4. Task-by-Task Plan

### Task 1: Freeze local audio acceptance contract

**Files:**
- Create: `docs/specs/local_audio_vertical_slice_fish_speech.md`
- Modify: `docs/architecture.md`
- Modify: `docs/task_status.md`
- Modify: `docs/workflow.md`
- Modify: `README.md`

**Step 1: Write failing doc-alignment checks**

Run:

```bash
rg -n "fish_speech|voice_runtime_mode|fallback" docs README.md
```

Expected:
- Existing docs do not yet encode strict local Fish-Speech acceptance truth.

**Step 2: Write contract doc**

Define:

- active voice path
- clone asset contract
- fallback policy
- acceptance truth fields
- mandatory validation evidence

**Step 3: Update source-of-truth docs**

Ensure docs consistently state:

- Fish-Speech local clone is the acceptance path.
- Edge TTS fallback is emergency-only and non-acceptance.

**Step 4: Verify references**

Run:

```bash
rg -n "Fish-Speech|edge_tts|fallback|voice clone" docs README.md
```

Expected: all relevant docs are aligned.

**Step 5: Commit**

```bash
git add docs/specs/local_audio_vertical_slice_fish_speech.md docs/architecture.md docs/task_status.md docs/workflow.md README.md
git commit -m "docs: freeze local fish-speech audio acceptance contract"
```

---

### Task 2: Add Fish-Speech runtime config and env contract

**Files:**
- Modify: `src/config/loader.py`
- Modify: `config/config.yaml`
- Modify: `.env.example`
- Test: `tests/test_property.py`

**Step 1: Write failing tests for config fields**

Add tests for required new config fields, for example:

```python
def test_voice_config_includes_fish_speech_runtime_fields():
    cfg = get_config()
    assert hasattr(cfg.voice, "fish_speech_base_url")
    assert hasattr(cfg.voice, "fish_speech_timeout_ms")
    assert hasattr(cfg.voice, "clone_reference_wav")
    assert hasattr(cfg.voice, "clone_reference_text")
```

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_property.py -q -p no:cacheprovider
```

Expected: FAIL because fields are missing.

**Step 3: Implement minimal config extension**

Add voice config keys:

- `fish_speech_base_url` (default `http://127.0.0.1:8080`)
- `fish_speech_timeout_ms`
- `clone_reference_wav`
- `clone_reference_text`
- `indonesian_smoke_text`

**Step 4: Re-run tests**

Run:

```bash
uv run pytest tests/test_property.py -q -p no:cacheprovider
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/config/loader.py config/config.yaml .env.example tests/test_property.py
git commit -m "feat: add fish-speech local runtime config contract"
```

---

### Task 3: Implement Fish-Speech API client adapter

**Files:**
- Create: `src/voice/fish_speech_client.py`
- Create: `tests/test_fish_speech_client.py`

**Step 1: Write failing client tests**

Cover:

- health endpoint handling
- synthesis request payload includes references
- timeout and non-200 response behavior

Example:

```python
@pytest.mark.asyncio
async def test_synthesize_posts_v1_tts_with_reference_payload(httpx_mock):
    client = FishSpeechClient(base_url="http://127.0.0.1:8080", timeout_ms=3000)
    httpx_mock.add_response(method="POST", url="http://127.0.0.1:8080/v1/tts", content=b"WAVDATA")
    audio = await client.synthesize(text="halo kak", reference_audio_b64="xxx", reference_text="halo")
    assert audio == b"WAVDATA"
```

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_fish_speech_client.py -q -p no:cacheprovider
```

Expected: FAIL because adapter file does not exist.

**Step 3: Implement minimal adapter**

Implement:

- `FishSpeechClient.health_check() -> bool`
- `FishSpeechClient.synthesize(...) -> bytes`
- explicit exceptions with actionable messages

**Step 4: Re-run tests**

Run:

```bash
uv run pytest tests/test_fish_speech_client.py -q -p no:cacheprovider
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/voice/fish_speech_client.py tests/test_fish_speech_client.py
git commit -m "feat: add fish-speech local api client adapter"
```

---

### Task 4: Implement real Fish-Speech path in `FishSpeechEngine`

**Files:**
- Modify: `src/voice/engine.py`
- Create: `tests/test_voice_engine.py`

**Step 1: Write failing engine tests**

Add tests proving:

- non-mock path calls Fish-Speech client
- missing clone assets produce explicit error
- fallback to `EdgeTTSEngine` occurs only on primary failure

Example:

```python
@pytest.mark.asyncio
async def test_voice_router_uses_fish_speech_when_primary_healthy(monkeypatch):
    router = VoiceRouter()
    monkeypatch.setattr(router.primary, "_run_inference", AsyncMock(return_value=b"wav"))
    result = await router.synthesize("halo kak", emotion="calm")
    assert result.audio_data == b"wav"
```

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_voice_engine.py -q -p no:cacheprovider
```

Expected: FAIL.

**Step 3: Implement minimal production path**

In `FishSpeechEngine`:

- load clone reference wav/text from config
- call `FishSpeechClient`
- propagate latency and error details

In `VoiceRouter`:

- keep fallback behavior
- tag fallback activation through runtime state (next task)

**Step 4: Re-run targeted tests**

Run:

```bash
uv run pytest tests/test_voice_engine.py -q -p no:cacheprovider
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/voice/engine.py tests/test_voice_engine.py
git commit -m "feat: implement local fish-speech synthesis path with controlled fallback"
```

---

### Task 5: Add truthful voice runtime state for dashboard truth model

**Files:**
- Create: `src/voice/runtime_state.py`
- Modify: `src/voice/engine.py`
- Modify: `src/dashboard/truth.py`
- Modify: `docs/specs/dashboard_truth_model.md`
- Test: `tests/test_dashboard.py`

**Step 1: Write failing truth tests**

Add tests proving runtime truth includes:

- requested/resolved voice engine
- fallback_active
- server_reachable

Example:

```python
@pytest.mark.asyncio
async def test_runtime_truth_has_voice_engine_fields():
    truth = get_runtime_truth_snapshot()
    assert "voice_engine" in truth
    assert "requested_engine" in truth["voice_engine"]
    assert "resolved_engine" in truth["voice_engine"]
    assert "fallback_active" in truth["voice_engine"]
```

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected: FAIL.

**Step 3: Implement runtime state**

Create a singleton-like runtime state updated by `VoiceRouter` after each synthesis:

- requested engine
- resolved engine
- fallback flag
- last error
- last latency

Then expose it in `get_runtime_truth_snapshot()`.

**Step 4: Re-run tests**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/voice/runtime_state.py src/voice/engine.py src/dashboard/truth.py docs/specs/dashboard_truth_model.md tests/test_dashboard.py
git commit -m "feat: expose truthful voice requested-resolved runtime state"
```

---

### Task 6: Add local voice readiness and validation gates

**Files:**
- Modify: `src/dashboard/readiness.py`
- Modify: `src/dashboard/api.py`
- Modify: `scripts/check_real_mode_readiness.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write failing readiness/validation tests**

Add tests for:

- missing `assets/voice/reference.wav` or `reference.txt` blocks voice clone readiness
- Fish-Speech endpoint unreachable is surfaced as blocker
- `POST /api/validate/voice-local-clone` returns explicit checks

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected: FAIL.

**Step 3: Implement checks**

Add readiness checks:

- `voice_reference_wav_ready`
- `voice_reference_text_ready`
- `fish_speech_server_reachable`

Add endpoint:

- `POST /api/validate/voice-local-clone`

This endpoint runs one Indonesian synthesis smoke and records evidence.

**Step 4: Re-run tests**

Run:

```bash
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
```

Expected: PASS.

**Step 5: Commit**

```bash
git add src/dashboard/readiness.py src/dashboard/api.py scripts/check_real_mode_readiness.py tests/test_dashboard.py
git commit -m "feat: add fish-speech local voice readiness and validation gates"
```

---

### Task 7: Add operator CLI hooks for fish-speech local flow

**Files:**
- Modify: `scripts/manage.py`
- Create: `scripts/setup_fish_speech.py`
- Modify: `tests/test_manage_cli.py`

**Step 1: Write failing CLI tests**

Add tests for:

- `manage.py setup-fish-speech`
- `manage.py validate fish-speech`

Expected behavior:

- deterministic command routing
- non-zero exit for unreachable sidecar
- clear operator message

**Step 2: Run targeted tests**

Run:

```bash
uv run pytest tests/test_manage_cli.py -q -p no:cacheprovider
```

Expected: FAIL.

**Step 3: Implement CLI wiring**

Implement:

- setup script for fish-speech path checks + startup guidance
- validate target that calls voice validation endpoint or direct health probe

**Step 4: Re-run tests**

Run:

```bash
uv run pytest tests/test_manage_cli.py -q -p no:cacheprovider
```

Expected: PASS.

**Step 5: Commit**

```bash
git add scripts/manage.py scripts/setup_fish_speech.py tests/test_manage_cli.py
git commit -m "feat: add fish-speech operator setup and validation commands"
```

---

### Task 8: Real local verification and evidence capture

**Files:**
- Create: `docs/audits/AUDIT_LOCAL_AUDIO_VERTICAL_SLICE_FISH_SPEECH_2026-03-09.md`
- Modify: `docs/task_status.md`
- Modify: `docs/workflow.md`
- Modify: `docs/changelogs.md`

**Step 1: Run local sidecar**

Use official Fish-Speech startup contract (local):

```bash
python -m tools.api_server --listen 127.0.0.1:8080 --llama-checkpoint-path <checkpoint_dir> --decoder-checkpoint-path <decoder_path>
```

**Step 2: Run app and validations**

```bash
uv run python scripts/manage.py serve --real
uv run python scripts/manage.py validate fish-speech
uv run python scripts/check_real_mode_readiness.py --json
```

Expected:

- voice clone checks pass
- runtime truth shows `resolved_engine=fish_speech` and `fallback_active=false`

**Step 3: Run regression tests**

```bash
uv run pytest tests/test_fish_speech_client.py -q -p no:cacheprovider
uv run pytest tests/test_voice_engine.py -q -p no:cacheprovider
uv run pytest tests/test_dashboard.py -q -p no:cacheprovider
uv run pytest tests -q -p no:cacheprovider
```

Expected:

- all pass (allow existing known Windows pytest temp cleanup warning as non-blocking noise)

**Step 4: Record audit and docs sync**

Document:

- commands
- requested/resolved voice truth
- latency snapshot
- blocker list (if any)

**Step 5: Commit**

```bash
git add docs/audits/AUDIT_LOCAL_AUDIO_VERTICAL_SLICE_FISH_SPEECH_2026-03-09.md docs/task_status.md docs/workflow.md docs/changelogs.md
git commit -m "docs: record local fish-speech audio vertical slice evidence"
```

---

## 5. Verification Checklist

- [ ] Non-mock local Fish-Speech synthesis works with Indonesian sample text
- [ ] Clone asset contract enforced (`reference.wav` + `reference.txt`)
- [ ] Runtime truth exposes requested/resolved voice engine and fallback
- [ ] Voice readiness checks are part of real-mode gate
- [ ] Validation endpoint records evidence for voice-local-clone
- [ ] Full test suite passes
- [ ] Source-of-truth docs are synchronized

---

## 6. Risks and Mitigations

1. **Fish-Speech sidecar cold start latency too high**
- Mitigation: add warmup call and latency threshold warning before go-live.

2. **Clone reference quality causes poor Indonesian intelligibility**
- Mitigation: enforce stricter reference asset checklist and add a deterministic Indonesian smoke phrase.

3. **Fallback silently masks primary failure**
- Mitigation: runtime truth + validation must fail acceptance when fallback is active.

4. **Operator confusion across multiple sidecars**
- Mitigation: keep `scripts/manage.py` as single operator interface and document exact command flow.

---

## 7. External Technical References

- Fish-Speech repository: https://github.com/fishaudio/fish-speech
- Official inference/API quickstart: https://speech.fish.audio/inference/
