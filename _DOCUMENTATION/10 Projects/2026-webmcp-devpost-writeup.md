---
title: Devpost write-up, Apartment Intelligence
para: project
status: ready to paste
---

# Apartment Intelligence

*Will this apartment get the sun you expect?*

## Inspiration

Architects answer that question with instruments: sun paths, radiation on every square metre of floor, hours of direct sun on the days that matter. When a home is sold, the same question gets a sentence. "Bright and airy." "Afternoon sun." Nobody measures it. We wanted the instruments architects use in practice in the hands of the person who will live there.

## What it does

Pick a real block and storey (SkyVille @ Dawson, Singapore, is covered). Choose the wing and layout you recognise on a 3D model of the tower. Confirm it with one click. The engine then computes sun path, shadow at sixteen instants, direct-sun hours on four key dates and annual radiation on a 0.1 to 0.5 m floor grid, room by room, and shows it on the apartment in 3D. Export a report with the cover, the plans, a north arrow, room labels and the result digest on every page, or the model as GLB, OBJ or 3DM.

## How WebMCP fits

The page registers nine tools on `document.modelContext`. An agent in the browser can list covered homes, open a study, stage a placement, run the analysis, switch the view, explain any number, export, and survey placements without a study. Tools and buttons share one state, so what the agent does is what the person sees.

Two modes, one rule. **Study**: the resident confirms the unit they will live in with a visible click, and only that path produces the report. **Survey**: `survey_unit` lets an agent analyse any placement without a click and compare units in a row, with every number labelled `survey_unconfirmed`. Agents explore, people vouch.

There is no confirmation tool. A `confirmed` argument is rejected. The click is exchanged for a ten-second single-use server challenge. This is the human-agent boundary made concrete: the agent does everything except the one thing only a person can vouch for.

## How we built it

Python: Ladybug and Radiance run headless on Render (one Docker container, Singapore). Geometry is a coordinate recipe of the published 4-room plans and the reconstructed tower plate, labelled sourced, inferred, reconstructed, assumed or human-confirmed. Every result is bound to a SHA-256 digest of recipe, placement, weather and method. Front end: React, Three.js, TypeScript. No LLM in the runtime, no scraping, no accounts, no database.

## Challenges

- Getting the practice capability out of Rhino at all. In practice these studies live inside Grasshopper on a licensed desktop, driven by hand. Our first attempt kept that shape: a Windows machine at home, a tunnel to the internet, a custom analysis loop that only imitated the real one. It worked once and taught us it could not be the product. The rebuild threw it away: Ladybug and Radiance run headless in one Docker container on Render, geometry is a coordinate recipe instead of a CAD file, and no Rhino, Grasshopper or Revit is in the runtime. That is what let a consumer page run a practice-grade study in ten seconds.
- Choosing where it could live. Our web work normally ships on Vercel, and the first plan put the page there with the analysis somewhere else. It cannot work that way: Radiance is a native x86-64 binary that has to sit on disk next to Python, run for several seconds per study, and keep a warm sky matrix between requests. Vercel's static and serverless model has no place for that. Render runs the whole thing as one Docker web service in Singapore, page and engine from one origin, rebuilt from the repo on every push, for about US$25 a month. Radiance ships Linux x86-64 only, so the image is amd64 and the analysis has a 15-second budget on one CPU; the fine 0.1 m grid runs in 10.6 s live.
- Making a confirmation that a tool cannot fake without making the product tedious. The answer was two modes with different labels, not a switch.
- A race that only showed on the live host: the page re-sent a placement an agent had staged, and on a slower network the re-send landed after the click and made the confirmation stale. Found by running the browser journeys against production, not localhost.

## Accomplishments

- A real ChatGPT desktop agent discovered all nine tools, surveyed three units, chose one, staged it, was refused, waited for the click, then ran and explained the confirmed study.
- A practitioner read the report and said it was what a sustainability consultant takes weeks to produce.
- Every export is byte-stable and digest-bound; the same inputs give the same file.

## What we learned

- Agents need labels more than they need permissions. Once every number said "confirmed" or "unconfirmed", we could open the analysis to agents without weakening the evidence.
- The rate limit that protects the server is the first thing an agent hits when it tries to be useful. Separate budgets by mode fixed it.
- Test against the deployed URL. Two bugs lived only there.
- The hard part was never the physics. It was taking a tool that lives inside a desktop CAD licence and making it a service. Once it was a service, both the consumer page and a practice could call it.
- The same engine that answers one resident can answer a practice. That is the door this challenge opened for us.

## What's next

- Proper base geometry. Today the tower and the apartments are coordinate recipes traced from published plans. The next step is to model the developments properly in Rhino or Revit once, keep provenance on every element, and feed that one model to everything: the 3D view, the analysis mesh, the plan cards and the exports. The engine stays headless; only the source of the geometry changes.
- More covered developments, starting with the nine already drawn on the grid.
- A survey progress indicator ("2 of 24 surveyed") and separate badges for survey and confirmed evidence in chat, both suggested by the ChatGPT agent that tested it.
- The practice-side version of the same engine.

## Links

- Live: https://apartments.senibina.com.sg
- Code: https://github.com/adibzailan/senibina-webmcp-apartment-intelligence (AGPL-3.0)
- A public-interest study by Senibina for apartment living. Singapore now, the region next.

## Testing instructions (private field)

Open https://apartments.senibina.com.sg in the ChatGPT desktop app's built-in browser (GPT-5.6 Sol or Terra) or Chrome 152 with `chrome://flags/#enable-webmcp-testing`. No login. Try: "List the tools. Survey NE wing tip Type A storey 12, SE near the core Type B storey 30 and SW wing tip Type C storey 44 at 0.5 m and compare the averages. Create a study for the one you would confirm, stage it, and try run_solar_analysis." The refusal is expected; click the green confirm button, then ask it to run again and export the PDF. Limits: five confirmed analyses and thirty surveys per ten minutes per browser session.
