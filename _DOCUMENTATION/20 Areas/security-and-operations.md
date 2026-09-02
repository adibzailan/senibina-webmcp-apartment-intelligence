---
title: Security and operations
para: area
status: implemented-and-verified
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

One FastAPI process serves the built web application and `/api` on
`127.0.0.1:8000` inside the dedicated Windows VM. A named Cloudflare Tunnel is
the only ingress; no RDP, port forwarding, admin route, filesystem path, or
tunnel control is publicly exposed. Deployment credentials remain VM-local.

## Evidence integrity

- Bind each analysis to the exact scene, weather source, period, assumptions,
  confirmation event, method version, and result digest.
- Preserve the distinction between live computed, cached, example, and failed
  results.
- Do not let an agent alter source labels, uncertainty, confirmation state, or
  deterministic values while producing plain-language explanations.
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

## Dependency intake decision — 1 September 2026

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
