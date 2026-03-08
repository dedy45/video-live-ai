# Claude Handoff Prompt — Svelte Dashboard Remediation

> Purpose: prompt copy-paste final untuk Claude Opus agar mengerjakan remediation dashboard Svelte dengan disiplin verifikasi yang ketat.
>
> Base plan: [2026-03-08-svelte-dashboard-verification-remediation.md](/c:/Users/dedy/Documents/!fast-track-income/videoliveai/docs/plans/2026-03-08-svelte-dashboard-verification-remediation.md)

## Recommended Use

1. Buka repo `videoliveai`.
2. Berikan prompt di bawah ini ke Claude Opus.
3. Minta Claude bekerja task-by-task, bukan big-bang rewrite.
4. Tolak klaim completion tanpa bukti command output segar.

---

## Copy-Paste Prompt

```text
You are Claude Opus working inside this repository:

C:\Users\dedy\Documents\!fast-track-income\videoliveai

Your job is not to redesign the project. Your job is to complete the remediation work for the partially landed Svelte dashboard migration and prove the result with fresh verification evidence.

Authoritative plan:
- docs/plans/2026-03-08-svelte-dashboard-verification-remediation.md

Related context:
- docs/plans/2026-03-08-svelte-dashboard-rebuild-plan.md
- docs/task_status.md
- docs/workflow.md
- docs/changelogs.md
- src/main.py
- src/dashboard/api.py
- src/face/livetalking_manager.py
- src/dashboard/frontend/

Verified starting state from independent review on 2026-03-08:
- `cd src/dashboard/frontend && npm run build` passes
- `uv run pytest tests -q -p no:cacheprovider` passes with `115 passed`
- `uv run python scripts/verify_pipeline.py` passes with `11/11 layers passed`
- `uv run python -m src.main` serves `/dashboard` from `src/dashboard/frontend/dist`
- `cd src/dashboard/frontend && npm run test` currently fails because no frontend test files exist
- Engine panel currently shows only resolved LiveTalking state, not explicit requested vs resolved fields
- docs are not fully synchronized with the migrated dashboard state

Mission:
- Close the verification gaps so the Svelte dashboard track can move from `PARTIAL` to honestly verifiable.
- Do not claim this migration is complete unless every required verification command has actually passed in your session.

Non-negotiable constraints:
1. Python environment is UV-only. Do not use conda. Do not add conda instructions anywhere.
2. Frontend toolchain may use npm only. Do not introduce pnpm, yarn, turborepo, Next.js, or NestJS.
3. Keep FastAPI as the operator control plane.
4. Keep `external/livetalking/web` as vendor debug-only pages, not the main dashboard.
5. Do not rewrite architecture, routing model, or unrelated subsystems.
6. Do not touch unrelated docs just to make status look nicer.
7. Do not mark anything complete based on assumption, static inspection, or previous agent claims.
8. Use test-first discipline for behavior changes.

Primary outcome required:
- `/dashboard` remains served from the Svelte build
- Engine panel explicitly shows:
  - requested model
  - resolved model
  - requested avatar
  - resolved avatar
- `npm run test` becomes a real and passing frontend gate
- a minimal Playwright smoke test exists and passes
- docs state the truth, not optimism

Required execution order:

Task 1. Expose requested/resolved LiveTalking state from backend
- Read:
  - src/face/livetalking_manager.py
  - src/dashboard/api.py
  - tests/test_livetalking_integration.py
  - tests/test_dashboard.py
- First, add or update failing backend tests for:
  - `/api/engine/livetalking/status`
  - `/api/engine/livetalking/config`
- Those responses must include:
  - `requested_model`
  - `resolved_model`
  - `requested_avatar_id`
  - `resolved_avatar_id`
- Run the targeted backend tests and confirm they fail before implementation.
- Implement the smallest backend change necessary.
- Re-run the targeted backend tests and confirm they pass.

Task 2. Surface requested/resolved state in the Svelte dashboard
- Read:
  - src/dashboard/frontend/src/lib/types.ts
  - src/dashboard/frontend/src/lib/api.ts
  - src/dashboard/frontend/src/components/panels/EnginePanel.svelte
  - src/dashboard/frontend/src/components/panels/ReadinessPanel.svelte
- First, add a failing frontend test for the Engine panel showing requested vs resolved values.
- Then implement the smallest UI change necessary.
- Re-run the targeted frontend test and confirm it passes.

Task 3. Establish a minimal frontend unit test suite
- Add the minimum missing test harness and baseline tests so:
  - `npm run test` is meaningful
  - `App.svelte` shell render is covered
  - API shape parsing is covered
  - Engine panel fallback/requested-vs-resolved rendering is covered
- Do not add a second unit test framework.
- Re-run `npm run test` until it passes.

Task 4. Add a minimal browser smoke test
- Add Playwright config and one smoke spec for `/dashboard`
- This is a smoke test only, not a full E2E suite
- It must verify:
  - dashboard page loads
  - Engine tab/control surface exists
  - at least one readiness indicator exists
- Install Chromium only if needed
- Re-run Playwright until it passes

Task 5. Sync docs with the verified state
- Update only these docs:
  - docs/task_status.md
  - docs/workflow.md
  - docs/changelogs.md
  - docs/plans/2026-03-08-svelte-dashboard-rebuild-plan.md if needed for status note consistency
- Docs must reflect actual verification state from your session, not projected future state

Task 6. Run the final verification gate
- Run every command fresh:
  - `cd src/dashboard/frontend && npm run build`
  - `cd src/dashboard/frontend && npm run test`
  - `cd src/dashboard/frontend && npx playwright test`
  - `uv run pytest tests -q -p no:cacheprovider`
  - `uv run python scripts/verify_pipeline.py`
- Then run:
  - `uv run python -m src.main`
- Manually verify:
  - `http://localhost:8000/dashboard` loads
  - requested vs resolved values are visible in the dashboard
  - vendor debug links are visible
  - no blank page

Forbidden shortcuts:
- Do not skip the failing-test step for Task 1 and Task 2
- Do not say "should pass" or "likely passes"
- Do not update docs before you know the real verification outcome
- Do not paper over missing tests by removing the test script
- Do not declare success if `npm run test` still reports no test files
- Do not claim requested/resolved support if the API or UI still only exposes final resolved values

Stop immediately and report if any of these happen:
- The repo state materially differs from the verified starting state above
- `/dashboard` is no longer served from Svelte build output
- a required change would force a major backend redesign
- Playwright setup would require nonstandard infrastructure beyond a local Chromium install

Required evidence format after each task:
- `Task N status: PASS` or `Task N status: BLOCKED`
- Files changed
- Commands run
- Exact result summary
- Remaining risk, if any

Required final response format:

1. Final verdict
- `COMPLETE` only if every verification command passed
- otherwise `PARTIAL` or `BLOCKED`

2. What changed
- concise summary grouped by backend, frontend, tests, docs

3. Verification evidence
- list every command run
- include whether it passed or failed
- include key counts such as `115 passed`

4. Residual gaps
- anything still not complete
- anything intentionally deferred

If you cannot complete a task, stop at the exact blocker and report it precisely. Do not continue with speculative changes.
```

---

## Notes for Review

- Prompt ini sengaja memaksa Claude untuk membuktikan hasilnya, bukan hanya mengulang klaim agent sebelumnya.
- Prompt ini juga membatasi scope agar tidak melebar ke rewrite arsitektur atau kosmetik dashboard yang tidak penting.
