---
title: v1 runtime (Windows VM)
para: archive
status: superseded-implementation
decision_date: 2026-09-03
---

# v1 runtime (Windows VM)

The first implementation (1–2 September 2026) ran a FastAPI app from `server/`
and a React app from `web/` on a Windows 11 ARM VM behind a Cloudflare Tunnel,
serving `apartment.senibina.com.sg`. It used a custom solar loop
(`apartment-intelligence-solar-v5`) with at most 256 floor sensors, an outline-only
unit plan compiled from the brochure, six WebMCP tools, and five 1600 × 2400 PNG
cards. Its deployment receipt and dependency intake are recorded below.

It was superseded by the v2 clean-room rebuild because the apartment showed no
walls, the radiation grid was too coarse, the tower was nearly invisible, and
the analysis was not the practice's Ladybug + Radiance method. The `server/` and
`web/` trees were removed from `main` in commit `461e344`; the last commit
containing them is `b9d3f37`. The VM was shut down on 3 September 2026 once v2 was
live on Render and both hostnames were repointed. The install procedure is in
`v1-windows-deployment.md`; its scripts and the Vercel edge-proxy route are
kept under `deploy/archive/`.

## Deployment boundary (v1)

One FastAPI process on `127.0.0.1:8000` inside the dedicated Windows VM behind
a named Cloudflare Tunnel, serving `apartment.senibina.com.sg` through a Vercel
proxy route. Deployment credentials were host-local.

## Superseded proposal: Vercel front end plus Render API

Replaced on 3 September 2026 by the single Render container (see
`20 Areas/security-and-operations.md`). The original text follows.

The preferred post-submission migration removes the home Mac and Windows VM
from the public request path:

- Vercel serves the React application at the canonical
  `apartments.senibina.com.sg` hostname and its project-provided
  `vercel.app` address.
- A Render web service runs the existing FastAPI, Ladybug, and `rhino3dm`
  runtime from a reproducible container. Grasshopper, Rhino, Rhino.Compute,
  persistent storage, and a runtime model remain unnecessary.
- Browser requests reach the Render API only through the declared application
  route. The same input validation, session ownership, analysis concurrency,
  timeout, export-size, and rate controls remain authoritative.

Render's free service is acceptable for the prototype even though it can sleep
after inactivity and restart at any time. The interface must treat wake-up as
an expected state, show that the analysis engine is starting, and retry with
bounded exponential backoff. A lightweight health endpoint may be warmed only
for a defined demonstration or judging interval; it must not run an analysis.
The schedule must have an explicit end date and be disabled after that window.

## Dependency intake decision — 1 September 2026 (v1)

The direct candidates below were checked against their official npm or PyPI
registry metadata and the OSV API before acquisition. OSV returned no known
advisories for the exact versions. Registry metadata showed no npm
`preinstall`, `install`, or `postinstall` hook on the direct packages. Python
installation must use wheels only; source builds are a stop condition.

| Runtime | Accepted direct candidates | Publisher/source and licence |
| --- | --- | --- |
| Browser | React/React DOM 19.2.8, Three.js 0.185.1, pdf-lib 1.17.1, fflate 0.8.3 | Meta/React (MIT), mrdoob/Three.js (MIT), Hopding/pdf-lib (MIT), 101arrowz/fflate (MIT) |
| Web build/test | Vite 8.2.2, plugin-react 6.1.1, TypeScript 7.0.2, Vitest 4.1.11 | Vite/Vitest maintainers (MIT), Microsoft (Apache-2.0) |
| Browser acceptance | `@playwright/cli` 0.1.18 | Microsoft/playwright-cli (Apache-2.0) |
| Server | FastAPI 0.141.1, Uvicorn 0.52.4, HTTPX 0.28.1 | fastapi/fastapi (MIT), Kludex/uvicorn (BSD-3-Clause), encode/httpx (BSD-3-Clause) |
| Analysis/export | ladybug-core 0.44.58, ladybug-geometry 1.35.4, rhino3dm 8.32.1 | Ladybug Tools (AGPL-3.0), McNeel (MIT) |
| Python test/lock | pytest 9.1.1, pip-tools 7.6.1 | pytest-dev (MIT), jazzband/pip-tools (BSD-3-Clause) |

The Windows x86-64 CPython 3.13 rhino3dm wheel is 2,525,056 bytes with SHA-256
`cf3f10a9cc683d5a222e8839ddfdc6a0a1282a03b5d37501f666e662888faa2f`.
No Windows ARM64 wheel is published for this version, so the VM gate uses
x86-64 Python under Windows ARM emulation.

Permission boundary: browser packages receive no server secrets; the server
binds only to loopback; analysis has no runtime network access. Before full
installation, generate metadata-only locks with scripts disabled, inspect every
transitive package and install hook, run registry audits, and stop on a changed
integrity, unresolved advisory, source build, or unexpected lifecycle hook.

Metadata lock result: npm resolved 101 transitive packages with zero registry
audit findings. Its only lifecycle hook is optional macOS watcher `fsevents`
2.3.3 (MIT, official `fsevents/fsevents`, no OSV advisory); installs must use
`--ignore-scripts`, allowing Vite's polling fallback. Python resolved 24 wheels
for both macOS ARM64 and Windows x86-64 with no OSV advisory; the committed lock
pins every selected artifact hash and forbids source distributions.

The later browser-acceptance intake checked `@playwright/cli` 0.1.18 from the
official Microsoft repository. The exact npm package has Apache-2.0 licensing,
no lifecycle hook, no OSV advisory, and its registry integrity is pinned by the
lockfile. It is development-only and is not included in the deployed bundle.

The 2 September 2026 floor-plate compiler intake accepted NumPy 2.4.6 and
`opencv-python-headless` 4.13.0.92 from PyPI for an isolated authoring
environment only. NumPy is published by the NumPy project from
`numpy/numpy` under BSD-3-Clause with bundled permissive components. The
OpenCV Python wrapper is published by the OpenCV Team from
`opencv/opencv-python` under MIT and bundles OpenCV 4.13 under Apache-2.0.
Both releases are not yanked, expose compatible CPython 3.13 macOS ARM64
wheels, report no PyPI vulnerabilities, and returned no OSV advisories for the
exact versions. Installation is restricted to the pinned binary-wheel hashes
in `data/compiler-requirements.txt`, so package build and setup scripts do not
execute. The compiler environment is excluded from the server lock and the
deployed Windows runtime; its input brochure raster and diagnostics remain
ignored local research material.

The first Windows installation correctly stopped because Click's Windows-only
`colorama` dependency was absent from the macOS-generated hash lock. Colorama
0.4.6 was checked against PyPI and the official `tartley/colorama` repository:
BSD licence, no OSV advisory, and wheel SHA-256
`4f1d9991f5acc0ca119f9d443620b77f9d6b33703e51011c16baf57afb285fc6`.
The lock now includes this conditional Windows pin; hash enforcement remains on.

The public tunnel uses Cloudflare `cloudflared` 2026.8.3 from Cloudflare's
official GitHub release. Windows ARM64 is not published, so the VM uses the
Authenticode-valid Cloudflare-signed AMD64 executable under Windows ARM
emulation. Its exact SHA-256 is
`83e726ed18ea78c5ad5213c4c3a3a27051393950d2bc8ed4de69bec12d14eaae`;
OSV reported no advisory for `github.com/cloudflare/cloudflared` 2026.8.3.
The service receives only outbound network access, reads a system-protected
named-tunnel credential, binds metrics to loopback, and forwards only the
declared public hostname to the loopback application.

## Public deployment receipt — 1 September 2026

- Windows binds the application only to `127.0.0.1:8000` under the non-admin
  `ApartmentIntel` account. The scheduled task and `cloudflared` service are
  automatic and running.
- The Cloudflare connector is `cloudflared` 2026.8.3 on Windows AMD64 emulation.
  A Vercel route preserves the required `apartment.senibina.com.sg` hostname
  while proxying to the Cloudflare-managed tunnel hostname.
- Public negative checks returned 403 for an unexpected Origin, 422 for an
  unknown confirmation field, and 404 for a cross-session study handle.
- A real restart returned the app and tunnel connector without manual
  intervention.
- Public Chrome discovered six WebMCP tools. Analysis was refused before the
  trusted visible confirmation action, then completed after the human click.
- Export readback proved five 1600 × 2400 PNGs, a five-page PDF, matching result
  digest, and a metre-unit `.3dm` with the five required layers and object
  metadata.

## Accepted v1 direction (1 September 2026)

- Focus on an existing HDB apartment rather than professional design authoring.
- Guarantee one Dawson journey for Blocks 86–94, centred on 87 Dawson Road,
  postal 141087, storey 30.
- Use a frozen, reproducible public-data fixture and label every inference.
- Require the resident to confirm an approximate target floor plate, facade, and window in 3D.
- Run sunpath, shadow, solar-access, and radiation studies deterministically.
- Present interactive 3D plus consistent architectural graphics.
- Export a report and models.
- Let WebMCP coordinate the same stateful actions exposed in the visible UI.

Milestones: lock the product contract and public/private boundary; pass
dependency intake and the WebMCP, VM and `.3dm` platform gates; prove one HDB
data-to-massing fixture; prove human confirmation and the four analyses;
implement the WebMCP tools with UI parity; generate cards and downloadable
artifacts; complete accessibility, abuse, failure, deployment and submission
checks. All were carried into v2 and closed there.
