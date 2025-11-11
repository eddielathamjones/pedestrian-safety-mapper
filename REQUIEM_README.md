# Requiem for the Pedestrian
## An Algorithmic Memorial in Sound

### Ethical Warning

**This project transforms death data into music. It is intentionally uncomfortable.**

Each note you hear represents a human life lost to traffic violence. The composition maps victim age to pitch, time of day to rhythm, lighting conditions to timbre, and geography to stereo position.

**The central question**: Does making tragedy beautiful help us remember, or does it distance us from suffering?

The answer is probably "yes" to both. Sit with that discomfort.

---

## Concept

Traditional memorials abstract tragedy: the Vietnam Wall's 58,000 names become texture. "Requiem for the Pedestrian" forces individual awareness—each note is a person. Each cluster is a bad intersection. Each movement is a year of policy failure.

Unlike awareness campaigns that show crash statistics (numbers that numb), this memorial makes you **listen** to each death individually while experiencing the overwhelming scale collectively.

## Musical Mapping

Every data attribute becomes a musical parameter:

| Data Attribute | Musical Parameter | Meaning |
|----------------|------------------|---------|
| **Victim Age** | Pitch | Younger = higher notes (tragic), Older = lower notes |
| **Time of Day** | Rhythm/Timing | Rush hours = dense clusters, Night = sparse |
| **Lighting Conditions** | Timbre (Instrument) | Daylight = violin (bright), Dark+lit = viola, Dark/unlit = cello (somber) |
| **Speed Limit** | Velocity & Duration | High speed = loud, short notes (violent), Low speed = soft, sustained |
| **Geographic Location** | Stereo Pan | West coast = left speaker, East coast = right speaker |
| **Year** | Position in Time | Decades become movements in the symphony |

### Musical Theory

- **Mode**: Locrian scale (the darkest church mode, inherently unstable)
- **Tempo**: 60 BPM = one beat per second (heartbeat, or stopped heartbeat)
- **Instruments**: String quartet (GM MIDI: violin, viola, cello, bass)
- **Form**: Through-composed, no repeats (each death is unique)
- **Dissonance**: High dissonance = children, high-speed crashes, night

## Installation

```bash
# Install dependencies
pip install midiutil pandas

# Already installed from main requirements:
# pandas, requests
```

## Usage

### 1. Generate MIDI Composition

```bash
# From GeoJSON fatality data
python scripts/requiem_sonification.py \
    data/pedestrian_fatalities.geojson \
    --output requiem.mid \
    --tempo 60 \
    --analysis requiem_analysis.json
```

**Output:**
- `requiem.mid`: MIDI file (playable in any DAW or MIDI player)
- `requiem_analysis.json`: Composition statistics and analysis

### 2. View Web Player

```bash
python -m http.server 8000
# Open: http://localhost:8000/requiem_player.html
```

Features:
- Ethical warning screen (informed consent)
- Visualization of waveform
- Statistics dashboard
- Explanation of musical mapping
- Ethical reflection

### 3. Render High-Quality Audio

**Option A: Software Synth (Free)**

Use any MIDI player:
- **MuseScore** (free, open source): Import MIDI, export to MP3/WAV
- **GarageBand** (Mac): High-quality software instruments
- **FL Studio** (Windows): Professional DAW
- **TiMidity++** (Linux): Command-line MIDI to WAV

```bash
# Linux example with TiMidity++
timidity requiem.mid -Ow -o requiem.wav
```

**Option B: Live Performance**

The MIDI file can be used as a score for actual orchestra:
1. Import into notation software (MuseScore, Sibelius, Finale)
2. Print parts for each instrument
3. Perform live

**Recommendation**: Include spoken introduction about what each note represents.

## Example Output

```
Composing Requiem for the Pedestrian...
Reading fatality data...
Found 21 fatalities
Geographic bounds: -122.68 to -71.06
Composed 100 notes...
Composition complete: 21 notes
Duration: 1980 beats
          = 33.0 minutes at 60 BPM

Exporting MIDI to requiem.mid...
MIDI file exported: requiem.mid

======================================================================
COMPOSITION ANALYSIS
======================================================================
Total notes (fatalities): 21
Duration: 33.0 minutes
Years covered: 1987-2020
Average victim age: 52.3 years
Children (under 18): 1
Elderly (65+): 6
Dissonance index: 0.523
======================================================================

ETHICAL REFLECTION
======================================================================
You have created music from death data.
Each note represents a human life lost to traffic violence.

Is this:
  - A memorial that honors the dead?
  - Art that makes tragedy visible?
  - Exploitation of suffering for aesthetic purposes?

The answer is probably 'yes' to all three.
Sit with that discomfort.
======================================================================
```

## Dissonance Index

The composition calculates a "dissonance index" (0.0-1.0) based on:
- **Child deaths** (40% weight): Most tragic, highest dissonance
- **High-speed crashes** (30% weight): Violence increases dissonance
- **Night crashes** (30% weight): Dark, unseen suffering

Higher dissonance = more tragic composition = more uncomfortable to hear.

**This is intentional.**

## For Exhibition/Museum Display

### Installation Setup

**Equipment:**
- Surround sound system (5.1 or 7.1)
- Dark room
- Seating for contemplation
- Wall text with ethical warning
- Optional: Real-time visualization on large screen

**Format:**
- Loop the composition continuously
- No beginning/end (like traffic deaths—ongoing)
- Visitors can enter/leave at any point
- Duration: Full dataset = hours of music

**Wall Text Example:**
```
REQUIEM FOR THE PEDESTRIAN (2024)
Algorithmic composition

Each sound represents a human life lost to traffic violence
in the United States. Age determines pitch. Time determines
rhythm. Infrastructure determines timbre.

This memorial makes you listen to policy failure.

Warning: Contains audio representations of real deaths.
```

### Performance Notes

If performed live by orchestra:

1. **Introduction**: Conductor explains what each note represents
2. **Silence**: 30 seconds before first note (anticipation)
3. **Performance**: No applause between movements (years)
4. **Ending**: Fade to silence, hold for 1 minute
5. **Reflection**: Audience asked to remain seated briefly

**No bowing. No applause.** This is a funeral.

## Academic Uses

### For Teaching

**Courses this could fit:**
- Data Sonification & Visualization
- Ethics of Computational Art
- Memorial Studies
- Sound Art & Installation
- Critical Infrastructure Studies
- Death & Dying in Contemporary Culture

**Discussion Questions:**
1. Is it ethical to make art from death data?
2. Does beauty help us remember or distance us from suffering?
3. How does sonification differ from visualization in emotional impact?
4. What is the responsibility of the artist to the dead?
5. Can this change policy, or is it just aesthetic experience?

### For Research

**Potential Papers:**
- "Sonification as Memorial: Making Policy Failure Audible"
- "Dissonance as Tragedy: Mapping Ethics to Aesthetics"
- "The Problem of Beautiful Death: Algorithmic Memorials"
- "Listening to Infrastructure Violence"

**Comparative Analysis:**
- Vietnam Veterans Memorial (visual abstraction)
- AIDS Memorial Quilt (tactile, personal)
- 9/11 Memorial (architectural void)
- Requiem for the Pedestrian (sonic, data-driven)

## Ethical Considerations

### What Makes This Different from Exploitation?

**Exploitation would:**
- Use deaths for entertainment without context
- Prioritize aesthetic beauty over memorial function
- Hide the data source
- Avoid uncomfortable questions

**This memorial:**
- Requires informed consent (warning screen)
- Explicitly names discomfort as intentional
- Centers the victims (each note = one person)
- Asks ethical questions rather than answering them
- Makes data source transparent
- Doesn't profit from suffering (open source)

### Criticism This Will Receive

**"This is disrespectful to the dead"**
Response: Is it more disrespectful than the policy decisions that killed them? This memorial names the problem.

**"You're profiting from tragedy"**
Response: This is open source. No profit. The goal is awareness, not monetization.

**"Making it beautiful trivializes suffering"**
Response: Maybe. That's the point of the question. The dissonance is intentional.

**"This is trauma porn"**
Response: It could be. The warning screen gives informed consent. No one is forced to listen.

### What About Families of Victims?

This is the hardest question.

**If you're a family member and you hear this:**
- You have every right to be angry
- You have every right to find it beautiful
- You have every right to find it inappropriate
- All of these reactions are valid

The composer (the algorithm) doesn't know your loved one's name or story. It only knows data. That anonymity is both the problem (dehumanization) and the solution (privacy).

If this causes pain, I'm sorry. The intention is memorial, not exploitation, but intention doesn't erase harm.

## Future Enhancements

Potential expansions:
- [ ] Real-time composition (new data → new notes automatically)
- [ ] Multiple movements: one per US state
- [ ] Victim names spoken between notes (with family permission)
- [ ] Interactive version: listeners choose which attributes to sonify
- [ ] Comparison version: US vs. European data (silence = success)
- [ ] Generative AI extension: machine learning creates variations
- [ ] Physical installation: speakers at actual crash sites

## Precedent & Influences

**Data Sonification:**
- Ryoji Ikeda: Data-driven sound art
- Mark Fell: Algorithmic composition
- Carsten Nicolai (Alva Noto): Data aesthetics

**Memorial Art:**
- Maya Lin: Vietnam Veterans Memorial (abstraction)
- Jenny Holzer: Truisms (text as memorial)
- Janet Cardiff: Sound walks (sonic memorials)

**Ethical Data Art:**
- Josh Begley: Drone strikes as metadata
- Jer Thorp: Data as human stories
- Giorgia Lupi: Data humanism

**Generative/Algorithmic:**
- Brian Eno: Generative music
- John Cage: Chance operations
- Steve Reich: Phase music (repetition as meaning)

## Technical Notes

### MIDI Implementation

- **Channels**: 4 channels (daylight, dark+lit, dark/unlit, unknown)
- **Instruments**: GM MIDI standard (40=Violin, 42=Viola, 43=Cello, 32=Acoustic Bass)
- **Range**: MIDI pitches 36-84 (C2 to C6)
- **Quantization**: Notes snapped to Locrian scale
- **Pan**: MIDI CC 10 (not implemented in basic version, for advanced rendering)

### Extending the Code

Add custom mappings:

```python
def custom_mapping(self, crash_data):
    """Your custom attribute → music parameter."""
    # Example: Vehicle type → percussion sound
    if crash_data.get('body_typ') == 49:  # SUV
        return PercussionNote(drum=35)  # Bass drum (violent)
    # Add more mappings...
```

### Performance Optimization

For large datasets (thousands of crashes):
- Process in chunks (1000 notes at a time)
- Use multi-threading for independent calculations
- Pre-calculate all parameters before MIDI generation

## License

MIT License

This is memorial art in the public domain. Use it. Remix it. Perform it. Question it.

The dead deserve to be remembered. The living deserve to hear policy failure made audible.

## Contact & Contributions

If you:
- Are a family member of a victim and want this taken down → Contact immediately
- Want to perform this with a live orchestra → Please do (share photos)
- Have ethical critiques → Open an issue (genuine discussion welcome)
- Want to extend the codebase → Pull requests welcome
- Teach this in a course → Let us know (we'd love to hear)
- Exhibit this in a gallery → Please credit properly

---

**Final Note**: This README is as uncomfortable as the project itself. That's intentional. Pedestrian deaths are policy choices. This memorial makes those choices audible.

If you listen to this and feel nothing, that's the real problem.
