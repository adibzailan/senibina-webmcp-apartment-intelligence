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

1. **Locate:** enter a Dawson address and storey; the precinct opens as a
   translucent north-west axonometric.
2. **Place:** choose the wing, the 4-room stack position (wing tip or near the
   core, both assumed), the published layout (Type A/B/C), mirroring, and which
   assumed openings apply.
3. **Confirm:** read the confirmation sentence and click; the click is exchanged
   for a ten-second single-use server challenge.
4. **Analyse:** run Ladybug + Radiance on a 0.1, 0.25 or 0.5 m floor grid and
   inspect sunpath, shadow, solar access and radiation in the same scene.
5. **Export:** download GLB, OBJ, 3DM, SVG cards, evidence.json, ZIP, and
   presentation PNG/PDF renders.

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
| `run_solar_analysis` | Run the deterministic analysis | Refused unless the current placement was confirmed by a click |
| `show_analysis` | Switch study, date, hour and camera in the visible page | Presentation only |
| `explain_evidence` | Return the provenance record for an item | Read-only, numbers unaltered |
| `export_study` | Trigger downloads from the visible page | Adds nothing to the evidence |

There is no confirmation tool. A `confirmed` argument is rejected with 422.
Tools and controls call the same actions and reducer; a Playwright test drives
both paths and compares state. Registration is on `document.modelContext` with
the `navigator.modelContext` fallback, `readOnlyHint` on the read tools, and
`AbortSignal` cleanup.

## End-state artifacts

- Interactive north-aligned translucent 3D precinct with the confirmed apartment
  (walls, columns, openings, balcony), the sensor grid heatmap, and the sun
  vector for the selected instant.
- `cards.svg`: radiation, four direct-sun-hours maps, sunpath and shadow cards,
  byte-stable and digest-bound; PNG and PDF are browser renders of it.
- `scene.glb`, `analytical.obj`, `scene.3dm` (layers context, tower, home,
  glass, analysis; provenance in user strings), `evidence.json`, and
  `bundle.zip` with `manifest.json` hashes.
