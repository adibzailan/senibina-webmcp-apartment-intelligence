---
title: WebMCP Challenge submission
para: project
status: submitted, judging until 21 September 2026
deadline: 2026-09-04T04:00:00+08:00
next_action: Keep https://apartments.senibina.com.sg free to test, unchanged in substance, until judging ends on 21 September 2026 (5:00 pm PT); winners announced around 23 September.
---

# WebMCP Challenge submission

## Outcome

Submit a working, publicly reviewable Apartment Intelligence application that helps a
Singapore resident understand the solar conditions of an existing HDB
apartment through researched context, human-confirmed unit geometry,
deterministic environmental analysis, and thoughtful WebMCP orchestration.

## Submitted

3 September 2026, about 23:30 SGT. Project page: https://devpost.com/software/apartment-intelligence.
Video: https://youtu.be/pkn1xDcIVq8. Live: https://apartments.senibina.com.sg. Repo: GitHub
`adibzailan/senibina-webmcp-apartment-intelligence`, AGPL-3.0. Submitter type Individual, Singapore,
App Status New. The write-up as pasted is `2026-webmcp-devpost-writeup.md`.

## Completion condition

This outcome is complete when the live application, public code repository,
project description, required visual material, and demo video are submitted and
the submitted URLs are read back successfully. All of these are done; what
remains is keeping the live host stable through judging.

## What was submitted

- Version 0 of the v2 build on `main`: one Docker container on Render
  (Singapore) serving the page and the Ladybug + Radiance engine from one origin.
- Nine WebMCP tools on `document.modelContext`, including `survey_unit` with
  its own budget of thirty surveys per ten minutes. No confirmation tool.
- A resident journey of Locate, Place, Confirm, Analyse and Keep, with a PDF
  report and GLB, OBJ, 3DM and ZIP exports, every result digest-bound.
- A 2:03 demo film showing the refusal, the visible click, the agent retry
  succeeding, and survey mode. Master in `video/apartment-intelligence-demo/`.
- An agent receipt from the ChatGPT desktop app's built-in browser: nine tools
  discovered, three surveys, one study staged, refused, confirmed by click,
  analysed and explained.

Dated build and test receipts are archived in
[`40 Archives/2026-09-submission-receipts.md`](../40%20Archives/2026-09-submission-receipts.md).

## Principal risks during judging

- The live host is rebuilt from `main` on every push. Do not merge anything
  that changes runtime behaviour until judging ends.
- Studies are in memory and expire after 30 minutes; a Render restart shows
  `STUDY_EXPIRED` with a next action rather than a broken page.
- Rate limits are per browser session: five confirmed analyses and thirty
  surveys per ten minutes. A judge who exceeds them sees a countdown.
- Solar results can appear authoritative unless assumptions and uncertainty
  stay visible in both the interface and the exports.

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

## Required proof (all met)

- One public HDB example can be researched, verified, located, analysed, and
  exported end to end.
- Every important fact is visibly labelled sourced, inferred, reconstructed,
  assumed, computed, or human-confirmed.
- Analysis cannot begin until the human confirms the unit geometry.
- WebMCP tool calls and manual actions update the same visible study state.
- The graphics use computed values and disclose dates, north, legend,
  assumptions, and uncertainty.
- Timeout, missing data, invalid geometry, and unavailable analysis states fail
  honestly without fabricated results.

## Official source

- [OpenAI WebMCP Challenge](https://openai.com/webmcp-challenge/)
