---
title: Security and operations
para: area
status: current
---

# Security and operations

This document owns the durable security, privacy, and runtime boundary.
Controls named in the release checks below were exercised on the live host;
unlisted controls remain requirements rather than claims.

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
analysis, five confirmed analyses and thirty surveys per session per ten minutes (separate budgets; a full plate of 24 slots fits one survey window), a terminating 15-second
worker timeout, 100 live studies, and 20 MB export bundles.

## Deployment boundary

One runtime is public, at <https://apartments.senibina.com.sg> (also
`apartment.senibina.com.sg` and the Render origin
`apartment-intelligence.onrender.com`): one Docker image (`deploy/Dockerfile`,
  linux/amd64) holding Python 3.13, Radiance 6.1a, the API, the data and the
  built web bundle; one Uvicorn worker; `/healthz`. Radiance is invoked as a
  subprocess with fixed arguments on server-generated geometry only. Studies
  are in memory and lost on restart, which the page reports as
  `STUDY_EXPIRED` with a next action.

### Why Render, and why a container

The page and the engine run as one Render web service because the analysis is a real server process, not a function:
Radiance is a native x86-64 binary (`gendaymtx`, `oconv`, `rcontrib`) that must sit on disk next
to Python and run for several seconds per study, and the sky matrix is cached on the local
filesystem between requests. Vercel's static and serverless model cannot host that binary or
hold a warm process; a Docker image can. Render builds `deploy/Dockerfile` on every push to
`main`, exactly like Vercel does for a Next.js repo, and serves the built web bundle from the
same process, so there is one origin, one CSP, and no cross-origin API. Singapore region keeps
latency low for residents and judges; the 1 CPU / 2 GB plan keeps the 0.25 m analysis inside its
15 s budget (6.2 s measured). Free instances (0.1 CPU, spin-down) cannot.

Deployment credentials remain host-local. On Render the service sets
`AI_EXPECTED_ORIGINS` (its own origin and `apartments.senibina.com.sg`) so state-changing API
calls from other origins receive 403, and `AI_COOKIE_SECURE=true`.

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

## Release evidence

The checks that gate the public runtime are the 20 Python tests, 4 reducer
parity tests and 6 Playwright journeys named in `deploy/RUNBOOK.md`, plus the
Docker lifecycle check and a serial journey run against the live URL. Survey
mode (`POST /api/survey`) runs an analysis on a staged placement with no study
and no confirmation, under its own rate budget and the single-worker lock; the
response is labelled `survey_unconfirmed` and carries no export. Not yet run:
axe audit, reduced-motion and 200% zoom checks. Dated receipts are archived in
`40 Archives/2026-09-submission-receipts.md`.

The v2 dependency intake is recorded in
[`dependency-intake-v2-2026-09-03.md`](dependency-intake-v2-2026-09-03.md).

The v1 dependency intake and the 1 September 2026 deployment receipt are
archived in `40 Archives/v1-windows-runtime.md`.
