# Documentation Index

> Last updated: 2026-03-08
> Scope: source-of-truth map for `videoliveai`

## Root Docs Only

Root `docs/` now keeps only the project-level source of truth:

- [architecture.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/architecture.md)
- [task_status.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/task_status.md)
- [workflow.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/workflow.md)
- [changelogs.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/changelogs.md)
- [contributing.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/contributing.md)
- [security.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/security.md)
- [README.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/README.md)

## Guides

- [LIVETALKING_QUICKSTART.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/LIVETALKING_QUICKSTART.md)
- [MODEL_COMPARISON.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/MODEL_COMPARISON.md)
- [LIVETALKING_WEB_ACCESS_ID.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/guides/LIVETALKING_WEB_ACCESS_ID.md)

## Operations

- [environment_policy.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/operations/environment_policy.md)
- [runtime_paths.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/operations/runtime_paths.md)
- [engine_ports.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/operations/engine_ports.md)
- [process_recovery_policy.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/operations/process_recovery_policy.md)
- [log_surfaces.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/operations/log_surfaces.md)
- [RUNBOOK_INTERNAL_LIVE.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/operations/RUNBOOK_INTERNAL_LIVE.md)

## Specs

- [acceptance_internal_live_v1.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/acceptance_internal_live_v1.md)
- [vertical_slice_v1.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/vertical_slice_v1.md)
- [livetalking_runtime_contract.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/livetalking_runtime_contract.md)
- [model_path_policy.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/model_path_policy.md)
- [avatar_asset_spec.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/avatar_asset_spec.md)
- [audio_asset_spec.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/specs/audio_asset_spec.md)

## Decisions

- [architecture_internal_live.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/decisions/architecture_internal_live.md)
- [dashboard_frontend_strategy.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/decisions/dashboard_frontend_strategy.md)
- [dashboard_ia.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/decisions/dashboard_ia.md)

## Research

- [realism_track_v1.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/research/realism_track_v1.md)
- [realism_scorecard.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/research/realism_scorecard.md)
- [tts_realism_policy.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/research/tts_realism_policy.md)
- [humanization_backlog.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/research/humanization_backlog.md)
- [failure_taxonomy.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/research/failure_taxonomy.md)

## Audits, Plans, Archive

- [AUDIT_CONTEXT_2026-03-07.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/audits/AUDIT_CONTEXT_2026-03-07.md)
- [2026-03-08-dashboard-single-truth-real-validation-plan.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/plans/2026-03-08-dashboard-single-truth-real-validation-plan.md)
- [plans](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/plans)
- [archive](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/archive)

## Current Delivery Status

- Dashboard Svelte operator shell is `LOCAL VERIFIED`
- Dashboard Single Truth Real Validation is `IN PROGRESS`
- Task 1-9 are locally verified; Task 10 is still blocked by missing real product data source

## Placement Rules

- Root project only keeps `README.md`.
- Root `docs/` only keeps cross-cutting source-of-truth documents.
- Use `docs/guides/` for how-to material.
- Use `docs/operations/` for runtime and operational procedures.
- Use `docs/specs/` for contracts, acceptance, and asset specs.
- Use `docs/decisions/` for architecture and UX decisions.
- Use `docs/research/` for realism and exploratory tracks.
- Use `docs/audits/` for audit snapshots.
- Use `docs/archive/` only for superseded or historical material.
