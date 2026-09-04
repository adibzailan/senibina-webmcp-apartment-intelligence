# Apartment Intelligence

Apartment Intelligence is both a WebMCP Challenge project and a Senibina
goodwill project for the public good. It brings early-stage architectural solar
analysis to a Singapore resident evaluating an existing HDB apartment.

We entered architecture because we love buildings, drawing, and 3D modelling.
This project asks how those same tools can help residents evaluate the
environmental conditions of a home empirically and objectively, with evidence,
provenance, and uncertainty kept visible.

The guaranteed demonstration starts with 87 Dawson Road and storey 30. An
agent resolves the bundled public context, the resident places and confirms a
published typical 4-room plan, with real walls, columns, openings and balcony,
inside a reconstructed Block 87 plate, and Ladybug + Radiance produce
deterministic sunpath, shadow, direct-sun and radiation evidence on a 0.1,
0.25 or 0.5 m floor grid, with per-room readings.

Status (4 September 2026): Version 0, built for the OpenAI WebMCP Challenge
and submitted on 3 September 2026; extended-close additions (delegation, section
cut, isometric view) on 4 September. The build on `main` is live at
<https://apartments.senibina.com.sg> (one Docker container on Render,
Singapore, rebuilt from `deploy/render.yaml` on every push).

## What the page does

1. **Locate.** A grid of ten HDB developments, each drawn as a pen-and-ink tile
   (`apps/web/public/projects/`). SkyVille @ Dawson is covered; the other nine
   are labelled Not Yet Covered. Below the grid the study rail offers the
   covered address as a dropdown and a storey field that shows the block's
   range.
2. **Place.** Eight outlined 4-room slots on the tower (four wings, wing tip or
   near the core), the published layout (Type A, B or C), a mirrored-plan
   toggle, and the assumed windows, balcony and railings in a folded list.
3. **Confirm.** A green button and a plain sentence. A tool cannot do this.
   Beneath it, a second button lets the resident delegate: for ten minutes, up
   to five placements staged in this study (by them or by their agent) are
   confirmed without another click. Every such result is labelled confirmed
   under your delegation rather than confirmed by you, the rail shows the uses
   and minutes left, and a Revoke button takes the permission back.
4. **Analyse.** Choose a measuring grid (Fine 0.1 m, Medium 0.25 m, Coarse
   0.5 m) and run. Sunpath, shadow, solar access and radiation share one 3D
   scene with room names floating above each room, a three-dimensional compass,
   an OpenStreetMap ground, and a Massing toggle that fades the tower away. A
   result opens in the Isometric camera (a steep view from the south-west) with
   the Section toggle on, which slices the apartment's walls 1.2 m above the
   floor so the floor colours read from any angle; both are ordinary buttons.
5. **Keep the evidence.** Pick a PDF report, GLB, OBJ, 3DM, or the full ZIP,
   then one Export button. The PDF carries a paper cover, a fixed apartment
   isometric and tower view, one drawing card per block with north arrow and
   room labels, page footers with the digest, and a paper back cover.

## Public-interest research

Apartment Intelligence begins in Singapore because this is where Senibina
practises and can evaluate the work responsibly. Its longer-term hypothesis is
that useful architectural knowledge about existing homes should not remain
available only to professionals: residents should be able to understand
sunlight, obstruction, environmental exposure, and the provenance and
uncertainty behind each conclusion.

The Dawson study is one deliberately bounded beginning. Future research may
reconstruct and validate reference floor plans for a wider subset of Singapore
housing, creating a transparent and reusable public-interest knowledge base.
Any reconstructed plan must retain its source, method, confidence, and limits;
it must never be presented as an authoritative unit survey or verified stack
without supporting evidence.

If the approach survives local scrutiny, the ambition is to extend the practice
across ASEAN and, eventually, other housing contexts globally. Singapore remains
the first case study, not a claim of official status or government endorsement.

## Product boundary

- V1 is an HDB-first consumer decision aid, not a professional certification or
  statutory compliance service.
- Public records provide footprints and storey counts. The 4-room Type A/B/C
  plans are traced from the published SkyVille @ Dawson brochure into coordinate
  recipes; the Block 87 upper-storey plate is reconstructed from the sourced
  footprint. Wing, stack position, layout, mirroring and openings are chosen and
  confirmed by the resident and labelled reconstructed or assumed.
- Ladybug (core, geometry, radiance) drives Radiance `gendaymtx` and `rcontrib`
  headlessly; there is no Rhino, Grasshopper, Revit or Rhino.Compute. Three.js
  renders the browser scene. `rhino3dm` writes the `.3dm` export.
- The runtime uses a frozen, attributed Dawson fixture and Changi TMYx weather;
  it has no listing scraper, floorplan upload, OneMap dependency, database,
  account, or LLM.
- Results distinguish sourced, inferred, reconstructed, assumed, computed and
  human-confirmed information, and every export carries the same record.

## How this was made

Most of this repository was dictated, not typed. Two weeks before the
challenge closed, an accident left the author with a wrist too painful to
type with, so the briefs were spoken (Wispr Flow into Codex),
Codex wrote the code, and the work went round in a loop: review every screen,
every number, every export and every claim in these documents, send back what
was wrong, repeat. That is a different way of working. The person reads less
code and judges more results; the agent runs the work; the person keeps the
decisions, the product boundary and the evidence rules. We cannot vouch for
every line the way a hand-written codebase would let us, and we say so; we can
vouch for what the application does, because that is what was reviewed. The
same division of labour is what the product asks of its own users: agents
explore, people vouch.

## Repository map

| Path | Owns |
| --- | --- |
| `packages/geometry/ai_geometry` | Recipe schema, plate derivation, 4R recipes, builders, GLB/OBJ/3DM writers |
| `packages/solar/ai_solar` | Weather, sunpath, Radiance sky matrix, intersection studies, result record and digest |
| `services/api/ai_api` | FastAPI app, session-bound studies, confirmation challenge, SVG cards, exports |
| `apps/web` | React + TypeScript + Three.js interface and the WebMCP tool registry |
| `data/` | Precinct fixture, recipes, weather, and the retained v1 fixtures |
| `tests/` | Unit and oracle tests, API tests, Playwright journeys, Gate 1 overlay script |
| `deploy/` | Dockerfile, compose, Render blueprint, runbook; `deploy/archive/` keeps retired v1 host material |

## Documentation

Repository knowledge follows PARA. Start at
[`_DOCUMENTATION/README.md`](_DOCUMENTATION/README.md).
The interface, architectural graphics, and evidence exports follow the
repository-local [`DESIGN.md`](DESIGN.md).

Founder-only competition evaluation and deployment notes live under the
Git-ignored `private/` directory. Ignored files are local working material and
are not backed up by Git.

## Local development

Prerequisites: CPython 3.13, Node 22, and Radiance 6.1a (LBNL-ETA release
`39b99660`) unzipped into `.tools/radiance` (ignored) or pointed to by
`RADIANCE_PATH`. Install only from the committed locks:

```sh
python3.13 -m venv .venv
.venv/bin/pip install -r requirements.lock.txt
.venv/bin/pip install --no-deps -e .
npm --prefix apps/web ci
npm --prefix apps/web run build
```

Run at `http://127.0.0.1:8000`:

```sh
.venv/bin/uvicorn ai_api.main:app --host 127.0.0.1 --port 8000
```

Verify with:

```sh
.venv/bin/python -m pytest tests/unit tests/api -q
npm --prefix apps/web test
(cd tests/e2e && npm ci && npx playwright test)
```

The Playwright journeys use installed Google Chrome 152 with
`--enable-features=WebMCP` at 1440, 1024 and 390 px widths. Point them at a
different port with `AI_BASE_URL=http://127.0.0.1:8001`.

## Docker

```sh
docker build --platform linux/amd64 -f deploy/Dockerfile -t apartment-intelligence:v2 .
docker compose -f deploy/compose.yaml up -d
```

Radiance publishes x86-64 Linux binaries only, so the image is linux/amd64 and
runs under emulation on Apple silicon. Full procedure and limits:
[`deploy/RUNBOOK.md`](deploy/RUNBOOK.md). The Render blueprint in
`deploy/render.yaml` is the live deployment.

## WebMCP

Nine tools register on `document.modelContext` (with the `navigator.modelContext`
fallback for Chrome before 152): `list_supported_homes`, `create_apartment_study`,
`propose_unit_placement`, `get_study_state`, `run_solar_analysis`,
`show_analysis`, `explain_evidence`, `export_study`, `survey_unit`. There is no
confirmation tool; a `confirmed` or `delegate` argument is rejected, and
confirmation is a visible click exchanged for a ten-second single-use server
challenge.

The resident may also delegate. One visible click on "Let my agent confirm"
grants a standing permission bound to the study and the session: ten minutes,
up to five placements, revocable with a click. Under it, `propose_unit_placement`
comes back already confirmed with `confirmation.kind = delegated`, and the
result, its provenance table and its digest carry `resident_delegated` instead
of `resident_confirmed`. The grant itself needs the click (`X-User-Activation:
trusted`), so an agent cannot give itself the permission; it can only ask the
resident for it. The five-analyses-per-ten-minutes budget is unchanged.
`show_analysis` drives camera (`precinct`, `tower`, `home`, `isometric`, `plan`,
`north`), massing, map and the `section` cut.

Two modes, one rule. **Study**: the resident confirms the unit they will live in
with a click; results are labelled human-confirmed and only this path produces
the report and the digest-bound bundle. **Survey**: `survey_unit` lets an agent
analyse any staged placement without a click, so it can compare several units
in a row; every number comes back labelled `survey_unconfirmed`, no study is
created, and no report can be made from it. Agents explore, people vouch. Enable
`chrome://flags/#enable-webmcp-testing` and inspect
`document.modelContext.getTools()` in DevTools.

### Checking the tool surface

Three checks, from cheapest to most complete:

- **DevTools.** On the live page, `document.modelContext.getTools().map(t => t.name)`
  lists the nine tools. Without the Chrome flag the page still registers them
  on `window.__aiTools` for tests, and the masthead says so.
- **Playwright.** `tests/e2e/journeys.spec.ts` runs the WebMCP journey: discovery,
  `create_apartment_study`, a staged placement, the refusal before the click,
  the click, `run_solar_analysis`, `get_study_state`, `explain_evidence`,
  `show_analysis`.
- **A multi-unit agent run.** `survey_unit` compares several placements in
  one page session with no click; each reply is labelled unconfirmed and
  carries the surveys left in the ten-minute window. A 3 September 2026 run in
  the ChatGPT desktop app's built-in browser surveyed three placements (NE wing
  tip Type A on storey 12, SE near the core Type B on storey 30, SW wing tip
  Type C on storey 44), chose one, staged it, was refused, waited for the
  click, then ran and explained the confirmed study.
