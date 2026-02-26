# Pedestrian Safety Mapper

An open-source web application for visualizing pedestrian fatality data from the [Fatality Analysis Reporting System (FARS)](https://www.nhtsa.gov/research-data/fatality-analysis-reporting-system). Built for policy makers, transportation advocates, and urban planners.

![Project Status: Active](https://img.shields.io/badge/status-active-brightgreen)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Data: NHTSA FARS 2001–2022](https://img.shields.io/badge/data-FARS%202001–2022-blue)

---

## What It Does

- Plots every recorded pedestrian fatality (2001–2022) — over 123,000 incidents — as an interactive point on a US map
- Points are colour-coded by lighting condition so patterns of darkness-related fatalities are immediately visible
- Click any incident to see date, time of day, lighting, weather, road type, and victim demographics
- Filter by year, time of day (Day / Dawn / Dusk / Night), and road type (Interstate / Highway / Local)
- Toggle between point view and a heatmap for density analysis at national scale
- Trend indicator shows year-over-year % change at a glance

## Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Frontend | [MapLibre GL JS](https://maplibre.org/) | Open-source MapBox fork — no API key |
| Map tiles | [OpenFreeMap](https://openfreemap.org/) | Truly free, no rate limits |
| Backend | Python / Flask | REST API serving GeoJSON |
| Database | PostgreSQL + PostGIS | Spatial indexing for fast bbox queries |
| ETL | Python (stdlib only) | Processes raw FARS zips → PostGIS |
| Dev environment | Docker Compose | One command to start |
| Deployment target | Render + Neon | Zero ongoing cost |

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.8+ (for the ETL)
- FARS data zips in `data/raw/` (see [Data](#data) below)

### Run Locally

```bash
# 1. Clone (sparse — skips the large data zips)
git clone --filter=blob:none https://github.com/eddielathamjones/pedestrian-safety-mapper.git
cd pedestrian-safety-mapper

# 2. Configure environment
cp .env.example .env

# 3. Start PostGIS + Flask
docker compose up -d

# 4. Load a year of data
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pedestrian_safety \
  python -m src.data_processing.etl --years 2022 --data-dir data/raw

# 5. Open http://localhost:5000
```

To load all years at once (requires full `data/raw/` checkout):

```bash
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pedestrian_safety \
  python -m src.data_processing.etl --years 2001-2022 --data-dir data/raw
```

## Data

Raw FARS data (1975–2022) is stored in `data/raw/` as zip files from NHTSA. The repository includes a download script:

```bash
python scripts/data_download.py
```

This downloads all years to `data/raw/`. The ETL uses the National CSV zips — files named `FARS{year}NationalCSV.zip`.

**Coverage note:** Decimal lat/lon coordinates are available in FARS from 2001 onwards. The ETL filters out records with missing or sentinel coordinates. Pre-2001 geocoding via county centroid is tracked in [Issue #1](https://github.com/eddielathamjones/pedestrian-safety-mapper/issues/1).

## Project Structure

```
pedestrian-safety-mapper/
├── src/
│   ├── backend/
│   │   ├── app.py          # Flask API — GET /api/incidents?year=&bbox=
│   │   └── schema.sql      # incidents table + GiST spatial index
│   ├── frontend/
│   │   ├── index.html      # MapLibre map, year selector, click popup
│   │   ├── css/app.css
│   │   └── js/app.js
│   └── data_processing/
│       └── etl.py          # FARS zips → PostGIS
├── data/
│   └── raw/                # FARS zip files by year (not tracked in git)
├── docs/
│   ├── shaping/            # Product design decisions (R, shapes, slices)
│   └── research/           # NHTSA release notes and documentation
├── scripts/
│   └── data_download.py    # Downloads raw FARS data from NHTSA
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

## API

### `GET /api/summary`

Returns total incident counts by year.

```json
{ "2001": 4389, "2002": 4991, ... }
```

### `GET /api/incidents`

Returns a GeoJSON FeatureCollection of pedestrian fatalities.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | yes | Year to query (2001–2022) |
| `bbox` | string | no | `minLon,minLat,maxLon,maxLat` — filter to viewport |
| `tod` | string (repeatable) | no | Time of day: `day`, `dawn`, `dusk`, `night` |
| `road` | string (repeatable) | no | Road type: `interstate`, `highway`, `local` |

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
      "lgt_cond": 2, "weather": 2, "route": 1, "rur_urb": 2,
      "state": 1, "county": 73,
      "age": 27, "sex": 2, "inj_sev": 4
    }
  }]
}
```

## Roadmap

The project is built in vertical slices. Each slice ships a working, demo-able feature end-to-end.

| Slice | Status | Description |
|-------|--------|-------------|
| V1 — Data on the map | ✅ Done | 2022 fatalities as interactive points |
| V2 — Year selector | ✅ Done | Filter map by year (2001–2022) |
| V3 — Incident detail popup | ✅ Done | Click a point for full incident context |
| V4 — Viewport loading | ✅ Done | Fetch only visible incidents on pan/zoom |
| V5 — Extended history | ✅ Done | Data extended back to 2001 (123k+ incidents) |
| V6 — UI polish + filters | ✅ Done | Colour encoding, filters, trend indicator, heatmap |
| Future — Time-of-day animation | 💡 Planned | 24-hr animated cycle with daylight visualization |
| Future — Street View integration | 💡 Planned | Pull imagery for incident locations |

Full design decisions are documented in [`docs/shaping/`](docs/shaping/).

## Data Fields

The `incidents` table preserves the full FARS ACCIDENT + PERSON record to support future analysis without re-ingestion.

| Field | Source | Description |
|-------|--------|-------------|
| `geom` | ACCIDENT | Point geometry (EPSG:4326) |
| `year`, `month`, `day` | ACCIDENT | Crash date |
| `hour`, `minute` | ACCIDENT | Time of crash (99 = unknown) |
| `lgt_cond` | ACCIDENT | Lighting: 1=Daylight, 2=Dark-not lit, 3=Dark-lit, 4=Dawn, 5=Dusk |
| `weather` | ACCIDENT | 1=Clear, 2=Rain, 3=Sleet, 4=Snow, 5=Fog |
| `route` | ACCIDENT | 1=Interstate, 2=US Hwy, 3=State, 4=County, 5=Local |
| `rur_urb` | ACCIDENT | 1=Rural, 2=Urban |
| `state`, `county` | ACCIDENT | FIPS codes |
| `age`, `sex` | PERSON | Victim demographics |
| `inj_sev` | PERSON | Injury severity (all records = 4, fatal) |

## License

MIT — see [LICENSE](LICENSE) for details.

## Acknowledgments

- [NHTSA](https://www.nhtsa.gov/) for providing FARS data
- [MapLibre GL JS](https://maplibre.org/) and [OpenFreeMap](https://openfreemap.org/) for the mapping stack
- Open-source community for tooling and infrastructure

---

*This project is for research and educational purposes. Always consult official sources for safety-critical decisions.*
