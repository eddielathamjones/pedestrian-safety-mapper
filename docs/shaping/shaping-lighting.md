---
shaping: true
---

# Solar-Corrected Lighting Visualization — Shaping

---

## Requirements (R)

| ID | Requirement | Status |
|----|-------------|--------|
| R0 | Show when fatalities occur relative to actual astronomical darkness — not clock time — by making the day/night background solar-accurate for the region | Core goal |
| R1 | Day/night background transitions driven by SunCalc.js using real sunrise/sunset times — not hardcoded clock approximations | Must-have |
| R2 | Reference date: spring equinox (March 20) as baseline; seasonal variation is phase 2 | Must-have |
| R3 | Reference location: geographic centroid of the year's incident data, computed client-side at animation load | Must-have |
| R4 | Interface stripped to animation only — year selector, play/pause, rewind, trail slider; Points and Heatmap views removed | Must-have |
| R5 | No new backend infrastructure; SunCalc.js runs entirely client-side | Must-have |
| R6 | Dots not affected by solar computation — background shading only | Must-have |

---

## A: SunCalc thresholds fed into existing smoothstep machinery

Replace the four hardcoded clock constants with values computed from SunCalc.js.
Everything else — the night overlay layer, the smoothstep curve, the animation engine — is unchanged.

| Part | Mechanism | Flag |
|------|-----------|:----:|
| A1 | Add SunCalc.js via CDN `<script>` tag — no bundler, no install | |
| A2 | **Centroid computer** — after `loadAnimData()` resolves, compute mean lat/lon across all features in the year → `{ centLat, centLon }` | |
| A3 | **Solar threshold computer** — `SunCalc.getTimes(equinox, centLat, centLon)` → extract `dawn`, `sunrise`, `sunset`, `dusk` as fractional local hours → replace `DAWN_START / DAWN_END / DUSK_START / DUSK_END`; UTC→local via `Math.round(centLon / 15)` | |
| A4 | **Simplified UI** — remove Points / Heatmap view toggle; app opens directly in animation mode on load | |
| A5 | **Reference label** — small text in controls showing "Equinox · [lat, lon]" so the reference is visible | |
| A6 | **Per-slot solar curve** — for each hour slot (0–23), compute mean lat/lon of incidents at that slot; one `SunCalc.getPosition(equinox, slotLat, slotLon)` call per slot → `animSolarCurve[24]` of altitudes in degrees; `updateMapFilter()` interpolates this curve instead of the fixed smoothstep; sun elevation display uses the slot's own altitude | |

---

## Fit Check — R × A

| Req | Requirement | Status | A |
|-----|-------------|--------|---|
| R0 | Show fatalities relative to actual astronomical darkness | Core goal | ✅ |
| R1 | Background transitions driven by SunCalc, not hardcoded approximations | Must-have | ✅ |
| R2 | Spring equinox as reference date baseline | Must-have | ✅ |
| R3 | 🟡 Reference location = per-slot incident centroid (A6 upgrades A3 from one global centroid to one per hour slot) | Must-have | ✅ |
| R4 | Interface stripped to animation only | Must-have | ✅ |
| R5 | No new backend infrastructure | Must-have | ✅ |
| R6 | Dots unchanged | Must-have | ✅ |

**All parts resolved.**

---

## Phase 2 (out of scope now)

| ID | Idea |
|----|------|
| P2-1 | Seasonal scrubber — let user change reference date; background shifts to show winter short days vs. summer long days |
| P2-2 | Viewport-adaptive centroid — reference location updates as user pans, so zooming into Alaska shows Alaska's daylight hours |
| P2-3 | Per-incident solar classification — compute sun altitude at each incident's actual lat/lon/date/time; color or size dots by true darkness |
