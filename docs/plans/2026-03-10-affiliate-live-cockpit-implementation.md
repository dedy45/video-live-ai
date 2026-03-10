# Affiliate Live Cockpit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Evolve the current dashboard into a unified affiliate live cockpit that combines sales assistance, runtime operations, validation, and monitoring for TikTok and Shopee livestream workflows.

**Architecture:** Keep FastAPI as the control plane and the current Svelte dashboard shell, but restructure the frontend around a workflow-centric cockpit and extend backend truth, product, and stream surfaces to support affiliate live operations. Reuse existing truth, readiness, validation, and operator-action contracts wherever possible.

**Tech Stack:** FastAPI, Python, Svelte 5, Vitest, Playwright CLI, Fish-Speech, LiveTalking/MuseTalk, ffmpeg/RTMP.

---

### Task 1: Freeze the new cockpit information architecture

**Files:**
- Modify: `src/dashboard/frontend/src/App.svelte`
- Modify: `src/dashboard/frontend/src/components/layout/PageShell.svelte`
- Test: `src/dashboard/frontend/src/tests/App.test.ts`

**Step 1: Write the failing test**

Add a frontend test asserting the new workflow-centric navigation labels exist.

```ts
it('renders affiliate live cockpit navigation tabs', () => {
  render(App);

  expect(screen.getByRole('tab', { name: 'Live Console' })).toBeInTheDocument();
  expect(screen.getByRole('tab', { name: 'Products & Offers' })).toBeInTheDocument();
  expect(screen.getByRole('tab', { name: 'Voice & Face' })).toBeInTheDocument();
  expect(screen.getByRole('tab', { name: 'Stream & Platform' })).toBeInTheDocument();
  expect(screen.getByRole('tab', { name: 'Validation & Readiness' })).toBeInTheDocument();
  expect(screen.getByRole('tab', { name: 'Monitor & Incidents' })).toBeInTheDocument();
  expect(screen.getByRole('tab', { name: 'Diagnostics' })).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/App.test.ts`
Expected: FAIL because the new labels do not exist yet.

**Step 3: Write minimal implementation**

Update the tab list and routing skeleton only.

- `Overview` → `Live Console`
- `Commerce` → `Products & Offers`
- `Voice` + `Face Engine` → `Voice & Face`
- `Stream` → `Stream & Platform`
- `Validation` → `Validation & Readiness`
- `Monitor` → `Monitor & Incidents`

**Step 4: Run test to verify it passes**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/App.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/App.svelte src/dashboard/frontend/src/components/layout/PageShell.svelte src/dashboard/frontend/src/tests/App.test.ts
git commit -m "feat: adopt affiliate live cockpit navigation"
```

### Task 2: Build the Live Console shell

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/LiveConsolePanel.svelte`
- Modify: `src/dashboard/frontend/src/components/layout/PageShell.svelte`
- Test: `src/dashboard/frontend/src/tests/live-console-panel.test.ts`

**Step 1: Write the failing test**

```ts
it('renders live console sections for current product, script rail, and quick actions', async () => {
  render(LiveConsolePanel);

  expect(await screen.findByText(/live console/i)).toBeInTheDocument();
  expect(await screen.findByText(/current product/i)).toBeInTheDocument();
  expect(await screen.findByText(/script rail/i)).toBeInTheDocument();
  expect(await screen.findByText(/next best action/i)).toBeInTheDocument();
  expect(await screen.findByText(/quick actions/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/live-console-panel.test.ts`
Expected: FAIL because the component does not exist yet.

**Step 3: Write minimal implementation**

Create `LiveConsolePanel.svelte` with static placeholders wired to existing APIs where easy:
- current product summary
- operator alert
- script rail placeholder
- next best action placeholder
- quick action buttons linking to existing voice/stream actions

**Step 4: Run test to verify it passes**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/live-console-panel.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels/LiveConsolePanel.svelte src/dashboard/frontend/src/components/layout/PageShell.svelte src/dashboard/frontend/src/tests/live-console-panel.test.ts
git commit -m "feat: add live console shell"
```

### Task 3: Fix top-level alert alignment with readiness truth

**Files:**
- Modify: `src/dashboard/frontend/src/components/panels/OverviewPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/ReadinessPanel.svelte`
- Test: `src/dashboard/frontend/src/tests/overview-panel.test.ts`

**Step 1: Write the failing test**

```ts
it('shows warning operator alert when readiness is degraded', async () => {
  render(OverviewPanel);
  expect(await screen.findByText(/warning/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/overview-panel.test.ts`
Expected: FAIL because the alert still renders as normal.

**Step 3: Write minimal implementation**

Derive the operator alert from readiness status instead of a disconnected summary.

**Step 4: Run test to verify it passes**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/overview-panel.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels/OverviewPanel.svelte src/dashboard/frontend/src/components/panels/ReadinessPanel.svelte src/dashboard/frontend/src/tests/overview-panel.test.ts
git commit -m "fix: align operator alert with readiness state"
```

### Task 4: Add inline voice test speak interaction

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Modify: `src/dashboard/frontend/src/components/panels/VoicePanel.svelte`
- Modify: `tests/test_dashboard.py`
- Test: `src/dashboard/frontend/src/tests/voice-panel.test.ts`

**Step 1: Write the failing backend test**

```python
@pytest.mark.asyncio
async def test_voice_test_speak_receipt_shape() -> None:
    from src.dashboard.api import voice_test_speak

    result = await voice_test_speak(text="halo operator")
    assert result["status"] in {"success", "blocked", "error"}
    assert "message" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py::test_voice_test_speak_receipt_shape -q -p no:cacheprovider`
Expected: FAIL because the endpoint does not exist.

**Step 3: Write the minimal implementation**

Add a simple operator-safe test endpoint and frontend input/button for:
- inline text input
- `Test Speak` button
- receipt area

Do not overbuild audio playback yet; focus on receipt and functional test path.

**Step 4: Run backend test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py::test_voice_test_speak_receipt_shape -q -p no:cacheprovider`
Expected: PASS

**Step 5: Write the failing frontend test**

Add assertions for input + button + receipt placeholder in `voice-panel.test.ts`.

**Step 6: Run frontend test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/voice-panel.test.ts`
Expected: FAIL

**Step 7: Wire the frontend and re-run**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/voice-panel.test.ts`
Expected: PASS

**Step 8: Commit**

```bash
git add src/dashboard/api.py src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/components/panels/VoicePanel.svelte tests/test_dashboard.py src/dashboard/frontend/src/tests/voice-panel.test.ts
git commit -m "feat: add inline voice test speak control"
```

### Task 5: Unify Voice & Face panel with preview and performer truth

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/PerformerPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/layout/PageShell.svelte`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Test: `src/dashboard/frontend/src/tests/performer-panel.test.ts`

**Step 1: Write the failing test**

```ts
it('renders combined voice and face performer sections', async () => {
  render(PerformerPanel);
  expect(await screen.findByText(/voice and face/i)).toBeInTheDocument();
  expect(await screen.findByText(/voice runtime/i)).toBeInTheDocument();
  expect(await screen.findByText(/face engine/i)).toBeInTheDocument();
  expect(await screen.findByText(/preview/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/performer-panel.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

Create a single panel that composes voice truth plus face engine truth and a preview placeholder/link card.

**Step 4: Run test to verify it passes**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/performer-panel.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels/PerformerPanel.svelte src/dashboard/frontend/src/components/layout/PageShell.svelte src/dashboard/frontend/src/tests/performer-panel.test.ts
git commit -m "feat: combine voice and face into performer panel"
```

### Task 6: Add Run All Checks to validation

**Files:**
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Modify: `src/dashboard/frontend/src/components/panels/ValidationPanel.svelte`
- Test: `src/dashboard/frontend/src/tests/validation-panel.test.ts`

**Step 1: Write the failing test**

```ts
it('renders run all checks action', async () => {
  render(ValidationPanel);
  expect(await screen.findByRole('button', { name: /run all checks/i })).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/validation-panel.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

Add a `Run All Checks` button that sequentially triggers existing validation functions and aggregates receipts.

**Step 4: Run test to verify it passes**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/validation-panel.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/components/panels/ValidationPanel.svelte src/dashboard/frontend/src/tests/validation-panel.test.ts
git commit -m "feat: add run all checks validation action"
```

### Task 7: Fix Diagnostics panel rendering

**Files:**
- Modify: `src/dashboard/frontend/src/components/panels/DiagnosticsPanel.svelte`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Test: `src/dashboard/frontend/src/tests/diagnostics-panel.test.ts`

**Step 1: Write the failing test**

```ts
it('renders diagnostics payload instead of hanging on loading state', async () => {
  render(DiagnosticsPanel);
  expect(await screen.findByText(/system info/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/diagnostics-panel.test.ts`
Expected: FAIL because it remains stuck.

**Step 3: Write minimal implementation**

Fix the diagnostics fetch/parse/render path using the existing backend payload.

**Step 4: Run test to verify it passes**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/diagnostics-panel.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels/DiagnosticsPanel.svelte src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/tests/diagnostics-panel.test.ts
git commit -m "fix: render diagnostics panel from backend payload"
```

### Task 8: Expand backend product model for affiliate workflows

**Files:**
- Modify: `src/commerce/manager.py`
- Modify: `src/dashboard/api.py`
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing test**

```python
def test_products_api_exposes_affiliate_fields() -> None:
    from src.dashboard.api import list_products
    result = asyncio.run(list_products())
    first = result[0]
    assert "affiliate_links" in first
    assert "selling_points" in first
    assert "commission_rate" in first
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k affiliate_fields`
Expected: FAIL

**Step 3: Write minimal implementation**

Extend the product model with additive affiliate-friendly fields and default-safe values.

**Step 4: Run test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k affiliate_fields`
Expected: PASS

**Step 5: Commit**

```bash
git add src/commerce/manager.py src/dashboard/api.py tests/test_dashboard.py
git commit -m "feat: expand product model for affiliate cockpit"
```

### Task 9: Build Products & Offers panel with active product and queue

**Files:**
- Create: `src/dashboard/frontend/src/components/panels/ProductsOffersPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/layout/PageShell.svelte`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Test: `src/dashboard/frontend/src/tests/products-offers-panel.test.ts`

**Step 1: Write the failing test**

```ts
it('renders active product, queue, and affiliate context sections', async () => {
  render(ProductsOffersPanel);
  expect(await screen.findByText(/active product/i)).toBeInTheDocument();
  expect(await screen.findByText(/product queue/i)).toBeInTheDocument();
  expect(await screen.findByText(/commission/i)).toBeInTheDocument();
  expect(await screen.findByText(/affiliate links/i)).toBeInTheDocument();
});
```

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/products-offers-panel.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

Render:
- current active product
- queued products list
- commission summary
- affiliate links by platform
- basic talking points and CTA blocks

**Step 4: Run test to verify it passes**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/products-offers-panel.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels/ProductsOffersPanel.svelte src/dashboard/frontend/src/components/layout/PageShell.svelte src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/tests/products-offers-panel.test.ts
git commit -m "feat: add products and offers cockpit panel"
```

### Task 10: Add active product highlighting and time-on-product summary

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/frontend/src/components/panels/LiveConsolePanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/ProductsOffersPanel.svelte`
- Test: `tests/test_dashboard.py`
- Test: `src/dashboard/frontend/src/tests/products-offers-panel.test.ts`

**Step 1: Write the failing backend test**

Add a test for active-product metadata including `time_on_product_sec`.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k time_on_product`
Expected: FAIL

**Step 3: Write minimal implementation**

Track switch timestamps server-side and expose `time_on_product_sec` in summary/current product surfaces.

**Step 4: Run backend test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k time_on_product`
Expected: PASS

**Step 5: Write the failing frontend test**

Assert active badge and time-on-product display.

**Step 6: Run frontend test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/products-offers-panel.test.ts`
Expected: FAIL

**Step 7: Wire frontend and re-run**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/products-offers-panel.test.ts`
Expected: PASS

**Step 8: Commit**

```bash
git add src/dashboard/api.py src/dashboard/frontend/src/components/panels/LiveConsolePanel.svelte src/dashboard/frontend/src/components/panels/ProductsOffersPanel.svelte tests/test_dashboard.py src/dashboard/frontend/src/tests/products-offers-panel.test.ts
git commit -m "feat: track active product timing in cockpit"
```

### Task 11: Add stream target editing for TikTok and Shopee

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `tests/test_dashboard.py`
- Create: `src/dashboard/frontend/src/components/panels/StreamPlatformPanel.svelte`
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Test: `src/dashboard/frontend/src/tests/stream-platform-panel.test.ts`

**Step 1: Write the failing backend test**

Add a test for reading and updating platform target configuration via API.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k stream_target`
Expected: FAIL

**Step 3: Write minimal implementation**

Expose safe target-config read/update endpoints for:
- TikTok RTMP URL + key
- Shopee RTMP URL + key

Use masked output for stream keys in read responses where appropriate.

**Step 4: Run backend test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k stream_target`
Expected: PASS

**Step 5: Write the failing frontend test**

Assert fields for TikTok and Shopee targets plus save action.

**Step 6: Run frontend test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/stream-platform-panel.test.ts`
Expected: FAIL

**Step 7: Wire frontend and re-run**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/stream-platform-panel.test.ts`
Expected: PASS

**Step 8: Commit**

```bash
git add src/dashboard/api.py tests/test_dashboard.py src/dashboard/frontend/src/components/panels/StreamPlatformPanel.svelte src/dashboard/frontend/src/lib/api.ts src/dashboard/frontend/src/tests/stream-platform-panel.test.ts
git commit -m "feat: add editable tiktok and shopee stream targets"
```

### Task 12: Expand monitor with fuller component list and throughput metrics

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/resources.py`
- Modify: `src/dashboard/frontend/src/components/panels/MonitorPanel.svelte`
- Test: `tests/test_dashboard.py`
- Test: `src/dashboard/frontend/src/tests/monitor-panel.test.ts`

**Step 1: Write the failing backend test**

Assert that monitor/resource surfaces now include upload throughput and more component entries.

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k throughput`
Expected: FAIL

**Step 3: Write minimal implementation**

Add non-breaking metrics fields such as:
- `upload_mbps`
- fuller component health map including `voice`, `stream`, `brain`

**Step 4: Run backend test to verify it passes**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k throughput`
Expected: PASS

**Step 5: Write the failing frontend test**

Assert upload throughput and richer health sections render.

**Step 6: Run frontend test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/monitor-panel.test.ts`
Expected: FAIL

**Step 7: Wire frontend and re-run**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/monitor-panel.test.ts`
Expected: PASS

**Step 8: Commit**

```bash
git add src/dashboard/api.py src/dashboard/resources.py src/dashboard/frontend/src/components/panels/MonitorPanel.svelte tests/test_dashboard.py src/dashboard/frontend/src/tests/monitor-panel.test.ts
git commit -m "feat: expand monitor metrics for cockpit operations"
```

### Task 13: Add product script and objection-handling surfaces

**Files:**
- Modify: `src/dashboard/frontend/src/components/panels/ProductsOffersPanel.svelte`
- Test: `src/dashboard/frontend/src/tests/products-offers-panel.test.ts`

**Step 1: Write the failing test**

Assert sections for selling points, CTA lines, and objection handling.

**Step 2: Run test to verify it fails**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/products-offers-panel.test.ts`
Expected: FAIL

**Step 3: Write minimal implementation**

Add structured sections for:
- selling points
- CTA lines
- objection handling
- compliance notes

**Step 4: Run test to verify it passes**

Run: `cd src/dashboard/frontend && npm run test -- src/tests/products-offers-panel.test.ts`
Expected: PASS

**Step 5: Commit**

```bash
git add src/dashboard/frontend/src/components/panels/ProductsOffersPanel.svelte src/dashboard/frontend/src/tests/products-offers-panel.test.ts
git commit -m "feat: surface affiliate script and objection guidance"
```

### Task 14: Add browser verification for the new cockpit flow

**Files:**
- Modify: `src/dashboard/frontend/package.json` if needed
- Modify: existing Playwright workflow docs only if command names change

**Step 1: Verify with browser flow**

Run real-browser checks for:
- navigation to each new major surface
- Voice inline test speak receipt
- Run All Checks action visibility
- Products & Offers active product + queue
- Stream & Platform config fields
- Diagnostics rendering

**Step 2: Capture evidence**

Use Playwright snapshots for each surface.

**Step 3: Record any bug found and fix via TDD before continuing**

Do not claim browser success without fresh snapshots after fixes.

**Step 4: Commit**

```bash
git add <only files changed during verification fixes>
git commit -m "test: verify affiliate live cockpit flows in browser"
```

### Task 15: Update documentation truthfully after implementation

**Files:**
- Modify: `docs/architecture.md`
- Modify: `docs/workflow.md`
- Modify: `docs/changelogs.md`
- Modify: `docs/task_status.md`
- Modify: `docs/README.md`
- Modify: `docs/ide/ux.md` only if converting findings into status-tracked follow-up notes

**Step 1: Write the failing documentation checklist**

Create a checklist of architectural truths that must now be reflected.

**Step 2: Re-read the final implementation state**

Verify actual menu names, panel responsibilities, and backend truth contracts before editing docs.

**Step 3: Update docs minimally but completely**

Document:
- the new cockpit IA
- flexible operator model
- affiliate product context
- platform-aware stream targets
- new inline operator interactions

**Step 4: Run verification commands**

Run at minimum:
- `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider`
- `cd src/dashboard/frontend && npm run test`
- `cd src/dashboard/frontend && npm run build`
- browser verification for key surfaces

**Step 5: Commit**

```bash
git add docs/architecture.md docs/workflow.md docs/changelogs.md docs/task_status.md docs/README.md
git commit -m "docs: describe affiliate live cockpit architecture"
```
