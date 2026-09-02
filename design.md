# Apartment Intelligence design system

## The reader and the job

Apartment Intelligence is for a resident deciding whether an existing HDB apartment will receive the sun they expect. The reader must be able to identify the apartment, understand what is known versus approximated, inspect four environmental studies, and keep evidence without learning architectural software.

The apartment question and evidence come before branding. The interface should read like an architectural feature that is interactive, agent-operable, and exportable—not a dashboard, wizard, marketing page, or certification report.

## Composition

- Use an editorial workbench: quiet masthead, concise study summary, dominant architectural canvas, contextual reading rail, then paced evidence chapters.
- Desktop uses a 12-column grid. The canvas occupies eight columns and the rail four. Tablet uses six columns. Mobile uses four columns and places the canvas before controls.
- Prefer a continuous paper field, thin rules, precise alignment, and meaningful whitespace. A bordered surface exists only when containment or interaction requires it.
- The 3D precinct is the lead image. Sunpath is the celestial diagram; Shadow is a time study; Solar Access and Radiation are facade evidence drawings.
- The five steps remain product state, not a permanent tab strip. Show a short location line and a modest progress index.

## Typography

- Newsreader is the editorial voice: display headlines, study questions, explanatory prose, findings, and report narrative.
- Inter is the instrument voice: controls, numbers, captions, legends, provenance, metadata, and technical annotation.
- Display: 56–88 px desktop, 44–58 px tablet, 38–48 px mobile; line-height 0.95–1.02.
- Chapter title: 40–56 px desktop, 34–42 px mobile; line-height 1.02–1.1.
- Reading text: 18–22 px, line-height 1.45–1.6, maximum 66 characters.
- Interface text: 12–15 px, line-height 1.35–1.5. Use tabular figures for measurements.
- Labels use sentence case. Uppercase is reserved for compact drawing references of three words or fewer.

## Tokens

### Grid and rhythm

- Container: `min(100% - 48px, 1440px)` desktop; 32 px tablet; 20 px mobile gutters.
- Columns: 12 / 6 / 4 with 20 px desktop and tablet gaps, 12 px mobile gaps.
- Spacing scale: 4, 8, 12, 16, 24, 32, 48, 72, 96 px.
- Rules: 1 px graphite at full emphasis, 1 px stone for subordinate divisions.
- Controls: minimum 44 px target; square or 2 px radius; 2 px focus outline with 3 px offset.

### Colour

- Paper `#f5f2e9`; white paper `#fbfaf6`; ink `#18211d`; muted ink `#5f665f`; rule `#b9b7ae`.
- Sourced context `#d9ddd5`; inferred massing `#e7e1d4`; selected precinct `#bfc9bf`.
- Solar yellow `#f2c230`; confirmed home red `#c8472d`; shaded `#45534d`.
- Radiation scale: `#183f5a → #2b8c86 → #e3c946 → #c8472d`.
- Colour is semantic. Never use gradients, badges, or accent fills as decoration.

## Architectural canvas

- Open on an intentional north-west axonometric view with the full Dawson context visible, a level horizon, and useful ground margin.
- Orbit, pan, zoom, reset, north, and stage-aware presets must be visible and keyboard reachable.
- Surrounding buildings are neutral. Block 87 receives only a quiet secondary distinction. The confirmed window/unit zone alone receives the strongest red.
- North, view name, scale/extent note, and analysis legend belong to the drawing edge, not floating dashboard cards.
- A live 3D surface must respond to pointer orbit, right-button/modified pan, wheel/pinch zoom, and reset. A fixed render must never be presented as interactive 3D.

## Environmental studies

- **Sunpath:** show seasonal paths, selected-date path, cardinal directions, and date legend. Yellow is reserved for solar geometry.
- **Shadow:** provide 09:00, 12:00, and 15:00 conditions. Show the selected time, solar altitude/azimuth, and facade sunlit fraction.
- **Solar Access:** show a 16 × 8 facade grid for each seasonal date with one continuous hours scale.
- **Radiation:** show the annual 16 × 8 facade heatmap, minimum/average/maximum, units, and the approximation limits.
- Every graphic must make method, time period, units, orientation, and limitation inspectable without requiring provenance to dominate the view.

## Evidence states

- Sourced: quiet solid neutral fill and solid rule.
- Inferred: warm neutral fill and fine dashed annotation.
- Human-confirmed: confirmed-home red, solid rule, and explicit confirmation sentence.
- Generated/calculated: analysis scale plus method caption.
- Provenance lives in a disclosure and in report captions. Do not repeat large state labels across every surface.

## Interaction and copy

- Controls and WebMCP actions use the same reducer and visible state.
- Human confirmation remains a visible first-party action and cannot be supplied by a tool parameter.
- Lead with the resident’s next decision: “Choose the facade you recognise,” not system narration.
- Use direct, specific language. Avoid marketing claims, exclamation marks, AI vocabulary, and unexplained analysis jargon.
- Loading, refusal, stale confirmation, and export states stay inline and preserve the reader’s place.

## Responsive and accessible behaviour

- At 1024 px, the canvas spans all six columns and the reading rail becomes a two-column section below it.
- At 390 px, the canvas appears first at a 4:3 ratio. Controls follow in document order; no desktop split is squeezed into the viewport.
- Never rely on colour alone. Pair colour with line style, text, or pattern.
- Maintain WCAG AA contrast, visible focus, reduced-motion support, semantic landmarks, status announcements, and labels for canvas controls.
- No horizontal document overflow. The canvas must resize with its container and retain usable controls at 200% zoom.

## Export system

- All cards are exactly 1600 × 2400 and share one portrait editorial grid, type system, caption position, method/limitation block, source line, and digest footer.
- Each card has a distinct evidence composition; do not fit every result into the same generic card.
- Site & Unit uses the deterministic Dawson footprint scene and confirmed window geometry, never schematic placeholder blocks.
- The PDF is the five cards in order: Site & Unit, Sunpath, Shadow, Solar Access, Radiation.
- Export typography uses the loaded Newsreader and Inter faces before canvas rendering begins.

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
