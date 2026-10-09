import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./e2e",
  timeout: 180000,
  workers: 1,
  use: {
    baseURL: "http://127.0.0.1:3000",
    viewport: { width: 1440, height: 1100 },
    trace: "on",
    video: "on",
  },
  reporter: [["list"], ["html", { open: "never" }]],
});
