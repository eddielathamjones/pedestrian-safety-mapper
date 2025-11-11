"""
Forensic Archaeology of the Present
Excavating Invisible Graveyards

Applies rigorous archaeological field methods to pedestrian death sites,
treating car-centric infrastructure as if it were ancient ruins being
excavated by future archaeologists.

Concept:
- Each death site = archaeological dig site
- Document using standard archaeological methods
- Write in past tense ("the inhabitants constructed...")
- Catalog artifacts (street signs, paint, signals)
- Create stratigraphic analysis of road layers
- Context analysis of surrounding structures

This defamiliarizes the present by treating it as the past.
Makes our car culture strange and visible.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict


@dataclass
class ArchaeologicalSite:
    """Represents a pedestrian death site as an archaeological dig."""

    # Site identification (following archaeological conventions)
    site_number: str  # e.g., "CAL-2020-00342"
    site_name: str

    # Location
    latitude: float
    longitude: float
    grid_square: str  # 10m x 10m excavation grid

    # Temporal data
    date_of_deposition: str  # Death date (in archaeological terms)
    excavation_date: str  # When site was documented
    period: str  # "Late Automobile Age" (1980-2020)

    # Context
    context_type: str  # "High-speed arterial", "ritual vehicular corridor"
    stratigraphic_layer: str
    associated_structures: List[str]

    # Artifacts
    artifacts: List[Dict]  # Catalogued street infrastructure

    # Human remains (victim data)
    individual_age: Optional[int]
    individual_sex: Optional[str]

    # Environmental conditions at time of deposition
    lighting_condition: str
    weather_condition: str

    # Interpretation
    interpretation: str
    significance: str

    # Condition
    site_condition: str  # "Disturbed", "Intact", "Destroyed"
    preservation_quality: str


class ArchaeologicalReport:
    """Generates formal archaeological site reports."""

    PERIOD_NAMES = {
        (1900, 1945): "Early Automobile Age",
        (1945, 1970): "Interstate Highway Period",
        (1970, 1990): "Suburban Expansion Phase",
        (1990, 2010): "SUV Dominance Period",
        (2010, 2030): "Late Automobile Age",
    }

    ARTIFACT_TYPES = {
        'crosswalk_paint': "Type A Pedestrian Crossing Marker",
        'street_sign': "Type B Traffic Control Artifact",
        'traffic_signal': "Type C Ritual Control Device",
        'curb': "Type D Boundary Marker",
        'street_lamp': "Type E Illumination Structure",
        'storm_drain': "Type F Drainage Feature",
    }

    def __init__(self):
        self.sites: List[ArchaeologicalSite] = []

    def create_site_from_crash(self, crash_data: Dict, site_number: str) -> ArchaeologicalSite:
        """
        Convert a crash record into an archaeological site.

        Args:
            crash_data: GeoJSON feature with crash data
            site_number: Unique site identifier
        """
        props = crash_data['properties']
        coords = crash_data['geometry']['coordinates']

        # Determine period
        year = props.get('year', 2000)
        period = self._get_period(year)

        # Create grid reference
        grid = self._lat_lon_to_grid(coords[1], coords[0])

        # Interpret context
        func_sys = props.get('func_sys', 6)
        context = self._interpret_context(func_sys, props)

        # Catalog artifacts
        artifacts = self._catalog_artifacts(props)

        # Individual data (archaeological euphemism for victim)
        age = props.get('age', -1)
        sex_code = props.get('sex', 0)
        sex = {1: "Male", 2: "Female"}.get(sex_code, "Unknown")

        # Environmental conditions
        lighting = self._interpret_lighting(props.get('lighting', -1))
        weather = self._interpret_weather(props.get('weather', -1))

        # Site condition
        # If it's been years, the site is likely "disturbed" by new construction
        years_since = datetime.now().year - year
        condition = "Disturbed" if years_since > 5 else "Intact"

        # Generate interpretation
        interpretation = self._generate_interpretation(props, context)

        # Create site name
        street = props.get('name', 'Unnamed location')
        site_name = f"{street}, Grid {grid}"

        site = ArchaeologicalSite(
            site_number=site_number,
            site_name=site_name,
            latitude=coords[1],
            longitude=coords[0],
            grid_square=grid,
            date_of_deposition=f"{year}-{props.get('month', 1):02d}-01",  # Approximate
            excavation_date=datetime.now().strftime("%Y-%m-%d"),
            period=period,
            context_type=context,
            stratigraphic_layer="Surface (0-10cm)",
            associated_structures=self._identify_structures(props),
            artifacts=artifacts,
            individual_age=age if age > 0 else None,
            individual_sex=sex if sex != "Unknown" else None,
            lighting_condition=lighting,
            weather_condition=weather,
            interpretation=interpretation,
            significance=self._assess_significance(props),
            site_condition=condition,
            preservation_quality="Fair to Poor"
        )

        self.sites.append(site)
        return site

    def _get_period(self, year: int) -> str:
        """Assign archaeological period."""
        for (start, end), period_name in self.PERIOD_NAMES.items():
            if start <= year < end:
                return period_name
        return "Unknown Period"

    def _lat_lon_to_grid(self, lat: float, lon: float) -> str:
        """
        Create 10m x 10m grid reference (archaeological standard).

        Format: "N37E122-0042" (like a site number)
        """
        lat_grid = int(lat)
        lon_grid = int(abs(lon))
        subgrid = abs(int((lat % 1) * 100))

        return f"N{lat_grid}E{lon_grid}-{subgrid:04d}"

    def _interpret_context(self, func_sys: int, props: Dict) -> str:
        """Interpret site context in archaeological language."""
        contexts = {
            1: "Limited-access ritual vehicular corridor",
            2: "High-speed principal arterial complex",
            3: "Secondary arterial transportation feature",
            4: "Collector distribution network",
            6: "Local residential circulation space",
        }

        context = contexts.get(func_sys, "Unclassified transportation feature")

        # Add modifiers
        if props.get('is_stroad'):
            context += " (hybrid commercial-residential configuration)"

        return context

    def _catalog_artifacts(self, props: Dict) -> List[Dict]:
        """
        Catalog infrastructure artifacts in archaeological style.

        Each artifact gets:
        - Type classification
        - Condition assessment
        - Material analysis
        - Functional interpretation
        """
        artifacts = []

        # Crosswalk paint (if present)
        if props.get('has_crosswalk', False):
            artifacts.append({
                'type': self.ARTIFACT_TYPES['crosswalk_paint'],
                'catalog_number': 'CW-001',
                'material': 'Thermoplastic road marking compound',
                'condition': 'Heavily weathered, 60% abraded',
                'dimensions': '12 ft width, standard spacing',
                'function': 'Pedestrian crossing demarcation',
                'notes': 'Shows evidence of rapid abandonment and lack of maintenance'
            })

        # Traffic signals
        artifacts.append({
            'type': self.ARTIFACT_TYPES['traffic_signal'],
            'catalog_number': 'TS-001',
            'material': 'Metal housing, LED illumination elements',
            'condition': 'Functional',
            'function': 'Ritual traffic control device, vehicular priority',
            'notes': 'No pedestrian signal phase detected at time of deposition'
        })

        # Street lighting
        lighting_quality = props.get('lighting', 'unknown')
        if lighting_quality == 'none':
            artifacts.append({
                'type': self.ARTIFACT_TYPES['street_lamp'],
                'catalog_number': 'SL-001',
                'material': 'None present',
                'condition': 'Absent',
                'function': 'Illumination (absent from site)',
                'notes': 'Notable absence of illumination infrastructure. Possible evidence of resource allocation priorities.'
            })

        # Sidewalk (if present)
        if props.get('has_sidewalk'):
            artifacts.append({
                'type': 'Type G Pedestrian Infrastructure',
                'catalog_number': 'PW-001',
                'material': 'Concrete, poured in place',
                'condition': 'Fair',
                'dimensions': f"{props.get('sidewalk_width', 5)} ft width",
                'function': 'Separated pedestrian pathway',
                'notes': 'Indicates some concern for pedestrian movement, though inadequate to prevent deposition'
            })

        return artifacts

    def _identify_structures(self, props: Dict) -> List[str]:
        """Identify associated structures (buildings, features)."""
        structures = []

        # Infer from context
        if props.get('func_sys') == 2:
            structures.extend([
                "Commercial structure (Type C-1)",
                "Parking infrastructure (extensive)",
                "Signage complex (advertising function)"
            ])
        elif props.get('func_sys') == 6:
            structures.extend([
                "Residential structures (Type R-1)",
                "Street trees (limited)",
                "Domestic infrastructure"
            ])

        return structures

    def _interpret_lighting(self, code: int) -> str:
        """Interpret lighting in archaeological language."""
        conditions = {
            1: "Full daylight illumination",
            2: "Dark with artificial illumination present",
            3: "Dark with no artificial illumination (abandoned infrastructure)",
            -1: "Unknown illumination conditions"
        }
        return conditions.get(code, "Unknown")

    def _interpret_weather(self, code: int) -> str:
        """Interpret weather conditions."""
        weather = {
            1: "Clear atmospheric conditions",
            2: "Rain precipitation",
            3: "Snow/sleet precipitation",
            4: "Fog/reduced visibility",
            -1: "Unknown atmospheric conditions"
        }
        return weather.get(code, "Unknown")

    def _generate_interpretation(self, props: Dict, context: str) -> str:
        """Generate archaeological interpretation of the site."""
        interpretation_parts = []

        interpretation_parts.append(
            f"At this site, the inhabitants constructed a {context.lower()}. "
        )

        speed = props.get('speed_limit', 35)
        interpretation_parts.append(
            f"Design speed of {speed} mph indicates prioritization of vehicular throughput over human safety. "
        )

        if props.get('lighting') == 3:
            interpretation_parts.append(
                "The absence of illumination infrastructure suggests either resource scarcity "
                "or systematic deprioritization of pedestrian safety. "
            )

        if not props.get('has_sidewalk'):
            interpretation_parts.append(
                "Complete absence of separated pedestrian infrastructure indicates pedestrian "
                "movement was not accommodated in the site's original construction. "
            )

        if props.get('is_stroad'):
            interpretation_parts.append(
                "The combination of high-speed design and adjacent commercial/residential "
                "functions represents a hybrid form common in Late Automobile Age settlements. "
                "This design pattern shows evidence of fundamental misunderstanding of spatial "
                "requirements for different movement modes. "
            )

        interpretation_parts.append(
            "The deposition event (fatal pedestrian collision) was not an accident but rather "
            "a predictable outcome of the site's configuration. The infrastructure itself "
            "functioned as designed."
        )

        return ''.join(interpretation_parts)

    def _assess_significance(self, props: Dict) -> str:
        """Assess archaeological significance."""
        significance_parts = []

        if props.get('is_stroad'):
            significance_parts.append(
                "This site exemplifies the 'stroad' typology characteristic of Late "
                "Automobile Age American settlements. "
            )

        if props.get('lighting') == 3:
            significance_parts.append(
                "The site contributes to our understanding of infrastructure abandonment "
                "patterns in car-dependent societies. "
            )

        significance_parts.append(
            "As one of approximately 7,000 similar sites deposited annually during this "
            "period, this location documents the systematic nature of traffic violence "
            "in early 21st century American culture. "
        )

        significance_parts.append(
            "Future archaeologists will find this site's configuration inexplicable, "
            "much as we find human sacrifice sites from earlier civilizations puzzling."
        )

        return ''.join(significance_parts)

    def generate_site_report(self, site: ArchaeologicalSite, filename: str):
        """Generate formal archaeological site report (past tense)."""

        report = []
        report.append("=" * 80)
        report.append("ARCHAEOLOGICAL SITE RECORD")
        report.append("=" * 80)
        report.append("")

        report.append(f"SITE NUMBER: {site.site_number}")
        report.append(f"SITE NAME: {site.site_name}")
        report.append(f"GRID REFERENCE: {site.grid_square}")
        report.append(f"COORDINATES: {site.latitude:.6f}N, {site.longitude:.6f}W")
        report.append("")

        report.append(f"DATE OF DEPOSITION: {site.date_of_deposition}")
        report.append(f"EXCAVATION DATE: {site.excavation_date}")
        report.append(f"PERIOD: {site.period}")
        report.append("")

        report.append("=" * 80)
        report.append("SITE CONTEXT")
        report.append("=" * 80)
        report.append("")

        report.append(f"CONTEXT TYPE: {site.context_type}")
        report.append(f"STRATIGRAPHIC LAYER: {site.stratigraphic_layer}")
        report.append("")

        report.append("ASSOCIATED STRUCTURES:")
        for structure in site.associated_structures:
            report.append(f"  - {structure}")
        report.append("")

        report.append("=" * 80)
        report.append("ARTIFACT ASSEMBLAGE")
        report.append("=" * 80)
        report.append("")

        for i, artifact in enumerate(site.artifacts, 1):
            report.append(f"ARTIFACT {i}: {artifact['type']}")
            report.append(f"  Catalog Number: {artifact['catalog_number']}")
            report.append(f"  Material: {artifact['material']}")
            report.append(f"  Condition: {artifact['condition']}")
            report.append(f"  Function: {artifact['function']}")
            if 'dimensions' in artifact:
                report.append(f"  Dimensions: {artifact['dimensions']}")
            report.append(f"  Notes: {artifact['notes']}")
            report.append("")

        report.append("=" * 80)
        report.append("HUMAN REMAINS")
        report.append("=" * 80)
        report.append("")

        if site.individual_age:
            report.append(f"INDIVIDUAL AGE: Approximately {site.individual_age} years")
        if site.individual_sex:
            report.append(f"INDIVIDUAL SEX: {site.individual_sex}")
        report.append("")

        report.append(f"DEPOSITION CONDITIONS:")
        report.append(f"  Lighting: {site.lighting_condition}")
        report.append(f"  Weather: {site.weather_condition}")
        report.append("")

        report.append("=" * 80)
        report.append("INTERPRETATION")
        report.append("=" * 80)
        report.append("")
        report.append(site.interpretation)
        report.append("")

        report.append("=" * 80)
        report.append("SIGNIFICANCE")
        report.append("=" * 80)
        report.append("")
        report.append(site.significance)
        report.append("")

        report.append("=" * 80)
        report.append("SITE CONDITION")
        report.append("=" * 80)
        report.append("")
        report.append(f"CONDITION: {site.site_condition}")
        report.append(f"PRESERVATION QUALITY: {site.preservation_quality}")
        report.append("")

        report.append("=" * 80)
        report.append("RECOMMENDATIONS")
        report.append("=" * 80)
        report.append("")
        report.append("This site should be preserved as a memorial to traffic violence in the")
        report.append("Late Automobile Age. Infrastructure modifications are recommended to")
        report.append("prevent future depositions at this location.")
        report.append("")
        report.append("Recommended interventions:")
        report.append("  - Reduce design speed to 20 mph maximum")
        report.append("  - Install separated pedestrian infrastructure")
        report.append("  - Add adequate illumination")
        report.append("  - Implement traffic calming measures")
        report.append("")

        report.append("=" * 80)
        report.append("")
        report.append("Report prepared by: Forensic Archaeology of the Present Project")
        report.append(f"Report date: {datetime.now().strftime('%Y-%m-%d')}")
        report.append("")
        report.append("Note: This report uses archaeological methodology to document")
        report.append("contemporary infrastructure violence. The past tense is intentional:")
        report.append("it defamiliarizes the present and makes car culture strange.")
        report.append("")

        # Write to file
        with open(filename, 'w') as f:
            f.write('\n'.join(report))

        print(f"Site report written: {filename}")


def main():
    """Command-line interface for Forensic Archaeology project."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Forensic Archaeology of the Present - Excavating Invisible Graveyards'
    )
    parser.add_argument('input', help='Input GeoJSON with crash data')
    parser.add_argument('--output-dir', default='archaeological_sites', help='Output directory')
    parser.add_argument('--catalog', action='store_true', help='Generate artifact catalog')

    args = parser.parse_args()

    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)

    # Load crash data
    with open(args.input, 'r') as f:
        data = json.load(f)

    features = data.get('features', [])

    print(f"\n{'='*80}")
    print("FORENSIC ARCHAEOLOGY OF THE PRESENT")
    print("Excavating Invisible Graveyards")
    print(f"{'='*80}\n")

    print(f"Processing {len(features)} archaeological sites...")
    print("(Each pedestrian death site documented as an excavation)\n")

    # Create archaeological report generator
    archaeologist = ArchaeologicalReport()

    # Process each crash as an archaeological site
    for i, feature in enumerate(features):
        if feature['geometry']['type'] != 'Point':
            continue

        # Generate site number (following archaeological conventions)
        props = feature['properties']
        state = props.get('state', 0)
        year = props.get('year', 2000)
        case = props.get('case', i)

        site_number = f"USA-{state:02d}-{year}-{case:05d}"

        # Create site
        site = archaeologist.create_site_from_crash(feature, site_number)

        # Generate report
        report_filename = os.path.join(args.output_dir, f"site_{site_number.replace('-', '_')}.txt")
        archaeologist.generate_site_report(site, report_filename)

        if (i + 1) % 5 == 0:
            print(f"Documented {i + 1} sites...")

    print(f"\nExcavation complete. {len(archaeologist.sites)} sites documented.")
    print(f"Reports saved to: {args.output_dir}/")

    # Export site catalog
    catalog_file = os.path.join(args.output_dir, "site_catalog.json")
    with open(catalog_file, 'w') as f:
        json.dump([asdict(site) for site in archaeologist.sites], f, indent=2)

    print(f"Site catalog: {catalog_file}")

    print(f"\n{'='*80}")
    print("METHODOLOGY REFLECTION")
    print(f"{'='*80}")
    print("This project applies rigorous archaeological field methods to the present.")
    print("")
    print("By documenting crash sites as 'excavations' and writing in the past tense,")
    print("we make car-centric infrastructure strange and visible.")
    print("")
    print("Future archaeologists WILL study our car culture this way.")
    print("We're just doing it now, before it becomes past.")
    print("")
    print("The absurdity is the point: our current infrastructure IS absurd.")
    print("We've just normalized it.")
    print(f"{'='*80}\n")


if __name__ == '__main__':
    main()
