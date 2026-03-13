# TikTok-First Dashboard Control Plane Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Turn the existing dashboard into the single source of truth for a TikTok-first, single-host live session with durable stream targets, SQLite-backed product CRUD, session product pools, focus control, and operator-managed pause/resume state.

**Architecture:** Keep FastAPI and the Svelte dashboard as the only operator surface, but replace JSON/env/runtime drift with a SQLite-backed control-plane service layer. Implement controller-owned APIs first, then move the frontend to consume those APIs while preserving existing AI Brain and director runtime surfaces.

**Tech Stack:** FastAPI, Python, SQLite, Svelte 5, Vitest, pytest, ffmpeg/RTMP, existing AI Brain/prompt registry modules

---

### Task 1: Freeze the approved design in docs

**Files:**
- Create: `docs/plans/2026-03-12-tiktok-first-dashboard-control-plane-design.md`
- Create: `docs/plans/2026-03-12-tiktok-first-dashboard-control-plane-implementation.md`

**Step 1: Write the design and plan documents**

Document the chosen TikTok-first single-source-of-truth model, the domain entities, the Q&A interrupt policy, and the TDD execution order.

**Step 2: Review the docs against the approved conversation scope**

Check that the docs explicitly capture:

- `1 host GPU`
- `1 active live session`
- `many session_products`
- `one current_focus_product`
- `operator-assisted rotation`
- `Q&A pause/resume`

**Step 3: Proceed directly to implementation**

No code changes yet; the docs become the source of truth for the rest of the work.

### Task 2: Add failing backend tests for SQLite-backed product persistence

**Files:**
- Modify: `tests/test_dashboard.py`
- Modify: `tests/test_layers.py`

**Step 1: Write the failing tests**

Add tests asserting that:

- product records round-trip affiliate/compliance fields through SQLite
- product CRUD endpoints exist and persist changes
- runtime product listing no longer depends on `ProductManager.load_from_json()`

Example test shape:

```python
@pytest.mark.asyncio
async def test_create_product_persists_affiliate_fields() -> None:
    from src.dashboard.api import ProductCreateRequest, create_product, list_products

    created = await create_product(
        ProductCreateRequest(
            name="Lip Cream",
            price=89000,
            category="beauty",
            affiliate_links={"tiktok": "https://example.com"},
            commission_rate=12.5,
            selling_points=["ringan"],
            objection_handling={"aman?": "gunakan sesuai aturan"},
            compliance_notes="hindari klaim medis",
        )
    )

    products = await list_products()
    assert any(p["id"] == created["id"] for p in products)
```

**Step 2: Run the focused tests to verify they fail**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "product_persists or create_product or update_product or delete_product"`  
Expected: FAIL because the endpoints/service do not exist yet.

**Step 3: Do not write implementation yet**

Stay red until the expected failures are visible.

### Task 3: Add failing backend tests for stream target persistence and validation

**Files:**
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing tests**

Add tests asserting that:

- stream targets can be created and listed from SQLite
- TikTok stream target validation uses persisted data instead of raw env-only data
- only one stream target can be active at a time

**Step 2: Run the focused tests to verify they fail**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "stream_target or validate_tiktok_target or activate_stream_target"`  
Expected: FAIL because these APIs do not exist yet.

**Step 3: Keep the tests red**

No production code until the failures are confirmed.

### Task 4: Add failing backend tests for live session, session products, and focus state

**Files:**
- Modify: `tests/test_dashboard.py`

**Step 1: Write the failing tests**

Add tests asserting that:

- only one live session can be active
- a session can accept multiple products
- focus can switch among session products
- pause/resume state is durable

**Step 2: Run the focused tests to verify they fail**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "live_session or session_products or focus_product or pause_rotation"`  
Expected: FAIL because the controller state layer does not exist yet.

**Step 3: Stop at verified red**

Do not implement yet.

### Task 5: Add the SQLite control-plane schema and repository layer

**Files:**
- Modify: `src/data/schema.sql`
- Create: `src/control_plane/store.py`
- Create: `src/control_plane/models.py`
- Modify: `src/data/database.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write the minimal implementation**

Add durable tables for:

- `stream_targets`
- `live_sessions`
- `session_products`
- `session_state`
- `operator_commands`
- `runtime_events`

Extend `products` with serialized affiliate/compliance fields if needed.

Create a repository/service layer that exposes methods like:

```python
create_product(...)
update_product(...)
delete_product(...)
list_products(...)
create_stream_target(...)
activate_stream_target(...)
start_live_session(...)
add_session_products(...)
set_current_focus_product(...)
pause_rotation(...)
resume_rotation(...)
```

**Step 2: Run the focused backend tests**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "product_persists or stream_target or live_session or session_products or pause_rotation"`  
Expected: PASS for the newly added control-plane tests, while unrelated failures are triaged separately.

**Step 3: Refactor only after green**

Keep the repository small and direct; no extra abstraction layers yet.

### Task 6: Wire dashboard API endpoints to the control-plane store

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/main.py`
- Test: `tests/test_dashboard.py`

**Step 1: Add or replace the backend endpoints**

Implement:

- `GET /api/products`
- `POST /api/products`
- `PUT /api/products/{id}`
- `DELETE /api/products/{id}`
- `GET /api/stream-targets`
- `POST /api/stream-targets`
- `PUT /api/stream-targets/{id}`
- `POST /api/stream-targets/{id}/validate`
- `POST /api/stream-targets/{id}/activate`
- `GET /api/live-session`
- `POST /api/live-session/start`
- `POST /api/live-session/stop`
- `POST /api/live-session/products`
- `DELETE /api/live-session/products/{id}`
- `POST /api/live-session/focus`
- `POST /api/live-session/pause`
- `POST /api/live-session/resume`

Return operator receipts with explicit `status`, `message`, and relevant state.

**Step 2: Run focused backend tests**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "create_product or stream_target or live_session or focus_product or pause_rotation"`  
Expected: PASS

**Step 3: Remove duplicated RTMP validation route**

Keep one controller-backed validation surface only.

### Task 7: Adapt runtime truth and status endpoints to the new controller state

**Files:**
- Modify: `src/dashboard/api.py`
- Modify: `src/dashboard/truth.py`
- Test: `tests/test_dashboard.py`

**Step 1: Write the minimal implementation**

Make runtime/status/truth endpoints expose:

- active session summary
- current focus product
- active stream target
- pause reason
- current mode
- command/incident counts where appropriate

**Step 2: Run focused tests**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "runtime_truth or get_status or ops_summary"`  
Expected: PASS

**Step 3: Keep compatibility where safe**

Preserve existing AI Brain and director runtime surfaces unless they conflict with the new controller truth.

### Task 8: Add failing frontend tests for product CRUD and session product pool behavior

**Files:**
- Modify: `src/dashboard/frontend/src/tests/products-offers-panel.test.ts`
- Modify: `src/dashboard/frontend/src/tests/api.test.ts`

**Step 1: Write the failing tests**

Add tests asserting that:

- the panel can display a product catalog plus session pool
- create/update/delete actions call the new APIs
- focus state is read from live session data instead of the old status-only contract

**Step 2: Run the focused frontend tests to verify they fail**

Run: `npm test -- --run src/tests/products-offers-panel.test.ts src/tests/api.test.ts`  
Expected: FAIL because the UI still uses the old APIs and types.

**Step 3: Keep the tests red until verified**

### Task 9: Implement frontend API client and type updates

**Files:**
- Modify: `src/dashboard/frontend/src/lib/api.ts`
- Modify: `src/dashboard/frontend/src/lib/types.ts`
- Test: `src/dashboard/frontend/src/tests/api.test.ts`

**Step 1: Add the minimal client surface**

Add typed helpers for:

- product CRUD
- stream target CRUD/validation/activation
- live session start/stop
- session product assignment
- focus/pause/resume actions

**Step 2: Run focused API tests**

Run: `npm test -- --run src/tests/api.test.ts`  
Expected: PASS

### Task 10: Implement dashboard panels against the new single-source-of-truth APIs

**Files:**
- Modify: `src/dashboard/frontend/src/components/panels/ProductsOffersPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/StreamPanel.svelte`
- Modify: `src/dashboard/frontend/src/components/panels/LiveConsolePanel.svelte`
- Modify: `src/dashboard/frontend/src/App.svelte`
- Test: `src/dashboard/frontend/src/tests/products-offers-panel.test.ts`
- Test: `src/dashboard/frontend/src/tests/stream-panel-layout.test.ts`
- Test: `src/dashboard/frontend/src/tests/live-console-panel.test.ts`

**Step 1: Write the minimal implementation**

Update the panels so they:

- render durable product catalog and session pool data
- allow CRUD and session assignment
- manage persisted TikTok stream targets
- start/stop/pause/resume live session flows from controller APIs

**Step 2: Run focused frontend tests**

Run: `npm test -- --run src/tests/products-offers-panel.test.ts src/tests/stream-panel-layout.test.ts src/tests/live-console-panel.test.ts`  
Expected: PASS

**Step 3: Refactor after green**

Keep UI logic simple and explicit; avoid hidden browser-only state.

### Task 11: Add command journaling and incident logging for new controller actions

**Files:**
- Modify: `src/control_plane/store.py`
- Modify: `src/dashboard/api.py`
- Test: `tests/test_dashboard.py`

**Step 1: Add failing tests**

Add tests asserting that key actions create durable command and runtime-event records.

**Step 2: Run them to confirm failure**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "operator_command or runtime_event"`  
Expected: FAIL

**Step 3: Implement minimal journaling**

Persist command receipts and key events for:

- product CRUD
- stream target activation/validation
- session start/stop
- focus switch
- pause/resume

**Step 4: Re-run the focused tests**

Run: `uv run pytest tests/test_dashboard.py -q -p no:cacheprovider -k "operator_command or runtime_event"`  
Expected: PASS

### Task 12: Run full verification before claiming completion

**Files:**
- Verify only

**Step 1: Run the backend verification suite**

Run: `uv run pytest tests/test_dashboard.py tests/test_layers.py tests/test_config.py tests/test_manage_cli.py -q -p no:cacheprovider`

**Step 2: Run the frontend verification suite**

Run: `npm test -- --run src/tests/api.test.ts src/tests/products-offers-panel.test.ts src/tests/stream-panel-layout.test.ts src/tests/live-console-panel.test.ts`

**Step 3: Run the production build**

Run: `npm run build`

**Step 4: Run manual smoke on the local controller**

Verify:

- `http://127.0.0.1:8001/dashboard`
- product CRUD works
- TikTok stream target can be created and validated
- live session can start with multiple products
- focus switch and pause/resume update the UI

**Step 5: Only report actual results**

If any verification command fails, report the failing command and the blocker instead of claiming completion.
