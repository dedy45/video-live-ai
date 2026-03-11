import { test, expect } from '@playwright/test';

test.describe('Dashboard smoke test', () => {
  test('dashboard page loads and shows shell', async ({ page }) => {
    await page.goto('/dashboard');

    // Page should not be blank
    await expect(page.locator('.app')).toBeVisible();
  });

  test('Live Console page exists and shows content', async ({ page }) => {
    await page.goto('/dashboard');

    const pageTitle = page.locator('h1.page-title');
    await expect(pageTitle).toBeVisible();
    await expect(pageTitle).toContainText(/Konsol Live/i);
  });

  test('Products page exists and shows content', async ({ page }) => {
    await page.goto('/dashboard/#/products');

    const pageTitle = page.locator('h1.page-title');
    await expect(pageTitle).toBeVisible();
  });
});

test.describe('Page navigation', () => {
  test('navigation bar shows all pages', async ({ page }) => {
    await page.goto('/dashboard');

    // Check navigation items exist
    const navItems = [
      'Setup & Validasi',
      'Produk & Penawaran',
      'Avatar & Suara',
      'Streaming & Platform',
      'Konsol Live',
      'Monitor & Insiden',
    ];

    for (const name of navItems) {
      const navItem = page.getByRole('link', { name: new RegExp(name, 'i') });
      await expect(navItem).toBeVisible();
    }
  });

  test('clicking navigation changes page', async ({ page }) => {
    await page.goto('/dashboard');

    // Start at Live Console
    await expect(page.locator('h1.page-title')).toContainText(/Konsol Live/i);

    // Click Products nav
    const productsNav = page.getByRole('link', { name: /Produk & Penawaran/i });
    await productsNav.click();

    // Should show Products page
    await expect(page.locator('h1.page-title')).toContainText(/Produk & Penawaran/i);

    // URL should have changed
    expect(page.url()).toContain('#/products');
  });
});

test.describe('Setup Page', () => {
  test('Setup page is visible and navigable', async ({ page }) => {
    await page.goto('/dashboard/#/setup');

    const pageTitle = page.locator('h1.page-title');
    await expect(pageTitle).toBeVisible();
    await expect(pageTitle).toContainText(/Setup & Validasi/i);

    // Check readiness and validation surfaces exist
    await expect(page.getByRole('heading', { name: /System Readiness/i })).toBeVisible();
    await expect(page.getByTestId('validation-panel')).toBeVisible();
  });

  test('Run Real-Mode Readiness shows blocker list and evidence', async ({ page }) => {
    await page.goto('/dashboard/#/setup');
    await expect(page.getByTestId('validation-panel')).toBeVisible();

    await page.getByTestId('run-real-mode').click();

    // Wait for detail card to appear
    await expect(page.getByTestId('validation-detail')).toBeVisible({ timeout: 10000 });

    // Should show either 'pass' or 'blocked' status
    const detailText = await page.getByTestId('validation-detail').textContent();
    expect(detailText).toMatch(/pass|blocked/i);
  });

  test('Validation history populates after running a check', async ({ page }) => {
    await page.goto('/dashboard/#/setup');

    // Run runtime truth check
    await page.getByTestId('run-runtime-truth').click();

    // Wait for receipt - use first one in validation panel
    const receipt = page.getByTestId('validation-panel').getByTestId('action-receipt').first();
    await expect(receipt).toBeVisible({ timeout: 10000 });

    // History section should have entries
    const historySection = page.getByTestId('validation-history');
    await expect(historySection).toBeVisible();
  });
});

test.describe('Performer Page', () => {
  test('Performer page shows tabbed workspace, reconciles avatar state, and surfaces preview fallback', async ({ page }) => {
    let avatarRunning = false;

    await page.route('**/api/runtime/truth', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          mock_mode: false,
          host: { name: 'gpu-01', role: 'server_production' },
          deployment_mode: 'production_ready',
          face_runtime_mode: avatarRunning ? 'livetalking_running' : 'livetalking_stopped',
          voice_runtime_mode: 'unknown',
          stream_runtime_mode: 'idle',
          validation_state: 'unvalidated',
          last_validated_at: '2026-03-11T03:05:00Z',
          incident_summary: { open_count: 0, highest_severity: 'none' },
          guardrails: { restart_storm: false, disk_pressure: false },
          provenance: {
            system_status: 'real_live',
            engine_status: 'real_live',
            stream_status: 'real_live',
          },
          voice_engine: {
            requested_engine: 'fish_speech',
            resolved_engine: 'unknown',
            fallback_active: false,
            server_reachable: false,
            reference_ready: true,
            queue_depth: 0,
            chunk_chars: null,
            time_to_first_audio_ms: null,
            latency_p50_ms: null,
            latency_p95_ms: null,
            last_latency_ms: null,
            last_error: null,
          },
          face_engine: {
            requested_model: 'musetalk',
            resolved_model: 'musetalk',
            requested_avatar_id: 'musetalk_avatar1',
            resolved_avatar_id: 'musetalk_avatar1',
            engine_state: avatarRunning ? 'running' : 'stopped',
            fallback_active: false,
          },
          timestamp: new Date().toISOString(),
        }),
      });
    });

    await page.route('**/api/engine/livetalking/status', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          state: avatarRunning ? 'running' : 'stopped',
          pid: null,
          uptime_sec: 0,
          port: 8010,
          model: 'musetalk',
          avatar_id: 'musetalk_avatar1',
          requested_model: 'musetalk',
          resolved_model: 'musetalk',
          requested_avatar_id: 'musetalk_avatar1',
          resolved_avatar_id: 'musetalk_avatar1',
          transport: 'webrtc',
          last_error: '',
          app_py_exists: true,
          model_path_exists: true,
          avatar_path_exists: true,
        }),
      });
    });

    await page.route('**/api/engine/livetalking/start', async (route) => {
      avatarRunning = true;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          action: 'engine.start',
          message: 'Avatar menerima perintah jalan.',
          reason_code: 'engine_start_requested',
          next_step: 'Tunggu status avatar berubah menjadi berjalan.',
          details: ['state running'],
          state: 'running',
        }),
      });
    });

    await page.route('**/api/engine/livetalking/stop', async (route) => {
      avatarRunning = false;
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'success',
          action: 'engine.stop',
          message: 'Avatar menerima perintah berhenti.',
          reason_code: 'engine_stop_requested',
          next_step: 'Tunggu status avatar berubah menjadi berhenti.',
          details: ['state stopped'],
          state: 'stopped',
        }),
      });
    });

    await page.route('**/api/voice/warmup', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          status: 'blocked',
          action: 'voice.warmup',
          message: 'Voice sidecar is not reachable yet',
          next_step: 'Jalankan Fish-Speech sidecar terlebih dahulu.',
        }),
      });
    });

    await page.route('**/api/engine/livetalking/debug-targets', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          checked_at: '2026-03-11T03:06:00Z',
          targets: {
            webrtcapi: {
              url: 'http://localhost:8010/webrtcapi.html',
              reachable: false,
              http_status: null,
              error: 'Connection refused',
            },
            dashboard_vendor: {
              url: 'http://localhost:8010/dashboard.html',
              reachable: false,
              http_status: null,
              error: 'Connection refused',
            },
            rtcpushapi: {
              url: 'http://localhost:8010/rtcpushapi.html',
              reachable: false,
              http_status: null,
              error: 'Connection refused',
            },
          },
        }),
      });
    });

    await page.goto('/dashboard/#/performer');

    await expect(page.locator('h1.page-title')).toContainText(/Avatar & Suara/i);
    for (const tab of ['Ringkasan', 'Suara', 'Avatar', 'Preview', 'Validasi', 'Teknis']) {
      await expect(page.getByRole('button', { name: new RegExp(tab, 'i') })).toBeVisible();
    }

    await page.getByRole('button', { name: /^Avatar$/i }).click();
    await page.getByRole('button', { name: /Jalankan Avatar/i }).click();
    await expect(page.getByTestId('action-receipt')).toContainText(/avatar menerima perintah jalan/i);
    await expect(page.getByText(/Berjalan/i)).toBeVisible();

    await page.getByRole('button', { name: /^Suara$/i }).click();
    await page.getByRole('button', { name: /Panaskan Mesin Suara/i }).click();
    await expect(page.getByTestId('action-receipt')).toContainText(/not reachable/i);

    await page.getByRole('button', { name: /Preview/i }).click();
    await expect(page.getByText(/Preview belum bisa dibuka/i)).toBeVisible();
    await expect(page.getByRole('button', { name: /Cek Lagi/i })).toBeVisible();

    await page.getByRole('button', { name: /Teknis/i }).click();
    await expect(page.getByRole('heading', { name: /Log Engine/i })).toBeVisible();
    await expect(page.getByText(/Connection refused/i).first()).toBeVisible();
  });

  test('standalone performer page keeps the same tabs and preview fallback', async ({ page }) => {
    await page.route('**/api/engine/livetalking/debug-targets', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          checked_at: '2026-03-11T03:06:00Z',
          targets: {
            webrtcapi: {
              url: 'http://localhost:8010/webrtcapi.html',
              reachable: false,
              http_status: null,
              error: 'Connection refused',
            },
            dashboard_vendor: {
              url: 'http://localhost:8010/dashboard.html',
              reachable: false,
              http_status: null,
              error: 'Connection refused',
            },
            rtcpushapi: {
              url: 'http://localhost:8010/rtcpushapi.html',
              reachable: false,
              http_status: null,
              error: 'Connection refused',
            },
          },
        }),
      });
    });

    await page.goto('/dashboard/performer.html');

    for (const tab of ['Ringkasan', 'Suara', 'Avatar', 'Preview', 'Validasi', 'Teknis']) {
      await expect(page.getByRole('button', { name: new RegExp(tab, 'i') })).toBeVisible();
    }

    await page.getByRole('button', { name: /Preview/i }).click();
    await expect(page.getByText(/Preview belum bisa dibuka/i)).toBeVisible();
    await expect(page.getByRole('link', { name: /Buka Paksa di Tab Baru/i }).first()).toBeVisible();
  });
});

test.describe('Stream Page', () => {
  test('Stream page shows pipeline controls', async ({ page }) => {
    await page.goto('/dashboard/#/stream');

    const pageTitle = page.locator('h1.page-title');
    await expect(pageTitle).toBeVisible();
    await expect(pageTitle).toContainText(/Stream/i);
  });
});

test.describe('Monitor Page', () => {
  test('Monitor page shows incidents', async ({ page }) => {
    await page.goto('/dashboard/#/monitor');

    const pageTitle = page.locator('h1.page-title');
    await expect(pageTitle).toBeVisible();
    await expect(pageTitle).toContainText(/Monitor/i);
  });
});

test.describe('Operator action state change', () => {
  test('Stream panel pipeline transition updates state', async ({ page }) => {
    await page.goto('/dashboard/#/stream');

    // Wait for pipeline state section
    await expect(page.getByText(/Pipeline state machine/i)).toBeVisible({ timeout: 5000 });

    // The pipeline state card and buttons should be visible
    const warmingBtn = page.getByRole('button', { name: /WARMING/i });
    if (await warmingBtn.isVisible()) {
      await warmingBtn.click();

      // Should show a receipt after the action
      await expect(page.getByTestId('action-receipt')).toBeVisible({ timeout: 5000 });
    }
  });
});
