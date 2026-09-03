---
title: WebMCP Challenge submission receipts (1–3 September 2026)
para: archive
status: complete
decision_date: 2026-09-03
---

# WebMCP Challenge submission receipts

Dated build, test and deployment receipts gathered during the challenge window.
The live state is owned by `10 Projects/2026-webmcp-challenge-submission.md`;
the current checklist is `30 Resources/challenge-submission-checklist.md`.

## Build diary

- 1 September 2026: v1 public baseline, dependency locks, Dawson fixture,
  application, analysis engine, export pipeline and six WebMCP tools published
  from the Windows VM (see `v1-windows-runtime.md`).
- 3 September 2026, morning: the v2 clean-room rebuild (real apartment walls,
  Ladybug + Radiance, 0.25 m grid, eight WebMCP tools, Docker image) merged to
  `main` with Gate 1 accepted by Adib (see `2026-09-clean-room-reconstruction.md`).
- 3 September 2026, afternoon: v2 live at `apartment-intelligence.onrender.com`
  (Render blueprint, Singapore, 1 CPU / 2 GB). Public readback: six Playwright
  journeys pass, a 0.25 m analysis completes in 6.2 s, every export downloads.
  The Windows VM shut down.
- 3 September 2026, evening: Version 0 polish. Ten-tile development grid with
  pen-and-ink art, address dropdown and storey range, title-case choice labels,
  green confirm, three-dimensional compass, Massing toggle, room labels in the
  scene and on every card, north arrow on every card, Fine 0.1 m / Medium
  0.25 m / Coarse 0.5 m grid, pick-then-Export with a designed PDF report.
  Verified headless: every export produces a real file; a three-unit agent
  sequence through the WebMCP tools; 6 Playwright, 4 vitest, 20 pytest pass.
- 3 September 2026, night: survey mode (`survey_unit`, nine tools) with its own
  budget of thirty per ten minutes; `show_analysis` drives camera, massing and
  map; both senibina hostnames live on Render; ChatGPT desktop agent receipt;
  demo film mastered at 2:03; Devpost submitted about 23:30 SGT.

## v2 release checks — 3 September 2026

- 20 Python tests: closed schemas, cross-session 403, expired 404, stale
  confirmation 409, single-use challenge, determinism, watertight mesh, pvlib
  oracle (0.008°), EPW closure (1.03%).
- 4 reducer parity tests and 6 Playwright journeys (human and WebMCP,
  1440/1024/390) in Chrome 152 with `--enable-features=WebMCP`; eight tools
  discovered natively, nine after `survey_unit` was added.
- Docker compose up, healthz, in-container analysis, kill, up, healthz.
- Render deploy executed the same afternoon; six journeys pass against the
  live URL run serially with `--workers=1`.
- Every page export verified headless (PDF read page by page); a three-unit
  sequence through the tools with one visible click per unit and distinct
  digests read back; horizontal overflow check passes at 390 px after the
  address dropdown fix.
- Live grid timings on Render: 0.5 m 4.4 s, 0.25 m 5.4 s, 0.1 m 10.6 s server
  time, all inside the 15 s budget.
- A stale-confirmation race found only on the live host (a debounced re-stage
  landing after the click) was fixed the same evening.
- The ChatGPT desktop run hit the five-per-ten-minutes limit while surveying;
  surveys were given their own budget of thirty per window with a countdown in
  the refusal.
- `apartments.senibina.com.sg` and `apartment.senibina.com.sg` attached on
  Render with CNAMEs in Vercel DNS. Six journeys pass on `apartments.`, two on
  `apartment.`. One local Mac still had the old Vercel answer cached; public
  resolvers answered Render.
- Not run: axe audit, reduced-motion and 200% zoom checks.

## Agent receipt — 3 September 2026, about 21:10 SGT

ChatGPT desktop in-app browser (GPT-5.6 Sol): nine tools discovered, three
surveys run (NE wing tip Type A storey 12, SE near the core Type B storey 30,
SW wing tip Type C storey 44), study created and staged, `CONFIRMATION_REQUIRED`
refusal captured, human click accepted, confirmed 0.5 m analysis and evidence
retrieved.
