---
title: Security and operations
para: area
status: current
---

# Security and operations

This document owns the durable security, privacy, and runtime boundary. The
controls named in the public deployment receipt below were exercised on
1 September 2026; unlisted controls remain requirements rather than claims.

## Security objectives

- WebMCP tool discovery grants no authority beyond the visible application.
- Direct API and WebMCP callers receive identical validation, ownership, state,
  quota, and output controls.
- Listing content, floorplans, tool arguments, geometry, metadata, and exports
  remain untrusted data and never become executable instructions.
- Personal apartment information is minimized, purpose-bound, and not included
  in public examples without explicit authorization.
- Every result retains source, assumption, confirmation, method, and version
  provenance without exposing secrets or internal diagnostics.
- Public callers cannot create unbounded CPU, memory, storage, network, or
  third-party API cost.

## Trust boundaries

| Boundary | Untrusted input | Required control |
| --- | --- | --- |
| Agent or browser to WebMCP tool | Repeated calls, malformed arguments, invented facts | Closed schemas, server validation, study ownership, current-state checks |
| Bundled fixture to application | Public geometry, metadata, provenance | Hash verification, closed schema, fixed coordinate frame |
| Scene record to analysis worker | Geometry and analysis parameters | Coordinate, range, count, period, mesh, time, and output limits |
| Result to browser or download | Metadata, geometry, labels, filenames | Text-only rendering, size limits, safe content types, sanitized filenames |

## Input policy

- Do not implement a server endpoint that fetches an arbitrary caller-supplied
  URL. This prevents an unbounded scraper and server-side request-forgery path.
- The MVP accepts only address, storey, bounded proposal controls, analysis
  presentation choices, and export requests. It has no upload endpoint.
- The MVP has no runtime upstream data call or model provider.
- Studies use opaque session-bound handles and expire from memory after 30
  minutes; no personal study data is persisted.

## Admission and resource controls

Before public exposure, the implemented application must enforce:

- strict schemas with no unknown fields, enumerated analysis types, bounded
  coordinates, dates, periods, storeys, geometry counts, and export formats;
- per-study ownership, unguessable handles, expiry, idempotency, and replay
  protection;
- request-size, concurrency, queue, execution-time, memory, mesh, output, API,
  and global cost limits;
- cancellation and worker cleanup that reclaim resources rather than merely
  ending the HTTP request;
- health checks, backpressure, sanitized errors, and a fail-closed circuit
  breaker; and
- safe logs containing opaque IDs, source types, sizes, timings, decisions, and
  failure classes rather than floorplans, tokens, internal paths, or listing
  contents.

The public runtime additionally enforces a 256 KB request limit, one concurrent
analysis, five analyses per session per ten minutes, a terminating 15-second
worker timeout, 100 live studies, and 20 MB export bundles.

## Deployment boundary

One runtime is public on 3 September 2026:

- **v1 (shut down 3 September 2026):** one FastAPI process on `127.0.0.1:8000`
  inside the dedicated Windows VM behind a named Cloudflare Tunnel, serving
  `apartment.senibina.com.sg`. Its source trees were removed from `main` in
  commit `461e344`. The VM is off; the tunnel and Vercel proxy are to be
  retired once `apartments.senibina.com.sg` points at Render.
- **v2 (live at https://apartment-intelligence.onrender.com since 3 September 2026):** one Docker image (`deploy/Dockerfile`,
  linux/amd64) holding Python 3.13, Radiance 6.1a, the API, the data and the
  built web bundle; one Uvicorn worker; `/healthz`. Radiance is invoked as a
  subprocess with fixed arguments on server-generated geometry only. Studies
  are in memory and lost on restart, which the page reports as
  `STUDY_EXPIRED` with a next action.

### Why Render, and why a container

The v1 plan put the React app on Vercel and the API on a managed container host. v2 collapses
that into one Render web service because the analysis is a real server process, not a function:
Radiance is a native x86-64 binary (`gendaymtx`, `oconv`, `rcontrib`) that must sit on disk next
to Python and run for several seconds per study, and the sky matrix is cached on the local
filesystem between requests. Vercel's static and serverless model cannot host that binary or
hold a warm process; a Docker image can. Render builds `deploy/Dockerfile` on every push to
`main`, exactly like Vercel does for a Next.js repo, and serves the built web bundle from the
same process, so there is one origin, one CSP, and no cross-origin API. Singapore region keeps
latency low for residents and judges; the 1 CPU / 2 GB plan keeps the 0.25 m analysis inside its
15 s budget (6.2 s measured). Free instances (0.1 CPU, spin-down) cannot.

Deployment credentials remain host-local in both cases. On Render the service sets
`AI_EXPECTED_ORIGINS` (its own origin and `apartments.senibina.com.sg`) so state-changing API
calls from other origins receive 403, and `AI_COOKIE_SECURE=true`.

### Superseded proposal: Vercel front end plus Render API

Kept for the record; the section above replaced it on 3 September 2026. The
original text follows.

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

This is an approved direction, not evidence that the managed deployment has
been created or that the current VM deployment has been retired.

## Evidence integrity

- Bind each analysis to the exact scene, weather source, period, assumptions,
  confirmation event, method version, and result digest.
- Preserve the distinction between live computed, cached, example, and failed
  results.
- Do not let an agent alter source labels, uncertainty, confirmation state, or
  deterministic values while producing plain-language explanations.
- A trusted browser click requests a ten-second, session- and revision-bound
  single-use confirmation challenge. The server rejects a static activation
  header, a replayed challenge, or a challenge for stale geometry. This is an
  application interaction boundary, not cryptographic proof of a physical
  person's identity against a compromised same-origin page.
- Exports must carry the same provenance and uncertainty shown in the page.

## Release gate

Public release requires the implemented architecture to remain reconciled
against this owner and negative tests to prove:

- unconfirmed geometry cannot be analysed;
- unknown fields, unsupported formats, arbitrary URLs, paths, scripts, and
  executable model content are rejected;
- cross-study, expired, and replayed handles fail;
- oversized or hung work is rejected or terminated within its resource budget;
- secrets, personal input, internal paths, and stack traces are absent from
  client bundles, tool results, errors, logs, and example exports; and
- UI and WebMCP paths enforce the same state and authorization rules.

Competition tactics, real deployment configuration, hostnames, credentials,
and operational receipts belong only in ignored local notes. Ignored notes are
not backed up by Git.

## v2 release checks — 3 September 2026

- 20 Python tests: closed schemas, cross-session 403, expired 404, stale
  confirmation 409, single-use challenge, determinism, watertight mesh, pvlib
  oracle (0.008°), EPW closure (1.03%).
- 4 reducer parity tests and 6 Playwright journeys (human and WebMCP, 1440/1024/390)
  in Chrome 152 with `--enable-features=WebMCP`; eight tools discovered natively.
- Docker compose up, healthz, in-container analysis, kill, up, healthz.
- Render deploy executed the same afternoon; live readback in the submission project.
- Evening, local build: every page export verified headless (PDF read page by page); a
  three-unit sequence through the eight tools with one visible click per unit; horizontal
  overflow check passes at 390 px after the address dropdown fix.
- After the Version 0 push: six journeys pass against the live URL run serially; live grid
  timings 4.4 / 5.4 / 10.6 s for 0.5 / 0.25 / 0.1 m. A stale-confirmation race found only on the
  live host (a debounced re-stage landing after the click) was fixed the same evening.
- Not run: axe audit, reduced-motion and 200% zoom checks.

The v2 dependency intake is recorded in
[`dependency-intake-v2-2026-09-03.md`](dependency-intake-v2-2026-09-03.md).

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
