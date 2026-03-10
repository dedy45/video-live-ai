import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  timeout: 30000,
  use: {
    baseURL: 'http://localhost:8001',
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
    url: 'http://localhost:8001/api/status',
    reuseExistingServer: true,
    timeout: 30000,
  },
});
