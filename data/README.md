# Data

## Precinct fixture (v2)

`precinct/dawson-v2.json` is the runtime precinct: thirteen sourced HDB
footprints and storey counts around 87 Dawson Road in a local east/north metre
frame, with SkyVille and SkyTerrace labels, sky-garden storeys for Blocks 86–88,
and the assumed storey-height model (3.6 m first, 2.8 m typical, 5.6 m
sky-garden storeys, 4.0 m roof structures; reconciles to the published 147.8 m).
Rebuild it from the frozen v1 footprints with:

```shell
.venv/bin/python data/precinct/build_dawson_v2.py
```

`fixtures/dawson-v1.json` and `scripts/build_dawson_fixture.py` remain the
sourced upstream (data.gov.sg downloads, hashes recorded, Singapore Open Data
Licence v1.0).

## Geometry recipes

`recipes/skyville-block87-plate.recipe.json` is the reconstructed Block 87
plate: sourced footprint, derived core, four wings with a 4-room slot at each
end, and storey bands. `recipes/4r-type-{a,b,c}.recipe.json` are the 4-room
Type A/B/C plans traced from the HDB SkyVille @ Dawson brochure (Dec 2009,
page 5) as coordinates only: exterior and interior walls, columns, windows,
doors, slabs, AC ledge, service-yard railing and an assumed balcony, each with a
source state and confidence. Regenerate with:

```shell
.venv/bin/python data/recipes/build_recipes.py
```

Gate 1 overlays of these recipes on the local rasters are produced by
`tests/acceptance/gate1_overlays.py` into the ignored `output/gate1/`. No
brochure or WOHA raster is committed; `fixtures/unit-plans/` and
`scripts/compile_unit_plan.py` are the retained v1 outline compiler.

## Weather fixture

`weather/singapore-changi-2011-2025.epw` is the frozen Singapore Changi
International Airport 486980 TMYx file for 2011–2025, retrieved on
1 September 2026 from Climate.OneBuilding.Org, SHA-256
`9293635032609058428c34809b0c2fa90178cb73d2aaf857f0918b46893bf60c`. Cite
Lawrie and Crawley (2026), “Development of Global Typical Meteorological Years
(TMYx),” https://climate.onebuilding.org. The site publishes no standalone
licence; the file is redistributed only as the frozen input needed to reproduce
the study. The gendaymtx sky matrix derived from it is cached under the ignored
`.cache/sky/` keyed by the file hash.
