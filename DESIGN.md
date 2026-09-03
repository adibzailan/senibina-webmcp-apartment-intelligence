# Apartment Intelligence design system

## The reader and the job

Apartment Intelligence is for a resident deciding whether an existing HDB apartment will receive the sun they expect. The reader must be able to identify the apartment, understand what is known versus approximated, inspect four environmental studies, and keep evidence without learning architectural software.

The apartment question and evidence come before branding. The interface should read like an architectural feature that is interactive, agent-operable, and exportable—not a dashboard, wizard, marketing page, or certification report.

## Composition

- Use an editorial workbench: quiet masthead, concise study summary, dominant architectural canvas, contextual reading rail, then paced evidence chapters.
- Desktop uses a 12-column grid. The canvas occupies eight columns and the rail four. Tablet uses six columns. Mobile uses four columns and places the canvas before controls.
- Prefer a continuous paper field, thin rules, precise alignment, and meaningful whitespace. A bordered surface exists only when containment or interaction requires it.
- The 3D precinct is the lead image. Sunpath is the celestial diagram; Shadow is a time study; Solar Access and Radiation are horizontal apartment-floor evidence drawings.
- The five steps remain product state, not a permanent tab strip. Show a short location line and a modest progress index.

## Typography

- Newsreader is the editorial voice: display headlines, study questions, explanatory prose, findings, and report narrative.
- Inter is the instrument voice: controls, numbers, captions, legends, provenance, metadata, and technical annotation.
- Display: 56–88 px desktop, 44–58 px tablet, 38–48 px mobile; line-height 0.95–1.02.
- Chapter title: 40–56 px desktop, 34–42 px mobile; line-height 1.02–1.1.
- Reading text: 18–22 px, line-height 1.45–1.6, maximum 66 characters.
- Interface text: 12–15 px, line-height 1.35–1.5. Use tabular figures for measurements.
- Prose, field labels and captions use sentence case. Choice buttons and the tile meta line use title case ("NE Wing, Wing Tip", "Type A, Three Bedrooms", "Queenstown, Blocks 86–88, 47 Storeys"). Uppercase is reserved for the two control-row labels, Look at and View.
- Dividers in copy are full stops or commas, never middle dots. A middle dot may separate fields in a data caption (the canvas edge line).
- Step headings sit on one line above the workbench; the opener above the development grid may take two balanced lines.

## Tokens

### Grid and rhythm

- Container: `min(100% - 48px, 1440px)` desktop; 32 px tablet; 20 px mobile gutters.
- Columns: 12 / 6 / 4 with 20 px desktop and tablet gaps, 12 px mobile gaps.
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 72, 96 px.
- Rules: 1 px graphite at full emphasis, 1 px stone for subordinate divisions.
- Controls: minimum 44 px target; square or 2 px radius; 2 px focus outline with 3 px offset.

### Colour

- Paper `#f5f2e9`; white paper `#fbfaf6`; ink `#18211d`; muted ink `#5f665f`; rule `#b9b7ae`.
- Sourced context `#d9ddd5`; inferred massing `#e7e1d4`; selected precinct `#bfc9bf`. The Massing toggle drops the tower and context fills to faint edges so the apartment reads alone.
- Solar yellow `#f2c230`; confirmed home red `#c8472d`; shaded `#45534d`; go green `#2f6b4f` (the confirm action button only).
- Radiation scale: `#183f5a → #2b8c86 → #e3c946 → #c8472d`.
- Colour is semantic. Never use gradients, badges, or accent fills as decoration.

## Architectural canvas

- Open on an intentional north-west axonometric view with the full Dawson context visible, a level horizon, and useful ground margin.
- Orbit, pan, zoom, reset, north, and stage-aware presets must be visible and keyboard reachable. Two rows under the canvas: Look at (Precinct, Tower, Apartment, From above, Face north) and View (Map, Massing, Reset). The colour scale sits between the canvas and the rows.
- The compass is three-dimensional: a small gizmo drawn in the canvas corner that shares the camera rotation, with a red north arrow, east–west bar and an up post. The same north arrow appears on every plan card.
- Room names float above each room as paper tags once a slot is chosen, in the scene and on the plan cards.
- From Locate onward, Block 87 and surrounding massing are translucent context. The proposed floor plate is an outline; the human-confirmed apartment floor plate and opening alone receive the strongest red.
- View name and extent note sit on the drawing edge; the compass sits in the canvas corner; the analysis legend sits directly under the canvas. None of them float as dashboard cards.
- A live 3D surface must respond to pointer orbit, right-button/modified pan, wheel/pinch zoom, and reset. A fixed render must never be presented as interactive 3D.

## Environmental studies

- **Sunpath:** show seasonal paths, selected-date path, cardinal directions, and date legend. Yellow is reserved for solar geometry.
- **Shadow:** provide 09:00, 12:00, 15:00 and 17:00 floor conditions on the four key dates. Show the selected time, solar altitude/azimuth, and the lit fraction.
- **Solar Access:** show the confirmed horizontal floor grid for each seasonal date with one continuous hours scale.
- **Radiation:** show approximate annual interior floor exposure through the confirmed window, with minimum/average/maximum, units, components, and limitations.
- Every graphic must make method, time period, units, orientation, and limitation inspectable without requiring provenance to dominate the view.

## Evidence states

- Sourced: quiet solid neutral fill and solid rule.
- Inferred: warm neutral fill and fine dashed annotation.
- Human-confirmed: confirmed-home red on the geometry, solid rule, and explicit confirmation sentence. The confirm button itself is go green, since red reads as "stop" to a person about to commit.
- Generated/calculated: analysis scale plus method caption.
- Survey, unconfirmed: agent-run numbers listed in the rail in muted ink under a dashed rule, with the sentence "Nobody has vouched for these placements." They never take the confirmed red and never reach the report.
- Provenance lives in a disclosure and in report captions. Do not repeat large state labels across every surface.

## Interaction and copy

- Controls and WebMCP actions use the same reducer and visible state.
- Human confirmation remains a visible first-party action and cannot be supplied by a tool parameter.
- Choices are picked first, then acted on: a grid size then Run the analysis; export formats then Export. A single click never starts a download or a run by itself.
- Date and hour go idle under Radiation, with the label saying the number is a whole-year total.
- Lead with the resident’s next decision: “Choose the wing and layout you recognise,” not system narration. The five step headings are: Start with your block and storey. Choose the wing and layout you recognise. Confirm the placement you see. Sun, shade and radiation on your floor. Keep the evidence.
- Use direct, specific language. Avoid marketing claims, exclamation marks, AI vocabulary, and unexplained analysis jargon.
- Loading, refusal, stale confirmation, and export states stay inline and preserve the reader’s place.

## Responsive and accessible behaviour

- At 1024 px, the canvas spans all six columns and the reading rail becomes a two-column section below it.
- At 390 px, the canvas appears first at a 4:3 ratio. Controls follow in document order; no desktop split is squeezed into the viewport.
- Never rely on colour alone. Pair colour with line style, text, or pattern.
- Maintain WCAG AA contrast, visible focus, reduced-motion support, semantic landmarks, status announcements, and labels for canvas controls.
- No horizontal document overflow. The canvas must resize with its container and retain usable controls at 200% zoom.

## Export system

- The server writes one stacked `cards.svg` (radiation, four direct-sun-hours maps, sunpath, shadow instants). Every plan card carries the room labels and a north arrow; the SVG is byte-stable and digest-bound.
- The PDF report is a page composition of those cards, A4 proportion at 1190 × 1684 units. Cover and back cover use paper `#f5f2e9`; inner pages use white paper. Every page repeats the masthead ("Apartment Intelligence" over a 1 px ink rule), and inner pages carry a footer with development, block, storey, short digest and page number.
- Cover: the question line in the serif, then development, block, storey and placement, then a ruled table of generated date, method, weather file and full digest, then the Senibina line and the Version 0 line.
- "Site and unit" page: two fixed views rendered at export time, never the user's current camera: the apartment isometric with massing off and room tags on, then the tower in its precinct.
- Cards are placed whole, one after another; a card that does not fit the remaining page starts a new page. Nothing is tiled across a page break.
- Back cover: masthead rule, the Senibina line, the Ladybug and Radiance thesis line, the data licence line, the Version 0 line and senibina.com.sg.
- The page offers PDF, GLB, OBJ, 3DM and the full ZIP as a pick-then-Export list. PNG, `cards.svg` and `evidence.json` remain in the ZIP and available to agents by name.
- PDF text uses the PDF standard Times and Helvetica faces as stand-ins for Newsreader and Inter; the SVG cards keep their own type.

## Development grid

- Ten tiles, 1200 × 900 line art on white, black ink only, drawn in the Senibina pen-and-ink contract (see `apps/web/public/projects/README.md`). Covered developments sit on white paper with a red Ready line and a red frame when selected; the rest are washed into the grey card and read Not Yet Covered.
- Hovering a covered tile swaps its art for a live snapshot of the 3D scene; clicking it selects the address and scrolls to the step heading.

## Rejection patterns

- **Eyebrow soup:** repeated uppercase metadata used as hierarchy.
- **Dashboard confetti:** grids of equal cards, badges, KPIs, and decorative status furniture.
- **Museum-poster hero:** oversized brand title that delays the apartment task.
- **Panel prison:** every item trapped in a bordered or shadowed box.
- **Orange target syndrome:** the whole target tower shouted in the confirmation accent.
- **Fixed render masquerading as 3D:** a canvas that cannot orbit, pan, zoom, or reset.
- **Provenance wallpaper:** source-state labels repeated until evidence becomes harder to read.

## Evaluation rule

Every release is captured at 1440 × 1000, 1024 × 900, and 390 × 844 for the fixed scenarios in `web/evaluation/scenarios.md`. A direct human must accept a blind before/after comparison before the deployed interface is replaced. Recurring corrections move to the narrowest owner: judgment here, reusable mechanics in primitives, and mechanical failures in tests.
