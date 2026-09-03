import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: ".",
  testMatch: /.*\.spec\.ts/,
  timeout: 120_000,
  retries: 0,
  workers: 1,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  use: {
    baseURL: process.env.AI_BASE_URL || "http://127.0.0.1:8000",
    channel: "chrome",
    launchOptions: { args: ["--enable-features=WebMCP", "--enable-unsafe-webgpu", "--use-gl=angle"] },
    screenshot: "on",
    trace: "retain-on-failure",
  },
  projects: [
    { name: "desktop-1440", use: { viewport: { width: 1440, height: 1000 } } },
    { name: "tablet-1024", use: { viewport: { width: 1024, height: 900 } } },
    { name: "mobile-390", use: { viewport: { width: 390, height: 844 }, isMobile: true, hasTouch: true } },
  ],
});
