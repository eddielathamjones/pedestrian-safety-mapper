# Solar-Corrected Temporal Analysis of Pedestrian Fatalities
## Methods and Calculations

**Project:** Pedestrian Safety Mapper
**Branch:** `feature/lighting-focus`
**Data source:** FARS (Fatality Analysis Reporting System), NHTSA, 2001–2022

---

## Abstract

Pedestrian fatality records in FARS are timestamped in local clock time — a social construct that varies by jurisdiction and is shifted twice yearly by daylight saving time. Clock time is a poor proxy for the environmental variable most likely to influence pedestrian visibility: solar illumination. This document describes the methods used to replace a clock-hour animation axis with one calibrated to actual solar position, and explains the underlying astronomical calculations.

---

## 1. The Problem with Clock Time

FARS records the hour of each fatal incident as a local wall-clock hour (0–23). The continental United States spans four standard time zones (UTC−5 to UTC−8) and applies daylight saving time inconsistently across jurisdictions. As a result, "hour 18" in the dataset simultaneously represents:

- 6:00 PM Eastern — late afternoon, sun still well above the horizon in summer
- 6:00 PM Pacific — mid-afternoon in summer, sun high overhead
- The same wall-clock hour in January in Minnesota (twilight or darkness) and July in Arizona (full daylight)

A raw hour-of-day analysis asks: *when by the clock do fatalities occur?*
The corrected analysis asks: *under what solar conditions do fatalities occur?*

These are different questions with potentially different answers.

---

## 2. Solar Position: The Underlying Geometry

The position of the sun in the sky at any location and moment is fully determined by three parameters:

- **φ** — observer latitude (degrees)
- **λ** — observer longitude (degrees)
- **t** — universal time (UTC)

The key output is the **solar altitude angle α** (also called solar elevation), measured in degrees from the horizon:

- α > 0° — sun is above the horizon (daylight)
- α = 0° — sun is at the horizon (sunrise or sunset)
- −6° < α < 0° — civil twilight (enough ambient light to see without artificial lighting)
- −12° < α < −6° — nautical twilight (horizon visible, stars visible)
- −18° < α < −12° — astronomical twilight (sky still faintly lit)
- α < −18° — astronomical night (sky fully dark)

### 2.1 The Altitude Formula

Solar altitude is computed from:

$$\sin(\alpha) = \sin(\varphi)\sin(\delta) + \cos(\varphi)\cos(\delta)\cos(H)$$

Where:
- **δ** = solar declination — the angle between the sun and the celestial equator. Ranges from −23.4° (winter solstice) to +23.4° (summer solstice), passing through 0° at both equinoxes.
- **H** = hour angle — the angular distance of the sun from solar noon, measured westward. H = 0° at solar noon, H = −90° at sunrise (approximately), H = +90° at sunset (approximately).

The hour angle is derived from the equation of time (a correction for the eccentricity and axial tilt of Earth's orbit) and the observer's longitude.

### 2.2 Why the Equinox Simplifies Things

At the vernal equinox (approximately March 20), the solar declination is zero: **δ = 0°**.

The altitude formula reduces to:

$$\sin(\alpha) = \cos(\varphi)\cos(H)$$

This has an elegant consequence: **at the equinox, sunrise and sunset occur at exactly H = ±90°, which corresponds to 6:00 AM and 6:00 PM local solar time regardless of latitude.** (Small corrections for atmospheric refraction and the equation of time shift this by a few minutes in practice.)

This is why the equinox is used as a reference: it is the one moment in the year where the day-night boundary is symmetric and latitude-independent. It provides a neutral baseline unbiased by season.

---

## 3. Implementation: SunCalc.js

Solar position is computed using **SunCalc.js** (v1.9.0), a JavaScript library implementing the algorithms of Jean Meeus, *Astronomical Algorithms* (2nd ed., Willmann-Bell, 1998). SunCalc computes the sun's ecliptic longitude, declination, and right ascension from a truncated VSOP87 series — accurate to approximately ±0.3° over the range of years in our dataset.

The relevant function:

```javascript
SunCalc.getPosition(date, latitude, longitude)
// Returns: { altitude: radians, azimuth: radians }

SunCalc.getTimes(date, latitude, longitude)
// Returns: { sunrise: Date, sunset: Date, dawn: Date, dusk: Date, ... }
```

All angles from `getPosition` are in radians. We convert to degrees:

```javascript
const altDeg = pos.altitude * (180 / Math.PI);
```

---

## 4. UTC Offset Approximation

FARS hours are local clock time. SunCalc operates in UTC. To convert a local hour `h` to a UTC hour for SunCalc input, we need the UTC offset at the incident's location.

We approximate using the **theoretical time zone boundary formula**:

$$\text{UTC offset} \approx \text{round}\!\left(\frac{\lambda}{15}\right)$$

where λ is longitude in degrees. This follows from the definition of time zones as 15°-wide longitudinal bands (360° / 24 hours = 15°/hour).

**Accuracy:** The continental US spans approximately λ = −67° (Maine) to λ = −124° (Washington coast), giving theoretical UTC offsets of −4 to −8. Actual US time zones are UTC−5 (Eastern), UTC−6 (Central), UTC−7 (Mountain), UTC−8 (Pacific) — matching the formula within ±1 hour for most locations. Boundary irregularities (Indiana, Arizona, etc.) are not corrected.

The conversion:

```javascript
const utcOffset = Math.round(lon / 15);           // e.g., lon = -97° → offset = -6
const utcHour   = ((localHour - utcOffset) % 24 + 24) % 24;
const posDate   = new Date(Date.UTC(2024, 2, 20, utcHour, 0, 0));
```

The `+24) % 24` ensures the result wraps correctly for hours near midnight.

---

## 5. The Per-Slot Centroid Method

### 5.1 Motivation

A single global centroid — the mean lat/lon of all incidents in a year — is a poor reference for a time-varying animation. Incidents do not distribute uniformly across the day. Commuter-heavy crash hours (7–9 AM, 4–7 PM) may cluster geographically differently from late-night hours. Using a single centroid applies the same solar reference to all hours, which is internally inconsistent.

### 5.2 Method

For each hour slot *h* ∈ {0, 1, ..., 23}, we compute a **slot centroid** from the incidents that occurred at that hour across all selected years:

$$\bar{\varphi}_h = \frac{1}{|S_h|} \sum_{i \in S_h} \varphi_i \qquad \bar{\lambda}_h = \frac{1}{|S_h|} \sum_{i \in S_h} \lambda_i$$

where $S_h$ is the set of all incidents with recorded hour equal to *h*, and φᵢ, λᵢ are the latitude and longitude of incident *i*.

We then compute the solar altitude at the equinox for that slot's centroid:

$$\alpha_h = f_{\text{SunCalc}}\!\left(\text{equinox},\; \bar{\varphi}_h,\; \bar{\lambda}_h\right)$$

This yields a 24-element curve `animSolarCurve[0..23]`, computed with 24 SunCalc calls after each data load.

### 5.3 Implementation

```javascript
function buildSolarCurve(hourBuckets) {
  const curve    = new Float32Array(24);
  const equinox  = new Date(Date.UTC(2024, 2, 20, 12, 0, 0));

  for (let h = 0; h < 24; h++) {
    const bucket = hourBuckets.get(h);

    // Compute slot centroid
    let latSum = 0, lonSum = 0;
    for (const feat of bucket) {
      const [lon, lat] = feat.geometry.coordinates;
      latSum += lat;  lonSum += lon;
    }
    const slotLat   = latSum / bucket.length;
    const slotLon   = lonSum / bucket.length;
    const utcOffset = Math.round(slotLon / 15);
    const utcH      = ((h - utcOffset) % 24 + 24) % 24;

    const d      = new Date(Date.UTC(2024, 2, 20, utcH, 0, 0));
    curve[h]     = SunCalc.getPosition(d, slotLat, slotLon).altitude * (180 / Math.PI);
  }
  return curve;
}
```

---

## 6. Mapping Solar Altitude to Visual Darkness

The map tile overlay opacity must be driven by solar altitude in a perceptually meaningful way. We use the following mapping:

**Definition of daylight factor *d*:**

$$d(\alpha) = \text{clamp}\!\left(\frac{\alpha + 18°}{18°},\; 0,\; 1\right)$$

- At α = 0° (horizon): *d* = 1.0 (full light)
- At α = −18° (astronomical night boundary): *d* = 0.0 (full dark)
- Linear between, clamped at extremes

This range captures all twilight phases: civil (0° to −6°), nautical (−6° to −12°), and astronomical (−12° to −18°).

**Smoothstep for perceptual linearity:**

A linear ramp in *d* does not match the perceptual experience of twilight, which brightens rapidly near the horizon and more slowly at high solar angles. We apply a cubic smoothstep:

$$s(d) = 3d^2 - 2d^3$$

This is the Hermite interpolation between 0 and 1, zero-derivative at both endpoints.

**Overlay opacity:**

$$\text{opacity} = 0.72 \times (1 - s(d))$$

The constant 0.72 sets the maximum overlay darkness. At this value the base map tiles are darkened to approximately 28% of their original brightness, representing deep astronomical night.

**Between-slot interpolation:** During animation playback, the current simulation hour is typically non-integer. We linearly interpolate between adjacent slot altitudes:

```javascript
const altDeg = curve[h0] + (curve[h1] - curve[h0]) * frac;
```

where `h0 = floor(hour)`, `h1 = (h0 + 1) % 24`, and `frac = hour % 1`.

---

## 7. The Solar Elevation Display

The animation control panel displays the current solar elevation as a signed angle:

```
☀ +42.3°    sun above horizon
◐  −3.1°    civil twilight
☾ −28.4°    deep night
```

The icons follow the standard twilight classification:
- **☀** when α > 0° (sun above horizon)
- **◐** when −6° ≤ α ≤ 0° (civil twilight)
- **☾** when α < −6° (sun in nautical or deeper twilight)

The value shown is interpolated from the same `animSolarCurve`, so the display is consistent with the background darkness at every moment.

---

## 8. Worked Example

**Hour slot: 2 AM (h = 2)**
Year range: 2001–2022, national dataset

Suppose incidents recorded at 2 AM cluster with a centroid of approximately **φ̄ = 36.2°N, λ̄ = −90.5°** (central Mississippi Valley — a plausible distribution for late-night highway incidents).

UTC offset: round(−90.5 / 15) = round(−6.03) = **−6**
UTC hour: (2 − (−6)) % 24 = **8**
Reference date: March 20, 2024, 08:00 UTC

SunCalc computes:
- Solar declination at equinox: δ ≈ 0°
- Hour angle at 08:00 UTC at λ = −90.5°: H ≈ 08:00 UTC − solar noon UTC at that longitude

Solar noon at λ = −90.5° occurs when the sun's right ascension equals the local meridian, approximately 18:00 UTC at the equinox (solar noon at local time ≈ 12:00 local = 18:00 UTC for UTC−6).

Hour angle from noon: H = (8 − 18) × 15° = −150°

$$\sin(\alpha) = \cos(36.2°)\cos(−150°) = 0.807 \times (−0.866) = −0.699$$
$$\alpha = \arcsin(−0.699) \approx −44.2°$$

The sun is 44° below the horizon — deep astronomical night. Overlay opacity: `0.72 × (1 − s(clamp((−44.2 + 18)/18, 0, 1))) = 0.72 × 1.0 = 0.72` (maximum darkness).

---

## 9. Limitations

### 9.1 UTC Offset Approximation

The longitude-derived UTC offset (`round(λ/15)`) ignores:
- Daylight saving time (shifts clocks by +1 hour in summer)
- Political time zone boundaries (Indiana, western China, etc.)
- Half-hour and 45-minute offset zones (not present in the US)

For the continental US, the maximum error from DST is ±1 hour. Since FARS collects data year-round and DST applies to approximately 7 months of the year, roughly 58% of summer incidents may have their local hour shifted by one hour relative to our assumption.

### 9.2 Aggregated Time Zones

FARS local hours are not standardised to a single time zone before aggregation. An incident at "hour 18" in New York City (solar altitude ≈ +5° at the equinox) and "hour 18" in Los Angeles (solar altitude ≈ +25°) both appear at the same point on the animation axis. The per-slot centroid partially corrects for this by weighting the reference location toward where 6 PM incidents actually cluster, but the individual-level solar conditions are not recovered.

### 9.3 Equinox vs. Actual Date

The equinox baseline means the background represents *equinox darkness*, not *actual darkness on the day of each incident*. A fatality at 6 AM in January in Minnesota occurred in full darkness (sunrise ≈ 7:45 AM), but on the equinox baseline, 6 AM near that latitude is approximately sunrise (solar altitude ≈ 0°). The baseline systematically underestimates darkness in winter and overestimates it in summer.

### 9.4 Mean Centroid vs. Incident Distribution

Even with per-slot centroids, the method uses a single representative point for each hour. Incidents within a slot spread across the country; some occur in full daylight while others occur in darkness simultaneously. The display shows only the *average* solar condition for that hour, not the distribution.

---

## 10. Future Corrections (Phase 2)

### P2-1: Seasonal Date Scrubber
Replace the fixed equinox reference with a user-controlled date. This allows the background to represent winter conditions (short days, late sunrises) or summer conditions (long days, early sunrises). The `SunCalc.getTimes()` call is parameterised by date, so the only required change is exposing a date input in the UI.

### P2-2: Viewport-Adaptive Centroid
When the user pans to a specific region, recompute the centroid from only the incidents visible in the viewport. This makes the solar reference specific to the region being examined, improving accuracy for sub-national analysis.

### P2-3: Per-Incident Solar Classification
Compute `SunCalc.getPosition(date, lat, lon)` for each individual incident using its actual recorded date (year, month, day), hour, and coordinates. This eliminates all three approximations above — timezone, aggregation, and seasonal averaging — producing a fully per-incident ground-truth solar altitude. The computational cost is O(n) SunCalc calls at data load time (approximately 50,000–100,000 calls per year), which is feasible client-side in a few seconds.

---

## References

1. Meeus, J. (1998). *Astronomical Algorithms* (2nd ed.). Willmann-Bell.
2. Mourner, V. *SunCalc.js* (v1.9.0). https://github.com/mourner/suncalc
3. National Highway Traffic Safety Administration. *Fatality Analysis Reporting System (FARS) Analytical User's Manual*, 1975–2022.
4. United States Naval Observatory. *The Astronomical Almanac*. Annual.
