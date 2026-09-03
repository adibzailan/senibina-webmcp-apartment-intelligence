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
deterministic sunpath, shadow, direct-sun and radiation evidence on a 0.25 m
floor grid.

Status (3 September 2026): the v2 clean-room rebuild is on `main`. It runs
locally and as one Docker image. The public hostname
<https://apartment.senibina.com.sg> still serves the earlier v1 build from the
Windows VM; v2 has not been deployed anywhere yet. See
[`_DOCUMENTATION/10 Projects/2026-09-clean-room-reconstruction.md`](_DOCUMENTATION/10%20Projects/2026-09-clean-room-reconstruction.md).

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

## Repository map

| Path | Owns |
| --- | --- |
| `packages/geometry/ai_geometry` | Recipe schema, plate derivation, 4R recipes, builders, GLB/OBJ/3DM writers |
| `packages/solar/ai_solar` | Weather, sunpath, Radiance sky matrix, intersection studies, result record and digest |
| `services/api/ai_api` | FastAPI app, session-bound studies, confirmation challenge, SVG cards, exports |
| `apps/web` | React + TypeScript + Three.js interface and the WebMCP tool registry |
| `data/` | Precinct fixture, recipes, weather, and the retained v1 fixtures |
| `tests/` | Unit and oracle tests, API tests, Playwright journeys, Gate 1 overlay script |
| `deploy/` | Dockerfile, compose, Render blueprint, runbook; v1 Windows and edge-proxy material |

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
`--enable-features=WebMCP` at 1440, 1024 and 390 px widths.

## Docker

```sh
docker build --platform linux/amd64 -f deploy/Dockerfile -t apartment-intelligence:v2 .
docker compose -f deploy/compose.yaml up -d
```

Radiance publishes x86-64 Linux binaries only, so the image is linux/amd64 and
runs under emulation on Apple silicon. Full procedure and limits:
[`deploy/RUNBOOK.md`](deploy/RUNBOOK.md). The Render blueprint in
`deploy/render.yaml` is documented, not deployed. The v1 Windows VM procedure in
[`WINDOWS_DEPLOYMENT.md`](WINDOWS_DEPLOYMENT.md) is retained for the live v1
host and is superseded for new deployments.

## WebMCP

Eight tools register on `document.modelContext` (with the `navigator.modelContext`
fallback for Chrome before 152): `list_supported_homes`, `create_apartment_study`,
`propose_unit_placement`, `get_study_state`, `run_solar_analysis`,
`show_analysis`, `explain_evidence`, `export_study`. There is no confirmation
tool; a `confirmed` argument is rejected, and confirmation is a visible click
exchanged for a ten-second single-use server challenge. Enable
`chrome://flags/#enable-webmcp-testing` and inspect
`document.modelContext.getTools()` in DevTools.
