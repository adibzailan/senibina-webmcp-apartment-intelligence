---
title: Dependency intake, v2 clean room
date: 2026-09-03
owner: 20 Areas
---

# Dependency intake (same-day, 2026-09-03)

Every item below was checked on the registry the same day: publisher, version, licence, and a
working install on macOS arm64 (local) and Debian bookworm (Docker). Pins live in
`requirements.lock.txt`, `apps/web/package-lock.json` and `deploy/Dockerfile`.

| Item | Version | Source | Licence | Check |
|---|---|---|---|---|
| Radiance | 6.1a 2026-05-05 (tag 39b99660) | github.com/LBNL-ETA/Radiance releases | Radiance licence (LBNL) | Linux zip SHA-256 `fe2b0df32acb90e5b03e37039555aea85098f5343f17247bfec700189009b7c7`; macOS arm64 zip `00b368c6f1e00bf94b17d52adf2f933fe8f91862a5a0ae77d1e6dd7d31992f5d`; `rtrace -version` prints `RADIANCE 6.1a 2026-05-05 LBNL (6.1.39b9966033)` |
| ladybug-radiance | 0.2.12 (2026-05-18) | PyPI, Ladybug Tools | AGPL-3.0 | sky matrix via gendaymtx in 0.2 s; rcontrib intersection on 1,270 sensors in about 2.5 s |
| ladybug-core / ladybug-geometry | 0.44.59 / 1.35.4 | PyPI | AGPL-3.0 | Sunpath within 0.008° of pvlib NREL SPA at 12 instants |
| fastapi / starlette / uvicorn / pydantic | 0.141.1 / 1.6.0 / 0.52.4 / 2.13.5 | PyPI | MIT / BSD-3 / BSD-3 / MIT | API tests pass |
| numpy / shapely / trimesh / rhino3dm | 2.5.2 / 2.1.2 / 5.1.0 / 8.32.1 | PyPI | BSD-3 / BSD-3 / MIT / MIT | GLB byte-stable; 3DM writes with fresh GUIDs |
| pvlib (dev oracle) / pytest / hypothesis / httpx | 0.15.2 / 9.1.1 / 6.167.1 / 0.28.1 | PyPI | BSD-3 / MIT / MPL-2.0 / BSD-3 | dev only |
| react / react-dom / three / vite / typescript / vitest / @playwright/test / fflate / pdf-lib | 19.2.8 / 19.2.8 / 0.185.1 / 8.2.2 / 7.0.2 / 4.1.11 / 1.62.1 / 0.8.3 / 1.17.1 | npm | MIT / MIT / MIT / MIT / Apache-2.0 / MIT / Apache-2.0 / MIT / MIT | build and tests pass; pdf-lib is unmaintained and used only for presentation PDFs |
| Google Chrome | 152.0.7977.65 | installed | proprietary | Playwright `channel: chrome` with `--enable-features=WebMCP` |

Not added: mapbox-earcut / triangle (trimesh triangulation engines). Extrusion uses
ladybug-geometry's pure-Python earcut instead, so no new dependency. `pillow` is used only by
the local Gate 1 overlay script and is not in the lock.

Radiance discovery order at runtime: `RADIANCE_PATH`, then `.tools/radiance` (local, ignored by
Git), then `/usr/local/radiance` (Docker). `ladybug_radiance` reads `BINPATH` at import, which
`ai_solar.radiance_env` sets before the import.
