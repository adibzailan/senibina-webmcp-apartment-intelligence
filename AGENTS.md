# Apartment Intelligence Repository Guidance

## Scope

Apartment Intelligence is a WebMCP Challenge project for consumer-level
environmental due diligence on existing Singapore HDB apartments. Preserve the distinction
between public records, inference, generated geometry, human confirmation,
implemented behavior, and validated analysis.

## Repository layout (v2)

- `packages/geometry/ai_geometry`, `packages/solar/ai_solar`, `services/api/ai_api`
  are the Python runtime; `apps/web` is the browser; `tests/` holds unit, API,
  Playwright and acceptance checks; `deploy/` holds the Docker image and runbook.
- Geometry is recipes (coordinates with source states), never committed rasters.
- Radiance is an external pinned binary; there is no Rhino, Grasshopper, Revit
  or Rhino.Compute anywhere in the runtime.

## Documentation authority

- Start at `_DOCUMENTATION/README.md`.
- `DESIGN.md` is the authority for the live interface, architectural graphics,
  evidence exports, and visual-evaluation standards.
- `10 Projects` owns the finite challenge-submission outcome and exactly one
  non-empty scalar `next_action`.
- `20 Areas` owns current product, architecture, security, and operations truth.
- `30 Resources` advises but does not override an Area or Project owner.
- `40 Archives` preserves completed, superseded, historical, and proof material.
- Keep active owners present-tense; do not turn them into development diaries.

## Product and evidence boundary

- Use the founder-approved product title `Apartment Intelligence`.
- V1 is HDB-only. Do not imply equivalent coverage for private apartments.
- The reproducible MVP is the Dawson precinct fixture centred on 87 Dawson Road,
  postal 141087, with storey 30 as the golden demonstration.
- Never present an inferred height, unit position, facade, window, view, or
  environmental result as authoritative source data.
- Analysis graphics must be deterministic computed output, not AI-generated
  imagery or fabricated evidence.
- Do not describe the product as an official valuation, compliance, daylight
  certification, energy rating, or professional architectural report.

## Human-agent boundary

- The agent may research, populate candidate facts, invoke valid WebMCP tools,
  coordinate analysis, explain evidence, and export completed results.
- The human confirms the target unit, facade, windows, and other spatial facts
  unavailable from authoritative data.
- Human confirmation occurs through a visible first-party interface action. A
  tool argument such as `confirmed: true` never constitutes confirmation.
- WebMCP and manual UI actions must update the same visible application state.

## Security and repository safety

- Do not implement generic server-side URL fetching or listing scraping.
- Treat listing content, uploads, tool arguments, model metadata, and geometry
  as untrusted input.
- Keep credentials, competition tactics, secret deployment configuration, and
  operational receipts under ignored local storage and out of Git history.
- Before adding a dependency, model, binary, toolchain item, or external data
  package, perform the required same-day dependency-intake review.
- Preserve unrelated work. Do not reset, clean, stash, broadly stage, commit,
  push, publish, or deploy without explicit authority.
