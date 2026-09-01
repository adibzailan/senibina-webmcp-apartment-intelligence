---
title: Research and source register
para: resource
status: reference
checked_at: 2026-09-01
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
| [EnergyPlus weather](https://energyplus.net/weather) | Obtain Singapore EPW weather data | Sourced | Record station, period, file/version, and coverage assumptions |

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

## Deferred listing and floorplan research

No universal listing API is accepted for V1. Listing availability and page
structure vary, and server-side arbitrary URL fetching is excluded.

Listing parsing, OneMap and floorplan upload are outside the MVP. They require a
separate accepted trust, licence, retention, and human-verification contract.

## Known source gaps

- Exact unit position, facade, windows, balcony, and internal layout.
- Authoritative building height for every HDB block.
- Equivalent consistent geometry coverage for private condominiums.
- Guaranteed listing availability, reusable listing images, or standardized
  floorplans.

These gaps are product inputs for confirmation or visible uncertainty, not
permission to invent data.
