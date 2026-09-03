---
title: Apartment Intelligence demo film, storyboard
para: project
status: draft for founder review
target: 160 s (2:40), 1920 x 1080, 30 fps, H.264 + AAC
---

# Apartment Intelligence demo film

Three acts. Practice, the sales claim, the product. Ends on the thesis line and the URL.
Lineage: Savills Signal-to-Space (structure, timings, gates) and Living Atelier (voice, music,
burned-in captions, cursor).

## Fixed decisions carried over

- Voice: ElevenLabs professional clone "Adib" (`PI7cqzPMpSlJicFtS4WY`), model `eleven_v3`, one
  generation, natural speed, no time-stretch. About 380 words for 2:40.
- Music: ElevenLabs Music v2, instrumental, warm and slow, generated to narration length, mixed
  at about 0.1 under a 1.0 narration. Master near -16 LUFS, peaks under -1 dBTP.
- Captions: burned in, phrase-timed, bottom centre. Inter 500 on a paper box, ink text,
  110 px side margins, 44 px from the bottom at 1440 x 900, scaled to the 1920 frame. One
  thought per caption, never a paragraph. (Savills dropped captions because they fought the
  action; here the captions carry the argument in acts one and two, so they stay.)
- Cursor: the Atelier red cursor with the press pulse, injected by the capture script.
- Frame: paper `#f5f2e9` cards for opening, act breaks and close; the live page fills the frame
  in act three. Centred compositions, hard cuts, slow pushes of 2 to 4 percent, nothing bounces.
- Product footage is captured with Playwright `recordVideo` at 1920 x 1080 against the live URL,
  with every action stamped into a timing file so the edit cuts to real events.

## Beats

| # | Time | Picture | Caption | Narration |
|---|---|---|---|---|
| 1 | 0:00–0:07 | Paper card. Serif question: "Will this apartment get the sun you expect?" | none | (music alone, then) Will this apartment get the sun you expect? |
| 2 | 0:07–0:34 | Practice supercut: sunpath diagram, a floor-plate radiation study, direct-sun hours by date, a tower-scale precinct study. Each holds 4 to 6 s with a slow push. | "How architects answer it." then "Sun path." "Radiation on the floor." "Hours of direct sun." "The tower among its neighbours." | In practice we answer it with instruments. A sun path for the site. Radiation on every square metre of floor. Hours of direct sun on the days that matter. All of it computed, all of it on the drawing, before anyone commits. |
| 3 | 0:34–0:52 | Paper cards in sequence, each a phrase a listing might carry: "Bright and airy." "Gets the afternoon sun." "Unblocked, high floor." Then one card: "None of it is measured." | the phrases themselves | When a home is sold, the same question gets a sentence. Bright and airy. Afternoon sun. High floor, unblocked. Every word is a guess about light. None of it is measured. |
| 4 | 0:52–1:00 | Paper card: "Apartment Intelligence" masthead, sub "Version 0, built for the OpenAI WebMCP Challenge". Cut to the live page: the grid of ten drawn developments. | "The same instruments, for the person who will live there." | Apartment Intelligence takes the practice instruments, Ladybug and Radiance, and hands them to the person who will live there. |
| 5 | 1:00–1:12 | Human beat. Cursor clicks SkyVille @ Dawson; page lands on "Start with your block and storey." Storey set to 30. Start the study. | "A real block. A real storey." | Start with a real block. Eighty-seven Dawson Road, storey thirty. |
| 6 | 1:12–1:30 | Agent beat. A dark console panel slides in bottom-right and prints calls as they run: `create_apartment_study`, `propose_unit_placement`. The page follows: slots outline on the tower, one turns red. Then `run_solar_analysis` prints and the page answers CONFIRMATION_REQUIRED inline. | "An agent can stage a placement." then "It cannot confirm one." | An agent working through WebMCP can open the study and stage a placement. It can ask for the analysis. It will be refused. |
| 7 | 1:30–1:38 | Human beat. Cursor reads the confirm sentence, clicks the green button. Step moves to Analyse. | "That click belongs to a person." | Confirmation is a visible click, and it belongs to a person. |
| 8 | 1:38–1:58 | Agent runs the analysis. Heat spreads across the floor, room names float above the rooms, the compass turns as the camera settles on the apartment. Console prints `explain_evidence`; the rail's plain sentence appears. Massing off for two seconds. | "Radiation, per room." "Every number carries its source." | Now the agent runs it. Annual radiation on the floor, room by room. Every number comes back with its method and its digest, and the agent can explain any of them without changing one. |
| 9 | 1:58–2:14 | Comparison beat. Console rolls three units in sequence, one click each, and prints a small table: NE tip storey 12, SE core storey 30, SW tip storey 44 with averages. Page flashes each placement. | "Three units. Three clicks. One table." | Ask about three units and it gathers them one by one. Each one still needs its click. |
| 10 | 2:14–2:30 | Export. Pick PDF report, Export. Cut to the PDF: paper cover, the site page with the isometric, a card page, the back cover. | "Keep the evidence." | Then keep the evidence. A report with the cover, the plans, the digest on every page. |
| 11 | 2:30–2:40 | Paper close card: "Built with Ladybug and Radiance, the same engines architects use in practice, so the study a practice would run for a client is now open to the people who live there." Below: apartments.senibina.com.sg, "A public-interest study by Senibina for apartment living. Singapore now, the region next." | none | The same engines. Now for the people who live there. Apartment Intelligence, by Senibina. |

Word count of the narration column: about 300. Room to breathe; full stops land on cuts.

## Practice supercut sources (act one)

Use our own material only, no search-engine images:

- Sunpath and radiation cards rendered by this engine for the Dawson study.
- A precinct-scale study rendered from the same engine on the whole block plate, for the
  "tower among its neighbours" shot.
- Adib's own Grasshopper and Ladybug screens from practice, if he supplies them, for one shot.

## Split screen convention (act three)

The page fills the frame. The agent is a bottom-right console panel, 560 x 300, dark ink on
paper, monospace, printing each tool name, its key arguments and a one-line reply. The human is
the red cursor. If Adib records a webcam clip of himself for the confirm click, it sits top-left
at 320 x 180 for beats 5 and 7 only.

## Gates

1. Founder approves this storyboard and the script wording.
2. Capture against the live URL; timing file reviewed; no console errors.
3. Narration generated once; auditioned; accepted.
4. Music generated once; accepted.
5. Assembly preview at full length; founder accepts; final render; upload unlisted; anonymous
   playback checked; production receipt written.
