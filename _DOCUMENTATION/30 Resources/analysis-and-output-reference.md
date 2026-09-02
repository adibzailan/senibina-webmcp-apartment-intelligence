---
title: Analysis and output reference
para: resource
status: current
---

# Analysis and output reference

This reference defines the implemented V1 study and presentation contract.

## Study set

| Study | Consumer question | Proposed calculation | Primary graphic |
| --- | --- | --- | --- |
| Sunpath | Where does the sun travel relative to this home? | Equinox, solstice, and selected-date solar positions | North-aligned 3D sunpath and key positions |
| Shadow | Where does direct sun reach the apartment floor? | Aperture-gated context intersections at 09:00, 12:00, and 15:00 SGT | Horizontal sun-patch map |
| Solar access | For how long can the apartment floor see direct sun through its window? | Four seasonal dates at 30-minute intervals | Floor hours-of-sun colour map |
| Radiation | How much approximate solar exposure reaches the apartment floor through its window? | Up to 256 floor sensors; 12 monthly representative days; aperture- and obstruction-gated DNI plus isotropic DHI through a sampled aperture factor | Horizontal exposure map with numeric legend |

Every study must record north, location, date or analysis period, time zone,
weather source, geometry version, sampling settings, legend, units, assumptions,
uncertainty, and a plain-language finding.

The current deterministic method is `apartment-intelligence-solar-v5`. Its
digest includes the accepted unit-fixture digest, placement transform,
handedness, aperture, weather, method assumptions, and computed results.

Radiation is not interchangeable with daylight, glare, indoor temperature,
cooling load, comfort, or energy consumption. Those require different models
and remain out of V1.

The radiation method excludes glazing transmittance, inter-reflection, internal
partitions, balcony slabs, and overhangs. Diffuse exposure uses an isotropic sky
and a visible sensor-to-aperture configuration factor. It is approximate
interior solar exposure, not a Radiance simulation or certification.

## Five-card graphic system

All PNG artifacts use the same 2:3 portrait canvas at 1600 × 2400 pixels.

1. **Site & Unit** — address context, north, target block/unit, source layers,
   height basis, and confirmed openings.
2. **Sunpath** — solar path, selected dates/times, target orientation, and key
   exposure finding.
3. **Shadow** — comparable shadow evidence for the selected critical period.
4. **Solar Access** — hours-of-sun map, sampling period, legend, and result.
5. **Radiation** — energy map, units, period, EPW source, legend, and result.

The cards are generated from the same scene and result record shown in the
interactive application. AI-generated imagery must not substitute for analysis
graphics. Plain-language copy may be agent-drafted but cannot alter numeric
results, labels, provenance, or uncertainty.

## Download package

| Artifact | Contents |
| --- | --- |
| PNG set | Five standalone 1600 × 2400 cards |
| PDF | The same five compositions in a fixed order with no hidden extra claims |
| ZIP | PNGs, PDF, `.3dm`, and machine-readable provenance/result summary |
| `.3dm` | Metre-unit scene, layers, names, source/confidence metadata, confirmed floor plate/window, horizontal analysis grids, and coloured result meshes |

Required `.3dm` layers are `01_SOURCED_CONTEXT`, `02_INFERRED_MASSING`,
`03_HUMAN_CONFIRMED_UNIT`, `04_GENERATED_ANALYSIS`, and `05_RESULTS`.
The file is a downstream professional artifact; it does not imply that Rhino
created, validated, or certified the analysis.

## Failure and uncertainty presentation

- Missing source data produces an explicit gap, adjustable assumption, or
  blocked analysis—not a guessed authoritative value.
- Unconfirmed target geometry prevents analysis.
- Unavailable weather or failed geometry produces no result card.
- Cached or example output is labelled and cannot be presented as a live run.
- Low-resolution or simplified geometry remains visible in both graphics and
  downloadable provenance.
