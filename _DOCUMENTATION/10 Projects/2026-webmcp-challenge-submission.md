---
title: WebMCP Challenge submission
para: project
status: active
deadline: 2026-09-03T13:00:00-07:00
next_action: Pass the Windows rhino3dm and public-tunnel gates, then complete deployed end-to-end artifact verification.
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
  engine, export pipeline, and six WebMCP tools are implemented locally.
- Apartment Intelligence is the founder-approved product title.
- Automated backend and frontend tests pass. A real Chrome WebMCP invocation
  created a study and correctly returned `CONFIRMATION_REQUIRED` before human
  confirmation.
- Windows acceptance, public deployment, full artifact acceptance, video, and
  challenge submission do not yet exist.
- JourneyProof remains a separate earlier concept and repository.

## Accepted v1 direction

- Focus on an existing HDB apartment rather than professional design authoring.
- Guarantee one Dawson journey for Blocks 86–94, centred on 87 Dawson Road,
  postal 141087, storey 30.
- Use a frozen, reproducible public-data fixture and label every inference.
- Require the resident to confirm the target facade, unit, and windows in 3D.
- Run sunpath, shadow, solar-access, and radiation studies deterministically.
- Present interactive 3D plus five consistent architectural graphics.
- Export the five PNG cards, combined PDF, ZIP, and layered `.3dm`.
- Let WebMCP coordinate the same stateful actions exposed in the visible UI.

## Milestones

1. Lock the product contract, product title, and public/private boundary.
2. Pass dependency intake and the WebMCP, VM, and `.3dm` platform gates. WebMCP
   is proven locally; the Windows and public-tunnel portions remain open.
3. Prove one HDB data-to-massing fixture with visible source and confidence.
4. Prove human unit confirmation and the four deterministic analyses.
5. Implement the WebMCP tools and verify human-agent/UI state parity.
6. Generate the five cards and downloadable PDF, ZIP, and `.3dm` artifacts.
7. Complete accessibility, abuse, failure, deployment, and submission checks.

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
- Generic prompt-to-3D, arbitrary scripts, Rhino.Compute, Grasshopper execution,
  or Revit integration.
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
