---
title: WebMCP Challenge submission
para: project
status: active
deadline: 2026-09-04T04:00:00+08:00
next_action: Adib reviews the verified gates 1–5 and approves preparation of the demo video and final submission materials.
---

# WebMCP Challenge submission

## Outcome

Submit a working, publicly reviewable Apartment Intelligence application that helps a
Singapore resident understand the solar conditions of an existing HDB
apartment through researched context, human-confirmed unit geometry,
deterministic environmental analysis, and thoughtful WebMCP orchestration.

## Completion condition

This outcome is complete only when the live application, public code repository,
project description, required visual material, and demo video are submitted and
the submitted URLs are read back successfully.

## Current state

- The public baseline, dependency locks, Dawson fixture, application, analysis
  engine, export pipeline, and six WebMCP tools are implemented and published.
- Apartment Intelligence is the founder-approved product title.
- Ten backend and five frontend tests pass on macOS; the same backend tests and
  frontend suite/build also pass in Windows.
- The Windows runtime runs the app under the dedicated non-admin
  `ApartmentIntel` account on loopback.
- The named Cloudflare Tunnel and Vercel hostname bridge serve
  <https://apartment.senibina.com.sg>. Both services and the app recovered after
  a real Windows restart.
- A real public Chrome WebMCP journey discovered all six tools, returned
  `CONFIRMATION_REQUIRED`, accepted confirmation through the visible UI, then
  analysed and exported successfully.
- Artifact readback proved five 1600 × 2400 PNGs, a five-page PDF, one manifest,
  and a metre-unit `.3dm` with five expected layers, 29 objects, and metadata.
- Demo-video preparation and final challenge submission remain deliberately
  unstarted.
- JourneyProof remains a separate earlier concept and repository.

## Accepted v1 direction

- Focus on an existing HDB apartment rather than professional design authoring.
- Guarantee one Dawson journey for Blocks 86–94, centred on 87 Dawson Road,
  postal 141087, storey 30.
- Use a frozen, reproducible public-data fixture and label every inference.
- Require the resident to confirm an approximate target floor plate, facade, and window in 3D.
- Run sunpath, shadow, solar-access, and radiation studies deterministically.
- Present interactive 3D plus five consistent architectural graphics.
- Export the five PNG cards, combined PDF, ZIP, and layered `.3dm`.
- Let WebMCP coordinate the same stateful actions exposed in the visible UI.

## Milestones

1. Lock the product contract, product title, and public/private boundary.
2. Pass dependency intake and the WebMCP, VM, and `.3dm` platform gates. Done.
3. Prove one HDB data-to-massing fixture with visible source and confidence.
4. Prove human unit confirmation and the four deterministic analyses.
5. Implement the WebMCP tools and verify human-agent/UI state parity.
6. Generate the five cards and downloadable PDF, ZIP, and `.3dm` artifacts.
7. Complete accessibility, abuse, failure, deployment, and submission checks.

Milestones 3–6 are implemented and exercised. Milestone 7 is complete through
deployment and restart recovery; video and submission checks remain.

## Principal risks

- Public records do not identify exact unit, facade, windows, or internal plan.
- Listing availability and formats are inconsistent; generic scraping is not a
  reliable or accepted ingestion contract.
- Inferred building height and simplified massing can create false precision.
- Solar results can appear authoritative unless assumptions and uncertainty are
  visible in both the interface and exported artifacts.
- The challenge window is short; scope must remain one excellent HDB journey.

## Non-goals

- Private-condominium coverage, universal listing extraction, or floorplan upload.
- Statutory compliance, property valuation, professional certification, or
  replacement of an architect or environmental consultant.
- Full internal-apartment simulation, annual energy modelling, CFD, or thermal
  comfort certification.
- Generic prompt-to-3D, arbitrary scripts, Grasshopper execution, remote CAD
  computation, or Revit integration.
- Accounts, billing, database persistence, runtime LLMs, live OneMap calls,
  enterprise administration, or a general AEC platform.

## Required proof

- One public HDB example can be researched, verified, located, analysed, and
  exported end to end.
- Every important fact is visibly labelled sourced, inferred, generated, or
  human-confirmed.
- Analysis cannot begin until the human confirms the unit geometry.
- WebMCP tool calls and manual actions update the same visible study state.
- The four graphics use computed values and disclose dates, north, legend,
  assumptions, and uncertainty.
- Timeout, missing data, invalid geometry, and unavailable analysis states fail
  honestly without fabricated results.

## Official source

- [OpenAI WebMCP Challenge](https://openai.com/webmcp-challenge/)
