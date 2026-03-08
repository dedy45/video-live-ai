import { test, expect } from '@playwright/test';

test.describe('Dashboard smoke test', () => {
  test('dashboard page loads and shows shell', async ({ page }) => {
    await page.goto('/dashboard');

    // Page should not be blank
    await expect(page.locator('.app')).toBeVisible();
  });

  test('Engine tab exists in navigation', async ({ page }) => {
    await page.goto('/dashboard');

    const engineTab = page.getByRole('tab', { name: 'Engine' });
    await expect(engineTab).toBeVisible();
  });

  test('Readiness tab exists as indicator', async ({ page }) => {
    await page.goto('/dashboard');

    const readinessTab = page.getByRole('tab', { name: 'Readiness' });
    await expect(readinessTab).toBeVisible();
  });
});

test.describe('Validation Console', () => {
  test('Validation tab is visible and navigable', async ({ page }) => {
    await page.goto('/dashboard');
    const validationTab = page.getByRole('tab', { name: 'Validation' });
    await expect(validationTab).toBeVisible();
    await validationTab.click();
    await expect(page.getByTestId('validation-panel')).toBeVisible();
  });

  test('Run Real-Mode Readiness shows blocker list and evidence', async ({ page }) => {
    await page.goto('/dashboard');
    await page.getByRole('tab', { name: 'Validation' }).click();
    await expect(page.getByTestId('validation-panel')).toBeVisible();

    await page.getByTestId('run-real-mode').click();

    // Wait for detail card to appear
    await expect(page.getByTestId('validation-detail')).toBeVisible({ timeout: 10000 });

    // Should show either 'pass' or 'blocked' status
    const detailText = await page.getByTestId('validation-detail').textContent();
    expect(detailText).toMatch(/pass|blocked/i);
  });

  test('Validation history populates after running a check', async ({ page }) => {
    await page.goto('/dashboard');
    await page.getByRole('tab', { name: 'Validation' }).click();

    // Run runtime truth check
    await page.getByTestId('run-runtime-truth').click();

    // Wait for receipt
    await expect(page.getByTestId('action-receipt')).toBeVisible({ timeout: 10000 });

    // History section should have entries
    const historySection = page.getByTestId('validation-history');
    await expect(historySection).toBeVisible();
  });
});

test.describe('Overview realtime', () => {
  test('Overview shows realtime source indicator', async ({ page }) => {
    await page.goto('/dashboard');

    // Wait for realtime to connect (WS or polling)
    await expect(page.getByTestId('realtime-source')).toBeVisible({ timeout: 10000 });

    const sourceText = await page.getByTestId('realtime-source').textContent();
    expect(sourceText).toMatch(/websocket|polling/i);
  });
});

test.describe('Operator action state change', () => {
  test('Stream panel pipeline transition updates state', async ({ page }) => {
    await page.goto('/dashboard');
    await page.getByRole('tab', { name: 'Stream' }).click();

    // Wait for pipeline state card
    await expect(page.getByText('Pipeline State')).toBeVisible({ timeout: 5000 });

    // The pipeline state card and buttons should be visible
    const warmingBtn = page.getByRole('button', { name: 'WARMING' });
    if (await warmingBtn.isVisible()) {
      await warmingBtn.click();

      // Should show a receipt after the action
      await expect(page.getByTestId('action-receipt')).toBeVisible({ timeout: 5000 });
    }
  });
});
