# Server-Hosted Ops Controller Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Upgrade the existing dashboard into a server-hosted operations controller that keeps livestream execution on the server, exposes honest long-run state, and preserves local validation as the promotion gate.

**Architecture:** Keep the existing FastAPI control plane and Svelte dashboard, but extend them with host-aware truth, incidents, resources, voice operations, and production-safe controller behavior. Local remains the functional validation lab; the server becomes the only execution host for live runs.

**Tech Stack:** FastAPI, Python, Svelte 5, Vitest, Playwright, Fish-Speech sidecar, LiveTalking/MuseTalk, ffmpeg/RTMP, reverse proxy (`Kong`/`Nginx`/`Caddy`)

---

### Task 1: Freeze the New Truth Contract

**Files:**
- Modify: `docs/specs/dashboard_truth_model.md`
- Modify: `src/dashboard/truth.py`
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add a backend test that asserts runtime truth now exposes host/deployment fields and voice queue/incident placeholders.

```python
@pytest.mark.asyncio
async def test_runtime_truth_exposes_ops_contract() -> None:
    from src.dashboard.api import get_runtime_truth

    result = await get_runtime_truth()
    assert "host" in result
    assert "deployment_mode" in result
    assert "incident_summary" in result
    assert "guardrails" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py::test_runtime_truth_exposes_ops_contract -q -p no:cacheprovider`  
Expected: FAIL because the keys do not exist yet.

**Step 3: Write minimal implementation**

Extend `src/dashboard/truth.py` with server-side defaults such as:

```python
"host": {"name": socket.gethostname(), "role": "local_lab"},
"deployment_mode": "cold",
"incident_summary": {"open_count": 0, "highest_severity": "none"},
"guardrails": {"restart_storm": False, "disk_pressure": False},
```

Update the spec doc to match the new contract.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py::test_runtime_truth_exposes_ops_contract -q -p no:cacheprovider`  
Expected: PASS

**Step 5: Commit**

```bash
git add docs/specs/dashboard_truth_model.md src/dashboard/truth.py tests/test_dashboard.py
git commit -m "feat: extend dashboard runtime truth for ops controller"
```

### Task 2: Add Server-Side Ops State and Incident Registry

**Files:**
- Create: `src/dashboard/ops_state.py`
- Create: `src/dashboard/incidents.py`
- Modify: `src/dashboard/api.py`
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add tests for incident creation/listing and server-side deployment mode tracking.

```python
def test_incident_registry_tracks_open_incidents() -> None:
    from src.dashboard.incidents import IncidentRegistry

    reg = IncidentRegistry()
    incident = reg.open("voice.timeout", "error", subsystem="voice")
    assert incident["resolved"] is False
    assert reg.summary()["open_count"] == 1
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py::test_incident_registry_tracks_open_incidents -q -p no:cacheprovider`  
Expected: FAIL because the module/class does not exist yet.

**Step 3: Write minimal implementation**

Create a small in-process registry with methods like:

```python
class IncidentRegistry:
    def open(self, code: str, severity: str, subsystem: str) -> dict[str, Any]: ...
    def resolve(self, incident_id: str) -> None: ...
    def acknowledge(self, incident_id: str, actor: str = "operator") -> None: ...
    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]: ...
    def summary(self) -> dict[str, Any]: ...
```

Expose initial endpoints:

- `GET /api/incidents`
- `POST /api/incidents/{id}/ack`

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "incident or runtime_truth"`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/ops_state.py src/dashboard/incidents.py src/dashboard/api.py tests/test_dashboard.py
git commit -m "feat: add dashboard ops state and incident registry"
```

### Task 3: Add Resource and Restart Visibility

**Files:**
- Create: `src/dashboard/resources.py`
- Modify: `src/dashboard/truth.py`
- Modify: `src/dashboard/api.py`
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add a test that resource metrics and restart counters appear in truth and the ops summary endpoint.

```python
@pytest.mark.asyncio
async def test_ops_summary_exposes_resource_and_restart_state() -> None:
    from src.dashboard.api import get_ops_summary

    result = await get_ops_summary()
    assert "resource_metrics" in result
    assert "restart_counters" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py::test_ops_summary_exposes_resource_and_restart_state -q -p no:cacheprovider`  
Expected: FAIL because the endpoint does not exist yet.

**Step 3: Write minimal implementation**

Create lightweight resource probes and counters:

```python
def get_resource_metrics() -> dict[str, Any]:
    return {"cpu_pct": 0.0, "ram_pct": 0.0, "disk_pct": 0.0, "vram_pct": None}
```

Expose:

- `GET /api/resources`
- `GET /api/ops/summary`

Make sure truth includes these structures even before production wiring is complete.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "ops_summary or resources"`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/resources.py src/dashboard/api.py src/dashboard/truth.py tests/test_dashboard.py
git commit -m "feat: expose ops summary and resource metrics"
```

### Task 4: Make Voice Operations First-Class

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/truth.py`
- Modify: `src/voice/runtime_state.py`
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add tests for voice warmup, queue clear, and voice truth metrics.

```python
@pytest.mark.asyncio
async def test_voice_warmup_receipt_shape() -> None:
    from src.dashboard.api import voice_warmup

    result = await voice_warmup()
    assert result["status"] in {"success", "blocked", "error"}
    assert "message" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py::test_voice_warmup_receipt_shape -q -p no:cacheprovider`  
Expected: FAIL because the endpoint does not exist yet.

**Step 3: Write minimal implementation**

Add endpoints:

- `POST /api/voice/warmup`
- `POST /api/voice/queue/clear`
- `POST /api/voice/restart`

Extend voice runtime state with fields like:

```python
queue_depth: int = 0
chunk_chars: int | None = None
time_to_first_audio_ms: float | None = None
latency_p50_ms: float | None = None
latency_p95_ms: float | None = None
```

Every action returns an operator receipt with explicit status and message.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "voice_warmup or voice_local_clone or runtime_truth"`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/api.py src/dashboard/truth.py src/voice/runtime_state.py tests/test_dashboard.py
git commit -m "feat: add voice operations and truth metrics"
```

### Task 5: Add Production Validation Gates

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/readiness.py`
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing test**

Add tests for the new validation gates:

```python
@pytest.mark.asyncio
async def test_audio_chunking_smoke_endpoint_shape() -> None:
    from src.dashboard.api import validate_audio_chunking_smoke

    result = await validate_audio_chunking_smoke()
    assert result["status"] in {"pass", "fail", "blocked", "error"}
    assert "checks" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py::test_audio_chunking_smoke_endpoint_shape -q -p no:cacheprovider`  
Expected: FAIL because the endpoint does not exist yet.

**Step 3: Write minimal implementation**

Add endpoints:

- `POST /api/validate/audio-chunking-smoke`
- `POST /api/validate/stream-dry-run`
- `POST /api/validate/resource-budget`
- `POST /api/validate/soak-sanity`

Each endpoint should reuse `record_validation(...)` and return explicit blockers where appropriate.

**Step 4: Run focused tests**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "validate_"`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/api.py src/dashboard/readiness.py tests/test_dashboard.py
git commit -m "feat: add production validation gates for ops controller"
```

### Task 6: Extend Frontend Types and API Client

**Files:**
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Modify: `src/dashboard/frontend/src/tests/truth-bar.test.ts`
- Modify: `src/dashboard/frontend/src/tests/validation-panel.test.ts`

**Step 1: Write the failing test**

Update frontend tests to expect new truth fields and new validation buttons.

```ts
it('shows host role and deployment mode in the truth bar', async () => {
  render(TruthBar);
  pushSnapshot({
    truth: {
      host: { name: 'gpu-01', role: 'server_production' },
      deployment_mode: 'ready',
    },
  });
  expect(await screen.findByText(/gpu-01/i)).toBeInTheDocument();
});
```

**Step 2: Run tests to verify they fail**

Run: `cd src/dashboard/frontend && npm run test -- truth-bar.test.ts validation-panel.test.ts`  
Expected: FAIL because the UI and types do not know these fields yet.

**Step 3: Write minimal implementation**

Extend types and API exports to include:

- `OpsSummary`
- `Incident`
- `ResourceMetrics`
- `VoiceEngineTruth` expanded fields
- new API methods for incidents, resources, ops summary, and voice actions

**Step 4: Run tests to verify they pass**

Run: `cd src/dashboard/frontend && npm run test -- truth-bar.test.ts validation-panel.test.ts`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/lib/types.ts src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/tests/truth-bar.test.ts src/dashboard/frontend/src/tests/validation-panel.test.ts
git commit -m "feat: extend dashboard frontend contracts for ops controller"
```

### Task 7: Add Ops Summary Panel

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/OpsSummaryPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/layout/PageShell.svelte`
- Create: `src/dashboard/frontend/src/tests/ops-summary-panel.test.ts`

**Step 1: Write the failing test**

```ts
it('renders core ops summary metrics', async () => {
  render(OpsSummaryPanel);
  expect(await screen.findByText(/overall status/i)).toBeInTheDocument();
  expect(await screen.findByText(/restart count/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- ops-summary-panel.test.ts`  
Expected: FAIL because the panel does not exist yet.

**Step 3: Write minimal implementation**

Create a panel that reads `getOpsSummary()` and renders:

- overall status
- deployment mode
- voice/face/stream health
- uptime
- restart count
- last incident severity
- resource pressure summary

Mount it near the top of `Overview`.

**Step 4: Run test to verify it passes**

Run: `cd src/dashboard/frontend && npm run test -- ops-summary-panel.test.ts`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels/OpsSummaryPanel.svelte src/dashboard/frontend/src/components/layout/PageShell.svelte src/dashboard/frontend/src/tests/ops-summary-panel.test.ts
git commit -m "feat: add ops summary panel"
```

### Task 8: Add Voice Panel and Expand Validation Console

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/VoicePanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/ValidationPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/common/TruthBar.svelte`
- Create: `src/dashboard/frontend/src/tests/voice-panel.test.ts`
- Modify: `src/dashboard/frontend/src/tests/validation-panel.test.ts`

**Step 1: Write the failing tests**

```ts
it('renders voice engine truth and operator actions', async () => {
  render(VoicePanel);
  expect(await screen.findByText(/requested engine/i)).toBeInTheDocument();
  expect(await screen.findByText(/warmup voice/i)).toBeInTheDocument();
});
```

```ts
it('renders voice local clone and stream dry-run validation actions', async () => {
  render(ValidationPanel);
  expect(await screen.findByText(/voice local clone/i)).toBeInTheDocument();
  expect(await screen.findByText(/stream dry run/i)).toBeInTheDocument();
});
```

**Step 2: Run tests to verify they fail**

Run: `cd src/dashboard/frontend && npm run test -- voice-panel.test.ts validation-panel.test.ts`  
Expected: FAIL because the panel/buttons do not exist yet.

**Step 3: Write minimal implementation**

Add `VoicePanel` with:

- requested/resolved engine
- fallback badge
- server reachability
- reference readiness
- queue depth
- last latency
- p50/p95
- operator buttons wired to API receipts

Expand `ValidationPanel` with the new gate buttons and grouped readiness labels.

**Step 4: Run tests to verify they pass**

Run: `cd src/dashboard/frontend && npm run test -- voice-panel.test.ts validation-panel.test.ts`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels/VoicePanel.svelte src/dashboard/frontend/src/components/panels/ValidationPanel.svelte src/dashboard/frontend/src/components/common/TruthBar.svelte src/dashboard/frontend/src/tests/voice-panel.test.ts src/dashboard/frontend/src/tests/validation-panel.test.ts
git commit -m "feat: add voice panel and production validation controls"
```

### Task 9: Add Incident Panel and Resource-Focused Monitor

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/IncidentsPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/MonitorPanel.svelte`
- Create: `src/dashboard/frontend/src/tests/incidents-panel.test.ts`

**Step 1: Write the failing test**

```ts
it('renders incident rows with severity and ack action', async () => {
  render(IncidentsPanel);
  expect(await screen.findByText(/critical/i)).toBeInTheDocument();
  expect(await screen.findByText(/acknowledge/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- incidents-panel.test.ts`  
Expected: FAIL because the panel does not exist yet.

**Step 3: Write minimal implementation**

Create a panel that loads `getIncidents()` and supports `ackIncident(id)`.

Refocus `MonitorPanel` toward:

- component health
- resource pressure
- recent incidents
- recent chat as secondary information

**Step 4: Run tests to verify they pass**

Run: `cd src/dashboard/frontend && npm run test -- incidents-panel.test.ts`  
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels/IncidentsPanel.svelte src/dashboard/frontend/src/components/panels/MonitorPanel.svelte src/dashboard/frontend/src/tests/incidents-panel.test.ts
git commit -m "feat: add incident panel and resource monitor"
```

### Task 10: Update Architecture and Operations Docs

**Files:**
- Modify: `README.md`
- Modify: `docs/architecture.md`
- Modify: `docs/workflow.md`
- Modify: `docs/decisions/architecture_internal_live.md`
- Modify: `docs/security.md`
- Modify: `docs/README.md`

**Step 1: Write the failing doc check**

Create a manual checklist entry that fails if docs still claim `localhost` as the only operator model.

```text
- [ ] README no longer frames /dashboard as localhost-only
- [ ] architecture doc states server-hosted operator model
- [ ] security doc requires reverse proxy auth/TLS for production
```

**Step 2: Run the doc grep check**

Run: `rg -n "localhost:8000/dashboard|No auth system|only operator UI" README.md docs/architecture.md docs/workflow.md docs/decisions/architecture_internal_live.md docs/security.md`  
Expected: hits that must be reviewed and updated.

**Step 3: Write minimal documentation updates**

Document:

- local truth-lab role
- server-hosted production role
- reverse proxy requirement
- browser disconnect does not stop stream
- operator SOP for preflight, dry-run, live, and incident response

**Step 4: Re-run the doc grep check**

Run: `rg -n "localhost:8000/dashboard|No auth system|only operator UI" README.md docs/architecture.md docs/workflow.md docs/decisions/architecture_internal_live.md docs/security.md`  
Expected: only intentional references remain.

**Step 5: Commit**

```bash
git add README.md docs/architecture.md docs/workflow.md docs/decisions/architecture_internal_live.md docs/security.md docs/README.md
git commit -m "docs: update architecture and ops guidance for server-hosted dashboard"
```

### Task 11: Full Verification

**Files:**
- No code changes required

**Step 1: Run backend verification**

Run: `uv run pytest tests -q -p no:cacheprovider`  
Expected: PASS

**Step 2: Run frontend unit verification**

Run: `cd src/dashboard/frontend && npm run test`  
Expected: PASS

**Step 3: Run frontend build**

Run: `cd src/dashboard/frontend && npm run build`  
Expected: PASS

**Step 4: Run browser smoke**

Run: `cd src/dashboard/frontend && npx playwright test`  
Expected: PASS

**Step 5: Run local truth-lab checks**

Run:

```bash
uv run python scripts/check_real_mode_readiness.py --json
uv run python scripts/manage.py validate fish-speech
uv run python scripts/manage.py serve --real
```

Expected:

- readiness reports ready or explicit blockers
- Fish-Speech validation reports honest pass/block status
- dashboard opens with extended ops truth

**Step 6: Commit verification artifacts if needed**

```bash
git add .
git commit -m "test: verify server-hosted ops controller"
```

---

Plan complete and saved to `docs/plans/2026-03-10-server-hosted-ops-controller-implementation.md`. Two execution options:

**1. Subagent-Driven (this session)** - I dispatch fresh subagent per task, review between tasks, fast iteration

**2. Parallel Session (separate)** - Open new session with executing-plans, batch execution with checkpoints

**Which approach?**
