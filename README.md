# Pedestrian Safety Mapper

An interactive map of every recorded pedestrian fatality in the United States from 2001 to 2023 — over 123,000 incidents — drawn from the [NHTSA Fatality Analysis Reporting System (FARS)](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system-fars).

![Project Status: Active](https://img.shields.io/badge/status-active-brightgreen)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Data: NHTSA FARS 2001–2023](https://img.shields.io/badge/data-FARS%202001–2023-blue)

---

## What It Does

Each dot on the map is a person who died. The map makes two arguments visually:

1. **Darkness kills.** Fatalities cluster at dusk, night, and dawn — the solar overlay makes this causally visible, not just decorative.
2. **The same roads keep killing.** The road heat layer traces the arterial pathology of every city. The same stretches appear year after year.

### Features

**Static mode** (default)
- Browse the full 22-year dataset with time-of-day and day-of-week filters
- Presets: Day / Sunset / Night / Sunrise / All Day
- Custom time window slider (noon-anchored, wraps midnight)
- Solar-adjusted night overlay — background darkness matches actual sun position at the selected hour
- Sun HUD compass showing solar bearing and altitude above/below horizon

**Animate mode**
- **Week** — cycles Monday through Sunday; shows which days and corridors are most dangerous
- **24h** — cycles through a 24-hour day aggregated across selected days (weekdays, weekends, or any combination)
- Incident dots fade in on first appearance and decay into the road heat layer over 8 simulated hours
- Playback speed: Slow / Normal / Fast

**Incident popup**
- Click any dot: date, time, lighting condition, weather, victim age and sex
- "Open Street View" — opens Google Street View oriented to the road bearing at that location (computed via OpenStreetMap Overpass API)

**Road heat layer**
- Kernel-density heat lines overlaid on roads weighted by fatality count
- Toggleable; persists in both Static and Animate modes

**Year range selector**
- Multi-year queries: any range from 2001 to 2023
- Defaults to last 5 years (2019–2023)

---

## Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | [MapLibre GL JS](https://maplibre.org/) | Open-source Mapbox fork — no API key |
| Map tiles | [OpenFreeMap](https://openfreemap.org/) | Free, no rate limits |
| Solar math | [SunCalc.js](https://github.com/mourner/suncalc) | Per-slot centroid solar altitude curves |
| Backend | Python / Flask | REST API serving GeoJSON |
| Database | PostgreSQL + PostGIS | Spatial indexing for fast bbox queries |
| ETL | Python (stdlib only) | Processes raw FARS zips → PostGIS |
| Dev environment | Docker Compose | One command to start |
| Deployment target | Render + Neon | Zero ongoing cost |

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for the ETL)
- FARS data zips in `data/raw/`

### Run Locally

```bash
# 1. Clone (sparse — skips the large data zips)
git clone --filter=blob:none https://github.com/eddielathamjones/pedestrian-safety-mapper.git
cd pedestrian-safety-mapper

# 2. Configure environment
cp .env.example .env

# 3. Start PostGIS + Flask
docker compose up -d

# 4. Load data
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Single year
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pedestrian_safety \
  python -m src.data_processing.etl --years 2023 --data-dir data/raw

# All years (requires full data/raw/ checkout)
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pedestrian_safety \
  python -m src.data_processing.etl --years 2001-2023 --data-dir data/raw

# 5. Open http://localhost:5001
```

### Download FARS Data

```bash
python scripts/data_download.py
```

Downloads all years to `data/raw/` as `FARS{year}NationalCSV.zip`. Decimal lat/lon coordinates are available from 2001 onwards; the ETL filters out records with missing or sentinel coordinates.

---

## Project Structure

```
pedestrian-safety-mapper/
├── src/
│   ├── backend/
│   │   ├── app.py          # Flask API
│   │   └── schema.sql      # incidents table + GiST spatial index
│   ├── frontend/
│   │   ├── index.html
│   │   ├── css/app.css
│   │   └── js/app.js       # map, animation, filter, solar overlay, popup
│   └── data_processing/
│       └── etl.py          # FARS zips → PostGIS
├── data/
│   └── raw/                # FARS zip files (not tracked in git)
├── docs/
│   ├── roadmap.md          # Design direction and priorities
│   ├── solar-correction.md # Solar position methodology — full technical writeup
│   ├── future-ml-direction.md
│   └── shaping/            # Product design decisions (R, shapes, slices)
├── scripts/
│   └── data_download.py
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

---

## API

### `GET /api/incidents`

Returns a GeoJSON FeatureCollection of pedestrian fatalities.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | yes | Year to query (2001–2023) |
| `bbox` | string | no | `minLon,minLat,maxLon,maxLat` |

**Example response:**

```json
{
  "type": "FeatureCollection",
  "features": [{
    "type": "Feature",
    "geometry": { "type": "Point", "coordinates": [-86.69, 33.54] },
    "properties": {
      "year": 2022, "month": 1, "day": 2,
      "hour": 18, "minute": 48,
      "lgt_cond": 2, "weather": 1, "route": 5, "rur_urb": 2,
      "state": 1, "county": 73,
      "age": 27, "sex": 1, "inj_sev": 4
    }
  }]
}
```

### `GET /api/summary`

Returns total incident counts by year.

```json
{ "2001": 4389, "2022": 7522 }
```

---

## Data Fields

| Field | Source | Description |
|-------|--------|-------------|
| `geom` | ACCIDENT | Point geometry (EPSG:4326) |
| `year`, `month`, `day` | ACCIDENT | Crash date |
| `hour`, `minute` | ACCIDENT | Local wall-clock time (99 = unknown) |
| `lgt_cond` | ACCIDENT | 1=Daylight, 2=Dark–not lit, 3=Dark–lit, 4=Dawn, 5=Dusk |
| `weather` | ACCIDENT | 1=Clear, 2=Rain, 3=Sleet, 4=Snow, 5=Fog |
| `route` | ACCIDENT | 1=Interstate, 2=US Hwy, 3=State, 4=County, 5=Local |
| `rur_urb` | ACCIDENT | 1=Rural, 2=Urban (available 2013+) |
| `state`, `county` | ACCIDENT | FIPS codes |
| `age`, `sex` | PERSON | Victim demographics (FARS sentinel values suppressed in display) |
| `inj_sev` | PERSON | Injury severity (all records = 4, fatal) |

---

## Solar Correction Methodology

The map applies a solar position overlay rather than using the FARS `lgt_cond` field directly. Clock time is a social construct that varies by time zone and daylight saving. Solar altitude is a physical measurement.

For each hour slot, the app computes a centroid from all incidents at that hour, then uses SunCalc.js to calculate the sun's altitude at the equinox for that location. This produces a 24-element solar curve that drives the night overlay opacity and Sun HUD display.

Full technical writeup — altitude formula, UTC offset approximation, smoothstep opacity mapping, per-slot centroid method, and known limitations — is in [`docs/solar-correction.md`](docs/solar-correction.md).

---

## Roadmap

| Slice | Status | Description |
|-------|--------|-------------|
| V1 — Data on the map | ✅ Done | Fatalities as interactive points |
| V2 — Year selector | ✅ Done | Multi-year filter (2001–2023) |
| V3 — Incident popup | ✅ Done | Date, time, lighting, weather, demographics, Street View |
| V4 — Viewport loading | ✅ Done | Fetch only visible incidents on pan/zoom |
| V5 — Extended history | ✅ Done | Full 2001–2023 dataset (123k+ incidents) |
| V6 — Solar overlay + animation | ✅ Done | 24h and week animation, solar-corrected night overlay, Sun HUD |
| V7 — Static filter mode | ✅ Done | Time window, day-of-week chips, presets, solar condition label |
| V8 — Road heat layer | ✅ Done | Kernel-density heat lines on roads |
| Phase 2 — Solar terminator | 💡 Planned | Real terminator line as a GeoJSON layer |
| Phase 2 — Sound layer | 💡 Planned | Ambient tone per dot on first appearance |
| Phase 2 — Streetlight overlay | 💡 Planned | OSM streetlight data correlated with fatality clusters |
| Phase 3 — Predictive risk model | 💡 Planned | ML risk scoring from FARS feature data |
| Phase 3 — Street View forensics | 💡 Planned | Embedded panel, thumbnails, vehicle direction |

See [`docs/roadmap.md`](docs/roadmap.md) for design direction and priorities.

---

## License

MIT — see [LICENSE](LICENSE) for details.

## Acknowledgments

- [NHTSA](https://www.nhtsa.gov/) for FARS data
- [MapLibre GL JS](https://maplibre.org/) and [OpenFreeMap](https://openfreemap.org/) for the mapping stack
- [SunCalc.js](https://github.com/mourner/suncalc) by Vladimir Agafonkin for solar position calculations
- OpenStreetMap / Overpass API for road geometry used in Street View orientation

---

*Research and educational use. Consult official sources for safety-critical decisions.*
