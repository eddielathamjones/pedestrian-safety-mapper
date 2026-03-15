'use strict';

// ── Config ────────────────────────────────────────────────────
const YEAR_MIN = 2001;
const YEAR_MAX = 2023;
const DEFAULT_YEAR = YEAR_MAX;

// ── Animation constants ────────────────────────────────────────
const ANIM_STEP        = 0.25;   // advance in 15-min increments
const ANIM_SPEED_FAST  = 1.2;    // sim-hours/sec when sparse
const ANIM_SPEED_SLOW  = 0.15;   // sim-hours/sec when dense
const ANIM_BASE_RADIUS = 4;
const ANIM_START_HOUR  = 12;     // clock and dead-dot accumulation begin here

// ── Solar thresholds — set by updateSolarThresholds() after data loads ──
// Defaults are equinox approximations; replaced with SunCalc values at runtime.
let DAWN_START = 5.5;
let DAWN_END   = 7.0;
let DUSK_START = 19.0;
let DUSK_END   = 20.5;

// ── State ─────────────────────────────────────────────────────
let yearFrom = DEFAULT_YEAR;
let yearTo   = DEFAULT_YEAR;
let animMode    = 'week';  // 'day' | 'week'
let animData    = null;   // Map<slot, Feature[]>
let animFrame   = null;
let animPlaying = false;
let animHour    = ANIM_START_HOUR;
let animLastTs  = null;
let animLastUpdateHour = -1;
const animTrailHours = 3;
let animMaxDensity  = 1;
let animCentLat     = 39.5;   // updated by updateSolarThresholds()
let animCentLon     = -98.35;
let animUtcOffset   = -6;
let animSolarCurve  = null;   // Float32Array[24] of solar altitudes in degrees, one per hour slot
let allLoadedFeatures = [];   // all features from the last loadAnimData() call

// ── Animation speed multiplier ────────────────────────────────
let animSpeedMult = 1.0;

// ── Animate day-of-week filter ─────────────────────────────────
let animDows = new Set([0, 1, 2, 3, 4, 5, 6]); // Mon=0…Sun=6

// ── Filter state ───────────────────────────────────────────────
let viewMode        = 'animate'; // 'animate' | 'filter'
let filterFrom      = 17; // slider value 12–35 (noon-based)
let filterTo        = 23; // 11:00 PM default
let filterDows      = new Set([0, 1, 2, 3, 4, 5, 6]); // Mon=0…Sun=6
let filteredFeatures = []; // current filter result, kept for viewport count updates

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

// Double-click the compass to reset pitch back to top-down view.
// Single click (MapLibre default) already resets bearing to north.
setTimeout(() => {
  const compassBtn = document.querySelector('.maplibregl-ctrl-compass');
  if (!compassBtn) return;
  compassBtn.title = 'Click: reset north  ·  Double-click: top-down view';
  compassBtn.addEventListener('dblclick', e => {
    e.stopPropagation();
    map.easeTo({ pitch: 0, bearing: 0, duration: 400 });
  });
}, 0);

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

// ── Sprite: sun marker ────────────────────────────────────────
function createSunSprite(size) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  const cx = size / 2, cy = size / 2;

  // Soft outer corona
  const corona = ctx.createRadialGradient(cx, cy, size * 0.12, cx, cy, size * 0.48);
  corona.addColorStop(0,   'rgba(255,230,80,0.7)');
  corona.addColorStop(0.5, 'rgba(255,180,0,0.3)');
  corona.addColorStop(1,   'rgba(255,120,0,0)');
  ctx.beginPath(); ctx.arc(cx, cy, size * 0.48, 0, Math.PI * 2);
  ctx.fillStyle = corona; ctx.fill();

  // Disc
  const disc = ctx.createRadialGradient(cx, cy, 0, cx, cy, size * 0.18);
  disc.addColorStop(0,   '#fffde0');
  disc.addColorStop(0.6, '#ffe066');
  disc.addColorStop(1,   '#ffa500');
  ctx.beginPath(); ctx.arc(cx, cy, size * 0.18, 0, Math.PI * 2);
  ctx.fillStyle = disc; ctx.fill();

  return ctx.getImageData(0, 0, size, size);
}

// ── Sprite: soft glowing ember ────────────────────────────────
function createEmberSprite(size) {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = size;
  const ctx = canvas.getContext('2d');
  const cx = size / 2, cy = size / 2;

  // Outer halo — three-phase decay: bright → ember → dark → gone
  const halo = ctx.createRadialGradient(cx, cy, 0, cx, cy, size * 0.48);
  halo.addColorStop(0.0,  'rgba(255,200,80,0.9)');
  halo.addColorStop(0.35, 'rgba(255,60,0,0.7)');
  halo.addColorStop(0.7,  'rgba(180,0,0,0.3)');
  halo.addColorStop(0.88, 'rgba(80,0,0,0.08)');
  halo.addColorStop(1.0,  'rgba(0,0,0,0)');
  ctx.beginPath();
  ctx.arc(cx, cy, size * 0.48, 0, Math.PI * 2);
  ctx.fillStyle = halo;
  ctx.fill();

  // Bright core
  const core = ctx.createRadialGradient(cx, cy, 0, cx, cy, size * 0.18);
  core.addColorStop(0,   '#fff8d0');
  core.addColorStop(0.5, '#ffcc00');
  core.addColorStop(1,   '#ff4400');
  ctx.beginPath();
  ctx.arc(cx, cy, size * 0.18, 0, Math.PI * 2);
  ctx.fillStyle = core;
  ctx.fill();

  return ctx.getImageData(0, 0, size, size);
}


// ── Road heat lines ───────────────────────────────────────────
// Connect each dead point to its nearest neighbor(s) within THRESHOLD degrees.
// Because FARS points are on roads, edges naturally follow road geometry.
// Density = number of nearby points, drives color and width.
function buildRoadHeatLines(features) {
  if (features.length < 2) return { type: 'FeatureCollection', features: [] };

  const THRESHOLD = 0.0012; // ~130m — spans a city block
  const CELL      = 0.0008; // grid cell slightly smaller than threshold

  // Spatial grid index
  const grid = new Map();
  for (const f of features) {
    const [lon, lat] = f.geometry.coordinates;
    const key = `${Math.floor(lon / CELL)},${Math.floor(lat / CELL)}`;
    if (!grid.has(key)) grid.set(key, []);
    grid.get(key).push(f);
  }

  const lines = [];
  const seen  = new Set();

  for (const f of features) {
    const [lon, lat] = f.geometry.coordinates;
    const gx = Math.floor(lon / CELL);
    const gy = Math.floor(lat / CELL);

    let nearest     = null;
    let nearestDist = Infinity;
    let nearbyCount = 0;

    for (let dx = -2; dx <= 2; dx++) {
      for (let dy = -2; dy <= 2; dy++) {
        const cell = grid.get(`${gx + dx},${gy + dy}`);
        if (!cell) continue;
        for (const other of cell) {
          if (other === f) continue;
          const d = Math.hypot(lon - other.geometry.coordinates[0], lat - other.geometry.coordinates[1]);
          if (d < THRESHOLD) {
            nearbyCount++;
            if (d < nearestDist) { nearestDist = d; nearest = other; }
          }
        }
      }
    }

    if (!nearest) continue;

    const edgeKey = [
      f.geometry.coordinates.join(','),
      nearest.geometry.coordinates.join(','),
    ].sort().join('|');
    if (seen.has(edgeKey)) continue;
    seen.add(edgeKey);

    lines.push({
      type: 'Feature',
      geometry: { type: 'LineString', coordinates: [f.geometry.coordinates, nearest.geometry.coordinates] },
      properties: { density: nearbyCount },
    });
  }

  return { type: 'FeatureCollection', features: lines };
}

// ── Map layers + boot ─────────────────────────────────────────
map.on('load', () => {
  map.addImage('ember', createEmberSprite(64));
  map.addImage('sun',   createSunSprite(48));

  // Road heat lines source
  map.addSource('road-heat-lines', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  });

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

  // Solar terminator + sun marker
  map.addSource('terminator-src', {
    type: 'geojson',
    data: { type: 'Feature', geometry: { type: 'LineString', coordinates: [] }, properties: {} },
  });
  // Wide soft glow behind the line
  map.addLayer({
    id: 'terminator-glow',
    type: 'line',
    source: 'terminator-src',
    paint: {
      'line-color': '#fbbf24',
      'line-width': 12,
      'line-opacity': 0.18,
      'line-blur': 8,
    },
  });
  // Crisp line on top
  map.addLayer({
    id: 'terminator',
    type: 'line',
    source: 'terminator-src',
    paint: {
      'line-color': '#fde68a',
      'line-width': 2,
      'line-opacity': 0.9,
    },
  });

  // Sun marker at the subsolar point
  map.addSource('sun-src', {
    type: 'geojson',
    data: { type: 'Feature', geometry: { type: 'Point', coordinates: [0, 0] }, properties: {} },
  });
  map.addLayer({
    id: 'sun-marker',
    type: 'symbol',
    source: 'sun-src',
    layout: {
      'icon-image': 'sun',
      'icon-size': 1,
      'icon-allow-overlap': true,
      'icon-ignore-placement': true,
    },
    paint: { 'icon-opacity': 0 },  // hidden until terminator is active
  });

  // Active animated dots
  map.addLayer({
    id: 'incidents-circle',
    type: 'symbol',
    source: 'incidents',
    layout: {
      'icon-image':             'ember',
      'icon-allow-overlap':     true,
      'icon-ignore-placement':  true,
      'icon-size': ['interpolate', ['linear'], ['get', 'anim_radius'], 4, 0.32, 6, 0.55, 8, 0.85],
    },
    paint: {
      'icon-opacity': ['get', 'anim_opacity'],
    },
  });

  // Dead dots — persistent residue after trail expires
  map.addSource('incidents-dead', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  });
  // Road heat glow — same source as dead dots, renders below them
  map.addLayer({
    id: 'road-heat',
    type: 'heatmap',
    source: 'incidents-dead',
    paint: {
      'heatmap-weight':     1,
      'heatmap-radius':     ['interpolate', ['linear'], ['zoom'],  4, 10,  12, 30],
      'heatmap-intensity':  ['interpolate', ['linear'], ['zoom'],  4, 0.6, 12, 2.5],
      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0.00, 'rgba(0,0,0,0)',
        0.10, 'rgba(25,0,0,0.4)',
        0.30, 'rgba(90,5,0,0.65)',
        0.55, 'rgba(200,25,0,0.80)',
        0.75, 'rgba(255,90,0,0.88)',
        0.90, 'rgba(255,175,10,0.93)',
        1.00, 'rgba(255,245,120,0.97)',
      ],
      'heatmap-opacity': 0.5,
    },
  });

  // Road heat glow lines — directional heat following road geometry
  map.addLayer({
    id: 'road-heat-glow',
    type: 'line',
    source: 'road-heat-lines',
    layout: { 'line-join': 'round', 'line-cap': 'round' },
    paint: {
      'line-color': [
        'interpolate', ['linear'], ['get', 'density'],
        1,   '#1a0000',
        3,   '#6b0000',
        8,   '#cc2200',
        20,  '#ff5500',
        50,  '#ff9900',
        100, '#ffee44',
      ],
      'line-width': [
        'interpolate', ['linear'], ['get', 'density'],
        1, 2, 10, 5, 50, 10, 100, 16,
      ],
      'line-blur':    4,
      'line-opacity': 0.85,
    },
  });

  map.addLayer({
    id: 'incidents-dead',
    type: 'symbol',
    source: 'incidents-dead',
    layout: {
      'icon-image':             'ember',
      'icon-allow-overlap':     true,
      'icon-ignore-placement':  true,
      'icon-size': ['interpolate', ['linear'], ['zoom'], 4, 0.10, 10, 0.22],
    },
    paint: {
      'icon-opacity': 0.3,
    },
  });

  loadAnimData();
});

// ── N6: Pop/fade function ─────────────────────────────────────
function popFade(age, trailHours) {
  if (age < 0 || age >= trailHours) return null;
  const t         = age / trailHours;
  const opacity   = Math.max(0.35, Math.pow(1 - t, 1.5));
  const popFactor = Math.max(0, 1 - age * 3);
  const radius    = ANIM_BASE_RADIUS * (1 + popFactor);
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
    } else if (s >= getAnimStartHour() && s <= hour - animTrailHours) {
      for (const feat of bucket) {
        dead.push({ ...feat, properties: { ...feat.properties, died_at_slot: s } });
      }
    }
  }

  // Decay opacity: fresh dead dots start at 0.5, fade to 0.03 over DECAY_HOURS sim-hours.
  // Expression is evaluated per-feature on the GPU; we just bake in the current cutoff.
  const DECAY_HOURS  = 8;
  const deathCutoff  = hour - animTrailHours;
  map.setPaintProperty('incidents-dead', 'icon-opacity', [
    'max', 0.30,
    ['-', 0.35,
      ['*', 0.05,
        ['min', 1, ['max', 0,
          ['/', ['-', deathCutoff, ['get', 'died_at_slot']], DECAY_HOURS],
        ]],
      ],
    ],
  ]);

  map.getSource('incidents').setData({ type: 'FeatureCollection', features: active });
  map.getSource('incidents-dead').setData({ type: 'FeatureCollection', features: dead });
  map.getSource('road-heat-lines').setData(buildRoadHeatLines(dead));

  updateMapFilter(hour % 24);
  updateTerminator(hour % 24);
  drawSunHUD(hour % 24);

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

  // Build clock string (12h AM/PM)
  const hInt   = Math.floor(h24);
  const mInt   = Math.floor((h24 % 1) * 60);
  const h12    = hInt % 12 || 12;
  const ampm   = hInt < 12 ? 'AM' : 'PM';
  const timeStr = `${h12}:${mInt.toString().padStart(2, '0')} ${ampm}`;

  // In week mode, prepend day name
  const totalH = animTotalHours();
  const absH   = Math.floor(hour) % totalH;
  const prefix = animMode === 'week' ? `${DAYS[Math.floor(absH / 24)]}  ` : '';

  countEl.textContent = `${prefix}${timeStr}`;
  countEl.classList.add('anim-clock');

  // Progress bar
  const progressFill = document.getElementById('anim-progress-fill');
  if (progressFill) progressFill.style.width = `${(h24 / 24) * 100}%`;

  // Solar condition label
  const solarRef = document.getElementById('solar-ref');
  if (solarRef) {
    const condition = altDeg > 6   ? 'Daytime'
                    : altDeg > 0   ? 'Sunrise / Sunset'
                    : altDeg > -6  ? 'Civil twilight'
                    : altDeg > -12 ? 'Nautical twilight'
                    :                'Night';
    solarRef.textContent = `${condition}  ·  sun ${sign}${absAlt}° altitude`;
  }
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

// ── Solar terminator ──────────────────────────────────────────
// Computes the great-circle boundary between day and night on Earth's surface.

function getSubsolarPoint(utcDate) {
  // Approximate subsolar longitude: the meridian where it is currently solar noon.
  const utcH = utcDate.getUTCHours() + utcDate.getUTCMinutes() / 60;
  const lon = ((12 - utcH) * 15 + 180) % 360 - 180;
  // Binary-search for subsolar latitude (= solar declination).
  let lat = 0;
  for (let step = 45; step > 0.05; step /= 2) {
    const up   = SunCalc.getPosition(utcDate, lat + step, lon).altitude;
    const down = SunCalc.getPosition(utcDate, lat - step, lon).altitude;
    if (up > down) lat += step; else lat -= step;
  }
  return { lat, lon };
}

function buildTerminatorGeoJSON(subsolarLat, subsolarLon) {
  const φs = subsolarLat * Math.PI / 180;
  const λs = subsolarLon * Math.PI / 180;

  // Subsolar unit vector in 3-D Cartesian.
  const sx = Math.cos(φs) * Math.cos(λs);
  const sy = Math.cos(φs) * Math.sin(λs);
  const sz = Math.sin(φs);

  // Two orthogonal basis vectors in the terminator plane (perpendicular to S).
  let ux, uy, uz;
  if (Math.abs(sz) > 0.99) {
    ux = 1; uy = 0; uz = 0;
  } else {
    const len = Math.hypot(sy, sx);
    ux = sy / len; uy = -sx / len; uz = 0;
  }
  const vx = sy * uz - sz * uy;
  const vy = sz * ux - sx * uz;
  const vz = sx * uy - sy * ux;

  // Parameterise the great circle and project back to (lon, lat).
  const N = 180;
  const raw = [];
  for (let i = 0; i <= N; i++) {
    const t = (i / N) * 2 * Math.PI;
    const c = Math.cos(t), s = Math.sin(t);
    const px = c * ux + s * vx;
    const py = c * uy + s * vy;
    const pz = c * uz + s * vz;
    raw.push([
      Math.atan2(py, px) * 180 / Math.PI,
      Math.asin(Math.max(-1, Math.min(1, pz))) * 180 / Math.PI,
    ]);
  }

  // Split at antimeridian jumps to avoid lines crossing the whole map.
  const segments = [[]];
  for (let i = 0; i < raw.length; i++) {
    if (i > 0 && Math.abs(raw[i][0] - raw[i - 1][0]) > 180) segments.push([]);
    segments[segments.length - 1].push(raw[i]);
  }
  const lines = segments.filter(s => s.length > 1);

  return {
    type: 'Feature',
    geometry: lines.length === 1
      ? { type: 'LineString', coordinates: lines[0] }
      : { type: 'MultiLineString', coordinates: lines },
    properties: {},
  };
}

// ── Sun HUD ───────────────────────────────────────────────────
// A small compass drawn on a canvas fixed to the map corner.
// The sun dot's angle = azimuth; distance from centre = 1 − (altitude/90°),
// clamped so the dot sits on the ring when the sun is on the horizon.
function drawSunHUD(hour24) {
  const canvas = document.getElementById('sun-hud-canvas');
  const hud    = document.getElementById('sun-hud');
  if (!canvas || !hud) return;

  const center = map.getCenter();
  const utcH   = ((hour24 - animUtcOffset) % 24 + 24) % 24;
  const date   = new Date(Date.UTC(2024, 2, 20, Math.floor(utcH),
                                    Math.round((utcH % 1) * 60)));
  const pos    = SunCalc.getPosition(date, center.lat, center.lng);
  const altDeg = pos.altitude * 180 / Math.PI;
  // SunCalc azimuth: 0 = south, clockwise positive when viewed from above.
  // Convert to compass bearing (0 = north, clockwise).
  const bearing = ((pos.azimuth * 180 / Math.PI) + 180 + 360) % 360;

  const W = canvas.width, H = canvas.height;
  // Compass occupies top 74px; bottom 16px reserved for time label.
  const compassH = 74;
  const cx = W / 2, cy = compassH / 2;
  const R = cy - 5;  // ring radius

  const ctx = canvas.getContext('2d');
  ctx.clearRect(0, 0, W, H);

  // Background disc
  ctx.beginPath(); ctx.arc(cx, cy, R + 3, 0, Math.PI * 2);
  ctx.fillStyle = 'rgba(15,23,42,0.75)'; ctx.fill();

  // Ring
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(255,255,255,0.2)'; ctx.lineWidth = 1; ctx.stroke();

  // Horizon circle (dashed) — where altitude = 0
  ctx.beginPath(); ctx.arc(cx, cy, R * 0.68, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(255,255,255,0.15)';
  ctx.setLineDash([2, 4]); ctx.lineWidth = 1; ctx.stroke(); ctx.setLineDash([]);

  // Cardinal tick marks + labels — drawn before the sun dot
  ctx.font = '8px system-ui, sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  for (const [compassDeg, label] of [[0,'N'],[90,'E'],[180,'S'],[270,'W']]) {
    const rad = (compassDeg - 90) * Math.PI / 180;
    // Tick
    ctx.beginPath();
    ctx.moveTo(cx + (R - 5) * Math.cos(rad), cy + (R - 5) * Math.sin(rad));
    ctx.lineTo(cx + R * Math.cos(rad), cy + R * Math.sin(rad));
    ctx.strokeStyle = 'rgba(255,255,255,0.35)'; ctx.lineWidth = 1; ctx.stroke();
    // Label
    ctx.fillStyle = label === 'N' ? 'rgba(255,255,255,0.9)' : 'rgba(255,255,255,0.45)';
    ctx.fillText(label, cx + (R - 10) * Math.cos(rad), cy + (R - 10) * Math.sin(rad));
  }

  // ── Sun — rendered last so it always appears on top ───────────
  const bearingRad = (bearing - 90) * Math.PI / 180;
  const rawDist = altDeg >= 0
    ? R * 0.68 * (1 - altDeg / 90)
    : R * 0.68 + (R - R * 0.68) * Math.min(1, -altDeg / 18);
  // Cap so dot never reaches the ring edge and disappears
  const dist = Math.min(rawDist, R * 0.82);
  const sx = cx + dist * Math.cos(bearingRad);
  const sy = cy + dist * Math.sin(bearingRad);

  // Direction tick on the ring
  ctx.beginPath();
  ctx.moveTo(cx + (R - 6) * Math.cos(bearingRad), cy + (R - 6) * Math.sin(bearingRad));
  ctx.lineTo(cx + R * Math.cos(bearingRad), cy + R * Math.sin(bearingRad));
  ctx.strokeStyle = altDeg >= 0 ? 'rgba(255,240,100,0.9)' : 'rgba(255,200,100,0.5)';
  ctx.lineWidth = 2; ctx.stroke();

  // Sun dot — pure radial glow, no hard edge
  const sunAlpha = altDeg > -18 ? Math.max(0.5, 1 - Math.max(0, -altDeg) / 18) : 0;
  if (sunAlpha > 0) {
    const sg = ctx.createRadialGradient(sx, sy, 0, sx, sy, 7);
    sg.addColorStop(0,   `rgba(255,240,100,${sunAlpha})`);
    sg.addColorStop(0.5, `rgba(255,160,0,${sunAlpha * 0.7})`);
    sg.addColorStop(1,   'rgba(255,100,0,0)');
    ctx.beginPath(); ctx.arc(sx, sy, 7, 0, Math.PI * 2);
    ctx.fillStyle = sg; ctx.fill();
  }

  // Time label at bottom
  const h = Math.round(hour24) % 24;
  const h12 = h % 12 || 12;
  const ampm = h < 12 ? 'AM' : 'PM';
  ctx.font = 'bold 9px system-ui, sans-serif';
  ctx.textAlign = 'center'; ctx.textBaseline = 'middle';
  ctx.fillStyle = 'rgba(255,255,255,0.6)';
  ctx.fillText(`${h12}:00 ${ampm}`, cx, compassH + 8);

  hud.classList.remove('hidden');
}

function updateTerminator(hour24) {
  const terminatorSrc = map.getSource('terminator-src');
  const sunSrc        = map.getSource('sun-src');
  if (!terminatorSrc) return;

  const utcH = ((hour24 - animUtcOffset) % 24 + 24) % 24;
  const date = new Date(Date.UTC(2024, 2, 20, Math.floor(utcH),
                                  Math.round((utcH % 1) * 60)));
  const { lat, lon } = getSubsolarPoint(date);

  terminatorSrc.setData(buildTerminatorGeoJSON(lat, lon));

  if (sunSrc) {
    sunSrc.setData({
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [lon, lat] },
      properties: {},
    });
    map.setPaintProperty('sun-marker', 'icon-opacity', 0.9);
  }
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
  return (ANIM_SPEED_FAST + (ANIM_SPEED_SLOW - ANIM_SPEED_FAST) * density) * animSpeedMult;
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
  animHour    = getAnimStartHour();
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
    allLoadedFeatures = allFeatures;
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
        if (!animDows.has(dow)) continue;
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

    if (viewMode === 'filter') {
      applyFilter();
    } else {
      updateVisibleCount();
      animPlaying = true;
      updatePlayPauseBtn();
      animFrame = requestAnimationFrame(animTick);
    }
  } catch (err) {
    countEl.textContent = 'Error loading data';
    endLoad();
    console.error(err);
  }
}

// ── Rebuild anim data from already-loaded features ────────────
// Used when animMode or animDows changes — avoids re-fetching.
function rebuildAnimData() {
  if (!allLoadedFeatures.length) return;
  if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
  animHour = getAnimStartHour();
  animLastTs = null;
  animLastUpdateHour = -1;

  animData = new Map();
  for (const feat of allLoadedFeatures) {
    const h = feat.properties.hour;
    if (h == null || h > 23) continue;

    let slot;
    if (animMode === 'week') {
      const { year, month, day } = feat.properties;
      if (!year || !month || !day) continue;
      const dow = (new Date(year, month - 1, day).getDay() + 6) % 7;
      if (!animDows.has(dow)) continue;
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

  const hourBuckets = new Map();
  for (const [slot, bucket] of animData.entries()) {
    const h = slot % 24;
    if (!hourBuckets.has(h)) hourBuckets.set(h, []);
    hourBuckets.get(h).push(...bucket);
  }
  animSolarCurve = buildSolarCurve(hourBuckets);

  map.getSource('incidents-dead').setData({ type: 'FeatureCollection', features: [] });
  updateVisibleCount();
  animPlaying = true;
  updatePlayPauseBtn();
  animFrame = requestAnimationFrame(animTick);
}

// ── Animation start hour ──────────────────────────────────────
// In week mode, start at the first selected day's noon slot so the animation
// doesn't always begin on Monday when other days are selected.
function getAnimStartHour() {
  if (animMode === 'week') return Math.min(...animDows) * 24 + ANIM_START_HOUR;
  return ANIM_START_HOUR;
}

// ── Playback controls ─────────────────────────────────────────
const animPlayPauseBtn = document.getElementById('anim-playpause');

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
  const start        = getAnimStartHour();
  animHour           = start;
  animLastTs         = null;
  animLastUpdateHour = -1;
  map.getSource('incidents-dead').setData({ type: 'FeatureCollection', features: [] });
  buildActiveSet(start);
});

document.getElementById('anim-mode-day').addEventListener('click', () => {
  if (animMode === 'day') return;
  animMode = 'day';
  document.getElementById('anim-mode-day').classList.add('active');
  document.getElementById('anim-mode-week').classList.remove('active');
  document.getElementById('anim-dow-wrap').classList.add('hidden');
  rebuildAnimData();
});

document.getElementById('anim-mode-week').addEventListener('click', () => {
  if (animMode === 'week') return;
  animMode = 'week';
  document.getElementById('anim-mode-week').classList.add('active');
  document.getElementById('anim-mode-day').classList.remove('active');
  document.getElementById('anim-dow-wrap').classList.remove('hidden');
  rebuildAnimData();
});

// Speed buttons
document.querySelectorAll('[data-speed]').forEach(btn => {
  btn.addEventListener('click', () => {
    animSpeedMult = Number(btn.dataset.speed);
    document.querySelectorAll('[data-speed]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
  });
});

// Animate day-of-week chips
document.querySelectorAll('[data-anim-dow]').forEach(btn => {
  btn.addEventListener('click', () => {
    const dow = Number(btn.dataset.animDow);
    if (animDows.has(dow)) {
      if (animDows.size > 1) {
        animDows.delete(dow);
        btn.classList.remove('active');
      }
    } else {
      animDows.add(dow);
      btn.classList.add('active');
    }
    rebuildAnimData();
  });
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

// ── Road heat toggle ──────────────────────────────────────────
document.getElementById('heat-on').addEventListener('click', () => {
  ['road-heat', 'road-heat-glow'].forEach(id => map.setLayoutProperty(id, 'visibility', 'visible'));
  document.getElementById('heat-on').classList.add('active');
  document.getElementById('heat-off').classList.remove('active');
});
document.getElementById('heat-off').addEventListener('click', () => {
  ['road-heat', 'road-heat-glow'].forEach(id => map.setLayoutProperty(id, 'visibility', 'none'));
  document.getElementById('heat-off').classList.add('active');
  document.getElementById('heat-on').classList.remove('active');
});

// ── Visible feature counter ───────────────────────────────────
const incidentTotalEl = document.getElementById('incident-total');

function updateFilterCount() {
  if (!incidentTotalEl) return;
  const b = map.getBounds();
  const w = b.getWest(), e = b.getEast(), s = b.getSouth(), n = b.getNorth();
  let inView = 0;
  for (const f of filteredFeatures) {
    const [lon, lat] = f.geometry.coordinates;
    if (lon >= w && lon <= e && lat >= s && lat <= n) inView++;
  }
  const total = allLoadedFeatures.length.toLocaleString();
  incidentTotalEl.textContent =
    `${total} total · ${inView.toLocaleString()} in view`;
}

function updateVisibleCount() {
  if (viewMode === 'filter') return;
  if (!incidentTotalEl || allLoadedFeatures.length === 0) return;
  const b = map.getBounds();
  const w = b.getWest(), e = b.getEast(), s = b.getSouth(), n = b.getNorth();
  let visible = 0;
  for (const f of allLoadedFeatures) {
    const [lon, lat] = f.geometry.coordinates;
    if (lon >= w && lon <= e && lat >= s && lat <= n) visible++;
  }
  const total = allLoadedFeatures.length.toLocaleString();
  const vis   = visible.toLocaleString();
  incidentTotalEl.textContent = `${total} total · ${vis} in view`;
}

map.on('moveend', () => {
  if (viewMode === 'filter') updateFilterCount(); else updateVisibleCount();
  const h = viewMode === 'filter' ? (filterFrom + filterTo) / 2 % 24 : animHour % 24;
  drawSunHUD(h);
});
map.on('zoomend', updateVisibleCount);

// ── Filter mode ───────────────────────────────────────────────
function formatHour(h) {
  const h12 = h % 12 || 12;
  return `${h12}:00 ${h < 12 ? 'AM' : 'PM'}`;
}

function getDow(feat) {
  const { year, month, day } = feat.properties;
  if (!year || !month || !day) return -1;
  return (new Date(year, month - 1, day).getDay() + 6) % 7; // Mon=0…Sun=6
}

function applyFilter() {
  if (!allLoadedFeatures.length) return;

  const from = filterFrom; // slider value in 12–35 range
  const to   = filterTo;

  const matched = allLoadedFeatures.filter(f => {
    const h = f.properties.hour;
    if (h == null) return false;
    // Normalize to noon-based range: noon=12, midnight=24, 11am=35
    const normH = h >= 12 ? h : h + 24;
    if (normH < from || normH > to) return false;
    if (filterDows.size < 7) {
      const dow = getDow(f);
      if (dow < 0 || !filterDows.has(dow)) return false;
    }
    return true;
  });

  filteredFeatures = matched;

  map.getSource('incidents').setData({ type: 'FeatureCollection', features: [] });
  map.getSource('incidents-dead').setData({ type: 'FeatureCollection', features: matched });
  map.getSource('road-heat-lines').setData(buildRoadHeatLines(matched));

  // Solar context at midpoint of window (convert back to 0-23).
  // Full-range "All" preset: clear the night overlay and hide solar indicators.
  const isFullRange = (from === 12 && to === 35);
  const midHour = ((from + to) / 2) % 24;
  if (isFullRange) {
    map.setPaintProperty('night-overlay', 'fill-opacity', 0);
    map.setLayoutProperty('terminator', 'visibility', 'none');
    map.setLayoutProperty('terminator-glow', 'visibility', 'none');
    document.getElementById('sun-hud')?.classList.add('hidden');
  } else {
    map.setLayoutProperty('terminator', 'visibility', 'visible');
    map.setLayoutProperty('terminator-glow', 'visibility', 'visible');
    updateMapFilter(midHour);
    updateTerminator(midHour);
    drawSunHUD(midHour);
  }

  // Clock shows the time range (convert to 0-23 for display)
  countEl.textContent = `${formatHour(from % 24)} – ${formatHour(to % 24)}`;
  countEl.classList.add('anim-clock');

  // Count
  updateFilterCount();

  // Progress bar: highlight the selected window
  const fill   = document.getElementById('anim-progress-fill');
  const win    = document.getElementById('anim-progress-window');
  if (fill) fill.style.width = '0';
  if (win) {
    // Slider is 12–35; map to 0–100% of the progress bar
    win.style.left  = `${((from - 12) / 24) * 100}%`;
    win.style.width = `${((to - from + 1) / 24) * 100}%`;
    win.style.display = 'block';
  }

  // Solar condition label
  const solarRef = document.getElementById('solar-ref');
  if (solarRef && animSolarCurve) {
    const altDeg = animSolarCurve[Math.round(midHour) % 24];
    const condition = altDeg > 6   ? 'Daytime'
                    : altDeg > 0   ? 'Sunrise / Sunset'
                    : altDeg > -6  ? 'Civil twilight'
                    : altDeg > -12 ? 'Nautical twilight'
                    :                'Night';
    const sign   = altDeg >= 0 ? '+' : '−';
    const note   = to >= 24 ? ' · crosses midnight' : '';
    solarRef.textContent = `${condition} · ${sign}${Math.abs(altDeg).toFixed(1)}° at midpoint${note}`;
  }
}

function enterFilterMode() {
  viewMode = 'filter';
  animPlaying = false;
  updatePlayPauseBtn();
  // Filter-mode features have no died_at_slot — restore static opacity
  map.setPaintProperty('incidents-dead', 'icon-opacity', 0.3);
  document.getElementById('animate-sub').classList.add('hidden');
  document.getElementById('filter-sub').classList.remove('hidden');
  document.getElementById('view-animate').classList.remove('active');
  document.getElementById('view-filter').classList.add('active');
  applyFilter();
}

function enterAnimateMode() {
  viewMode = 'animate';
  document.getElementById('animate-sub').classList.remove('hidden');
  document.getElementById('filter-sub').classList.add('hidden');
  document.getElementById('view-filter').classList.remove('active');
  document.getElementById('view-animate').classList.add('active');
  const win = document.getElementById('anim-progress-window');
  if (win) win.style.display = 'none';
  loadAnimData();
}

// View toggle
document.getElementById('view-animate').addEventListener('click', () => {
  if (viewMode !== 'animate') enterAnimateMode();
});
document.getElementById('view-filter').addEventListener('click', () => {
  if (viewMode !== 'filter') enterFilterMode();
});

// Hour sliders
const filterFromEl       = document.getElementById('filter-from');
const filterToEl         = document.getElementById('filter-to');
const filterFromValueEl  = document.getElementById('filter-from-value');
const filterToValueEl    = document.getElementById('filter-to-value');

filterFromEl.addEventListener('input', () => {
  filterFrom = Number(filterFromEl.value);
  filterFromValueEl.textContent = formatHour(filterFrom % 24);
  document.querySelectorAll('[data-preset]').forEach(b => b.classList.remove('active'));
  if (viewMode === 'filter') applyFilter();
});
filterToEl.addEventListener('input', () => {
  filterTo = Number(filterToEl.value);
  filterToValueEl.textContent = formatHour(filterTo % 24);
  document.querySelectorAll('[data-preset]').forEach(b => b.classList.remove('active'));
  if (viewMode === 'filter') applyFilter();
});

// Time-of-day presets — noon-based slider values (12=noon … 35=11 AM next day)
const TOD_PRESETS = {
  day:     { from: 12, to: 17 },  // noon – 5 PM
  sunset:  { from: 16, to: 21 },  // 4 PM – 9 PM
  night:   { from: 21, to: 28 },  // 9 PM – 4 AM
  sunrise: { from: 28, to: 32 },  // 4 AM – 8 AM
  all:     { from: 12, to: 35 },  // full 24-hour range
};

function setFilterWindow(from, to) {
  filterFrom = from;
  filterTo   = to;
  filterFromEl.value = from;
  filterToEl.value   = to;
  filterFromValueEl.textContent = formatHour(from % 24);
  filterToValueEl.textContent   = formatHour(to % 24);
  if (viewMode === 'filter') applyFilter();
}

document.querySelectorAll('[data-preset]').forEach(btn => {
  btn.addEventListener('click', () => {
    const p = TOD_PRESETS[btn.dataset.preset];
    if (!p) return;
    document.querySelectorAll('[data-preset]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    setFilterWindow(p.from, p.to);
  });
});

// Day-of-week chips
document.querySelectorAll('[data-dow]').forEach(btn => {
  btn.addEventListener('click', () => {
    const dow = Number(btn.dataset.dow);
    if (filterDows.has(dow)) {
      if (filterDows.size > 1) { // don't allow deselecting all
        filterDows.delete(dow);
        btn.classList.remove('active');
      }
    } else {
      filterDows.add(dow);
      btn.classList.add('active');
    }
    if (viewMode === 'filter') applyFilter();
  });
});

// ── FARS data-currency check ──────────────────────────────────
(async () => {
  try {
    const res = await fetch('/api/data-status');
    if (!res.ok) return;
    const { update_available, latest_available_year, db_max_year } = await res.json();
    if (update_available) {
      const badge = document.getElementById('data-update-badge');
      if (badge) {
        badge.textContent = `Data available through ${latest_available_year}`;
        badge.classList.remove('hidden');
      }
      // Also update the subtitle link text to reflect what's actually in the DB
      const subtitleLink = document.querySelector('#controls-header .subtitle-link');
      if (subtitleLink) subtitleLink.textContent = `FARS · 2001–${db_max_year}`;
    }
  } catch (_) { /* network error — fail silently */ }
})();

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
