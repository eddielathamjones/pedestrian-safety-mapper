# Pedestrian Safety Mapper — Roadmap

## Design direction

Two perspectives inform this project's visual and analytical direction:

**Tufte:** Show the data honestly. Maximise data-ink ratio. Every visual element should encode
a variable, not decorate. The solar overlay is the most honest encoding on the map — darkness
in the data shown as darkness in the display. Lean into that. Remove what doesn't carry information.

**Byrne:** Make it impossible to look away. These are deaths. The violence of the symbol is
appropriate to the subject. The road heat lines showing the city's arterial pathology are the
best thing on the map — lean into them. Sound is data too. The week mode tells a richer story
than the day mode. The solar overlay doesn't just look interesting — it's evidence.

Where they agree: the solar overlay from geochron-web is the next priority. Darkness is causal,
not decorative. Tile vibes are the wrong direction for this project — the map already has its own
mood, it doesn't need a filter applied from outside.

---

## Phase 1 — Polish the flagship (current priority)

- [x] Time-of-day animation — 24hr animated cycle showing fatalities across the day
- [x] Progress bar, 12h clock, incident count (total + visible in view)
- [x] Sprite differentiation — active dots loud/vivid on first appearance, accumulated/dead dots
      smaller and quieter; the moment of impact should matter visually (Byrne)
- [x] Week mode elevated — default mode, day name prepended to clock display (Byrne)
- [ ] Static time-window filter mode — hour range sliders, solar-adjusted, multi-year density
      heatmap (issue #5); use raw `hour` data as ground truth, cross-reference `tod` field as
      data quality validation (Tufte)
- [ ] Street View integration — pull imagery for incident locations on click; only valuable if
      it shows something causal (no crosswalk, unlit road, high-speed geometry) (Tufte)
- [ ] Performance and UX polish
- [ ] Self-host on HP server at `mapper.eddielathamjones.com` (always-on, no cold starts)

---

## Phase 2 — Absorb from POC experiments

### Solar / Daylight Overlay (from geochron-web) — PRIORITY
- Extract solar geometry module from geochron-web backend (terminator, night polygon, subsolar point)
- Add `/api/solar` endpoint to safety mapper backend
- Render actual solar terminator as a GeoJSON layer in MapLibre — not just a uniform opacity
  overlay but the real terminator line moving across the map
- This becomes MORE powerful here than in geochron-web — darkness is causal, not aesthetic.
  The correlation between the terminator and the fatality clusters will be visually obvious.
- Do this before tile vibes (Tufte + Byrne agree)
- See: https://github.com/eddielathamjones/geochron-web

### Sound layer (Byrne)
- A quiet ambient tone when each dot first appears during animation
- Density becomes audible — evening peak hours will sound different from 4am silence
- Sound is data; the ear catches temporal patterns the eye misses
- Low priority technically but high impact for installation/presentation contexts

### Streetlight data overlay (Byrne)
- Real streetlight coverage as a layer alongside the solar overlay
- Hypothesis: the places without streetlights match the fatality clusters exactly
- That visual correlation would be the most powerful single frame in the project
- Data source TBD — OpenStreetMap has some streetlight data; city open data portals may have better

### Tile Vibe System (from map-tile-interceptor) — DEPRIORITISED
- This map already has its own mood. Applying noir or vintage filters from outside adds nothing.
- The POC repo stays as the canonical demonstration of the server-side raster approach
- Do not absorb into safety mapper — wrong direction for this project
- See: https://github.com/eddielathamjones/map-tile-interceptor

---

## Phase 3 — Future ML direction

- Predictive risk scoring model — "where will fatalities happen" not just "where did they"
- FARS feature data (time, road type, lighting, weather) makes this viable
- See: docs/future-ml-direction.md

---

## Portfolio narrative

This project is the flagship of a "lab + flagship" portfolio structure.
The POC repos (tile-interceptor, geochron-web) are experiments that proved out
components before they were absorbed here. The Ghost site at eddielathamjones.com
tells this story.

The solar overlay arc is the narrative spine: built as a standalone visual experiment
in geochron-web, it becomes analytically meaningful here — the same code answers a
different question. That transformation of purpose is what makes the portfolio compelling.
