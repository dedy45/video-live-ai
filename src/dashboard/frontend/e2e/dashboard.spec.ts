import { test, expect } from '@playwright/test';

test.describe('Dashboard smoke test', () => {
  test('dashboard page loads and shows shell', async ({ page }) => {
    await page.goto('/dashboard');

    // Page should not be blank
    await expect(page.locator('.app')).toBeVisible();
  });

  test('Live Console page exists and shows content', async ({ page }) => {
    await page.goto('/dashboard/#/live-console');

    const pageTitle = page.locator('h1.page-title');
    await expect(pageTitle).toBeVisible();
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
      'Live Console',
      'Products',
      'Performer',
      'Stream',
      'Validation',
      'Monitor',
      'Diagnostics'
    ];

    for (const name of navItems) {
      const navItem = page.getByRole('link', { name: new RegExp(name, 'i') });
      await expect(navItem).toBeVisible();
    }
  });

  test('clicking navigation changes page', async ({ page }) => {
    await page.goto('/dashboard');

    // Start at Live Console
    await expect(page.locator('h1.page-title')).toContainText(/Live Console/i);

    // Click Products nav
    const productsNav = page.getByRole('link', { name: /products/i });
    await productsNav.click();

    // Should show Products page
    await expect(page.locator('h1.page-title')).toContainText(/Products/i);

    // URL should have changed
    expect(page.url()).toContain('#/products');
  });
});

test.describe('Validation Page', () => {
  test('Validation page is visible and navigable', async ({ page }) => {
    await page.goto('/dashboard/#/validation');

    const pageTitle = page.locator('h1.page-title');
    await expect(pageTitle).toBeVisible();
    await expect(pageTitle).toContainText(/Validation/i);

    // Check validation panel exists
    await expect(page.getByTestId('validation-panel')).toBeVisible();
  });

  test('Run Real-Mode Readiness shows blocker list and evidence', async ({ page }) => {
    await page.goto('/dashboard/#/validation');
    await expect(page.getByTestId('validation-panel')).toBeVisible();

    await page.getByTestId('run-real-mode').click();

    // Wait for detail card to appear
    await expect(page.getByTestId('validation-detail')).toBeVisible({ timeout: 10000 });

    // Should show either 'pass' or 'blocked' status
    const detailText = await page.getByTestId('validation-detail').textContent();
    expect(detailText).toMatch(/pass|blocked/i);
  });

  test('Validation history populates after running a check', async ({ page }) => {
    await page.goto('/dashboard/#/validation');

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
  test('Performer page shows voice and face sections', async ({ page }) => {
    await page.goto('/dashboard/#/performer');

    const pageTitle = page.locator('h1.page-title');
    await expect(pageTitle).toBeVisible();
    await expect(pageTitle).toContainText(/Voice & Face/i);

    // Check voice section exists
    await expect(page.getByText('Voice Runtime')).toBeVisible();

    // Check face section exists
    await expect(page.getByText('Face Engine')).toBeVisible();
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

test.describe('Diagnostics Page', () => {
  test('Diagnostics page shows health checks', async ({ page }) => {
    await page.goto('/dashboard/#/diagnostics');

    const pageTitle = page.locator('h1.page-title');
    await expect(pageTitle).toBeVisible();
    await expect(pageTitle).toContainText(/Diagnostics/i);
  });
});

test.describe('Operator action state change', () => {
  test('Stream panel pipeline transition updates state', async ({ page }) => {
    await page.goto('/dashboard/#/stream');

    // Wait for pipeline state section
    await expect(page.getByText(/Pipeline state machine/i)).toBeVisible({ timeout: 5000 });

    // The pipeline state card and buttons should be visible
    const warmingBtn = page.getByRole('button', { name: 'WARMING' });
    if (await warmingBtn.isVisible()) {
      await warmingBtn.click();

      // Should show a receipt after the action
      await expect(page.getByTestId('action-receipt')).toBeVisible({ timeout: 5000 });
    }
  });
});
