import { existsSync } from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import { defineConfig, devices } from "@playwright/test";

const webDir = path.dirname(fileURLToPath(import.meta.url));
const backendDir = path.resolve(webDir, "../../backend");
const venvPython = path.join(backendDir, ".venv", "Scripts", "python.exe");
const backendPython = existsSync(venvPython) ? venvPython : "python";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  fullyParallel: false,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["list"], ["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://127.0.0.1:4173",
    trace: "retain-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `"${backendPython}" -m uvicorn carepath.main:app --host 127.0.0.1 --port 8000 --log-level warning`,
      cwd: backendDir,
      url: "http://127.0.0.1:8000/health",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
      env: {
        APP_ENV: "development",
        DATABASE_URL: "sqlite+aiosqlite:///./carepath-e2e.db",
        SECRET_KEY: "e2e-secret-key-at-least-32-characters",
      },
    },
    {
      command: "pnpm preview --host 127.0.0.1 --port 4173 --strictPort",
      url: "http://127.0.0.1:4173",
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});
