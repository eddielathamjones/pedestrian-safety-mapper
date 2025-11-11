# ☠ TUCSON STREET DEATHS ☠

## THE UGLY TRUTH

Your streets are killing machines. **719 people dead** since 1991. That's not an accident—that's a **design failure**.

## THE BODY COUNT

```
2018: 30 DEAD
2019: 42 DEAD  (+40%)
2020: 46 DEAD  (+9%)
2021: 45 DEAD  (-2%)
2022: 64 DEAD  (+42%)

DOUBLED IN 4 YEARS.
```

## WHERE THEY DIED

- **67%** died MID-BLOCK (not at crosswalks)
- **63%** killed in DARKNESS
- **45%** on PRINCIPAL ARTERIALS
- **Peak killing hours**: 6PM-10PM

## THE DESIGN

### BLACK & RED INTERFACE
No soft colors. No gentle language. Just the raw data.

- **Black background**: Like the asphalt where they died
- **Blood red accents**: You can't miss it
- **Brutal typography**: Bebas Neue, Anton, Space Mono
- **Zine aesthetic**: DIY, punk, unfiltered

### WHAT YOU GET

```
☠ DEATH MARKERS - Every fatality mapped with GPS precision
☠ CARNAGE FILTER - Year, road type, time, lighting, location
☠ DANGER ZONES - Heatmap showing where streets kill most
☠ BODY COUNT CHARTS - The numbers don't lie
☠ DEADLIEST STREETS - Hot spots with 3+ deaths
☠ RAW API - All data, no sugarcoating
```

## RUNNING IT

### 1. Get MapBox Token

https://www.mapbox.com/signup/ (free)

### 2. Add Your Token

Edit `src/frontend/js/app.js` line 2:
```javascript
mapboxgl.accessToken = 'pk.YOUR_TOKEN_HERE';
```

### 3. Run

```bash
pip install -r requirements.txt
python3 src/backend/app.py
```

### 4. View

**Standard version**: http://localhost:5000
**EDGY version**: http://localhost:5000/edgy ← **THIS ONE**

## THE FEATURES

### DEATH MAP
- Click markers → See when & where they died
- Toggle heatmap → Danger zone visualization
- Cluster view → Performance with 445 mapped deaths

### FILTER THE CARNAGE
- **Years**: 1991-2022 (focus on 2018-2022 for the crisis)
- **Road Type**: Which roads kill most? (Arterials = 45%)
- **Time**: Evening rush = death rush
- **Lighting**: Dark = deadly
- **Location**: Mid-block deaths = design failure

### THE CHARTS

1. **BODY COUNT RISES** - Year trend showing DOUBLING
2. **DEATH BY HOUR** - 6pm-10pm is slaughter time
3. **WHICH ROADS KILL** - Arterials dominate
4. **DARKNESS KILLS** - 63% in dark conditions

### DEADLIEST STREETS

Auto-detected high-risk corridors. Click to zoom.

Example hot spots:
- W VALENCIA RD
- E SPEEDWAY BLVD
- N CAMPBELL AVE
- E IRVINGTON RD

## THE DATA

**Source**: FARS (Fatality Analysis Reporting System) - NHTSA
**Coverage**: 1991-2022 (32 years)
**Total**: 719 pedestrian fatalities
**Mapped**: 445 with GPS coordinates (62%)

## THE MESSAGE

This isn't about "accidents." This is about:

- **ROADS DESIGNED FOR SPEED** over safety
- **MISSING CROSSWALKS** where people need them
- **INADEQUATE LIGHTING** at night
- **CAR-CENTRIC PLANNING** that kills pedestrians

## WHAT NEEDS TO HAPPEN

```
→ PROTECTED CROSSWALKS at mid-block crossings
→ STREET LIGHTING on arterials
→ TRAFFIC CALMING in residential areas
→ VISION ZERO implementation NOW
→ PROTECTED BIKE LANES & pedestrian infrastructure
→ LOWER SPEED LIMITS on arterials
```

## THE TECH

- **Backend**: Flask + Python (REST API, 9 endpoints)
- **Frontend**: HTML5 + CSS3 (brutal design)
- **Mapping**: MapBox GL JS (WebGL accelerated)
- **Charts**: Chart.js (data visualization)
- **Typography**: Bebas Neue, Anton, Space Mono (aggressive)
- **Aesthetic**: Black/red, zine-inspired, punk DIY

## API ACCESS

All data available via REST API:

```bash
# Get recent deaths
curl "http://localhost:5000/api/incidents?year_start=2020"

# Get arterial deaths at night
curl "http://localhost:5000/api/incidents?road_type=Principal%20Arterial%20-%20Other&lighting=Dark"

# Get hot spots
curl "http://localhost:5000/api/hot_spots"

# Get trends
curl "http://localhost:5000/api/trends"
```

## THE DIFFERENCE

### Standard Version (index.html)
- Professional design
- Policy-maker friendly
- Neutral language
- Blue gradients
- "Pedestrian fatalities"

### Edgy Version (index-edgy.html) ← **YOU WANT THIS**
- Confrontational design
- Activist-oriented
- Raw language
- Blood red on black
- "DEAD"

## USE CASES

### For Activists
- Show city council the body count
- Demand Vision Zero NOW
- Visualize the crisis

### For Journalists
- Data-driven stories about street safety
- Compare years, show trends
- Hot spot investigations

### For Citizens
- Know which streets kill
- Understand the scale
- Demand better from elected officials

## NO BULLSHIT

64 people died on Tucson streets in 2022.
That's **113% more than 2018**.
They were walking. On foot. In their own neighborhoods.

Your streets killed them.

**FIX. THE. STREETS.**

---

## Files

- `src/frontend/index-edgy.html` - Confrontational UI
- `src/frontend/css/styles-edgy.css` - Black/red brutal design
- `src/backend/app.py` - Serves both versions
- Same data, different presentation

## Credits

Data: NHTSA FARS database
Design: Inspired by zine culture, Marco Pierre White intensity, punk DIY aesthetic
Message: Vision Zero, pedestrian safety advocacy

**Built for accountability. Not decoration.**

---

☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠

**719 DEAD. DEMAND BETTER.**

☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠☠
