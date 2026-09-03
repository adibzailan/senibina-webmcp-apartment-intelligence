---
title: Analysis and output reference
para: resource
status: current
---

# Analysis and output reference

This reference defines the v2 study and presentation contract.

## Study set

| Study | Consumer question | Calculation | Primary graphic |
| --- | --- | --- | --- |
| Sunpath | Where does the sun travel relative to this home? | Ladybug Sunpath (NOAA): day arcs for 21 Mar, 21 Jun, 22 Sep, 21 Dec and hourly analemmas | Stereographic sunpath card and sun vector in the scene |
| Shadow | Is the floor in direct sun at this instant? | `rcontrib` boolean intersection per sensor for 16 instants (four dates × 09:00, 12:00, 15:00, 17:00) | Lit/shaded sensor map and lit fraction |
| Solar access | For how long does the floor see direct sun? | Half-hour sun vectors on four key dates, `rcontrib` intersection, hours per sensor | Hours-of-sun heatmap per date |
| Radiation | How much annual solar exposure reaches the floor? | `gendaymtx` Reinhart sky (577 patches, direct + diffuse) × cosine-weighted `rcontrib` intersection matrix; ground patches at 0.2 reflectance | Annual kWh/m² heatmap with min/avg/max and per-room table |

Sensors sit on a 0.25 m plan grid (0.5 m in fast mode) at 0.8 m above the
finished floor, inside the rooms of the placed unit and outside walls, columns,
the household shelter and the AC ledge. The analytical mesh holds every
`blocks_sun` element: neighbour towers (sourced footprints extruded to the
assumed height model), the target plate per storey band with sky-garden voids
and slab overhangs, the home storey's plate minus the unit envelope, and the
unit's own walls, columns, slabs and balcony. Glazing is transparent.

The method version is `apartment-intelligence-solar-v6-ladybug-radiance`. The
digest is the SHA-256 of the canonical JSON of recipe digest, placement,
weather hash, method version and the result body. Identical inputs give
identical digests and identical GLB, OBJ, SVG and evidence.json bytes on the
same platform; arm64 macOS and amd64 Docker differ in floating point, so the
Docker image is the reference platform for published digests.

Oracles: sun position within 0.008° of pvlib's NREL SPA at twelve instants;
unobstructed horizontal annual radiation within 1.03% of the EPW global
horizontal sum.

Radiation is not daylight, glare, temperature, cooling load, comfort or
energy. There are no inter-reflections, no glazing transmittance, and the
upper-storey plate, heights, openings and balcony are inferred or assumed.

## Cards

`cards.svg` stacks the radiation heatmap, one direct-sun-hours map per key
date, the sunpath diagram and the shadow-instant table. It is generated
server-side with fixed number formatting and no timestamps, so it is
byte-stable and digest-bound. PNG and PDF (1600 × 2400 pages, Site & Unit page
first from the live canvas) are browser renders of the same SVG and are
presentation only.

## Download package

| Artifact | Contents |
| --- | --- |
| `scene.glb` | Visual scene; every node carries element id, kind, source state, confidence, document, opacity token |
| `analytical.obj` | The watertight obstruction mesh used by Radiance |
| `scene.3dm` | Metre-unit meshes on layers `context`, `tower`, `home`, `glass`, `analysis` with provenance user strings; embeds fresh GUIDs, so not byte-stable |
| `evidence.json` | The full result record, canonical JSON |
| `cards.svg` | Digest-bound evidence cards |
| `bundle.zip` | All of the above plus `manifest.json` with SHA-256 per file (fixed 1980 timestamps) |

## Failure and uncertainty presentation

- Unconfirmed or stale placement returns `CONFIRMATION_REQUIRED` or
  `STALE_CONFIRMATION`; analysis never runs on it.
- A busy engine returns `ANALYSIS_BUSY`; a run over 15 s returns
  `ANALYSIS_TIMEOUT` with the advice to use the 0.5 m grid.
- Every displayed number sits beside a disclosure of method, sources and
  limitations; exports carry the same record.
