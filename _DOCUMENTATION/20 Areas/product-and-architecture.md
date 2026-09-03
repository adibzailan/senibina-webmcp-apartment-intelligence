---
title: Product and architecture
para: area
status: current
---

# Product and architecture

This document owns Apartment Intelligence's current product and system boundary.

## Product promise

Apartment Intelligence helps a resident ask a practical question before choosing an
existing HDB apartment: what will sunlight and surrounding buildings mean for
this particular home?

It is both a WebMCP Challenge project and a Senibina goodwill project for the
public good. It begins in Singapore, where Senibina practises, with a longer-term
ambition to carry proven methods across ASEAN and other housing contexts.

It translates professional early-stage environmental-study methods into a
consumer journey without hiding the model's simplifications. It is a decision
aid, not a professional, statutory, or valuation report.

## V1 audience and scope

The primary user is a Singapore resident evaluating one HDB apartment. V1 does
not promise coverage for private condominiums because equivalent authoritative
footprint and height data has not been established.

Guaranteed input:

- one address from the frozen Dawson fixture; and
- the apartment storey.

## Human and agent responsibilities

| Actor | Owns | Does not own |
| --- | --- | --- |
| Resident | Apartment choice, target facade, unit, windows, corrections, and visible confirmation | Public-data research or repetitive analysis setup |
| Agent | Research coordination, candidate facts, tool use, analysis sequencing, explanation, and export | Spatial certainty, professional judgement, or confirmation |
| Deterministic engines | Geometry construction, solar position, ray intersection, aggregation, graphics, and files | Meaning, property advice, or authority |

## Five-screen journey

1. **Locate:** pick a development from the grid of ten tiles (SkyVille @
   Dawson is covered; nine are Not Yet Covered), choose the covered address
   from a dropdown and a storey inside the block's range; the precinct opens as
   a translucent north-west axonometric over an OpenStreetMap ground.
2. **Place:** choose the wing and the 4-room stack position (Wing Tip or Near
   the Core, both assumed), the published layout (Type A, B or C), As Published
   or Mirrored, and which assumed openings apply. Room names appear above the
   rooms in the scene.
3. **Confirm:** read the confirmation sentence and click; the click is exchanged
   for a ten-second single-use server challenge.
4. **Analyse:** choose Fine 0.1 m, Medium 0.25 m or Coarse 0.5 m, run
   Ladybug + Radiance, and inspect sunpath, shadow, solar access and radiation
   in the same scene, with a Massing toggle and a three-dimensional compass.
5. **Keep the evidence:** pick a PDF report, GLB, OBJ, 3DM or the full ZIP,
   then Export. The ZIP also carries `cards.svg` and `evidence.json`; agents
   can request any format, PNG included, through `export_study`.

## Information states

| State | Meaning | Example |
| --- | --- | --- |
| Sourced | Directly returned by a named public source | HDB footprint polygon, storey count |
| Inferred | Calculated from sourced facts and a disclosed assumption | Upper-storey plate as the footprint extruded per band |
| Reconstructed | Traced from a published drawing with a stated tolerance | 4R Type A walls and columns (±0.25 m) |
| Assumed | Not on any source; a labelled default the resident can change | Window sill/head, balcony, side windows, storey heights |
| Computed | Produced deterministically by the engine | Sky matrix, intersection matrix, radiation per sensor |
| Human-confirmed | Explicitly checked by the resident | Wing, stack, layout, mirroring, openings |
| Missing | Not established and not safe to infer | Verified Block 87 storey-30 plan and stack |

## System

1. The browser or agent supplies an address and storey through a closed schema.
2. The API resolves them against `data/precinct/dawson-v2.json`, the plate
   recipe and the 4R recipes; it never scrapes or calls an upstream service.
3. Builders turn recipe + placement into one geometry with two meshes: a visual
   GLB with provenance and opacity tokens in node extras (context 0.16, tower
   0.28, home 1.0, glass 0.35) and a watertight analytical mesh containing only
   `blocks_sun` elements.
4. Three.js renders the GLB; the resident confirms by a visible click.
5. `ai_solar` runs Ladybug's Sunpath, a Radiance `gendaymtx` Reinhart sky
   matrix, and `rcontrib` intersection matrices for radiation, direct-sun hours
   on four key dates, and shadow instants, on 0.8 m-plane sensors.
6. The result record (`apartment-intelligence.result.v6`) binds recipe digest,
   placement, weather hash, method version and results into one SHA-256 digest.
7. The API writes byte-stable SVG cards, GLB, OBJ and evidence.json; `rhino3dm`
   writes the layered `.3dm`; the ZIP carries a manifest of hashes.

Rhino, Grasshopper, Revit and Rhino.Compute are not used. Radiance is an
external binary bundled in the Docker image.

## WebMCP contract

| Tool | Purpose | Effect |
| --- | --- | --- |
| `list_supported_homes` | Addresses and storey ranges this build covers | Read-only |
| `create_apartment_study` | Open a study for an address and storey | Creates a study; nothing is confirmed |
| `propose_unit_placement` | Stage wing, stack position, layout, mirroring | Staging only |
| `get_study_state` | Concise state and provenance summary | Read-only |
| `run_solar_analysis` | Run the deterministic analysis; `grid_spacing_m` 0.1, 0.25 or 0.5 | Refused unless the current placement was confirmed by a click |
| `show_analysis` | Switch study, date, hour, camera (precinct, tower, home, plan, north), massing and map in the visible page | Presentation only; every visible control except free orbit, pan and zoom has a tool equivalent |
| `explain_evidence` | Return the provenance record for an item | Read-only, numbers unaltered |
| `export_study` | Trigger downloads from the visible page: glb, obj, 3dm, evidence.json, cards.svg, png, pdf, zip | Adds nothing to the evidence |
| `survey_unit` | Analyse a staged placement for an address, storey, facade, stack, layout without a click | Survey mode: every number labelled `survey_unconfirmed`; no study, no report; listed in the rail as unconfirmed |

There is no confirmation tool. A `confirmed` argument is rejected with 422.
Two modes share one rule: a **study** is confirmed by a person and is the only
source of the report; a **survey** is agent exploration, labelled unconfirmed on
every number, so several units can be compared before one is confirmed.
One study is live per page session. An agent comparing several units runs
them in sequence, each with its own visible click, and keeps its own table;
a 3 September 2026 run did this for three placements in one session.
Tools and controls call the same actions and reducer; a Playwright test drives
both paths and compares state. Registration is on `document.modelContext` with
the `navigator.modelContext` fallback, `readOnlyHint` on the read tools, and
`AbortSignal` cleanup.

## End-state artifacts

- Interactive north-aligned translucent 3D precinct with the confirmed apartment
  (walls, columns, openings, balcony), the sensor grid heatmap, and the sun
  vector for the selected instant.
- `cards.svg`: radiation, four direct-sun-hours maps, sunpath and shadow cards,
  each plan card with room labels and a north arrow; byte-stable and
  digest-bound. PNG is a browser render of it.
- `apartment-intelligence-report.pdf`: a browser-composed report with a paper
  cover, a "Site and unit" page of two fixed views (apartment isometric with
  massing off, tower in its precinct), the cards one per block with page
  footers, and a paper back cover. Presentation only; the digest is printed on
  the cover and every footer. Layout rules live in `DESIGN.md`.
- `scene.glb`, `analytical.obj`, `scene.3dm` (layers context, tower, home,
  glass, analysis; provenance in user strings), `evidence.json`, and
  `bundle.zip` with `manifest.json` hashes.
