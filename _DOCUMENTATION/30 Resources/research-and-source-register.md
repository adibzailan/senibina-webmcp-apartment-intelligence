---
title: Research and source register
para: resource
status: reference
checked_at: 2026-09-03
---

# Research and source register

This register records the proposed sources and what each can support. It does
not guarantee availability, licence suitability, schema stability, or product
coverage; those require fresh implementation-time verification.

## Public context

| Source | Proposed use | Evidence class | Important boundary |
| --- | --- | --- | --- |
| [HDB Existing Building](https://data.gov.sg/datasets/d_16b157c52ed637edd6ba1232e026258d/view) | Obtain HDB building footprint polygons | Sourced | Footprint is building context, not exact facade openings or unit layout |
| [HDB Property Information](https://data.gov.sg/datasets/d_17f5382f26140b1fdae0ba2ef6239d2f/view) | Obtain block, street, and maximum floor level | Sourced | Building height remains inferred unless a direct height source is established |
| [Climate.OneBuilding.Org TMYx](https://climate.onebuilding.org) | Singapore Changi 486980 TMYx 2011–2025 EPW | Sourced | Cite Lawrie & Crawley; no standalone licence published |
| HDB press release, 3 Nov 2016 (NAS archives) | Sky gardens at storeys 3, 14, 25, 36; roof garden at 47 | Verified secondary | Storey heights remain assumed |
| Architectural Record / Skyscraper Center | SkyVille @ Dawson tower height 147.8 m | Verified secondary | Used only to reconcile the assumed height model |
| [HDB Precast Pictorial Guide 2014](https://www.bca.gov.sg) | 2.8 m typical and 3.6 m first-storey floor-to-floor | Reference | Not SkyVille-specific |

Proposed derived height is `storeys × disclosed floor-to-floor assumption`.
This is inferred and adjustable, never authoritative building height.

## Analysis and geometry libraries

| Source | Proposed use | Evidence class | Important boundary |
| --- | --- | --- | --- |
| [Ladybug Tools](https://www.ladybug.tools/ladybug.html) | Sunpath, shadow, solar-access, and radiation concepts | Reference | Product methods must name the exact implemented library and version |
| [ladybug-core](https://www.ladybug.tools/ladybug-core/docs/) | EPW parsing and solar positions | Generated from sourced weather | Does not establish input geometry accuracy |
| [ladybug-geometry](https://www.ladybug.tools/ladybug-geometry/docs/) | Headless geometry and ray-intersection operations | Generated | Validate coordinate, tolerance, mesh, and performance limits |
| [Three.js ExtrudeGeometry](https://threejs.org/docs/#api/en/geometries/ExtrudeGeometry) | Browser massing from verified footprint rings | Generated | Three.js renders; it does not improve source-data accuracy |
| [rhino3dm](https://developer.rhino3d.com/guides/opennurbs/what-is-rhino3dmio/) | Write layered `.3dm` files without running Rhino | Generated export | Packaging preserves geometry and metadata; it does not make inference authoritative |
| [ladybug-radiance](https://github.com/ladybug-tools/ladybug-radiance) 0.2.12 | Sky matrix via `gendaymtx`; intersection matrices via `rcontrib` | Computed | Requires a Radiance installation; no inter-reflections |
| [Radiance](https://github.com/LBNL-ETA/Radiance) 6.1a (39b99660) | `gendaymtx`, `oconv`, `rcontrib` | Computed | x86-64 Linux and macOS builds only; pinned by SHA-256 |
| [pvlib](https://pvlib-python.readthedocs.io) 0.15.2 | NREL SPA oracle for sunpath tests | Development only | Never in the runtime |
| [WebMCP spec](https://webmachinelearning.github.io/webmcp) and [Chrome WebMCP docs](https://developer.chrome.com/docs/ai/webmcp) | `document.modelContext` registration, flag, origin trial | Reference | Navigator alias removed in Chrome 152 |

## Published drawings

| Source | Implemented use | Evidence class | Important boundary |
| --- | --- | --- | --- |
| [SkyVille @ Dawson sales brochure](https://assets.hdb.gov.sg/residential/buying-a-flat/finding-a-flat/sales-brochure/skyville-dawson.pdf) (Dec 2009), page 5 | 4R Type A/B/C recipes: walls, columns, openings, wet zone, kitchen, service yard traced at the published 12.5 m frontage scale (±0.25 m) | Published typical reference, then reconstructed geometry | Not a verified Block 87/storey-30 dwelling; sills, side windows, kitchen window, balcony and railings are assumed; official URL was dead on 2 Sep 2026 |
| WOHA storey plans (via gooood.cn; storeys 3, 4, 5, 14, 15, 16–24, 36, 37, 38–46, roof) | Block 87 wing/slot layout and Gate 1 cross-check | Published, © WOHA | No storey-30 plan; wing splay differs from the HDB footprint by up to 15°, footprint kept as authority |

Only coordinates, calibrations, hashes and references are tracked. Brochure and
WOHA rasters and overlay diagnostics are never committed.

## Deferred listing and floorplan research

No universal listing API is accepted for V1. Listing availability and page
structure vary, and server-side arbitrary URL fetching is excluded.

Listing parsing, OneMap and floorplan upload are outside the MVP. They require a
separate accepted trust, licence, retention, and human-verification contract.

## Known source gaps

- Verified stack assignment, exact unit position, facade, windows, balcony, and internal layout.
- Authoritative building height for every HDB block.
- Equivalent consistent geometry coverage for private condominiums.
- Guaranteed listing availability, reusable listing images, or standardized
  floorplans.

These gaps are product inputs for confirmation or visible uncertainty, not
permission to invent data.
