'use strict';

// ── Config ────────────────────────────────────────────────────
const YEAR_MIN = 2001;
const YEAR_MAX = 2022;
const DEFAULT_YEAR = YEAR_MAX;

// ── Animation constants ────────────────────────────────────────
const ANIM_STEP        = 0.25;   // advance in 15-min increments
const ANIM_SPEED_FAST  = 1.2;    // sim-hours/sec when sparse
const ANIM_SPEED_SLOW  = 0.15;   // sim-hours/sec when dense
const ANIM_BASE_RADIUS = 4;
const ANIM_START_HOUR  = 4;      // clock and dead-dot accumulation begin here

// ── Solar thresholds — set by updateSolarThresholds() after data loads ──
// Defaults are equinox approximations; replaced with SunCalc values at runtime.
let DAWN_START = 5.5;
let DAWN_END   = 7.0;
let DUSK_START = 19.0;
let DUSK_END   = 20.5;

// ── State ─────────────────────────────────────────────────────
let yearFrom = DEFAULT_YEAR;
let yearTo   = DEFAULT_YEAR;
let animMode    = 'day';  // 'day' | 'week'
let animData    = null;   // Map<slot, Feature[]>
let animFrame   = null;
let animPlaying = false;
let animHour    = ANIM_START_HOUR;
let animLastTs  = null;
let animLastUpdateHour = -1;
let animTrailHours  = 3;
let animMaxDensity  = 1;
let animCentLat     = 39.5;   // updated by updateSolarThresholds()
let animCentLon     = -98.35;
let animUtcOffset   = -6;
let animSolarCurve  = null;   // Float32Array[24] of solar altitudes in degrees, one per hour slot

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

// ── DOM refs ──────────────────────────────────────────────────
const countEl      = document.getElementById('count');
const loadingBar   = document.getElementById('loading-bar');

// ── Map init ──────────────────────────────────────────────────
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://tiles.openfreemap.org/styles/liberty',
  center: [-110.9747, 32.2226],  // Tucson, Pima County
  zoom: 11,
  attributionControl: true,
});

map.addControl(new maplibregl.NavigationControl(), 'top-right');

// ── Year range selectors ──────────────────────────────────────
const yearFromEl = document.getElementById('year-from');
const yearToEl   = document.getElementById('year-to');

for (let y = YEAR_MAX; y >= YEAR_MIN; y--) {
  const makeOpt = () => { const o = document.createElement('option'); o.value = y; o.textContent = y; return o; };
  yearFromEl.appendChild(makeOpt());
  yearToEl.appendChild(makeOpt());
}
yearFromEl.value = DEFAULT_YEAR;
yearToEl.value   = DEFAULT_YEAR;

// ── Map layers + boot ─────────────────────────────────────────
map.on('load', () => {
  // Incident source (active animated dots)
  map.addSource('incidents', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  });

  // Night overlay — between base tiles and incident layers
  map.addSource('night-overlay-src', {
    type: 'geojson',
    data: {
      type: 'Feature',
      geometry: {
        type: 'Polygon',
        coordinates: [[[-180,-85.051129],[180,-85.051129],[180,85.051129],[-180,85.051129],[-180,-85.051129]]],
      },
      properties: {},
    },
  });
  map.addLayer({ id: 'night-overlay', type: 'fill', source: 'night-overlay-src',
    paint: { 'fill-color': '#0a1628', 'fill-opacity': 0 } });

  // Active animated dots
  map.addLayer({
    id: 'incidents-circle',
    type: 'circle',
    source: 'incidents',
    paint: {
      'circle-radius':       ['get', 'anim_radius'],
      'circle-color':        '#ff1744',
      'circle-opacity':      ['get', 'anim_opacity'],
      'circle-stroke-width': 0,
    },
  });

  // Dead dots — persistent residue after trail expires
  map.addSource('incidents-dead', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  });
  map.addLayer({
    id: 'incidents-dead',
    type: 'circle',
    source: 'incidents-dead',
    paint: {
      'circle-radius':       ['interpolate', ['linear'], ['zoom'], 4, 1.5, 10, 3],
      'circle-color':        '#000000',
      'circle-opacity':      1,
      'circle-stroke-width': 0,
    },
  });

  loadAnimData();
});

// ── N6: Pop/fade function ─────────────────────────────────────
function popFade(age, trailHours) {
  if (age < 0 || age >= trailHours) return null;
  const t         = age / trailHours;
  const opacity   = Math.pow(1 - t, 1.5);
  const popFactor = Math.max(0, 1 - age * 3);
  const radius    = ANIM_BASE_RADIUS * (1 + 0.5 * popFactor);
  return { opacity, radius };
}

// ── N7: Active set builder ────────────────────────────────────
function buildActiveSet(hour = animHour) {
  if (!animData) return;

  const total  = animTotalHours();
  const active = [];
  const dead   = [];

  for (let s = 0; s < total; s++) {
    const bucket = animData.get(s);
    if (!bucket) continue;

    const age = (hour - s + total) % total;
    const pf  = popFade(age, animTrailHours);

    if (pf) {
      for (const feat of bucket) {
        active.push({
          ...feat,
          properties: { ...feat.properties, anim_opacity: pf.opacity, anim_radius: pf.radius },
        });
      }
    } else if (s >= ANIM_START_HOUR && s <= hour - animTrailHours) {
      for (const feat of bucket) dead.push(feat);
    }
  }

  map.getSource('incidents').setData({ type: 'FeatureCollection', features: active });
  map.getSource('incidents-dead').setData({ type: 'FeatureCollection', features: dead });

  updateMapFilter(hour % 24);

  // Solar elevation display — interpolated from per-slot curve
  const h24    = hour % 24;
  const h0     = Math.floor(h24) % 24;
  const h1     = (h0 + 1) % 24;
  const frac   = h24 % 1;
  const altDeg = animSolarCurve
    ? animSolarCurve[h0] + (animSolarCurve[h1] - animSolarCurve[h0]) * frac
    : 0;
  const icon    = altDeg > 0 ? '☀' : altDeg > -6 ? '◐' : '☾';
  const sign    = altDeg >= 0 ? '+' : '−';
  const absAlt  = Math.abs(altDeg).toFixed(1);

  // In week mode, prepend day name
  const totalH = animTotalHours();
  const absH   = Math.floor(hour) % totalH;
  const prefix = animMode === 'week' ? `${DAYS[Math.floor(absH / 24)]}  ` : '';

  countEl.textContent = `${prefix}${icon} ${sign}${absAlt}°`;
  countEl.classList.add('anim-clock');
}

// ── A2: Centroid computer ─────────────────────────────────────
function computeCentroid(features) {
  let latSum = 0, lonSum = 0, n = 0;
  for (const f of features) {
    const [lon, lat] = f.geometry.coordinates;
    if (lat != null && lon != null) { latSum += lat; lonSum += lon; n++; }
  }
  return n ? { lat: latSum / n, lon: lonSum / n } : { lat: 39.5, lon: -98.35 };
}

// ── A3: Solar threshold computer ──────────────────────────────
// Replaces hardcoded DAWN/DUSK constants with SunCalc values at the
// spring equinox for the data centroid. UTC offset approximated from
// centroid longitude: utcOffset = Math.round(centLon / 15).
function updateSolarThresholds(centLat, centLon) {
  animCentLat   = centLat;
  animCentLon   = centLon;
  const utcOffset = Math.round(centLon / 15);
  animUtcOffset = utcOffset;
  const equinox   = new Date(Date.UTC(2024, 2, 20, 12, 0, 0)); // March 20, 2024

  function toLocalHour(date) {
    return ((date.getUTCHours() + date.getUTCMinutes() / 60 + utcOffset) % 24 + 24) % 24;
  }

  const times = SunCalc.getTimes(equinox, centLat, centLon);
  DAWN_START = toLocalHour(times.dawn);
  DAWN_END   = toLocalHour(times.sunrise);
  DUSK_START = toLocalHour(times.sunset);
  DUSK_END   = toLocalHour(times.dusk);

  const latStr = Math.abs(centLat).toFixed(1) + '°' + (centLat >= 0 ? 'N' : 'S');
  const lonStr = Math.abs(centLon).toFixed(1) + '°' + (centLon >= 0 ? 'E' : 'W');
  document.getElementById('solar-ref').textContent = `Equinox · ${latStr}, ${lonStr}`;
}

// ── A6: Per-slot solar curve ──────────────────────────────────
// For each hour slot 0–23, compute mean lat/lon of incidents at that slot,
// then call SunCalc.getPosition(equinox, slotLat, slotLon) → altitude in degrees.
// 24 SunCalc calls total. Result drives updateMapFilter() directly.
function buildSolarCurve(hourBuckets) {
  const curve = new Float32Array(24);
  const equinox = new Date(Date.UTC(2024, 2, 20, 12, 0, 0));

  for (let h = 0; h < 24; h++) {
    const bucket = hourBuckets.get(h);
    if (!bucket || bucket.length === 0) {
      // fallback: use global centroid
      const utcH = ((h - animUtcOffset) % 24 + 24) % 24;
      const d = new Date(Date.UTC(2024, 2, 20, utcH, 0, 0));
      curve[h] = SunCalc.getPosition(d, animCentLat, animCentLon).altitude * (180 / Math.PI);
      continue;
    }

    let latSum = 0, lonSum = 0;
    for (const feat of bucket) {
      const [lon, lat] = feat.geometry.coordinates;
      latSum += lat; lonSum += lon;
    }
    const slotLat = latSum / bucket.length;
    const slotLon = lonSum / bucket.length;
    const utcOffset = Math.round(slotLon / 15);
    const utcH = ((h - utcOffset) % 24 + 24) % 24;
    const d = new Date(Date.UTC(2024, 2, 20, utcH, 0, 0));
    curve[h] = SunCalc.getPosition(d, slotLat, slotLon).altitude * (180 / Math.PI);
  }
  return curve;
}

// ── Map time-of-day filter ────────────────────────────────────
function updateMapFilter(hour24) {
  let altDeg;

  if (animSolarCurve) {
    // Interpolate between adjacent hour slots in the data-driven curve
    const h0   = Math.floor(hour24) % 24;
    const h1   = (h0 + 1) % 24;
    const frac = hour24 % 1;
    altDeg = animSolarCurve[h0] + (animSolarCurve[h1] - animSolarCurve[h0]) * frac;
  } else {
    // Fallback before curve is ready: use DAWN/DUSK thresholds
    const t = Math.max(0, Math.min(1,
      hour24 < DAWN_END   ? (hour24 - DAWN_START) / (DAWN_END - DAWN_START) :
      hour24 < DUSK_START ? 1 :
      hour24 < DUSK_END   ? 1 - (hour24 - DUSK_START) / (DUSK_END - DUSK_START) : 0
    ));
    altDeg = t * 90 - 18; // rough mapping: t=0 → -18°, t=1 → +72°
  }

  // Map altitude to overlay opacity: -18° = full dark, 0° = full light
  const daylight = Math.max(0, Math.min(1, (altDeg + 18) / 18));
  const s = daylight * daylight * (3 - 2 * daylight); // smoothstep
  map.setPaintProperty('night-overlay', 'fill-opacity',
    parseFloat((0.72 * (1 - s)).toFixed(2)));
}

// ── Dynamic speed ────────────────────────────────────────────
function animTotalHours() { return animMode === 'week' ? 168 : 24; }

function getDynamicSpeed() {
  const slot    = Math.floor(animHour) % animTotalHours();
  const count   = animData?.get(slot)?.length ?? 0;
  const density = Math.sqrt(count / animMaxDensity);
  return ANIM_SPEED_FAST + (ANIM_SPEED_SLOW - ANIM_SPEED_FAST) * density;
}

// ── N5: Animation clock ───────────────────────────────────────
function animTick(ts) {
  if (animPlaying && animLastTs !== null) {
    const dtHours = ((ts - animLastTs) / 1000) * getDynamicSpeed();
    animHour = (animHour + dtHours) % animTotalHours();

    const snapped = Math.floor(animHour / ANIM_STEP) * ANIM_STEP;
    if (snapped !== animLastUpdateHour) {
      buildActiveSet(snapped);
      animLastUpdateHour = snapped;
    }
  }
  animLastTs = ts;
  animFrame  = requestAnimationFrame(animTick);
}

// ── N4: Animation data loader ─────────────────────────────────
async function loadAnimData() {
  startLoad();
  animPlaying = false;
  animHour    = ANIM_START_HOUR;
  animLastTs  = null;
  animLastUpdateHour = -1;
  if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }

  try {
    const years = [];
    for (let y = Math.min(yearFrom, yearTo); y <= Math.max(yearFrom, yearTo); y++) years.push(y);

    const responses = await Promise.all(
      years.map(y => fetch(`/api/incidents?year=${y}`).then(r => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); }))
    );
    const allFeatures = responses.flatMap(r => r.features);
    const geojson = { features: allFeatures };

    // A2 + A3: compute centroid, update solar thresholds
    const { lat: centLat, lon: centLon } = computeCentroid(allFeatures);
    updateSolarThresholds(centLat, centLon);

    animData = new Map();
    for (const feat of geojson.features) {
      const h = feat.properties.hour;
      if (h == null || h > 23) continue;

      let slot;
      if (animMode === 'week') {
        const { year, month, day } = feat.properties;
        if (!year || !month || !day) continue;
        const dow = (new Date(year, month - 1, day).getDay() + 6) % 7; // Mon=0…Sun=6
        slot = dow * 24 + h;
      } else {
        slot = h;
      }

      if (!animData.has(slot)) animData.set(slot, []);
      animData.get(slot).push(feat);
    }

    animMaxDensity = 1;
    for (const bucket of animData.values()) {
      if (bucket.length > animMaxDensity) animMaxDensity = bucket.length;
    }

    // A6: build per-slot solar curve from hour-of-day buckets
    // In week mode, group by hour-of-day (slot % 24) for the solar lookup
    const hourBuckets = new Map();
    for (const [slot, bucket] of animData.entries()) {
      const h = slot % 24;
      if (!hourBuckets.has(h)) hourBuckets.set(h, []);
      hourBuckets.get(h).push(...bucket);
    }
    animSolarCurve = buildSolarCurve(hourBuckets);

    map.getSource('incidents-dead').setData({ type: 'FeatureCollection', features: [] });
    endLoad();
    animPlaying = true;
    updatePlayPauseBtn();
    animFrame = requestAnimationFrame(animTick);
  } catch (err) {
    countEl.textContent = 'Error loading data';
    endLoad();
    console.error(err);
  }
}

// ── Playback controls ─────────────────────────────────────────
const animPlayPauseBtn = document.getElementById('anim-playpause');
const trailSlider      = document.getElementById('trail-slider');
const trailValueEl     = document.getElementById('trail-value');

function updatePlayPauseBtn() {
  animPlayPauseBtn.textContent = animPlaying ? '⏸ Pause' : '▶ Play';
}

animPlayPauseBtn.addEventListener('click', () => {
  if (!animData) return;
  animPlaying = !animPlaying;
  if (animPlaying) animLastTs = null;
  updatePlayPauseBtn();
});

document.getElementById('anim-rewind').addEventListener('click', () => {
  if (!animData) return;
  animHour           = ANIM_START_HOUR;
  animLastTs         = null;
  animLastUpdateHour = -1;
  map.getSource('incidents-dead').setData({ type: 'FeatureCollection', features: [] });
  buildActiveSet(ANIM_START_HOUR);
});

document.getElementById('anim-mode-day').addEventListener('click', () => {
  if (animMode === 'day') return;
  animMode = 'day';
  document.getElementById('anim-mode-day').classList.add('active');
  document.getElementById('anim-mode-week').classList.remove('active');
  loadAnimData();
});

document.getElementById('anim-mode-week').addEventListener('click', () => {
  if (animMode === 'week') return;
  animMode = 'week';
  document.getElementById('anim-mode-week').classList.add('active');
  document.getElementById('anim-mode-day').classList.remove('active');
  loadAnimData();
});

trailSlider.addEventListener('input', () => {
  animTrailHours = Number(trailSlider.value);
  trailValueEl.textContent = `${animTrailHours}h`;
  if (animData) buildActiveSet();
});

yearFromEl.addEventListener('change', () => {
  yearFrom = Number(yearFromEl.value);
  // keep yearTo >= yearFrom
  if (yearTo < yearFrom) { yearTo = yearFrom; yearToEl.value = yearTo; }
  loadAnimData();
});

yearToEl.addEventListener('change', () => {
  yearTo = Number(yearToEl.value);
  // keep yearFrom <= yearTo
  if (yearFrom > yearTo) { yearFrom = yearTo; yearFromEl.value = yearFrom; }
  loadAnimData();
});

// ── Loading bar ───────────────────────────────────────────────
function startLoad() {
  loadingBar.classList.remove('hidden', 'done');
  loadingBar.classList.add('active');
  countEl.textContent = 'Loading…';
  countEl.classList.add('loading');
  countEl.classList.remove('anim-clock');
}

function endLoad() {
  loadingBar.classList.remove('active');
  loadingBar.classList.add('done');
  countEl.classList.remove('loading');
  setTimeout(() => loadingBar.classList.add('hidden'), 500);
}
