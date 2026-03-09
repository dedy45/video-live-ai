# MuseTalk Local Vertical Slice Real Design

**Status:** Approved design for the next execution phase  
**Date:** 2026-03-09  
**Audience:** Claude Opus / coding agent, operator, reviewer  
**Scope:** local UV environment first, real non-mock vertical slice, then live test later

---

## 1. Problem Statement

`videoliveai` currently has a working local control-plane baseline, but the media/runtime path is still ambiguous:

- too many face/runtime paths still look "possibly active"
- `MuseTalk` and `Wav2Lip` are both visible in practice
- some older face pipeline paths still exist but are not trustworthy for the current acceptance goal
- realism-oriented work risks being diluted by fallback-first progress

This causes repeated work and makes it hard to evaluate whether the system is moving toward a realistic livestream experience.

---

## 2. Design Decision

The project now freezes a single active face/runtime path for the next milestone:

- **Active face runtime:** `LiveTalking sidecar + MuseTalk`
- **Secondary fallback only:** `Wav2Lip`
- **Target only / not in active path:** `GFPGAN`, `ER-NeRF`
- **Voice redesign:** deferred to the next phase
- **Humanization layer:** mandatory, but only after the local real MuseTalk slice is actually running

This is a deliberate narrowing of scope to reduce repeated work and eliminate ambiguous acceptance criteria.

---

## 3. Target Milestone

The next milestone is:

## `LOCAL_VERTICAL_SLICE_REAL_MUSETALK`

This milestone means:

- local environment remains `uv`-only
- app runs with `MOCK_MODE=false`
- `/dashboard` is the operator source of truth
- product data is real local data, not dummy acceptance shortcuts
- reference media is real local media
- `musetalk_avatar1` is generated in the canonical vendor path
- `LiveTalking` sidecar starts through the official operator path
- runtime truth resolves to `musetalk`, not `wav2lip`
- one end-to-end local operator slice runs in non-mock mode with saved evidence

This milestone does **not** mean:

- production-ready livestream quality is final
- long-session stability is complete
- RTMP platform validation is complete
- voice architecture is final
- human realism is fully polished

---

## 4. Non-Negotiable Rules

### Active Path Rule

For this milestone, the only acceptable primary face path is:

`FastAPI -> dashboard/operator flow -> LiveTalking sidecar -> MuseTalk`

### Fallback Rule

`Wav2Lip` may remain in the repository and may still exist for emergency/dev fallback, but:

- it must not be counted as a pass for this milestone
- if runtime truth resolves to `wav2lip`, the milestone is not complete

### Truth Rule

Docs and runtime truth must be aligned:

- if `requested_model=musetalk` and `resolved_model=wav2lip`, the system is still `PARTIAL`
- docs must never imply MuseTalk success while fallback is active

### Scope Discipline Rule

The following are explicitly out of the critical path for this milestone:

- `GFPGAN`
- `ER-NeRF`
- voice engine redesign
- long-running watchdog/recovery layer
- blind testing
- production launch steps

---

## 5. Architecture Boundary

### Keep

- `FastAPI` as the control plane
- Svelte dashboard served by FastAPI
- `UV-only` environment policy
- `external/livetalking` as vendor sidecar
- `/dashboard` as the primary operator UI
- `localhost:8010/*.html` as vendor debug only

### De-emphasize

- legacy/experimental face branches not used by the active operator path
- vendor features that are not required for the current acceptance target

### Clarify

If `src/face/pipeline.py` is not part of the active operator path for this milestone, it should not drive acceptance.  
If it is still in the active path, then its current `NotImplementedError` behavior becomes a real blocker and must be fixed.

---

## 6. Canonical Runtime Truth for This Phase

The system is only considered locally real and MuseTalk-active if all of the following are true:

- `mock_mode = false`
- `requested_model = musetalk`
- `resolved_model = musetalk`
- `requested_avatar_id = musetalk_avatar1`
- `resolved_avatar_id = musetalk_avatar1`
- vendor sidecar port is reachable
- dashboard truth surfaces reflect the same values

Any silent or automatic downgrade to `wav2lip` must remain visible as a failure to complete this milestone.

---

## 7. Required Inputs

### Real Local Data

- local product data source accepted by the readiness gate
- real reference media for avatar generation
- real local config/env values required by non-mock mode

### Canonical Paths

- `external/livetalking/models/musetalk/`
- `external/livetalking/data/avatars/musetalk_avatar1/`
- `assets/avatar/reference.mp4`
- `assets/avatar/reference.wav`

---

## 8. Required Outputs

By the end of this milestone, the repo must have:

- one written spec for the milestone contract
- one truthful readiness gate that fails when MuseTalk falls back
- one official local operator command path for real non-mock startup
- one local audit showing the non-mock MuseTalk slice ran successfully
- updated source-of-truth docs reflecting the actual state

---

## 9. Humanization Phase Position

Humanization remains mandatory for the broader realism goal, but it is intentionally **Phase 2 of this narrowed track**, not Phase 1.

Reason:

- realistic micro-behavior only matters after the actual MuseTalk runtime path is stable
- otherwise the team risks polishing fallback behavior and repeating work

The humanization phase for the next milestone after this one should include:

- blink behavior
- eye drift
- idle head micro-motion
- idle presence / non-speaking motion
- pacing and response delay policy

Voice redesign is intentionally deferred until the face/runtime truth is stable.

---

## 10. Acceptance Criteria

This design is satisfied only if all of these are true:

1. local `uv` environment can run the non-mock stack through the official operator path
2. real local product data passes the readiness gate
3. canonical `musetalk_avatar1` exists and is used
4. runtime truth resolves to `musetalk`
5. `wav2lip` is no longer the resolved runtime in acceptance evidence
6. one local end-to-end operator slice is recorded with evidence
7. docs explicitly describe `MuseTalk active / Wav2Lip fallback only`

---

## 11. What Claude Opus Should Not Do

- do not re-open architecture choices unless hard evidence shows the active path is fundamentally broken
- do not broaden scope to `GFPGAN`, `ER-NeRF`, or voice redesign
- do not count `wav2lip` fallback as acceptable completion
- do not use synthetic success substitutes to close the milestone

---

## 12. Recommended Execution Order

1. freeze truth and docs
2. unblock real-local prerequisites
3. generate and activate canonical MuseTalk avatar
4. prove official non-mock operator path
5. run and audit one local real vertical slice
6. only then move to humanization and later live testing

---

## 13. Source of Truth After Approval

After implementation starts, the following should be treated as canonical:

- this design doc
- the implementation plan paired with it
- `docs/architecture.md`
- `docs/task_status.md`
- `docs/workflow.md`

Draft ideation files such as `docs/ide/saranopus46.md` should not override the above.
