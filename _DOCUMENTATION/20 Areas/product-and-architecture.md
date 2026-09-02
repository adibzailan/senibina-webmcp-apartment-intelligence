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

1. **Provide the apartment:** select or enter a Dawson address and storey.
2. **Research and verify:** review candidate address, building, height basis,
   surroundings, weather source, missing facts, and confidence.
3. **Locate the home:** inspect translucent approximate massing and confirm the
   target facade, storey, adjustable floor-plate width and depth, and window.
4. **Explore the sun:** view sunpath, shadow, solar-access, and radiation studies
   in the same scene with plain-language findings.
5. **Keep the evidence:** export five graphics, a PDF, a ZIP, and a layered
   `.3dm` for downstream professional use.

## Information states

| State | Meaning | Example |
| --- | --- | --- |
| Sourced | Directly returned by a named public source | HDB footprint polygon |
| Inferred | Calculated from sourced facts and a disclosed assumption | Height from storeys × floor-to-floor value |
| Generated | Produced deterministically by the application | Extruded massing or radiation mesh |
| Human-confirmed | Explicitly checked by the resident | Target facade and window positions |
| Missing | Not established and not safe to infer | Exact unit layout without a floorplan |

## Proposed system

1. The browser or agent supplies an address and storey through a closed schema.
2. The backend resolves these against the bundled Dawson fixture and Singapore
   weather file; it does not scrape listings or call a runtime upstream API.
3. A canonical scene record stores footprint rings, coordinate reference,
   north, base elevation, height basis, source, confidence, and the derived,
   resident-confirmed approximate floor plate and aperture.
4. Three.js extrudes and renders the same verified scene record in the browser.
5. The resident corrects and confirms the target unit geometry through a visible
   first-party action.
6. Ladybug's Python libraries calculate solar positions and geometry-based
   environmental results from the confirmed scene.
7. The application creates same-size analysis graphics and plain-language
   findings from the deterministic result record.
8. `rhino3dm.py` writes the massing, target annotations, metadata, analysis
   grids, and coloured result meshes into a downloadable `.3dm`.

Three.js is the browser renderer; Rhino is not required to display the model.
The application has no remote CAD computation service: Three.js, Ladybug
geometry, and `rhino3dm.py` cover the complete v1 runtime.

## Draft WebMCP contract

| Tool | Purpose | State effect |
| --- | --- | --- |
| `create_apartment_study` | Resolve a bundled Dawson address and storey and open Research and Verify | Creates `needs_confirmation` |
| `propose_unit_location` | Stage facade, storey, unit-zone, and opening candidates in the visible scene | Remains `needs_confirmation` |
| `get_study_state` | Read provenance, missing information, state, and the next human action | Read-only |
| `run_solar_analysis` | Run selected deterministic studies over a confirmed scene and period | `ready` to `analysing` to `complete` |
| `show_analysis` | Focus the visible interface on one completed study and date/time | Changes presentation, not evidence |
| `export_study` | Package completed artifacts in requested supported formats | Adds export records without changing analysis |

The study state is:

`draft → needs_confirmation → ready → analysing → complete`

`run_solar_analysis` rejects any study whose target unit has not been confirmed
through the visible first-party interface. Confirmation is not a WebMCP tool and
cannot be supplied as a Boolean argument. Manual UI and WebMCP actions call the
same application functions and update the same visible state.

The visible click is exchanged for a short-lived, revision-bound, single-use
server challenge. Replays and static activation headers cannot confirm a study.

Tool results stay concise and never return full geometry. Confirmation binds the
visible proposal revision and canonical scene digest; stale confirmation is
rejected.

## End-state artifacts

- Interactive north-aligned translucent 3D context with the confirmed apartment
  floor plate, window aperture, and horizontal analysis overlays.
- Five 1600 × 2400 portrait PNG cards: Site & Unit, Sunpath, Shadow, Solar
  Access, and Radiation.
- One combined PDF containing the same five compositions.
- One ZIP containing PNG, PDF, structured provenance, and `.3dm` outputs.
- One metre-unit layered `.3dm` containing sourced, inferred, generated, and
  human-confirmed geometry plus analysis meshes and object metadata.
