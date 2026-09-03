---
title: Challenge submission checklist
para: resource
status: active-reference
---

# Challenge submission checklist

- [x] Working public HTTPS URL: https://apartments.senibina.com.sg (Chrome WebMCP verified via Playwright; ChatGPT desktop in-app browser verified by Adib, 3 Sep ~21:10 SGT: nine tools discovered, three surveys run, study created and staged, CONFIRMATION_REQUIRED refusal captured, human click accepted, confirmed 0.5 m analysis and evidence retrieved, GPT-5.6 Sol).
- [x] Public repository with source baseline and visible AGPL-3.0 licence.
- [ ] Public repository final revision with all source, assets, build instructions,
  licence, and visible WebMCP registration code.
- [ ] Public YouTube demo shorter than three minutes with audio. Master ready: `video/apartment-intelligence-demo/renders/Apartment-Intelligence-Demo-v1.mp4`, 2:03, -16.1 LUFS.
- [x] Description drafted: `10 Projects/2026-webmcp-devpost-writeup.md` (WebMCP fit, two modes, human-agent boundary, build, lessons).
- [x] Demo shows the refusal, the visible click, the agent retry succeeding, and survey mode.
- [ ] Devpost fields and every submitted URL are read back before the
  4 September 2026, 04:00 SGT deadline.

- [x] ChatGPT desktop run also hit the five-per-ten-minutes limit while surveying storey 30; surveys now have their own budget of thirty per window with a countdown in the refusal (3 Sep ~21:30 SGT).

## Proven local receipts

- [x] Chrome 152 with WebMCP enabled exposed all eight registered tools (v2, Playwright, 3 Sep 2026); nine after `survey_unit` was added the same evening.
- [x] `create_apartment_study` moved the same visible UI to Place.
- [x] `run_solar_analysis` returned `CONFIRMATION_REQUIRED` before the trusted
  resident confirmation action.
- [x] 20 Python, 4 vitest and 6 Playwright tests pass locally (v2).
- [x] Docker image builds, serves, survives kill/restart, runs an analysis (v2).
- [x] v2 deployed to a public HTTPS URL: https://apartment-intelligence.onrender.com (3 Sep 2026).
- [x] Public read-back: six Playwright journeys, 0.25 m analysis in 6.2 s, every export.
- [x] 3 Sep 2026 evening, local build: each page export (PDF report, GLB, OBJ, 3DM, ZIP) produced a real file headless; PDF read page by page.
- [x] Three units driven through the eight tools in one page session, each with its own visible click; distinct digests read back.
- [x] Version 0 pushed to `main` 3 Sep 17:14 SGT; six journeys pass against the live URL with `--workers=1` (the server allows one analysis at a time).
- [x] Live grid timings on Render: 0.5 m 4.4 s, 0.25 m 5.4 s, 0.1 m 10.6 s server time, all inside the 15 s budget.
- [x] Live run exposed and fixed a stale-confirmation race (the page re-staged a tool-staged placement after the click); pushed 17:35 SGT.
- [x] `apartments.senibina.com.sg` and `apartment.senibina.com.sg` attached on Render, CNAMEs in Vercel DNS (Codex, 3 Sep ~18:50 SGT). Six journeys pass on `apartments.`, two on `apartment.`, in Chrome. Public resolvers answer Render; one Mac still had the old Vercel answer cached, which is local, not live.
