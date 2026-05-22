# Nightly Claude Routine — Multi-Repo Issue Triage

This repo participates in a combined nightly routine that processes `claude`-labeled issues across all four GIS/web projects. The schedule entry is registered once on the equity mapper; see that repo's `.github/claude-routine.md` for the full prompt.

## This repo's context (for the routine)

- **Repo:** `eddielathamjones/pedestrian-safety-mapper`
- **Working directory:** `/home/edwardlatham/repos/pedestrian-safety-mapper`
- **Site:** `https://mapper.eddielathamjones.com/` (planned; may not be live)
- **Key files:**
  - `src/frontend/index.html` — main page
  - `src/frontend/js/` — MapLibre config, filter logic, animation (week/24h), solar overlay
  - `src/frontend/css/` — styles
  - `src/backend/` — Flask API serving FARS incident data
- **Scope:** national (FARS 2001–2023, 123k+ incidents across the US — unlike equity mapper which is Tucson-only)
- **Deploy:** push to main triggers self-hosted GitHub Actions runner

## How to file an issue for the routine

Label the issue `claude`. Paste the current URL + any relevant state (active filters, year range, animate mode on/off, time window, screenshot) into the body. The routine reads this context to reproduce the problem.
