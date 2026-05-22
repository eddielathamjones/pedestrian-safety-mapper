# CLAUDE.md — Pedestrian Safety Mapper

## What this is

An interactive map of every recorded pedestrian fatality in the US from 2001–2024 — 123,000+ incidents from the NHTSA Fatality Analysis Reporting System (FARS). The map makes two arguments: darkness kills (solar overlay), and the same roads keep killing (road heat lines).

Design voices: Tufte (data honesty, data-ink ratio) and Byrne (the violence of the symbol is appropriate to the subject). Every visual decision should serve one of those two.

**Live site:** `https://mapper.eddielathamjones.com/` (planned; may not be live yet)

## Stack

| Layer | Technology |
|-------|-----------|
| Frontend | MapLibre GL JS (vanilla + CDN), SunCalc |
| Backend | Flask + gunicorn, Python 3.11 |
| Database | PostGIS (PostgreSQL 15) |
| Deploy | Docker on eddienet (192.168.0.84), `~/docker/gis/docker-compose.yml` |

## Key files

- `src/frontend/index.html` — main page, all UI markup
- `src/frontend/js/app.js` — MapLibre config, filter logic, week/24h animation, solar overlay, Sun HUD
- `src/frontend/css/app.css` — all styles
- `src/backend/app.py` — Flask API (`/api/incidents`, `/api/summary`, `/api/data-status`, `/api/report`)
- `src/backend/schema.sql` — PostGIS schema (incidents table with GIST index)
- `src/backend/Dockerfile` — backend container
- `docker-compose.yml` — local dev (DB + API)

## Common commands

```bash
# Local dev (spins up PostGIS + Flask API)
docker compose up --build

# Backend only (if DB is already running)
.venv/bin/python -m flask --app src/backend/app run --port 5001

# Run ETL to load FARS data (requires DATABASE_URL set)
python -m src.data_processing.load_fars --year 2024

# Check DB row count
psql postgresql://postgres:postgres@localhost:5432/pedestrian_safety \
  -c "SELECT year, count(*) FROM incidents GROUP BY year ORDER BY year"
```

## API routes

| Route | Description |
|-------|-------------|
| `GET /api/incidents?year=N` | GeoJSON FeatureCollection for one year; optional `bbox`, `tod`, `road` filters |
| `GET /api/summary` | Row counts per year |
| `GET /api/data-status` | Whether newer FARS data exists on NHTSA |
| `POST /api/report` | Create a GitHub issue (requires `GITHUB_TOKEN` env var) |

## Database schema (`incidents` table)

| Column | Notes |
|--------|-------|
| `geom` | Point, EPSG:4326, GIST-indexed |
| `year`, `month`, `day`, `hour`, `minute` | FARS datetime fields |
| `lgt_cond` | 1=Daylight 2=Dark-not-lit 3=Dark-lit 4=Dawn 5=Dusk |
| `weather` | 1=Clear 2=Rain 3=Sleet 4=Snow 10=Fog |
| `route` | 1=Interstate 2=US Hwy 3=State 4=County 5=Local |
| `state`, `county` | FIPS codes |
| `age`, `sex`, `inj_sev` | Victim demographics (all records fatal) |

## Frontend architecture

- **Static mode** (default): browse full dataset with time-of-day and day-of-week filters, presets, time-window slider, solar overlay, Sun HUD compass
- **Animate mode**: week cycle (Mon–Sun) or 24h cycle; dots appear on first occurrence and decay into road heat layer; playback speed control
- **Road heat layer**: kernel-density heat lines on road geometry weighted by fatality count; toggleable
- **Solar overlay**: background darkness matches actual sun position at selected hour (SunCalc); terminator line and night overlay derived from real solar geometry

Frontend is vanilla JS + CDN (MapLibre, SunCalc). No bundler — keep it that way.

## Deploy pattern (eddienet)

The app is deployed on eddienet (192.168.0.84) via the shared GIS docker-compose:

```
~/docker/gis/docker-compose.yml  →  pedestrian-safety-mapper container (port 5001)
                                      pedestrian-safety-mapper-db-1 (PostGIS)
```

Auto-deploy on push to `main` is **not yet configured** — deploy manually:

```bash
ssh eddienet "docker compose -f ~/docker/gis/docker-compose.yml up -d --build pedestrian-safety-mapper"
```

Cloudflare tunnel routes `mapper.eddielathamjones.com` → localhost:5001 via the system cloudflared on eddienet.

## Issue reporting

The "⚑ Report" button in the sidebar POSTs to `/api/report`, which creates a GitHub issue labeled `claude`. Requires `GITHUB_TOKEN` env var (fine-grained PAT, Issues: read+write on this repo). A nightly Claude routine reads these issues and opens fix PRs.

## What not to do

- Don't add a bundler — the frontend is intentionally vanilla
- Don't change the national scope to a city filter (unlike equity mapper, this is US-wide by design)
- Don't add tile vibes — the map has its own mood; the dark palette is the argument, not a filter
- Don't remove the solar overlay — darkness is causal, not decorative (Tufte + Byrne agree)
