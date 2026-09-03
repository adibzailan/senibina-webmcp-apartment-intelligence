---
title: Clean-room reconstruction (v2)
para: project
status: complete
decision_date: 2026-09-03
branch: v2-clean-room (merged to main on 2026-09-03)
next_action: None here; the live outcome is owned by 2026-webmcp-challenge-submission.md. A later project may plan the Rhino/Revit import path for founder-modelled tower massing.
---

# Clean-room reconstruction handoff

This note is the source truth for the v2 rebuild goal. It was prepared on
3 September 2026 from a read-only inspection of this repository, the local
research rasters under `output/research/`, and primary sources opened that day.
Labels: PROVEN (from this repository), VERIFIED (primary source opened
2026-09-03), INFERRED, PROPOSED, MISSING (needs founder confirmation).

## Founder decisions recorded on 2026-09-03

- Rebuild on branch `v2-clean-room` in this repository. Preserve history and
  the current mock on `main`.
- Analysis engine: Ladybug core, geometry and radiance with the Radiance
  `gendaymtx` binary, run headless. This reproduces the Grasshopper
  Incident Radiation and Direct Sun Hours workflow without Rhino. pvlib is a
  test oracle only.
- Geometry: a coordinate recipe measured from the local WOHA storey plans and
  HDB brochure plans, built into walls, openings, balcony, AC ledge, service
  yard and overhangs by code. Plausible over precise: the apartment must read
  as belonging to the tower, the tower to the precinct.
- Radiation grid: 0.25 m default, 0.5 m fast option, per-room readings. (Superseded 3 Sep evening: Fine 0.1 m, Medium 0.25 m, Coarse 0.5 m.)
- Functionality before UI. DESIGN.md stays the interface authority; no
  redesign in this goal.
- Deployment target: one Docker image, proven locally; Render deployment
  documented, not executed, in this goal.
- Assumptions accepted as labelled defaults: storey height 2.8 m typical and
  3.6 m first storey (HDB Precast Pictorial Guide 2014); storey 30 plan
  inferred from the published 16th–24th storey band; Changi TMYx weather kept
  with citation; only measured coordinates committed, never rasters.

## 1. Product journey (PROVEN)

1. Provide: address and storey from the frozen Dawson fixture.
2. Research and verify: sourced footprint and storey count; inferred height;
   missing unit facts stated.
3. Locate: place a published 4-room plan (Type A, B or C) on a stack position
   of the reconstructed plate, mirror if needed, set openings, confirm by a
   visible click. Agents may propose, never confirm.
4. Explore: sunpath, shadow at three instants, direct-sun hours on four dates,
   annual radiation on a fine floor grid. Same geometry, same digest.
5. Keep: GLB, 3DM, evidence.json, SVG cards (seven in one file), PNG/PDF, manifest, ZIP. (Superseded 3 Sep evening: the page offers a PDF report, GLB, OBJ, 3DM and ZIP.)

## 2. Current repository map (PROVEN)

| Subsystem | Path | Responsibility |
|---|---|---|
| Fixture builder | `data/scripts/build_dawson_fixture.py` | data.gov.sg → local ENU metres, 13 buildings, height = storeys × 3.0 m |
| Unit-plan compiler | `data/scripts/compile_unit_plan.py` | brochure raster → 20-vertex orthogonal polygon scaled to 87 m² |
| API | `server/app/main.py` | 8 routes, in-memory studies, 10 s single-use confirmation challenge |
| Analysis | `server/app/analysis.py` | edge placement, ≤256 sensors (falls back to 1.0 m), custom shadow/access/radiation loops |
| 3DM export | `server/app/export_3dm.py` | five layers, user strings |
| Web | `web/src/App.jsx`, `state.ts`, `Scene.jsx`, `sceneRender.js`, `webmcp.js`, `artifacts.ts` | reducer, Three.js, six WebMCP tools, canvas cards |
| Deployment | `WINDOWS_DEPLOYMENT.md`, `deploy/` | Windows VM, Cloudflare tunnel, Vercel proxy |

Known weaknesses to fix in v2 (PROVEN unless marked):

- Sensor cap of 256 in `derive_plate` silently coarsens the 87 m² plan to
  1.0 m cells.
- Radiation is a custom loop (one day per month, on the hour), not Ladybug's
  sky-matrix method; README overstates Ladybug's role.
- Massing opacity: DESIGN.md says translucent, test pins 0.16, code uses
  0.018/0.04 (`sceneRender.js:23`). Tower is nearly invisible.
- Placement uses the ground footprint, not the tower plate; no walls,
  openings, balcony, ledge or overhang.
- Sunpath card projection uses `1 − altitude/100` (nonstandard).
- Browser acceptance exists only as an ignored CDP script.
- Brochure source URL on assets.hdb.gov.sg does not resolve (VERIFIED); the
  file came from a third-party mirror.
- 87 m² reference area is not on the brochure page; cross-check source is not
  recorded (MISSING).

## 3. Behavioural inventory

| Behaviour | State | Evidence |
|---|---|---|
| Footprints 86–94 | Sourced | HDB Existing Building GeoJSON (VERIFIED) |
| Storeys, units, year | Sourced | HDB Property Information: 86/87/88 = 47 storeys, 320 units, 2015; Block 87 = 160 × 3-room + 160 × 4-room (VERIFIED) |
| Blocks 89–93 | Sourced | SkyTerrace @ Dawson (SCDA), 43 storeys (VERIFIED) |
| Tower height | Inferred | published 147.8 m; HDB typical 2.8 m; repo used 3.0 m (VERIFIED conflict) |
| Sky gardens | Sourced | storeys 3, 14, 25, 36; roof 47 (HDB press release 2016, VERIFIED) |
| Storey 30 plan | Inferred | band 25–35 assumed to mirror published 16–24 (MISSING) |
| 4-room stacks at storey 30 | Missing | storey-5 legend only (MISSING) |
| Unit plans | Published typical | brochure p.5, 4R Type A/B/C share outer boundary (VERIFIED) |
| Interior walls, columns, doors, windows | Reconstructed | readable from plan; positions ±0.3 m; heights assumed |
| Weather | Sourced, no licence | Climate.OneBuilding "All Rights Reserved", citation requested (VERIFIED) |
| Confirmation | Manual | client activation header + server challenge; not proof of a physical click |

## 4. Clean-room architecture (PROPOSED)

```
Browser (React 19 + TypeScript + Three.js)
  reducer (one visible state) · WebMCP adapters · GLB viewer with opacity tokens · export composer
Python service (FastAPI)
  studies · geometry (recipe → GLB + analytical mesh) · solar (Ladybug + gendaymtx)
  evidence (canonical JSON, SHA-256) · exports
Data (frozen, hashed)
  precinct fixture · recipes · calibrations · weather EPW
Docker image: Python 3.13 + Radiance + built web bundle
```

Principles: one geometry, two meshes; every element carries provenance;
deterministic by construction; container-first.

## 5. Contracts

### 5.1 API

| Route | Body | Response | Errors |
|---|---|---|---|
| `GET /api/context` | | fixture version, frame, buildings, recipes | |
| `POST /api/studies` | `{address, storey}` | `{study_id, state, next_action}` + cookie | FIXTURE_NOT_FOUND, STOREY_OUT_OF_RANGE |
| `GET /api/studies/{id}` | | study, placement, plate_summary, provenance | STUDY_EXPIRED |
| `PUT /api/studies/{id}/placement` | `{facade, stack_position, variant, mirrored, openings[]}` | `{state, placement_revision}` | PLACEMENT_INVALID |
| `POST /api/studies/{id}/confirmation-challenge` | `{placement_revision}` + activation header | `{challenge, expires_in_seconds}` | CONFIRMATION_REQUIRED, STALE_CONFIRMATION |
| `POST /api/studies/{id}/confirmation` | `{placement_revision, challenge}` | `{state: ready}` | same |
| `POST /api/studies/{id}/analysis` | | `{state, digest}` | CONFIRMATION_REQUIRED, STALE_CONFIRMATION, ANALYSIS_BUSY, ANALYSIS_TIMEOUT |
| `GET /api/studies/{id}/result` | | result record | EXPORT_NOT_READY |
| `GET /api/studies/{id}/scene.glb` | | visual GLB | |
| `GET /api/studies/{id}/export/{glb,obj,3dm,evidence.json,cards.svg}` | | files | |

Closed schemas (`extra=forbid`); errors are `{error, next_action}`. Limits:
256 KB body, one analysis at a time, five per session per ten minutes, 15 s
worker timeout, 100 live studies, 20 MB export.

### 5.2 WebMCP tools

Register on `document.modelContext` with `navigator.modelContext` fallback,
`AbortSignal` cleanup, `readOnlyHint` on reads (spec draft 2 Sep 2026; Chrome
152 removed the navigator alias; flag `chrome://flags/#enable-webmcp-testing`).

| Tool | Input | Effect |
|---|---|---|
| `list_supported_homes` (read) | | fixture addresses and storey ranges |
| `create_apartment_study` | address, storey | `needs_confirmation` |
| `propose_unit_placement` | study_id, facade, stack_position, variant, mirrored | stages only |
| `get_study_state` (read) | study_id | concise state and provenance summary |
| `run_solar_analysis` | study_id | refused unless confirmed and unchanged |
| `show_analysis` (read) | analysis, time/date, view | presentation only |
| `explain_evidence` (read) | study_id, item | provenance record, numbers unaltered |
| `export_study` | study_id, formats[] | download from visible page |

No confirmation tool. `confirmed: true` as an argument is rejected with 422.

### 5.3 Geometry recipe `apartment-intelligence.recipe.v1`

```
project → block → storey_band → stack → unit_type → variant
element: { id, kind: wall|column|opening|slab|balcony|ledge|overhang|core|void,
           geometry (polyline or rect, metres, plan frame), thickness_m, base_m, height_m,
           blocks_sun: bool, opacity_token,
           source: { state: published|reconstructed|inferred|assumed|resident_confirmed,
                     document, page, calibration_id, confidence_m } }
```

### 5.4 Result `apartment-intelligence.result.v6`

`method_version`, `weather{station, period, sha256}`, `sky{discretisation,
patches}`, `sensors{grid, spacing_m, xyz[], mask[], room_ids[]}`, `sunpath[]`,
`shadow{instants[]}`, `solar_access{date → sensor_hours[]}`,
`radiation{sensor_kwh_m2[], per_room{}, min, avg, max, components[],
limitations[]}`, `provenance[]`, `digest`.

Digest = SHA-256 of canonical JSON of `{recipe_digest, placement,
weather_sha256, method_version, result_without_digest}`.

### 5.5 Obstruction

Neighbours: extruded sourced footprints with the storey-height table,
labelled inferred. Target tower: reconstructed plate per band, sky-garden
voids and slab overhangs. Only `blocks_sun: true` elements enter the
analytical mesh; glazing and railings are excluded.

### 5.6 Evidence and exports

Every displayed number carries `{value, state, source_ref, method,
confidence, limitation}`. Exports embed the same record. GLB is the primary
open format (provenance in node `extras`); OBJ optional; 3DM kept for
professional downstream; SVG cards are byte-deterministic and digest-bound;
PNG and PDF are browser renders of the SVGs and are presentation only;
`manifest.json` lists every file with SHA-256.

## 6. Geometry workflow (PROPOSED)

| Step | Input | Output | Precision |
|---|---|---|---|
| 1 Calibrate WOHA 16–24 plan | 50 m scale bar, north arrow, Block 87 ring | raster → world similarity transform, receipt | ±0.2 m |
| 2 Trace plate | calibrated raster | core, lobby, four wings, eight unit envelopes | ±0.2 m |
| 3 Bands | sky gardens 3, 14, 25, 36, roof 47 | band table; storey 30 in 25–35 | storeys exact, plan inferred |
| 4 Unit type map | storey-5 legend | 3-room and 4-room wings for Block 87 | storey 5 only |
| 5 Variants | brochure p.5 | 4R Type A, B, C recipes, shared envelope | ±0.2 m |
| 6 Openings | glazing lines, photos | window positions; head/sill/width assumed | ±0.3 m |
| 7 Balcony, AC ledge, service yard, shelter | plan | slabs and screens | ±0.3 m |
| 8 Overhangs | sky-garden slabs in photos | projections at 14, 25, 36; depth assumed | |
| 9 Storey heights | 2.8 m typical, 3.6 m first; 147.8 m total | elevation table with ±1.5 m band | |
| 10 Gate 1 | overlays in the browser | founder accept or correct | |

Opacity tokens: context 0.16, target tower 0.28, edges always drawn, home
walls 1.0, floor grids opaque. Test opacity at the mesh, not the helper.
Rasters stay untracked; commit coordinates, calibrations, hashes and refs.

## 7. Research register (all opened 2026-09-03 unless noted)

| Source | URL / path | Fact | Licence / restriction | Unresolved |
|---|---|---|---|---|
| HDB Existing Building | data.gov.sg/datasets/d_16b157c52ed637edd6ba1232e026258d | footprints only | Singapore Open Data Licence v1.0; attribute; no endorsement | |
| HDB Property Information | data.gov.sg/datasets/d_17f5382f26140b1fdae0ba2ef6239d2f | storeys, units, year | same | |
| URA MP2019 Building | data.gov.sg/datasets/d_e8e3249d4433845bdd8034ae44329d9e | alternative footprints | same | no heights |
| Open Data Licence | data.gov.sg/open-data-licence | reuse terms | | |
| OneMap API terms | onemap.gov.sg/legal/apitermsofservice.html | runtime calls allowed with token | attribution | no height/3D API; rate limit inferred |
| HDB BTO Dec 2009 brochure | local `output/research/skyville-dawson-floorplans-2026-09-02/skyville-dawson-bto-brochure.pdf` | 47 storeys, 960 units, sky gardens every 11 storeys, 4R A/B/C plans | HDB copyright; no reproduction without written permission | official URL dead; 87 m² not on page |
| HDB terms of use | hdb.gov.sg/terms-of-use | no redistribution | | derivative status |
| WOHA e-brochure | woha.net/project/skyville-dawson | 85–88 Dawson Road, 12 villages, 960 homes, 2015 | © WOHA | |
| WOHA storey plans | local `output/research/.../architectural-plans/` (from gooood.cn) | plans 3, 4, 5, 14, 15, 16–24, 36, 37, 38–46, roof; 50 m bar; Block 87 legend | © WOHA | no storey 30 |
| HDB press release 3 Nov 2016 | nas.gov.sg archives | sky gardens 3, 14, 25, 36; roof 47 | government | |
| Skyscraper Center / Architectural Record | | 148 m / 147.8 m | | |
| PDA 2016 SkyTerrace | pda.designsingapore.org | Blocks 89–93 SkyTerrace (SCDA), 43 storeys | | |
| HDB Precast Pictorial Guide 2014 | bca.gov.sg PDF | 2.8 m typical, 3.6 m first storey | © HDB | not SkyVille-specific |
| Climate.OneBuilding TMYx | climate.onebuilding.org | Changi EPW | All Rights Reserved; citation Lawrie & Crawley | redistribution basis |
| WebMCP spec | webmachinelearning.github.io/webmcp | `document.modelContext`, registerTool, executeTool, getTools | W3C | |
| Chrome WebMCP docs | developer.chrome.com/docs/ai/webmcp | flag; OT 149–156; navigator alias removed in 152 | | |
| pvlib | pvlib-python.readthedocs.io | NREL SPA default, ±0.0003° | BSD-3 | |

## 8. Repository structure on the branch

```
AGENTS.md README.md DESIGN.md LICENSE THIRD_PARTY_NOTICES.md SECURITY.md
_DOCUMENTATION/          PARA (this note is the active project)
data/precinct/           dawson-v2.json + build script + hashes + storey-height table
data/recipes/            skyville-block87-plate.recipe.json, 4r-type-{a,b,c}.recipe.json, calibrations/
data/weather/            EPW + citation
services/api/            FastAPI app, studies, evidence, exports
packages/geometry/       recipe schema, builders, GLB/OBJ/3DM writers, overlay page
packages/solar/          Ladybug + Radiance wrappers, sky-matrix cache, oracle tests
apps/web/                React + TS, reducer, WebMCP, viewer, cards
tests/                   unit, golden, api, e2e (Playwright), acceptance scripts
deploy/                  Dockerfile, compose.yaml, render.yaml, RUNBOOK.md
```

## 9. Implementation sequence

1. Scaffold, lockfiles, dependency-intake record, Dockerfile with pinned Radiance.
2. Precinct fixture v2 with SkyVille/SkyTerrace labels and storey-height table.
3. Recipe schema, validators, calibration tool with receipts.
4. Trace plate and 4R Type A/B/C recipes; overlay page. Gate 1.
5. Builders: walls, columns, openings, slabs, balcony, ledge, overhangs → GLB + analytical mesh.
6. Solar: Sunpath, Wea, gendaymtx sky matrix, intersection matrix, radiation, direct-sun, shadow instants; oracle tests.
7. Evidence records, canonical JSON, digest.
8. API with sessions, challenge, limits, timeout.
9. Web: reducer, five screens, viewer with opacity tokens, presets, legends, responsive grid.
10. WebMCP registry and parity tests.
11. SVG cards, PNG/PDF, ZIP, manifest.
12. Playwright human and WebMCP journeys in Chrome with the flag; three viewports.
13. Docker build, local run, restart test, Render doc. Gate 2.
14. Docs sync, THIRD_PARTY_NOTICES, attribution.

## 10. Test and acceptance matrix

| Area | Test | Pass |
|---|---|---|
| Solar | altitude/azimuth at 12 instants vs pvlib SPA | ≤ 0.05° |
| Solar | equinox solar noon at 1.296° N | altitude ≥ 88° |
| Solar | unobstructed horizontal annual radiation vs EPW GHI | ≤ 3% |
| Solar | east obstruction | morning hours fall, afternoon unchanged |
| Determinism | same input twice | identical digest, GLB, SVG bytes |
| Geometry | recipe → GLB → reload | watertight analytical mesh; area within 1% |
| Geometry | Type A/B/C | identical envelope |
| Geometry | placement outside plate | PLACEMENT_INVALID |
| API | closed schema, cross-session, expiry, replay, stale revision | 422/404/403/409 |
| API | analysis before confirmation | CONFIRMATION_REQUIRED |
| WebMCP | 8 tools discovered; readOnlyHint on reads | Playwright, Chrome 152 + flag |
| WebMCP | tool vs click | deep-equal reducer state |
| WebMCP | `confirmed: true` argument | 422 |
| Browser | orbit, pan, zoom, reset, presets; 1440/1024/390; no horizontal overflow | screenshots + DOM |
| Evidence | every displayed number has provenance | DOM audit |
| Exports | manifest SHA-256 matches; GLB and SVG stable across runs | hash compare |
| Accessibility | axe, focus order, reduced motion | zero critical |
| Deployment | compose up, healthz, kill, restart, healthz; client backoff message | pass |

## 11. Dependencies (registry, publisher, licence, OSV checked 2026-09-03)

| Package | Version | Licence | Note |
|---|---|---|---|
| fastapi | 0.141.1 | MIT | pin starlette 1.6.0 |
| uvicorn | 0.52.4 | BSD-3 | |
| pydantic | 2.13.5 | MIT | |
| httpx | 0.28.1 | BSD-3 | tests |
| pytest | 9.1.1 | MIT | |
| hypothesis | 6.167.1 | MPL-2.0 | dev |
| numpy | 2.5.2 | BSD-3 | |
| ladybug-core | 0.44.59 | AGPL-3.0 | compatible with repo licence |
| ladybug-geometry | 1.35.4 | AGPL-3.0 | |
| ladybug-radiance | verify at intake | AGPL-3.0 (inferred) | sky matrix, radiation, direct sun |
| Radiance gendaymtx | verify at intake; LBNL/NREL GitHub release; pin SHA-256 | Radiance licence (inferred permissive) | Docker only |
| shapely | 2.1.2 | BSD-3 | |
| trimesh | 5.1.0 | MIT | GLB/OBJ; `ray_triangle` only if used |
| rhino3dm | 8.32.1 | MIT | macOS 14+ wheels |
| pvlib | 0.15.2 | BSD-3 | dev oracle |
| react, react-dom | 19.2.8 | MIT | |
| three / @types/three | 0.185.1 / 0.185.4 | MIT | `three/addons/*` |
| vite / @vitejs/plugin-react | 8.2.2 / 6.1.1 | MIT | |
| typescript | 7.0.2 | Apache-2.0 | proven to build here |
| vitest | 4.1.11 | MIT | |
| @playwright/test | 1.62.1 | Apache-2.0 | browsers via `playwright install` |
| fflate | 0.8.3 | MIT | |
| pdf-lib | 1.17.1 | MIT | unmaintained; alternative @cantoo/pdf-lib 2.9.1 |

Dropped: opencv-python-headless, pyembree, pygltflib, three-mesh-bvh.

## 12. Open items carried into the goal as labelled assumptions

- Storey-height model (2.8/3.6 m). Changes storey-30 elevation by ~6 m
  versus 3.0 m.
- Storey-30 plan basis (band symmetry).
- 4-room stacks at storey 30 (unknown; resident chooses a stack position).
- Weather licence (citation only).
- Derived-plan rights (coordinates only; no rasters).
- Study persistence on restart (in-memory, accepted loss with a clear message).
- Window, balcony and overhang defaults (assumed, labelled, adjustable).

## 13. Goal prompt

The measured copy-paste goal is stored beside this note as
`2026-09-clean-room-reconstruction.goal.txt`.

## 14. Gate 1 record (2026-09-03, founder accepted)

Overlays are rendered by `tests/acceptance/gate1_overlays.py` into `output/gate1/` (ignored;
rasters never committed). Committed artefacts are coordinates only:
`data/recipes/4r-type-{a,b,c}.recipe.json` and `data/recipes/skyville-block87-plate.recipe.json`.

- **4R Type A/B/C over brochure p.5** — envelope, interior walls, columns, shelter, service yard,
  kitchen and windows sit on the drawn walls within about 0.25 m at the published 12.5 m frontage
  scale. Type B removes bedroom 3; Type C merges bedroom 2 into the master suite. Side windows,
  kitchen window, balcony and railings are assumed and toggleable.
- **Block 87 plate over WOHA storey-5 plan** — the reconstructed core, four wings and two slots
  per wing sit on the sourced HDB footprint. Against the raster, the footprint's wing splay differs
  by up to about 15 degrees on one wing pair and the raster's storey-5 (sky-garden) plate is not
  the typical plate; blocks 86, 87 and 88 share the same wing angles in the sourced data, so the
  footprint was kept as authority and the raster treated as a secondary check.
- **Storey heights** — 3.6 m first, 2.8 m typical, 5.6 m at sky-garden storeys 3/14/25/36, 4.0 m
  roof structures; this sums to 147.6 m against the published 147.8 m. Storey 30 floor at 90.4 m.
- **Which wing end is the 4-room stack** is unknown; both `end` and `inner` are offered and
  labelled assumed.

## 15. Build status (2026-09-03)

- Radiance 6.1a (LBNL-ETA 39b99660) and ladybug-radiance 0.2.12 passed intake; both pinned.
- Sunpath within 0.008 degrees of pvlib NREL SPA at twelve instants; unobstructed horizontal
  annual radiation within 1.03% of EPW GHI with the Reinhart sky (Tregenza was 3.1%, so the
  577-patch sky is the default).
- Analysis on the 0.25 m grid (1,270 sensors) runs in about 2.5 s locally; identical inputs give
  identical digest, GLB, OBJ, SVG and evidence.json bytes. 3DM embeds fresh GUIDs.
- 20 Python tests, 4 vitest parity tests and 6 Playwright journeys (Chrome 152, WebMCP flag,
  1440/1024/390) pass. Chrome 152 in this environment did not expose `document.modelContext`
  under Playwright, so tool discovery was verified through the page's own registry; native
  `getTools()` is asserted whenever the API is present.
- Docker: Radiance's Linux build is x86-64 only, so the runtime stage is pinned to linux/amd64.
- Determinism holds per platform: the same inputs give the same digest on repeated runs, but the
  arm64 macOS run and the amd64 Docker run produce different digests (floating-point differences
  in Radiance and numpy). The Docker image is the reference platform for published digests.
- Docker lifecycle (compose up, healthz, in-container 0.25 m analysis in 4.8 s under emulation,
  kill, up, healthz) passed. Render deploy is documented in `deploy/render.yaml`, not executed.
- Not run: axe accessibility audit, reduced-motion check, 200% zoom check, Render deploy.
- Gate 1 accepted by Adib on 2026-09-03 after viewing the 3D apartment in the page ("I accept. This is good"). Apartment and tower recipes stand with their reconstructed/assumed labels.
- Gate 2 readback delivered 2026-09-03; goal complete on branch v2-clean-room, then merged to
  `main` and deployed to Render the same afternoon (see the submission project and
  `20 Areas/security-and-operations.md`). The interface polish that followed is recorded in the
  submission project's current state and in `DESIGN.md`, not here.
