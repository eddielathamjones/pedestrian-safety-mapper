---
shaping: true
---

# FARS Lat/Lon Spike: Geographic Coordinate Field Availability

## Context

Shape A requires plotting pedestrian fatality incidents as points on a map (R5). FARS data spans 1975–2022. Geographic coordinate fields (LATITUDE / LONGITUD) are believed to have been added to the ACCIDENT table at some point in the early 2000s — but the exact year, encoding, completeness, and quality of those fields is unconfirmed from the raw data.

A 2010 release note mentions a bug fix: "a problem in calculating the Latitude and Longitude data field in decimal format has been corrected. The problem was a conversion calculation from Degrees/Minutes/Seconds." This confirms decimal lat/lon existed by 2010 but had known quality issues in earlier years.

For years where no lat/lon exists, the ACCIDENT table encodes location via STATE, COUNTY, CITY, ROUTE, and MILEPT — coarser identifiers that could potentially be geocoded to centroid coordinates.

## Goal

Determine which FARS years have usable lat/lon data, understand the encoding and completeness of those fields, and establish what geographic identifiers are available in years without coordinates.

## Questions

| # | Question |
|---|----------|
| **S1-Q1** | In which year was LATITUDE/LONGITUD first added to the ACCIDENT table? |
| **S1-Q2** | What is the encoding format? (decimal degrees? degrees/minutes/seconds? special null values?) |
| **S1-Q3** | What fraction of records have valid (non-null, non-sentinel) lat/lon values in the first few years the field appears? |
| **S1-Q4** | Are there known sentinel/error values (e.g., 77.7777, 888.8888, 99.9999) that indicate missing data? |
| **S1-Q5** | For pre-lat/lon years, what geographic identifiers exist in the ACCIDENT table (STATE, COUNTY, CITY, ROUTE, MILEPT)? Are these consistent enough to geocode to centroids? |
| **S1-Q6** | Is the lat/lon data quality noticeably different before vs. after the 2010 decimal-conversion bug fix? |

## Findings

Ran against sampled ACCIDENT.csv files for years 1995, 2000, 2001, 2003, 2009, 2010, 2015, 2022.

### S1-Q1: When was LATITUDE/LONGITUD first added?

The field appears in the ACCIDENT table **starting in 2000**, but 2000 is not usable (see Q2/Q3).
The first year with practical decimal coordinates is **2001**.

| Year | Field present | Format | Valid records |
|------|:---:|--------|:---:|
| 1975–1999 | ❌ | — | — |
| 2000 | ✅ | DMS integers (see Q2) | ~0% |
| 2001 | ✅ | Decimal degrees | 81.6% |
| 2003 | ✅ | Decimal degrees | 92.8% |
| 2009 | ✅ | Decimal degrees | 98.8% |
| 2010 | ✅ | Decimal degrees | 98.8% |
| 2015 | ✅ | Decimal degrees | 99.6% |
| 2022 | ✅ | Decimal degrees | 99.7% |

### S1-Q2: Encoding format?

- **2001 onwards**: decimal degrees, high precision (up to 11 decimal places). Longitude is negative (west). Example: `(34.977425, -86.77585)`.
- **2000**: DMS encoded as packed integers (`38370000` = 38°37'00.00"N). However 99.4% of 2000 records are the sentinel `88888888`/`888888888`, so the field is effectively absent for that year.

### S1-Q3: Completeness in early years?

The 18.4% missing in 2001 are empty strings (not reported). Completeness improves steadily:
- 2001: 81.6% → 2003: 92.8% → 2009: 98.8% → 2015+: >99.5%

### S1-Q4: Sentinel / invalid values?

| Sentinel | Meaning |
|----------|---------|
| `''` (empty) | Not reported |
| `88888888` / `888888888` | Not reported (DMS-era integer sentinel) |
| `77.7777` | Not applicable |
| `99.9999` | Unknown |

Filter rule: drop any record where lat or lon is empty, `77.7777`, or `99.9999`. For 2000, drop the entire year (99.4% sentinel, <1% has DMS data).

### S1-Q5: Pre-lat/lon geographic identifiers?

All pre-2001 years have: `STATE` (FIPS state code), `COUNTY` (FIPS county code), `CITY` (FARS proprietary code), `ROUTE`, `MILEPT`.

Feasibility for centroid geocoding:
- **STATE + COUNTY (FIPS)** → county centroid. Straightforward — FIPS codes map directly to a standard lookup table. Granularity: county level.
- **CITY** → FARS-proprietary code, not standard FIPS. Requires a NHTSA lookup table (likely available in the user manuals). Granularity: city/place level if resolvable.
- **ROUTE + MILEPT** → could theoretically locate to a road segment, but this requires a route network dataset and is complex.

**Verdict**: County-centroid geocoding of pre-2001 data is feasible with STATE+COUNTY FIPS. Worth exploring as a "historical tier" (see GitHub Issue #1).

### S1-Q6: Quality before vs. after 2010 bug fix?

No difference visible in the data. The 2010 fix ("correction of decimal conversion from DMS") appears to have been applied retroactively when NHTSA re-released historical files in CSV format (2019 restructuring). The decimal values in 2009 and 2010 are both clean to the same precision.

---

## Conclusions for Shape A

**"Geo-enabled era"**: 2001–2022 — use these years for map point plotting.
**Data quality is excellent from 2003+** — 92%+ valid, rising to ~99.7% by 2022.
**Pre-2001 (1975–2000)**: no usable coordinates. Treat as a separate "historical tier" — plotted at county centroids — if/when that scope is added.
**2000**: skip entirely (99.4% sentinel; not worth the complexity).

**Sentinel filter for the ETL (A1)**:
```python
# Drop records where lat or lon is invalid
SENTINEL_LAT = {'', '77.7777', '99.9999'}
SENTINEL_LON = {'', '77.7777', '99.9999', '888.8888'}

def has_valid_coords(lat, lon):
    return lat not in SENTINEL_LAT and lon not in SENTINEL_LON
```

**Impact on R5**: R5 can now pass for Shape A, scoped to 2001–2022. Pre-2001 data is a future enhancement tracked in Issue #1.

## Related

- GitHub Issue: #1 — Explore FARS location encoding for pre-lat/lon years
- Shaping doc: R5, A1 (flagged)
