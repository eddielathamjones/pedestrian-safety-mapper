"""
Requiem for the Pedestrian - Algorithmic Death Music

Transforms pedestrian fatality data into musical composition where each
death becomes a note in an ongoing requiem. Raises questions about the
ethics of making art from tragedy.

Musical Mapping:
- Age → Pitch: Younger = higher notes, older = lower notes
- Time of Day → Rhythm: Rush hours = dense clusters, night = sparse
- Lighting → Timbre: Daylight = bright (violin), dark = somber (cello/bass)
- Speed Limit → Tempo: Higher speed = faster, more violent passages
- Location → Stereo Panning: Geographic position mapped to L/R
- Year → Movement: Decades become movements in symphony

Ethical Statement:
This project makes beauty from death data. It is intentionally uncomfortable.
The question is not "should we do this?" but "does making it beautiful help
us remember, or does it distance us from suffering?"
"""

import json
import math
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime
import os

try:
    from midiutil import MIDIFile
    HAS_MIDI = True
except ImportError:
    print("Warning: midiutil not installed. Run: pip install midiutil")
    HAS_MIDI = False


@dataclass
class MusicalNote:
    """Represents a single note in the requiem."""
    pitch: int  # MIDI pitch (0-127)
    start_time: float  # In beats
    duration: float  # In beats
    velocity: int  # Volume (0-127)
    channel: int  # MIDI channel (0-15), used for different instruments
    pan: float  # Stereo position (-1.0 to 1.0)

    # Metadata
    year: int
    age: int
    hour: int
    lighting: int
    speed: int
    location: Tuple[float, float]


class RequiemComposer:
    """Composes requiem from pedestrian fatality data."""

    # Musical scales and modes
    # Using Locrian mode (darkest) and Phrygian for somber quality
    LOCRIAN_SCALE = [0, 1, 3, 5, 6, 8, 10]  # Half-diminished sound
    PHRYGIAN_SCALE = [0, 1, 3, 5, 7, 8, 10]  # Spanish/Middle Eastern quality

    # Instrument channels (GM MIDI)
    INSTRUMENTS = {
        'daylight': (0, 40),      # Violin (bright)
        'dark_lit': (1, 42),      # Viola (medium)
        'dark_unlit': (2, 43),    # Cello (dark)
        'unknown': (3, 32),       # Acoustic Bass (very dark)
        'percussion': (9, 0),     # Percussion channel for impacts
    }

    def __init__(self, base_tempo: int = 60):
        """
        Initialize composer.

        Args:
            base_tempo: Base tempo in BPM (default 60 = one beat per second)
        """
        self.base_tempo = base_tempo
        self.notes: List[MusicalNote] = []

    def age_to_pitch(self, age: int, octave_range: int = 4) -> int:
        """
        Convert age to MIDI pitch.

        Younger victims = higher notes (more tragic)
        Older victims = lower notes (expected end of life)

        Args:
            age: Age of victim (0-120)
            octave_range: Number of octaves to span

        Returns:
            MIDI pitch (0-127)
        """
        if age < 0 or age > 120:
            age = 50  # Default to middle

        # Map age 0-100 to pitch range
        # Child (0-10): Very high (painful to hear)
        # Young adult (20-40): High-medium (tragedy of potential)
        # Middle age (40-60): Medium (established life cut short)
        # Elderly (70+): Low (life lived)

        # Invert: younger = higher
        normalized_age = max(0, min(100, age)) / 100.0
        inverted = 1.0 - normalized_age

        # Map to MIDI range C2 (36) to C6 (84)
        min_pitch = 36
        max_pitch = 84
        pitch_range = max_pitch - min_pitch

        raw_pitch = min_pitch + (inverted * pitch_range)

        # Quantize to scale (Locrian for dissonance)
        scale = self.LOCRIAN_SCALE
        octave = int(raw_pitch / 12)
        pitch_class = int(raw_pitch % 12)

        # Find nearest scale degree
        nearest = min(scale, key=lambda x: abs(x - pitch_class))

        return octave * 12 + nearest

    def hour_to_start_time(self, hour: int, year: int, base_year: int = 1975) -> float:
        """
        Convert time of day and year to start time in beats.

        Rush hours (7-9am, 5-7pm) create dense clusters.
        Night hours (midnight-6am) are sparse.

        Years are stretched across the composition.

        Args:
            hour: Hour of day (0-23)
            year: Year of incident
            base_year: Starting year for composition

        Returns:
            Start time in beats
        """
        if hour < 0:
            hour = 12  # Default to noon

        # Map year to large-scale structure (each year = 60 beats = 1 minute at 60 BPM)
        year_offset = (year - base_year) * 60

        # Map hour within the year's "day" (0-23 hours = 0-24 beats)
        hour_offset = (hour / 24.0) * 24

        return year_offset + hour_offset

    def lighting_to_channel(self, lighting: int) -> Tuple[int, int]:
        """
        Convert lighting condition to MIDI channel and program (instrument).

        Args:
            lighting: FARS lighting code (1=day, 2=lit, 3=unlit)

        Returns:
            (channel, program) tuple
        """
        if lighting == 1:
            return self.INSTRUMENTS['daylight']
        elif lighting == 2:
            return self.INSTRUMENTS['dark_lit']
        elif lighting == 3:
            return self.INSTRUMENTS['dark_unlit']
        else:
            return self.INSTRUMENTS['unknown']

    def speed_to_velocity(self, speed: int, func_sys: int) -> int:
        """
        Convert speed limit to note velocity (volume).

        Higher speeds = louder, more violent attacks.

        Args:
            speed: Speed limit in mph
            func_sys: Road functional class

        Returns:
            MIDI velocity (0-127)
        """
        # High-speed roads = loud (violent)
        if speed >= 45:
            base_velocity = 100
        elif speed >= 35:
            base_velocity = 80
        elif speed >= 25:
            base_velocity = 60
        else:
            base_velocity = 40

        # Add randomness for humanity (-10 to +10)
        import random
        variation = random.randint(-10, 10)

        return max(20, min(127, base_velocity + variation))

    def location_to_pan(self, lon: float, lat: float,
                       lon_min: float = -125, lon_max: float = -65) -> float:
        """
        Convert geographic location to stereo pan position.

        West coast = left, East coast = right.

        Args:
            lon: Longitude
            lat: Latitude
            lon_min: Westernmost longitude (default: West Coast)
            lon_max: Easternmost longitude (default: East Coast)

        Returns:
            Pan position (-1.0 = left, 1.0 = right)
        """
        # Normalize longitude to -1.0 to 1.0
        normalized = (lon - lon_min) / (lon_max - lon_min)
        return (normalized * 2.0) - 1.0

    def speed_to_duration(self, speed: int) -> float:
        """
        Convert speed to note duration.

        High speed = short, violent notes.
        Low speed = longer, sustained notes.

        Args:
            speed: Speed limit in mph

        Returns:
            Duration in beats
        """
        if speed >= 45:
            return 0.25  # Sixteenth note (violent)
        elif speed >= 35:
            return 0.5   # Eighth note
        elif speed >= 25:
            return 1.0   # Quarter note
        else:
            return 2.0   # Half note (lingering sadness)

    def compose_from_geojson(self, geojson_path: str):
        """
        Compose requiem from GeoJSON fatality data.

        Args:
            geojson_path: Path to GeoJSON file with fatality data
        """
        print("Composing Requiem for the Pedestrian...")
        print("Reading fatality data...")

        with open(geojson_path, 'r') as f:
            data = json.load(f)

        features = data.get('features', [])
        print(f"Found {len(features)} fatalities")

        # Find geographic bounds for panning
        lons = [f['geometry']['coordinates'][0] for f in features
                if f['geometry']['type'] == 'Point']
        lats = [f['geometry']['coordinates'][1] for f in features
                if f['geometry']['type'] == 'Point']

        if not lons:
            print("No point data found")
            return

        lon_min, lon_max = min(lons), max(lons)
        lat_min, lat_max = min(lats), max(lats)

        print(f"Geographic bounds: {lon_min:.2f} to {lon_max:.2f}")

        # Compose notes
        for i, feature in enumerate(features):
            if feature['geometry']['type'] != 'Point':
                continue

            props = feature['properties']
            coords = feature['geometry']['coordinates']

            # Extract attributes
            age = props.get('age', 50)
            hour = props.get('hour', 12)
            year = props.get('year', 2000)
            lighting = props.get('lighting', -1)
            speed = props.get('speed_limit', 35) if 'speed_limit' in props else 35
            func_sys = props.get('func_sys', 3)

            # Convert to musical parameters
            pitch = self.age_to_pitch(age)
            start_time = self.hour_to_start_time(hour, year)
            channel, program = self.lighting_to_channel(lighting)
            velocity = self.speed_to_velocity(speed, func_sys)
            duration = self.speed_to_duration(speed)
            pan = self.location_to_pan(coords[0], coords[1], lon_min, lon_max)

            note = MusicalNote(
                pitch=pitch,
                start_time=start_time,
                duration=duration,
                velocity=velocity,
                channel=channel,
                pan=pan,
                year=year,
                age=age,
                hour=hour,
                lighting=lighting,
                speed=speed,
                location=(coords[0], coords[1])
            )

            self.notes.append(note)

            if (i + 1) % 100 == 0:
                print(f"Composed {i + 1} notes...")

        print(f"\nComposition complete: {len(self.notes)} notes")
        print(f"Duration: {max(n.start_time + n.duration for n in self.notes):.0f} beats")
        print(f"          = {max(n.start_time + n.duration for n in self.notes) / 60:.1f} minutes at 60 BPM")

    def export_midi(self, output_path: str):
        """
        Export composition as MIDI file.

        Args:
            output_path: Path to output MIDI file
        """
        if not HAS_MIDI:
            print("ERROR: midiutil not installed. Cannot export MIDI.")
            print("Install with: pip install midiutil")
            return

        if not self.notes:
            print("No notes to export")
            return

        print(f"\nExporting MIDI to {output_path}...")

        # Create MIDI file with multiple tracks
        num_tracks = 4
        midi = MIDIFile(num_tracks)

        # Set tempo
        for track in range(num_tracks):
            midi.addTempo(track, 0, self.base_tempo)

        # Set instruments
        for name, (channel, program) in self.INSTRUMENTS.items():
            if channel < 9:  # Skip percussion channel
                midi.addProgramChange(channel, channel, 0, program)

        # Add notes
        for note in self.notes:
            track = note.channel % num_tracks
            midi.addNote(
                track=track,
                channel=note.channel,
                pitch=note.pitch,
                time=note.start_time,
                duration=note.duration,
                volume=note.velocity
            )

        # Write file
        with open(output_path, 'wb') as f:
            midi.writeFile(f)

        print(f"MIDI file exported: {output_path}")

    def export_analysis(self, output_path: str):
        """
        Export analysis of the composition.

        Args:
            output_path: Path to output JSON file
        """
        if not self.notes:
            print("No notes to analyze")
            return

        # Analyze composition
        years = [n.year for n in self.notes]
        ages = [n.age for n in self.notes if n.age > 0]
        hours = [n.hour for n in self.notes if n.hour >= 0]
        pitches = [n.pitch for n in self.notes]
        velocities = [n.velocity for n in self.notes]

        analysis = {
            'composition_stats': {
                'total_notes': len(self.notes),
                'duration_beats': max(n.start_time + n.duration for n in self.notes),
                'duration_minutes': max(n.start_time + n.duration for n in self.notes) / 60,
                'tempo_bpm': self.base_tempo,
            },
            'temporal': {
                'year_range': [min(years), max(years)] if years else [0, 0],
                'years_covered': max(years) - min(years) + 1 if years else 0,
                'avg_hour': sum(hours) / len(hours) if hours else 0,
                'rush_hour_count': sum(1 for h in hours if 7 <= h <= 9 or 17 <= h <= 19),
                'night_count': sum(1 for h in hours if h < 6 or h >= 22),
            },
            'demographic': {
                'avg_age': sum(ages) / len(ages) if ages else 0,
                'child_count': sum(1 for a in ages if a < 18),
                'elderly_count': sum(1 for a in ages if a >= 65),
            },
            'musical': {
                'pitch_range': [min(pitches), max(pitches)] if pitches else [0, 0],
                'avg_pitch': sum(pitches) / len(pitches) if pitches else 0,
                'avg_velocity': sum(velocities) / len(velocities) if velocities else 0,
                'dissonance_index': self._calculate_dissonance(),
            },
            'ethical_statement': (
                "This composition transforms human tragedy into musical form. "
                "Each note represents a life lost to traffic violence. "
                "The beauty of the music is intentional and uncomfortable. "
                "Does making it beautiful help us remember, or distance us from suffering?"
            )
        }

        with open(output_path, 'w') as f:
            json.dump(analysis, f, indent=2)

        print(f"\nAnalysis exported: {output_path}")
        print("\n" + "="*70)
        print("COMPOSITION ANALYSIS")
        print("="*70)
        print(f"Total notes (fatalities): {analysis['composition_stats']['total_notes']}")
        print(f"Duration: {analysis['composition_stats']['duration_minutes']:.1f} minutes")
        print(f"Years covered: {analysis['temporal']['year_range'][0]}-{analysis['temporal']['year_range'][1]}")
        print(f"Average victim age: {analysis['demographic']['avg_age']:.1f} years")
        print(f"Children (under 18): {analysis['demographic']['child_count']}")
        print(f"Elderly (65+): {analysis['demographic']['elderly_count']}")
        print(f"Dissonance index: {analysis['musical']['dissonance_index']:.3f}")
        print("="*70)

    def _calculate_dissonance(self) -> float:
        """
        Calculate musical dissonance of the composition.

        Higher dissonance = more tragic (children, high speeds)

        Returns:
            Dissonance index (0.0-1.0)
        """
        if not self.notes:
            return 0.0

        # Factors that increase dissonance
        child_notes = sum(1 for n in self.notes if n.age < 18)
        high_speed_notes = sum(1 for n in self.notes if n.speed >= 45)
        night_notes = sum(1 for n in self.notes if n.hour < 6 or n.hour >= 22)

        dissonance = (
            (child_notes / len(self.notes)) * 0.4 +
            (high_speed_notes / len(self.notes)) * 0.3 +
            (night_notes / len(self.notes)) * 0.3
        )

        return min(1.0, dissonance)


def main():
    """Command-line interface for Requiem composition."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Requiem for the Pedestrian - Algorithmic Death Music',
        epilog='Ethical Warning: This creates art from death data. Proceed thoughtfully.'
    )
    parser.add_argument('input', help='Input GeoJSON file with fatality data')
    parser.add_argument('--output', default='requiem.mid', help='Output MIDI file')
    parser.add_argument('--tempo', type=int, default=60, help='Tempo in BPM (default: 60)')
    parser.add_argument('--analysis', help='Export analysis JSON file')

    args = parser.parse_args()

    # Compose
    composer = RequiemComposer(base_tempo=args.tempo)
    composer.compose_from_geojson(args.input)

    # Export MIDI
    composer.export_midi(args.output)

    # Export analysis
    if args.analysis:
        composer.export_analysis(args.analysis)
    else:
        # Default analysis file
        analysis_path = args.output.replace('.mid', '_analysis.json')
        composer.export_analysis(analysis_path)

    print("\n" + "="*70)
    print("ETHICAL REFLECTION")
    print("="*70)
    print("You have created music from death data.")
    print("Each note represents a human life lost to traffic violence.")
    print("")
    print("Is this:")
    print("  - A memorial that honors the dead?")
    print("  - Art that makes tragedy visible?")
    print("  - Exploitation of suffering for aesthetic purposes?")
    print("")
    print("The answer is probably 'yes' to all three.")
    print("Sit with that discomfort.")
    print("="*70)


if __name__ == '__main__':
    main()
