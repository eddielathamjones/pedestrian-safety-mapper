'use strict';

// ── Config ────────────────────────────────────────────────────
const YEAR_MIN = 2010;
const YEAR_MAX = 2022;
const DEFAULT_YEAR = YEAR_MAX;

const LIGHT_LABELS = {
  1: 'Daylight', 2: 'Dark – not lit', 3: 'Dark – lit',
  4: 'Dawn', 5: 'Dusk', 6: 'Dark – unknown lighting',
  7: 'Other', 8: 'Not reported', 9: 'Unknown',
};

const WEATHER_LABELS = {
  1: 'Clear', 2: 'Rain', 3: 'Sleet/hail', 4: 'Snow',
  5: 'Fog/smog', 6: 'Severe crosswinds', 7: 'Blowing sand/dirt',
  8: 'Other', 10: 'Cloudy', 11: 'Blowing snow', 12: 'Freezing rain',
  98: 'Not reported', 99: 'Unknown',
};

const ROUTE_LABELS = {
  1: 'Interstate', 2: 'US Highway', 3: 'State Highway',
  4: 'County Road', 5: 'Local Street', 6: 'Trafficway',
  7: 'Parkway/Recreation', 8: 'Other', 9: 'Unknown',
};

const SEX_LABELS = { 1: 'Male', 2: 'Female', 8: 'Not reported', 9: 'Unknown' };

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

// ── Data layer ────────────────────────────────────────────────
let currentYear = DEFAULT_YEAR;

map.on('load', () => {
  map.addSource('incidents', {
    type: 'geojson',
    data: { type: 'FeatureCollection', features: [] },
  });

  map.addLayer({
    id: 'incidents-circle',
    type: 'circle',
    source: 'incidents',
    paint: {
      'circle-radius': ['interpolate', ['linear'], ['zoom'], 4, 3, 10, 7],
      'circle-color': '#e63946',
      'circle-opacity': 0.75,
      'circle-stroke-width': 1,
      'circle-stroke-color': '#fff',
    },
  });

  loadIncidents();
});

// ── Fetch + update ────────────────────────────────────────────
const countEl = document.getElementById('count');

// Use bbox when zoomed in enough that a viewport fetch makes sense.
// At zoom < 6 the bbox covers most of the US anyway, so skip it.
const BBOX_ZOOM_THRESHOLD = 6;

function getBbox() {
  const b = map.getBounds();
  return `${b.getWest()},${b.getSouth()},${b.getEast()},${b.getNorth()}`;
}

async function loadIncidents() {
  const zoom = map.getZoom();
  const bbox = zoom >= BBOX_ZOOM_THRESHOLD ? getBbox() : null;

  countEl.textContent = 'Loading…';
  try {
    let url = `/api/incidents?year=${currentYear}`;
    if (bbox) url += `&bbox=${bbox}`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const geojson = await res.json();
    map.getSource('incidents').setData(geojson);
    const suffix = bbox ? ' in view' : '';
    countEl.textContent = `${geojson.features.length.toLocaleString()} incidents${suffix}`;
  } catch (err) {
    countEl.textContent = 'Error loading data';
    console.error(err);
  }
}

// Debounced moveend — waits for the map to settle before fetching
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
document.getElementById('popup-close').addEventListener('click', closePopup);

function closePopup() {
  popup.classList.add('hidden');
}

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

  popupContent.innerHTML = [
    row('Date', date),
    row('Time', formatHour(p.hour, p.minute)),
    row('Lighting', LIGHT_LABELS[p.lgt_cond] ?? p.lgt_cond),
    row('Weather', WEATHER_LABELS[p.weather] ?? p.weather),
    row('Road type', ROUTE_LABELS[p.route] ?? p.route),
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
