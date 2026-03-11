import { defineConfig } from '@playwright/test';

const dashboardHost = process.env.DASHBOARD_HOST ?? '127.0.0.1';
const dashboardPort = process.env.DASHBOARD_PORT ?? '8001';
const baseURL = `http://${dashboardHost}:${dashboardPort}`;

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  use: {
    baseURL,
    headless: true,
  },
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },
  ],
  webServer: {
    command: 'cd ../../.. && uv run python -m src.main',
    url: `${baseURL}/api/status`,
    reuseExistingServer: true,
    timeout: 30000,
    env: {
      ...process.env,
      MOCK_MODE: process.env.MOCK_MODE ?? 'true',
      DASHBOARD_HOST: dashboardHost,
      DASHBOARD_PORT: dashboardPort,
    },
  },
});
