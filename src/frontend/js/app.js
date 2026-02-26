'use strict';

// ── Config ────────────────────────────────────────────────────
const YEAR_MIN = 2001;
const YEAR_MAX = 2022;
const DEFAULT_YEAR = YEAR_MAX;

// Lighting condition → point colour (matches legend)
const LIGHT_COLORS = [
  'match', ['get', 'lgt_cond'],
  1, '#F59E0B',   // Daylight — amber
  3, '#8B5CF6',   // Dark, lit — violet
  2, '#1E3A5F',   // Dark, unlit — deep navy
  4, '#FB923C',   // Dawn — warm orange
  5, '#F97316',   // Dusk — deep orange
  '#64748B',      // fallback (unknown / not reported)
];

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

// ── State ─────────────────────────────────────────────────────
let currentYear = DEFAULT_YEAR;
let currentView = 'points'; // 'points' | 'heatmap'
const todFilters = new Set(['day', 'dawn', 'dusk', 'night']);
const roadFilters = new Set(['interstate', 'highway', 'local']);
let summaryCache = null;

// ── Map init ──────────────────────────────────────────────────
const map = new maplibregl.Map({
  container: 'map',
  style: 'https://tiles.openfreemap.org/styles/liberty',
  center: [-98.5, 39.5],
  zoom: 4,
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
  const cls = delta > 0 ? 'trend-up' : 'trend-down';
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

  // Heatmap layer (visible in 'heatmap' view)
  map.addLayer({
    id: 'incidents-heat',
    type: 'heatmap',
    source: 'incidents',
    layout: { visibility: 'none' },
    paint: {
      'heatmap-weight': 1,
      'heatmap-intensity': [
        'interpolate', ['linear'], ['zoom'],
        4, 0.4,
        8, 1.8,
      ],
      'heatmap-radius': [
        'interpolate', ['linear'], ['zoom'],
        4, 10,
        8, 24,
      ],
      'heatmap-opacity': [
        'interpolate', ['linear'], ['zoom'],
        8, 1,
        10, 0,
      ],
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
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 3, 10, 7],
      'circle-color': LIGHT_COLORS,
      'circle-opacity': 0.85,
      'circle-stroke-width': 0.5,
      'circle-stroke-color': 'rgba(255,255,255,0.25)',
    },
  });

  updateLayerVisibility();
  fetchSummary(); // warm the cache in background
  loadIncidents();
});

// ── Layer visibility ──────────────────────────────────────────
function updateLayerVisibility() {
  if (!map.getLayer('incidents-circle')) return;
  if (currentView === 'heatmap') {
    map.setLayoutProperty('incidents-heat', 'visibility', 'visible');
    // Points fade in at high zoom in heatmap mode (auto-transition to points)
    map.setPaintProperty('incidents-circle', 'circle-opacity', [
      'interpolate', ['linear'], ['zoom'],
      8, 0,
      10, 0.85,
    ]);
  } else {
    map.setLayoutProperty('incidents-heat', 'visibility', 'none');
    map.setPaintProperty('incidents-circle', 'circle-opacity', 0.85);
  }
}

// ── View toggle ───────────────────────────────────────────────
document.getElementById('view-points').addEventListener('click', () => {
  currentView = 'points';
  document.getElementById('view-points').classList.add('active');
  document.getElementById('view-heat').classList.remove('active');
  updateLayerVisibility();
});

document.getElementById('view-heat').addEventListener('click', () => {
  currentView = 'heatmap';
  document.getElementById('view-heat').classList.add('active');
  document.getElementById('view-points').classList.remove('active');
  updateLayerVisibility();
});

// ── Filter chips ──────────────────────────────────────────────
document.getElementById('tod-filters').addEventListener('click', (e) => {
  const btn = e.target.closest('.chip[data-tod]');
  if (!btn) return;
  const key = btn.dataset.tod;
  if (todFilters.has(key)) {
    todFilters.delete(key);
    btn.classList.remove('active');
  } else {
    todFilters.add(key);
    btn.classList.add('active');
  }
  closePopup();
  loadIncidents();
});

document.getElementById('road-filters').addEventListener('click', (e) => {
  const btn = e.target.closest('.chip[data-road]');
  if (!btn) return;
  const key = btn.dataset.road;
  if (roadFilters.has(key)) {
    roadFilters.delete(key);
    btn.classList.remove('active');
  } else {
    roadFilters.add(key);
    btn.classList.add('active');
  }
  closePopup();
  loadIncidents();
});

// ── Fetch + update ────────────────────────────────────────────
const countEl = document.getElementById('count');
const loadingBar = document.getElementById('loading-bar');

const BBOX_ZOOM_THRESHOLD = 6;
const TOD_ALL = ['day', 'dawn', 'dusk', 'night'];
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

  // Only send TOD params if not all selected (avoids redundant DB clause)
  if (todFilters.size < TOD_ALL.length) {
    for (const t of todFilters) url += `&tod=${t}`;
  }

  // Only send road params if not all selected
  if (roadFilters.size < ROAD_ALL.length) {
    for (const r of roadFilters) url += `&road=${r}`;
  }

  return url;
}

function startLoad() {
  loadingBar.classList.remove('hidden', 'done');
  loadingBar.classList.add('active');
  countEl.textContent = 'Loading…';
  countEl.classList.add('loading');
  trendEl.textContent = '';
}

function endLoad() {
  loadingBar.classList.remove('active');
  loadingBar.classList.add('done');
  countEl.classList.remove('loading');
  setTimeout(() => loadingBar.classList.add('hidden'), 500);
}

async function loadIncidents() {
  startLoad();
  try {
    const res = await fetch(buildUrl());
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const geojson = await res.json();
    map.getSource('incidents').setData(geojson);

    const n = geojson.features.length;
    const isBbox = map.getZoom() >= BBOX_ZOOM_THRESHOLD;
    const suffix = isBbox ? ' in view' : '';
    countEl.textContent = `${n.toLocaleString()}${suffix}`;
    endLoad();

    if (!isBbox) updateTrend(currentYear, n);
  } catch (err) {
    countEl.textContent = 'Error loading data';
    endLoad();
    console.error(err);
  }
}

// Debounced moveend
let moveTimer;
map.on('moveend', () => {
  clearTimeout(moveTimer);
  moveTimer = setTimeout(loadIncidents, 300);
});

yearSelect.addEventListener('change', () => {
  currentYear = Number(yearSelect.value);
  closePopup();
  loadIncidents();
});

// ── Popup ─────────────────────────────────────────────────────
const popup = document.getElementById('popup');
const popupContent = document.getElementById('popup-content');
const popupHeader = document.getElementById('popup-header');
document.getElementById('popup-close').addEventListener('click', closePopup);

function closePopup() { popup.classList.add('hidden'); }

function formatHour(hour, minute) {
  if (hour == null || hour === 99) return 'Unknown';
  const h = hour % 12 || 12;
  const ampm = hour < 12 ? 'AM' : 'PM';
  const m = minute != null && minute !== 99 ? String(minute).padStart(2, '0') : '00';
  return `${h}:${m} ${ampm}`;
}

function row(label, value) {
  return `<div class="row"><span class="label">${label}</span><span class="value">${value ?? '—'}</span></div>`;
}

map.on('click', 'incidents-circle', (e) => {
  const p = e.features[0].properties;

  const date = (p.month && p.day && p.year)
    ? `${p.month}/${p.day}/${p.year}`
    : p.year ?? '—';

  popupHeader.textContent = `Incident · ${date}`;

  popupContent.innerHTML = [
    row('Time', formatHour(p.hour, p.minute)),
    row('Lighting', LIGHT_LABELS[p.lgt_cond] ?? '—'),
    row('Weather', WEATHER_LABELS[p.weather] ?? '—'),
    row('Road type', ROUTE_LABELS[p.route] ?? '—'),
    row('Location', p.rur_urb === 1 ? 'Rural' : p.rur_urb === 2 ? 'Urban' : '—'),
    row('Victim age', p.age && p.age < 997 ? p.age : '—'),
    row('Victim sex', SEX_LABELS[p.sex] ?? '—'),
  ].join('');

  popup.classList.remove('hidden');
});

map.on('mouseenter', 'incidents-circle', () => {
  map.getCanvas().style.cursor = 'pointer';
});
map.on('mouseleave', 'incidents-circle', () => {
  map.getCanvas().style.cursor = '';
});
