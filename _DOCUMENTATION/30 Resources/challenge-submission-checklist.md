---
title: Challenge submission checklist
para: resource
status: active-reference
---

# Challenge submission checklist

- [ ] Working public HTTPS URL in ChatGPT's in-app browser and Chrome WebMCP.
- [x] Public repository with source baseline and visible AGPL-3.0 licence.
- [ ] Public repository final revision with all source, assets, build instructions,
  licence, and visible WebMCP registration code.
- [ ] Public YouTube demo shorter than three minutes with audio.
- [ ] Description explains WebMCP fit, improved experience, human-agent
  collaboration, and implementation.
- [ ] Demo opens with `CONFIRMATION_REQUIRED`, shows visible UI confirmation,
  then shows the agent retry succeeding.
- [ ] Devpost fields and every submitted URL are read back before the
  4 September 2026, 04:00 SGT deadline.

## Proven local receipts

- [x] Chrome 152 with WebMCP enabled exposed all eight registered tools (v2, Playwright, 3 Sep 2026).
- [x] `create_apartment_study` moved the same visible UI to Place.
- [x] `run_solar_analysis` returned `CONFIRMATION_REQUIRED` before the trusted
  resident confirmation action.
- [x] 20 Python, 4 vitest and 6 Playwright tests pass locally (v2).
- [x] Docker image builds, serves, survives kill/restart, runs an analysis (v2).
- [ ] v2 deployed to a public HTTPS URL (the live URL still serves v1).
- [ ] Clean-profile five-screen journey and artifact read-back on the public URL.
