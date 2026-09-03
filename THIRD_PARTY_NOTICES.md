# Third-party notices

Apartment Intelligence is licensed under AGPL-3.0-only. Its dependency lockfiles
are the authoritative version inventory.

- Ladybug Core 0.44.58 and Ladybug Geometry 1.35.4 are distributed under
  AGPL-3.0.
- React, React DOM, Three.js, pdf-lib, fflate, Vite, Vite React plugin,
  rhino3dm, FastAPI, and pytest use permissive open-source licences recorded in
  their distributions.
- TypeScript uses Apache-2.0. Uvicorn, HTTPX, and pip-tools use BSD-family
  licences.
- Newsreader is copyright 2020 The Newsreader Project Authors and Inter is
  copyright 2020 The Inter Project Authors. Both self-hosted font families are
  redistributed under the SIL Open Font License 1.1; their licence texts and
  SHA-256 checksums are retained under `web/public/fonts/`.
- The Dawson fixture is derived from data.gov.sg datasets under the Singapore
  Open Data Licence. Government data does not imply endorsement.
- The bundled Singapore Changi TMYx weather file retains its source, citation,
  retrieval date and SHA-256 beside the data. Climate.OneBuilding.Org does not
  state a standalone licence for the file; see `data/README.md` before reuse.

See `_DOCUMENTATION/20 Areas/security-and-operations.md` for the dated intake
decision and the lockfiles for integrity hashes.

## v2 clean room (branch v2-clean-room)

- Radiance 6.1a (LBNL-ETA, tag 39b99660), Radiance licence, used as an external binary in Docker and locally; not redistributed in this repository.
- Ladybug Tools: ladybug-core 0.44.59, ladybug-geometry 1.35.4, ladybug-radiance 0.2.12, AGPL-3.0 (compatible with this repository's AGPL-3.0-only licence).
- pvlib 0.15.2 (BSD-3) as a development oracle only.
- three 0.185.1, react 19.2.8, vite 8.2.2, fflate 0.8.3, pdf-lib 1.17.1 (MIT); typescript 7.0.2 and @playwright/test 1.62.1 (Apache-2.0).
- HDB Existing Building and HDB Property Information datasets via data.gov.sg under the Singapore Open Data Licence v1.0; attribution given, no endorsement implied.
- Weather: Climate.OneBuilding.Org TMYx 2011-2025 for Singapore Changi (Lawrie & Crawley); cited, licence not stated by the publisher.
- Drawings: HDB sales brochure (Dec 2009) and WOHA storey plans were used as local references for tracing coordinates only; no raster is committed.
