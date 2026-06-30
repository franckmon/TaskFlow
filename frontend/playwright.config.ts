import { defineConfig, devices } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const frontendDir = path.dirname(fileURLToPath(import.meta.url));
const projectRoot = path.resolve(frontendDir, '..');
const e2eApiUrl = process.env.E2E_API_URL ?? 'http://127.0.0.1:8000';

process.env.E2E_API_URL = e2eApiUrl;

const e2eEnv = {
  ENVIRONMENT: 'development',
  SECRET_KEY: 'e2e-secret-key',
  ALGORITHM: 'HS256',
  ACCESS_TOKEN_EXPIRE_MINUTES: '30',
  DATABASE_URL: 'sqlite:///./e2e.db',
  BOOTSTRAP_ADMIN_USERNAME: 'admin',
  BOOTSTRAP_ADMIN_PASSWORD: 'admin',
  CORS_ORIGINS: 'http://127.0.0.1:3000,http://localhost:3000',
};

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [['list'], ['html', { open: 'never' }]],
  use: {
    baseURL: 'http://127.0.0.1:3000',
    trace: 'on-first-retry',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'firefox', use: { ...devices['Desktop Firefox'] } },
    { name: 'webkit', use: { ...devices['Desktop Safari'] } },
  ],
  webServer: [
    {
      command: `cd "${projectRoot}" && export PYTHONPATH="${projectRoot}" && .venv/bin/alembic upgrade head && .venv/bin/python scripts/seed_e2e_users.py && .venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000`,
      url: 'http://127.0.0.1:8000/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: e2eEnv,
    },
    {
      command: 'npm run dev -- --host 127.0.0.1 --port 3000',
      url: 'http://127.0.0.1:3000',
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
      cwd: frontendDir,
      env: {
        ...process.env,
        VITE_API_URL: 'http://127.0.0.1:8000',
        VITE_DEV_PROXY_TARGET: e2eApiUrl,
      },
    },
  ],
});
