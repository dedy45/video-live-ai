# Voice Lab ElevenLabs-Style Hybrid Design

**Date:** 2026-03-14

## Goal

Turn the `Suara` tab into a dashboard-first Voice Lab that feels like an operator-grade ElevenLabs-style workspace while remaining honest about the current runtime:

- `Quick Clone` for fast browser-driven reference cloning
- `Studio Voice` for production-stable bilingual (`Indonesia` + `English`) voice management
- `Generate` and `Library` as day-1 fully usable surfaces
- `Training Jobs` controlled from the dashboard, but blocked while a live session is active on the same host

## Product Decisions Locked

- Single host GPU, single active live session
- Dashboard is the single source of truth
- `Studio Voice` is `production stable`
- `Studio Voice` is bilingual under one voice identity, with explicit language choice per generation
- Dataset flow is `automatic-first`
- Training is blocked during active live sessions

## Scope For This Implementation Pass

### Must be real and browser-verified now

- Language choice in generator: `Indonesia` / `English`
- Multiple clone profiles with interactive browser form
- Better clone guidance and validation hints
- Audio result history that is actually playable and downloadable per item
- Library/history metadata rich enough to inspect which settings produced the output
- Standalone and attach-to-avatar generation continue to work

### Must have real control-plane foundations now

- `Studio Voice` profile type and minimal dashboard management surface
- `Training Jobs` persistence and dashboard controls
- Training preflight that blocks while live is active
- Durable SQLite storage for generator settings and audio artifacts

### Can be foundational in this pass, not fully production-trained yet

- Automatic long-recording segmentation and transcript/QC pipeline
- Full Fish-Speech fine-tune orchestration end-to-end on every machine

Those remain real design targets, but the immediate user-visible priority is to stop the Voice Lab from feeling incomplete or non-interactive.

## Architecture

### Voice Profile Classes

- `quick_clone`
  - Fast operator-generated profile from one or more reference assets
  - Suitable for testing and draft usage
- `studio_voice`
  - Production voice identity
  - Holds bilingual support metadata and revision history
  - Intended for live-safe use after training/publish

### Voice Lab Workspaces

- `Generate`
  - Pick language, voice profile, output mode, and generation settings
- `Quick Clone`
  - Upload/reference management plus operator guidance
- `Studio Voice`
  - Production voice metadata, revisions, and publish state
- `Training Jobs`
  - Queue, run, inspect, and cancel training work
- `Library`
  - Browse, play, download, and inspect generated audio

## Data Model Additions

### `voice_profiles`

Add:

- `profile_type`
- `supported_languages_json`
- `quality_tier`
- `guidance_json`

### `voice_generations`

Add:

- `language`
- `style_preset`
- `stability`
- `similarity`
- `audio_filename`
- `download_name`

### New `voice_training_jobs`

Durable background job state:

- `profile_id`
- `job_type`
- `status`
- `queued_at`, `started_at`, `finished_at`
- `progress_pct`
- `current_stage`
- `dataset_path`
- `log_path`
- `error_text`

### `voice_lab_state`

Add generator defaults:

- `selected_language`
- `selected_profile_type`
- `selected_revision_id`
- `selected_style_preset`
- `selected_stability`
- `selected_similarity`

## API Shape

### Generator / Library

- `GET /api/voice/lab`
- `PUT /api/voice/lab`
- `POST /api/voice/generate`
- `GET /api/voice/generations`
- `GET /api/voice/generations/{id}`
- `GET /api/voice/audio/{id}`
- `GET /api/voice/audio/{id}/download`

### Quick Clone

- `GET /api/voice/profiles`
- `POST /api/voice/profiles`
- `PUT /api/voice/profiles/{id}`
- `DELETE /api/voice/profiles/{id}`
- `POST /api/voice/profiles/{id}/activate`

### Studio Voice / Training

- `POST /api/voice/training-jobs`
- `GET /api/voice/training-jobs`
- `GET /api/voice/training-jobs/{id}`
- `POST /api/voice/training-jobs/{id}/cancel`

## Guardrails

- No training while live session is active
- No attach generation without active preview session
- No live production selection for `studio_voice` without a published revision
- All generated audio must be durable, playable, and downloadable

## Verification Target

The pass is complete only when:

- backend tests pass
- frontend tests pass
- build passes
- browser verification confirms:
  - language selector visible and functional
  - multi-clone UI usable
  - per-item play/download works
  - attach flow still works
  - training job controls surface correct blocked/runnable state
