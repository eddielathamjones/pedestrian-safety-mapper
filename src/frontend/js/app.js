'use strict';

// ── Config ────────────────────────────────────────────────────
const YEAR_MIN = 2001;
const YEAR_MAX = 2022;
const DEFAULT_YEAR = YEAR_MAX;

// Lighting condition → point colour
const LIGHT_COLORS = [
  'match', ['get', 'lgt_cond'],
  1, '#F59E0B',   // Daylight — amber
  3, '#8B5CF6',   // Dark, lit — violet
  2, '#1E3A5F',   // Dark, unlit — deep navy
  4, '#FB923C',   // Dawn — warm orange
  5, '#F97316',   // Dusk — deep orange
  '#64748B',      // fallback
];

// Static circle radius (zoom-interpolated)
const STATIC_RADIUS = ['interpolate', ['linear'], ['zoom'], 4, 3, 10, 7];

const LIGHT_LABELS = {
  1: 'Daylight', 2: 'Dark – unlit', 3: 'Dark – lit',
  4: 'Dawn', 5: 'Dusk', 6: 'Dark – unknown lit',
  7: 'Other', 8: 'Not reported', 9: 'Unknown',
};

const WEATHER_LABELS = {
  1: 'Clear', 2: 'Rain', 3: 'Sleet/hail', 4: 'Snow',
  5: 'Fog/smog', 6: 'Severe crosswinds', 7: 'Blowing sand',
  8: 'Other', 10: 'Cloudy', 11: 'Blowing snow', 12: 'Freezing rain',
  98: 'Not reported', 99: 'Unknown',
};

const ROUTE_LABELS = {
  1: 'Interstate', 2: 'US Highway', 3: 'State Highway',
  4: 'County Road', 5: 'Local Street', 6: 'Trafficway',
  7: 'Parkway/Recreation', 8: 'Other', 9: 'Unknown',
};

const SEX_LABELS = { 1: 'Male', 2: 'Female', 8: 'Not reported', 9: 'Unknown' };

// ── Animation constants ────────────────────────────────────────
const ANIM_STEP          = 0.25;   // advance in 15-min increments
const ANIM_SPEED_FAST    = 1.2;    // sim-hours/sec when sparse  (~20s full cycle)
const ANIM_SPEED_SLOW    = 0.15;   // sim-hours/sec when dense  (~160s full cycle)
const ANIM_BASE_RADIUS   = 4;                          // base point radius in animation mode

// ── State ─────────────────────────────────────────────────────
let currentYear = DEFAULT_YEAR;
let currentView = 'points'; // 'points' | 'heatmap' | 'anim'
const todFilters  = new Set(['day', 'dawn', 'dusk', 'night']);
const roadFilters = new Set(['interstate', 'highway', 'local']);
let summaryCache  = null;

// ── Animation state ────────────────────────────────────────────
let animMode     = 'day';  // 'day' | 'week'
let animData     = null;   // Map<slot, Feature[]> — slot = hour (day) or weekSlot (week)
let animFrame    = null;   // requestAnimationFrame id
let animPlaying  = false;
let animHour     = 0;      // 0–totalHours float, current sim time
let animLastTs   = null;   // last rAF timestamp
let animLastUpdateHour = -1;
let animTrailHours  = 3;
let animMaxDensity  = 1;   // max incidents in any single slot

const DAYS = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'];

// ── Map init ──────────────────────────────────────────────────
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://tiles.openfreemap.org/styles/liberty',
  center: [-110.9747, 32.2226],  // Tucson, Pima County
  zoom: 11,
  attributionControl: true,
});

map.addControl(new maplibregl.NavigationControl(), 'top-right');

// ── Year selector ─────────────────────────────────────────────
const yearSelect = document.getElementById('year-select');
for (let y = YEAR_MAX; y >= YEAR_MIN; y--) {
  const opt = document.createElement('option');
  opt.value = y;
  opt.textContent = y;
  yearSelect.appendChild(opt);
}
yearSelect.value = DEFAULT_YEAR;

// ── Summary cache ─────────────────────────────────────────────
async function fetchSummary() {
  if (summaryCache) return summaryCache;
  try {
    const res = await fetch('/api/summary');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    summaryCache = await res.json();
  } catch (_) {
    summaryCache = {};
  }
  return summaryCache;
}

// ── Trend indicator ───────────────────────────────────────────
const trendEl = document.getElementById('trend');

async function updateTrend(year, count) {
  if (!count || year <= YEAR_MIN) { trendEl.textContent = ''; return; }
  const summary = await fetchSummary();
  const prev = summary[String(year - 1)];
  if (!prev) { trendEl.textContent = ''; return; }
  const delta = ((count - prev) / prev * 100);
  const sign = delta > 0 ? '+' : '';
  const cls  = delta > 0 ? 'trend-up' : 'trend-down';
  const arrow = delta > 0 ? '▲' : '▼';
  trendEl.innerHTML =
    `<span class="${cls}">${arrow} ${sign}${delta.toFixed(1)}% vs ${year - 1}</span>`;
}

// ── Map layers ────────────────────────────────────────────────
map.on('load', () => {
  map.addSource('incidents', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  });

  // Heatmap layer
  map.addLayer({
    id: 'incidents-heat',
    type: 'heatmap',
    source: 'incidents',
    layout: { visibility: 'none' },
    paint: {
      'heatmap-weight': 1,
      'heatmap-intensity': ['interpolate', ['linear'], ['zoom'], 4, 0.4, 8, 1.8],
      'heatmap-radius':   ['interpolate', ['linear'], ['zoom'], 4, 10, 8, 24],
      'heatmap-opacity':  ['interpolate', ['linear'], ['zoom'], 8, 1, 10, 0],
      'heatmap-color': [
        'interpolate', ['linear'], ['heatmap-density'],
        0,   'rgba(0,0,0,0)',
        0.1, '#1e3a5f',
        0.3, '#7c3aed',
        0.5, '#ef4444',
        0.7, '#f97316',
        1.0, '#fef08a',
      ],
    },
  });

  // Points layer — colour encodes lighting condition
  map.addLayer({
    id: 'incidents-circle',
    type: 'circle',
    source: 'incidents',
    paint: {
      'circle-radius':       STATIC_RADIUS,
      'circle-color':        LIGHT_COLORS,
      'circle-opacity':      0.85,
      'circle-stroke-width': 0.5,
      'circle-stroke-color': 'rgba(255,255,255,0.25)',
    },
  });

  updateLayerVisibility();
  fetchSummary();
  loadIncidents();
});

// ── Layer visibility (static modes only) ─────────────────────
function updateLayerVisibility() {
  if (currentView === 'anim') return; // animation manages its own layers
  if (!map.getLayer('incidents-circle')) return;

  if (currentView === 'heatmap') {
    map.setLayoutProperty('incidents-heat', 'visibility', 'visible');
    map.setPaintProperty('incidents-circle', 'circle-opacity', [
      'interpolate', ['linear'], ['zoom'], 8, 0, 10, 0.85,
    ]);
  } else {
    map.setLayoutProperty('incidents-heat', 'visibility', 'none');
    map.setPaintProperty('incidents-circle', 'circle-opacity', 0.85);
  }
}

// ── N6: Pop/fade function ─────────────────────────────────────
// age: sim-hours since the incident's hour fired (0 = just fired)
// returns {opacity, radius} or null if outside trail window
function popFade(age, trailHours) {
  if (age < 0 || age >= trailHours) return null;
  const t         = age / trailHours;
  const opacity   = Math.pow(1 - t, 1.5);                       // non-linear fade
  const popFactor = Math.max(0, 1 - age * 3);                   // burst decays over 0.33 sim-hrs
  const radius    = ANIM_BASE_RADIUS * (1 + 0.5 * popFactor);   // peak 1.5× base, settles to base
  return { opacity, radius };
}

// ── N7: Active set builder ────────────────────────────────────
function buildActiveSet(hour = animHour) {
  if (!animData) return;

  const total    = animTotalHours();
  const features = [];
  for (let s = 0; s < total; s++) {
    const bucket = animData.get(s);
    if (!bucket) continue;

    const age = (hour - s + total) % total;
    const pf  = popFade(age, animTrailHours);
    if (!pf) continue;

    for (const feat of bucket) {
      features.push({
        ...feat,
        properties: {
          ...feat.properties,
          anim_opacity: pf.opacity,
          anim_radius:  pf.radius,
        },
      });
    }
  }

  map.getSource('incidents').setData({ type: 'FeatureCollection', features });

  // Clock display
  const totalH = animTotalHours();
  const absH   = Math.floor(hour) % totalH;
  const h      = absH % 24;
  const m      = Math.round((hour % 1) * 60);
  const ampm   = h < 12 ? 'AM' : 'PM';
  const dh     = h % 12 || 12;
  const dm     = String(m).padStart(2, '0');
  const timeStr = `${dh}:${dm} ${ampm}`;
  countEl.textContent = animMode === 'week'
    ? `${DAYS[Math.floor(absH / 24)]} ${timeStr}`
    : timeStr;
  countEl.classList.add('anim-clock');
  trendEl.textContent = '';
}

// ── Dynamic speed ────────────────────────────────────────────
// Slows when the current hour has many incidents, speeds up when sparse.
// Square-root easing softens the mapping so transitions feel gradual.
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
  animHour    = 0;
  animLastTs  = null;
  animLastUpdateHour = -1;
  if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }

  try {
    const res = await fetch(`/api/incidents?year=${currentYear}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const geojson = await res.json();

    animData = new Map();
    for (const feat of geojson.features) {
      const h = feat.properties.hour;
      if (h == null || h > 23) continue; // skip unknown (99) and sentinel

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

    // Pre-compute peak density for dynamic speed
    animMaxDensity = 1;
    for (const bucket of animData.values()) {
      if (bucket.length > animMaxDensity) animMaxDensity = bucket.length;
    }

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

// ── N8: Mode controller ───────────────────────────────────────
function enterAnimMode() {
  currentView = 'anim';

  // View toggle UI
  document.getElementById('view-points').classList.remove('active');
  document.getElementById('view-heat').classList.remove('active');
  document.getElementById('view-anim').classList.add('active');

  // Show animation controls
  document.getElementById('anim-controls').classList.remove('hidden');

  // Switch to data-driven paint — single high-contrast colour, no encoding
  map.setLayoutProperty('incidents-heat', 'visibility', 'none');
  map.setPaintProperty('incidents-circle', 'circle-color', [
    'interpolate', ['linear'], ['get', 'hour'],
    0,  '#6d28d9',  // midnight    — violet
    5,  '#2563eb',  // pre-dawn    — deep blue
    8,  '#38bdf8',  // morning     — sky blue
    15, '#fbbf24',  // afternoon   — amber
    18, '#f97316',  // dusk        — orange
    20, '#ef4444',  // evening     — red
    23, '#991b1b',  // late night  — crimson
  ]);
  map.setPaintProperty('incidents-circle', 'circle-stroke-color', 'rgba(0,0,0,0.4)');
  map.setPaintProperty('incidents-circle', 'circle-opacity', ['get', 'anim_opacity']);
  map.setPaintProperty('incidents-circle', 'circle-radius',  ['get', 'anim_radius']);

  closePopup();
  loadAnimData();
}

function exitAnimMode() {
  // Cancel clock
  if (animFrame) { cancelAnimationFrame(animFrame); animFrame = null; }
  animPlaying = false;
  animData    = null;

  // Hide animation controls, reset mode, clear clock display
  document.getElementById('anim-controls').classList.add('hidden');
  animMode = 'day';
  document.getElementById('anim-mode-day').classList.add('active');
  document.getElementById('anim-mode-week').classList.remove('active');
  countEl.classList.remove('anim-clock');

  // Restore static paint properties
  map.setPaintProperty('incidents-circle', 'circle-color',        LIGHT_COLORS);
  map.setPaintProperty('incidents-circle', 'circle-stroke-color', 'rgba(255,255,255,0.25)');
  map.setPaintProperty('incidents-circle', 'circle-opacity', 0.85);
  map.setPaintProperty('incidents-circle', 'circle-radius',  STATIC_RADIUS);
}

// ── View toggle ───────────────────────────────────────────────
document.getElementById('view-points').addEventListener('click', () => {
  if (currentView === 'anim') exitAnimMode();
  currentView = 'points';
  document.getElementById('view-points').classList.add('active');
  document.getElementById('view-heat').classList.remove('active');
  document.getElementById('view-anim').classList.remove('active');
  updateLayerVisibility();
  loadIncidents();
});

document.getElementById('view-heat').addEventListener('click', () => {
  if (currentView === 'anim') exitAnimMode();
  currentView = 'heatmap';
  document.getElementById('view-heat').classList.add('active');
  document.getElementById('view-points').classList.remove('active');
  document.getElementById('view-anim').classList.remove('active');
  updateLayerVisibility();
  loadIncidents();
});

document.getElementById('view-anim').addEventListener('click', () => {
  if (currentView === 'anim') return;
  enterAnimMode();
});

// ── Animation playback controls ───────────────────────────────
const animPlayPauseBtn = document.getElementById('anim-playpause');
const trailSlider      = document.getElementById('trail-slider');
const trailValueEl     = document.getElementById('trail-value');

function updatePlayPauseBtn() {
  animPlayPauseBtn.textContent = animPlaying ? '⏸ Pause' : '▶ Play';
}

animPlayPauseBtn.addEventListener('click', () => {
  if (!animData) return;
  animPlaying = !animPlaying;
  if (animPlaying) animLastTs = null; // prevent time-jump on resume
  updatePlayPauseBtn();
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

// ── Fetch + update (static modes) ────────────────────────────
const countEl      = document.getElementById('count');
const loadingBar   = document.getElementById('loading-bar');

const BBOX_ZOOM_THRESHOLD = 6;
const TOD_ALL  = ['day', 'dawn', 'dusk', 'night'];
const ROAD_ALL = ['interstate', 'highway', 'local'];

function getBbox() {
  const b = map.getBounds();
  return `${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}`;
}

function buildUrl() {
  const zoom = map.getZoom();
  const bbox = zoom >= BBOX_ZOOM_THRESHOLD ? getBbox() : null;

  let url = `/api/incidents?year=${currentYear}`;
  if (bbox) url += `&bbox=${encodeURIComponent(bbox)}`;
  if (todFilters.size  < TOD_ALL.length)  for (const t of todFilters)  url += `&tod=${t}`;
  if (roadFilters.size < ROAD_ALL.length) for (const r of roadFilters) url += `&road=${r}`;
  return url;
}

function startLoad() {
  loadingBar.classList.remove('hidden', 'done');
  loadingBar.classList.add('active');
  countEl.textContent = 'Loading…';
  countEl.classList.add('loading');
  countEl.classList.remove('anim-clock');
  trendEl.textContent = '';
}

function endLoad() {
  loadingBar.classList.remove('active');
  loadingBar.classList.add('done');
  countEl.classList.remove('loading');
  setTimeout(() => loadingBar.classList.add('hidden'), 500);
}

async function loadIncidents() {
  if (currentView === 'anim') return;
  startLoad();
  try {
    const res = await fetch(buildUrl());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const geojson = await res.json();
    map.getSource('incidents').setData(geojson);

    const n       = geojson.features.length;
    const isBbox  = map.getZoom() >= BBOX_ZOOM_THRESHOLD;
    const suffix  = isBbox ? ' in view' : '';
    countEl.textContent = `${n.toLocaleString()}${suffix}`;
    endLoad();

    if (!isBbox) updateTrend(currentYear, n);
  } catch (err) {
    countEl.textContent = 'Error loading data';
    endLoad();
    console.error(err);
  }
}

// Debounced moveend (static modes only)
let moveTimer;
map.on('moveend', () => {
  if (currentView === 'anim') return;
  clearTimeout(moveTimer);
  moveTimer = setTimeout(loadIncidents, 300);
});

yearSelect.addEventListener('change', () => {
  currentYear = Number(yearSelect.value);
  closePopup();
  if (currentView === 'anim') {
    loadAnimData(); // reload animation data for new year
  } else {
    loadIncidents();
  }
});

// ── Filter chips ──────────────────────────────────────────────
document.getElementById('tod-filters').addEventListener('click', (e) => {
  const btn = e.target.closest('.chip[data-tod]');
  if (!btn) return;
  const key = btn.dataset.tod;
  if (todFilters.has(key)) { todFilters.delete(key); btn.classList.remove('active'); }
  else                     { todFilters.add(key);    btn.classList.add('active'); }
  closePopup();
  loadIncidents();
});

document.getElementById('road-filters').addEventListener('click', (e) => {
  const btn = e.target.closest('.chip[data-road]');
  if (!btn) return;
  const key = btn.dataset.road;
  if (roadFilters.has(key)) { roadFilters.delete(key); btn.classList.remove('active'); }
  else                      { roadFilters.add(key);    btn.classList.add('active'); }
  closePopup();
  loadIncidents();
});

// ── Popup ─────────────────────────────────────────────────────
const popup        = document.getElementById('popup');
const popupContent = document.getElementById('popup-content');
const popupHeader  = document.getElementById('popup-header');
document.getElementById('popup-close').addEventListener('click', closePopup);

function closePopup() { popup.classList.add('hidden'); }

function formatHour(hour, minute) {
  if (hour == null || hour === 99) return 'Unknown';
  const h    = hour % 12 || 12;
  const ampm = hour < 12 ? 'AM' : 'PM';
  const m    = minute != null && minute !== 99 ? String(minute).padStart(2, '0') : '00';
  return `${h}:${m} ${ampm}`;
}

function row(label, value) {
  return `<div class="row"><span class="label">${label}</span><span class="value">${value ?? '—'}</span></div>`;
}

map.on('click', 'incidents-circle', (e) => {
  if (currentView === 'anim') return; // no popup during animation
  const p = e.features[0].properties;

  const date = (p.month && p.day && p.year)
    ? `${p.month}/${p.day}/${p.year}`
    : p.year ?? '—';

  popupHeader.textContent = `Incident · ${date}`;
  popupContent.innerHTML = [
    row('Time',       formatHour(p.hour, p.minute)),
    row('Lighting',   LIGHT_LABELS[p.lgt_cond] ?? '—'),
    row('Weather',    WEATHER_LABELS[p.weather] ?? '—'),
    row('Road type',  ROUTE_LABELS[p.route] ?? '—'),
    row('Location',   p.rur_urb === 1 ? 'Rural' : p.rur_urb === 2 ? 'Urban' : '—'),
    row('Victim age', p.age && p.age < 997 ? p.age : '—'),
    row('Victim sex', SEX_LABELS[p.sex] ?? '—'),
  ].join('');

  popup.classList.remove('hidden');
});

map.on('mouseenter', 'incidents-circle', () => {
  if (currentView !== 'anim') map.getCanvas().style.cursor = 'pointer';
});
map.on('mouseleave', 'incidents-circle', () => {
  map.getCanvas().style.cursor = '';
});
