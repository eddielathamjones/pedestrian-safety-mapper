# Forensic Archaeology of the Present
## Archaeological Site Reports for Traffic Violence

### Methodological Statement

**This project documents contemporary pedestrian deaths using archaeological field methodology.**

Crash sites become excavation sites. Infrastructure becomes artifacts. Deaths become "depositions." Everything is written in past tense, as if excavating ruins 500 years in the future.

**This is temporal displacement as critical method.**

By treating the present as archaeological past, we create critical distance from normalized violence. The future archaeologist cataloging "Late Automobile Age deposition events" forces us to see what we've accepted as inevitable.

---

## Concept

Archaeologists document the dead. They catalog artifacts. They interpret lost civilizations with empathy and horror.

**What if we did this for traffic deaths—right now, while they're still happening?**

The archaeological voice (detached, past tense, scientific) creates dissonance when applied to ongoing tragedy:

> "The individual, aged 8-10 years, was deposited at the intersection of two high-speed arterial corridors. Analysis of vehicular artifact assemblage suggests ritual prioritization of speed over safety. Cause of deposition: impact with 5,200-pound metal artifact traveling at 45 mph."

The absurdity of treating preventable deaths as "archaeological phenomena" is the point. Future civilizations will excavate our streets and wonder what the hell we were thinking.

## Archaeological Methodology Applied

### Standard Archaeological Practice

1. **Site Survey**: Document location, context, stratigraphy
2. **Artifact Cataloging**: Record all objects (street signs, paint, signals)
3. **Human Remains Documentation**: Age, sex, trauma analysis
4. **Context Interpretation**: Reconstruct activity at time of deposition
5. **Significance Assessment**: Cultural/historical importance
6. **Preservation Recommendations**: How to prevent future damage

### Applied to Traffic Violence

1. **Site Survey**: Crash location, road type, infrastructure
2. **Artifact Cataloging**: Crosswalk paint, traffic signals, street signs, vehicle fragments
3. **Human Remains Documentation**: Victim age, time of death, trauma (vehicle impact)
4. **Context Interpretation**: "High-speed arterial ritual corridor with inadequate pedestrian accommodation"
5. **Significance Assessment**: "Represents characteristic Late Automobile Age prioritization of vehicular speed"
6. **Preservation Recommendations**: "Immediate infrastructure modification to prevent recurrence"

## Installation

```bash
# Already installed from main requirements:
# pandas, requests

# No additional dependencies needed
```

## Usage

### 1. Generate Archaeological Site Report

```bash
# From pedestrian fatality GeoJSON
python scripts/forensic_archaeology.py \
    data/pedestrian_fatalities.geojson \
    --output-dir archaeological_sites/
```

**Output:**
- Individual site reports (one per fatality): `SITE_CA_2020_00342.txt`
- Summary catalog: `site_catalog.csv`
- Period analysis: `period_summary.json`
- Artifact inventory: `artifact_assemblage.csv`

### 2. Generate Period Summary

```bash
# Analyze by archaeological period
python scripts/forensic_archaeology.py \
    data/pedestrian_fatalities.geojson \
    --period-analysis \
    --output period_comparison.json
```

Compares deposition patterns across:
- Early Automobile Age (1900-1945)
- Interstate Highway Period (1945-1970)
- Suburban Expansion Phase (1970-1990)
- SUV Dominance Period (1990-2010)
- Late Automobile Age (2010-2030)

### 3. Artifact Assemblage Analysis

```bash
# Catalog infrastructure artifacts
python scripts/forensic_archaeology.py \
    data/pedestrian_fatalities.geojson \
    --artifact-focus \
    --output artifacts.csv
```

Catalogs:
- Traffic control devices
- Crosswalk markings (condition, wear patterns)
- Street lighting (presence, functionality)
- Vehicular fragments (make, model, size)

## Example Output

### Archaeological Site Report

```
======================================================================
ARCHAEOLOGICAL SITE REPORT
======================================================================

SITE IDENTIFICATION
Site Number:           CA-2020-00342
Grid Reference:        N37.8716, W122.2727
Excavation Date:       2024-11-11
Period:                Late Automobile Age (2010-2030 CE)
Site Type:             Deposition event, high-speed arterial context

STRATIGRAPHIC CONTEXT
Layer:                 Urban arterial surface, asphalt composition
Context Type:          High-speed principal arterial complex
Road Classification:   Principal Arterial (Federal Highway Admin. Type 2)
Posted Speed Limit:    45 mph (72 km/h)
Design Speed:          50+ mph (estimated from lane width, curvature)
Lighting Conditions:   Dark, artificially lighted (sodium vapor)

TEMPORAL CONTEXT
Date of Deposition:    2020-03-15
Time of Day:           21:30 (night, rush hour concluded)
Season:                Spring
Weather Conditions:    Clear

ARTIFACT ASSEMBLAGE
Total Artifacts:       8 in situ

Artifact 1: Traffic Control Device (Type IIA Pedestrian Signal)
  Material: Aluminum housing, LED elements
  Condition: Functional but degraded (estimated 40% luminosity)
  Location: 45 feet from deposition site
  Notes: Standard 7-second crossing time for 40-foot roadway
         (insufficient for elderly/mobility-impaired)

Artifact 2: Crosswalk Marking (Type A Ladder Style)
  Material: Thermoplastic paint, white pigment
  Condition: Heavily abraded, 60% material loss
  Width: 72 inches
  Notes: Wear pattern suggests inadequate maintenance cycle

Artifact 3: Street Lighting Standard (Cobra-Head Type)
  Material: Cast aluminum, high-pressure sodium lamp
  Condition: Functional, 150-foot spacing
  Notes: Illumination inadequate for pedestrian detection at 45 mph

Artifact 4: Vehicular Fragment (2019 Ford F-150 Pickup)
  Material: Steel/aluminum chassis, 5,200 lbs curb weight
  Condition: Minor damage to front right quarter panel
  Notes: Vehicle height (hood: 42 inches) incompatible with
         pedestrian anatomy (center of mass: 36 inches adult)

Artifact 5: Speed Limit Sign (Type R2-1)
  Material: Aluminum, reflective coating
  Text: "SPEED LIMIT 45"
  Condition: Compliant with MUTCD standards
  Notes: Posted speed exceeds safe pedestrian environment threshold

Artifact 6: Commercial Signage (Multiple)
  Density: 12 signs per 100 linear feet
  Notes: High visual complexity, driver attention dilution

Artifact 7: Sidewalk Infrastructure
  Width: 4 feet (substandard, AASHTO recommends 6-8 feet)
  Buffer: Absent (0 feet separation from travel lane)
  Condition: Adequate

Artifact 8: Pavement Marking (Skip Stripe)
  Type: Lane demarcation
  Condition: Standard
  Notes: Four travel lanes, enabling high-speed travel

HUMAN REMAINS
Individual Number:     CA-2020-00342-IND01
Age:                   65-75 years (osteological analysis: elderly adult)
Sex:                   Female (pelvic morphology)
Stature:               162 cm (5'4")
Time of Death:         21:30-21:35 (estimated from witness accounts)

TRAUMA ANALYSIS
Cause of Death:        Blunt force trauma, vehicular impact
Primary Impact Point:  Right lateral thorax
Impact Speed:          41-45 mph (estimated from injury pattern, vehicle damage)
Mechanism:             High-speed arterial crossing attempt during
                       inadequate pedestrian signal phase

Injury Pattern:        Consistent with "pedestrian projection" mechanism:
                       - Primary impact: lower extremity (bumper height 18")
                       - Secondary impact: hood/windshield (42" hood height)
                       - Tertiary impact: ground surface
                       Multiple fractures: femur, pelvis, ribs, skull

INTERPRETATION
This deposition event occurred within a characteristic Late Automobile
Age high-speed arterial corridor. The individual attempted to cross a
four-lane principal arterial designed for vehicular speeds of 45+ mph.

Infrastructure analysis reveals systematic prioritization of vehicular
throughput over pedestrian safety:
  - Excessive roadway width (48 feet) enabling high speeds
  - Inadequate pedestrian signal timing (7 seconds for 40+ feet)
  - Degraded crosswalk visibility (60% paint loss)
  - Vehicle design incompatible with vulnerable road user safety

The artifact assemblage is consistent with "stroad" typology—a hybrid
form attempting to serve both high-speed arterial (road) and commercial
access (street) functions. This design pattern is strongly correlated
with elevated pedestrian fatality rates.

COMPARATIVE CONTEXT
Similar deposition patterns documented at 43 other sites within 5-mile
radius (2015-2020 survey). Clustering suggests systemic infrastructure
failure rather than isolated incident.

European comparative data (Netherlands, Norway) from equivalent period
shows 80-90% reduction in deposition events through infrastructure
modification: speed reduction (30 km/h = 19 mph in urban contexts),
mode separation, vehicle design regulation.

CULTURAL INTERPRETATION
This site exemplifies Late Automobile Age contradictions. The society
possessed complete technical knowledge of causation (speed, vehicle
mass, infrastructure design) yet continued practices resulting in
systematic mortality.

Possible explanations:
  1. Ritual importance of speed exceeded safety considerations
  2. Economic structures prioritized vehicular commerce
  3. Cultural normalization of routine violence
  4. Political inability to override automobile industry influence
  5. Temporal discounting (future costs ignored for present convenience)

Future archaeologists will likely interpret this period as sacrificial:
routine human offerings to maintain high-speed transportation systems.

SIGNIFICANCE ASSESSMENT
This site is SIGNIFICANT for the following reasons:

  1. Typological: Represents characteristic stroad deposition pattern
  2. Chronological: Late Automobile Age (pre-transition period)
  3. Comparative: Demonstrates US infrastructure divergence from
     European safety standards
  4. Pedagogical: Illustrates preventable tragedy
  5. Memorial: Individual life lost to systemic design failure

RECOMMENDATIONS
Preservation Priority: URGENT

The site requires immediate infrastructure modification to prevent
additional deposition events:

  1. Speed reduction: 45 mph → 25 mph (evidence: 90% fatality risk
     reduction per FHWA)
  2. Road diet: 4 lanes → 2 lanes + center refuge island
  3. Crosswalk enhancement: High-visibility markings, raised crossing
  4. Signal timing: Extend pedestrian phase to 15 seconds minimum
  5. Buffer installation: 8-foot separation between sidewalk and travel lane
  6. Lighting upgrade: LED, pedestrian-scale, 50-foot spacing

Cost estimate: $250,000 per intersection
Lives saved (10-year projection): 2-4
Cost per life: $62,500-$125,000

Comparative cost of inaction: $9.6 million (USDOT value of statistical
life) × 2-4 lives = $19.2-38.4 million

SITE PRESERVATION STATUS
Current Status:         UNPROTECTED (no modifications implemented)
Threats:                Ongoing deposition risk (continued high-speed
                       arterial operation)
Mitigation:            None
Urgency:               IMMEDIATE

EXCAVATION TEAM
Principal Investigator: Forensic Archaeology Division
Field Date:             2024-11-11
Report Date:            2024-11-11
Institutional Affiliation: Pedestrian Safety Mapper Project

REFERENCES
- Federal Highway Administration (FHWA) Pedestrian Safety Data
- National Complete Streets Coalition Design Guidelines
- Vision Zero Network Infrastructure Standards
- Netherlands Sustainable Safety Principles
- Archaeological Site Recording Standards (adapted)

======================================================================
END REPORT
======================================================================
```

## Period Classification

The project divides crash history into archaeological periods based on infrastructure and vehicle characteristics:

### Early Automobile Age (1900-1945)
- **Characteristics**: Low speeds, mixed-mode streets, small vehicles
- **Deposition rate**: Moderate but climbing
- **Typical artifacts**: Hand-painted signs, brick streets, streetcar tracks
- **Cultural context**: Transition from pedestrian-priority to vehicle-priority streets

### Interstate Highway Period (1945-1970)
- **Characteristics**: Highway construction boom, suburban expansion
- **Deposition rate**: Sharply increasing
- **Typical artifacts**: Interstate signage, wide arterials, early traffic signals
- **Cultural context**: "Golden Age" of automobility, pedestrian infrastructure decay

### Suburban Expansion Phase (1970-1990)
- **Characteristics**: Strip mall development, stroad proliferation
- **Deposition rate**: Peak levels
- **Typical artifacts**: Commercial signage density, wide parking lots, minimal sidewalks
- **Cultural context**: "Drive everywhere" culture, maximum car dependency

### SUV Dominance Period (1990-2010)
- **Characteristics**: Vehicle mass increase, tall hood heights
- **Deposition rate**: Sustained high levels
- **Typical artifacts**: SUV/pickup artifacts (5,000+ lbs), pedestrian detection systems (ineffective)
- **Cultural context**: Light truck classification loophole, safety externalization

### Late Automobile Age (2010-2030)
- **Characteristics**: Awareness of crisis, beginning of reform (selective)
- **Deposition rate**: Slight decline in European cities, continued high levels in US
- **Typical artifacts**: LED signals, high-visibility markings (often degraded), contradictory infrastructure
- **Cultural context**: Vision Zero rhetoric, incomplete implementation

## Artifact Typology

### Traffic Control Artifacts

**Type I: Regulatory Signs**
- Speed limit signs (R2-1)
- Stop signs (R1-1)
- Yield signs (R1-2)
- Condition: Usually compliant with MUTCD, but speeds set above safe thresholds

**Type II: Pedestrian Signals**
- Walk/Don't Walk indicators
- Countdown timers
- Condition: Often inadequate timing, degraded visibility

**Type III: Street Lighting**
- Cobra-head high-pressure sodium (legacy)
- LED conversion (contemporary)
- Spacing: 100-150 feet typical (inadequate for pedestrian detection at high speeds)

### Pavement Markings

**Type A: Crosswalk Markings**
- Ladder style (high visibility)
- Continental style (European)
- Zebra style (standard)
- Condition: Frequent degradation, 50-80% material loss common

**Type B: Lane Demarcation**
- Skip stripes (dashed)
- Solid edge lines
- Interpretation: Wider/more lanes = higher speeds

### Vehicular Artifacts

**Light Truck Category** (1990-present)
- Ford F-150, Chevrolet Silverado, etc.
- Mass: 5,000-7,000 lbs
- Hood height: 42-48 inches
- Interpretation: Mass and height incompatible with pedestrian safety

**Sedan Category** (all periods)
- Lower mass (3,000-4,000 lbs)
- Lower hood height (32-38 inches)
- Interpretation: Still dangerous at high speeds, but less fatal impact pattern

## For Museum/Exhibition Display

### Installation Concept

**Title**: "Excavating the Present: Archaeological Reports from the Automobile Age"

**Setup:**
- Gallery designed as archaeological dig site
- Individual site reports displayed on clipboards (field notes aesthetic)
- Artifact displays: actual street signs, crosswalk paint samples, vehicle components
- Timeline wall showing "periods" of automobile age
- Listening stations with archaeologist narration (past tense, reading reports)
- "Preservation recommendations" section (calls to action)

**Wall Text Example:**
```
EXCAVATING THE PRESENT (2024)
Archaeological site documentation

These reports document deaths from the Late Automobile Age using
archaeological field methodology. Everything is written in past tense,
as if excavating ruins 500 years from now.

Why? Archaeologists see clearly what contemporary societies normalize.
The future archaeologist cataloging "high-speed arterial deposition
events" reveals the absurdity of what we accept as inevitable.

This is not metaphor. This is method: using temporal displacement to
create critical distance from ongoing violence.
```

### Interactive Elements

**Archaeological Layers Display:**
- Stratified cross-section showing road layers
- Each layer labeled with period (1950s arterial widening, 1990s resurfacing, 2020 paint)
- Interpretation: Infrastructure as archaeological record

**Artifact Handling Station:**
- Visitors can examine actual street artifacts
- Traffic signs, crosswalk paint samples, signal housings
- Catalog cards in archaeological format

**Period Comparison Wall:**
- Side-by-side photos of same intersection across periods
- 1960: Two lanes, mixed mode, pedestrians everywhere
- 2024: Six lanes, no pedestrians visible (designed out)
- Archaeological interpretation labels

## For Academic Use

### Teaching Applications

**Courses this fits:**
- Archaeology/Anthropology (applied methods, contemporary archaeology)
- Science & Technology Studies (infrastructural violence)
- Cultural Geography (spatial justice, mobility)
- Creative Writing (documentary forms, genre experiments)
- Urban Studies (critical infrastructure analysis)
- Memorial Studies (documentation practices)

**Discussion Questions:**
1. Does past tense create critical distance or ethical distance (avoidance)?
2. What does archaeological framing reveal that conventional crash reports miss?
3. Are traffic deaths "archaeological" (inevitable, ancient) or political (preventable, recent)?
4. What will future archaeologists actually say about our infrastructure?
5. Is this method respectful to victims, or does it dehumanize?

### Research Applications

**Potential Papers:**
- "Temporal Displacement as Critical Method: Archaeological Reports from the Present"
- "The Archaeology of Ongoing Violence: Traffic Deaths as Deposition Events"
- "Infrastructure as Artifact: Material Culture Analysis of Dangerous Streets"
- "Stratigraphic Analysis of Automobile Age Infrastructure Layers"
- "Comparative Archaeology of US vs. European Pedestrian Infrastructure"

**Research Questions:**
- What patterns emerge when deaths are analyzed as archaeological events?
- Do "artifact assemblages" (infrastructure configurations) predict danger?
- Can stratigraphic analysis of road layers show infrastructure evolution?
- What does archaeological language reveal about normalization of violence?

## Ethical Considerations

### Temporal Displacement Ethics

**Why past tense?**
- Creates critical distance from normalized horror
- Archaeological voice is empathetic but detached
- Forces recognition: future generations will judge us harshly
- Makes visible what familiarity has hidden

**Potential problems:**
- Past tense might imply inevitability (it happened, can't change)
- Archaeological framing might suggest ancient/natural (it's neither)
- Detachment might seem disrespectful to victims
- Future perspective might avoid present responsibility

**Resolution:**
The "Preservation Recommendations" section breaks the archaeological frame with urgent present-tense demands: "This site requires IMMEDIATE modification."

The past tense describes the death; the present tense demands prevention.

### Is This Respectful to Victims?

**Arguments it is disrespectful:**
- Treats human deaths as "data points" for archaeological analysis
- Clinical detachment seems cold
- Focuses on infrastructure more than individual lives
- "Artifact assemblage" language dehumanizes

**Arguments it is respectful:**
- Archaeological documentation honors the dead (standard practice for millennia)
- Systematic analysis reveals patterns that prevent future deaths
- Infrastructure focus correctly identifies systemic causes (not victim behavior)
- Future perspective demands: these deaths must not be forgotten

**The test:** Would families of victims find this helpful or painful?
- If helpful: validates that death was infrastructure failure, not their loved one's fault
- If painful: seems to treat their tragedy as academic exercise
- Answer is probably: both, simultaneously

### Criticism This Will Receive

**"This is disrespectful to the dead"**
Response: Archaeologists document the dead with great care. This method applies that care to contemporary victims.

**"Past tense implies it's over—it's not"**
Response: Correct. The past tense is intentional dissonance. It forces recognition that future generations will excavate our streets and ask: "Why did they accept this?"

**"This aestheticizes violence"**
Response: No. This systematizes violence documentation. The clinical tone reveals scale.

**"You're playing with genre, not solving problems"**
Response: Genre experiments can reveal structure. Archaeological framing highlights that our infrastructure will be judged as barbaric ritual by future standards.

## Technical Implementation

### Site Number Generation

```python
def generate_site_number(self, feature: Dict) -> str:
    """Generate archaeological site number."""
    state = feature['properties'].get('state', 'XX')
    year = feature['properties'].get('year', 9999)
    # Unique ID from coordinates
    lat = feature['geometry']['coordinates'][1]
    lon = feature['geometry']['coordinates'][0]
    unique_id = f"{abs(int(lat * 10000))}{abs(int(lon * 10000))}"[-5:]

    return f"{state}-{year}-{unique_id}"
```

Example: `CA-2020-00342`

### Period Classification

```python
PERIOD_NAMES = {
    (1900, 1945): "Early Automobile Age",
    (1945, 1970): "Interstate Highway Period",
    (1970, 1990): "Suburban Expansion Phase",
    (1990, 2010): "SUV Dominance Period",
    (2010, 2030): "Late Automobile Age",
}

def classify_period(self, year: int) -> str:
    """Assign archaeological period."""
    for (start, end), name in self.PERIOD_NAMES.items():
        if start <= year < end:
            return name
    return "Unclassified Period"
```

### Artifact Cataloging

```python
def _catalog_artifacts(self, props: Dict) -> List[Dict]:
    """Generate artifact assemblage from infrastructure data."""
    artifacts = []

    # Traffic signals
    if props.get('has_signals'):
        artifacts.append({
            'type': 'Type II Pedestrian Signal',
            'material': 'LED elements, aluminum housing',
            'condition': 'Functional but timing inadequate',
            'notes': 'Standard 7-second cycle insufficient'
        })

    # Crosswalk markings
    if props.get('has_crosswalk'):
        artifacts.append({
            'type': 'Crosswalk Marking (Type A)',
            'material': 'Thermoplastic paint',
            'condition': 'Heavily abraded, 60% material loss',
            'notes': 'Wear pattern suggests inadequate maintenance'
        })

    # Vehicle fragments (from crash data)
    body_type = props.get('body_typ', 0)
    if body_type == 49:  # Pickup/SUV
        artifacts.append({
            'type': 'Vehicular Fragment (Light Truck)',
            'material': 'Steel/aluminum, 5,000+ lbs',
            'condition': 'Minor damage',
            'notes': 'Vehicle mass incompatible with pedestrian safety'
        })

    return artifacts
```

## Future Enhancements

Potential expansions:
- [ ] Photographic documentation (street-view images as "field photos")
- [ ] Stratigraphic analysis (road layers, infrastructure history)
- [ ] Comparative archaeology (US vs. European site reports)
- [ ] Material culture analysis (artifact types by region/period)
- [ ] GIS integration (site distribution maps)
- [ ] 3D site reconstruction (crash scene modeling)
- [ ] Audio version (archaeologist reading reports in past tense)
- [ ] Museum partnership (actual exhibition installation)

## Precedents & Influences

**Contemporary Archaeology:**
- Michael Shanks: Archaeology of the contemporary past
- Rodney Harrison: Heritage of the recent past
- Matt Edgeworth: Industrial archaeology

**Critical Infrastructure Studies:**
- Susan Leigh Star: Infrastructure invisibility
- Brian Larkin: Infrastructural politics
- Ashley Dawson: Extreme cities

**Documentary Forms:**
- W.G. Sebald: Descriptive accumulation, temporal displacement
- Annie Dillard: Observation as moral act
- John McPhee: Deep time in present landscape

**Forensic Arts:**
- Forensic Architecture: Spatial analysis as evidence
- Trevor Paglen: Documentation of the invisible
- Jenny Holzer: Text as witness

## License

MIT License

This is temporal displacement as critical method. Use it. Question it. Extend it.

If it makes one person see traffic deaths as future archaeological horror, the genre experiment worked.

## Contact

If you:
- Are a family member of a victim → We understand if this feels wrong; that response is valid
- Use this in a course → Tell us how students respond to past tense framing
- Exhibit this in a museum → Please share documentation
- Find it ethically troubling → You should; that's the dissonance working
- Want to extend the code → Pull requests welcome

---

**Final Note**: This README is written in present tense. The site reports are written in past tense. The dissonance between them is intentional.

We describe ongoing deaths in past tense to force recognition: future archaeologists will excavate our streets and call us barbarians.

They will be right.
