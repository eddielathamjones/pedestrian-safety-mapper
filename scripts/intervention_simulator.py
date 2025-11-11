"""
Pedestrian Safety Intervention Simulator

Simulates the impact of infrastructure interventions on pedestrian safety.
Tests scenarios like speed limit reductions, sidewalk installation, lighting
improvements, and stroad conversions.

Based on evidence from European Vision Zero implementations.
"""

import copy
import json
from typing import Dict, List, Callable
from dataclasses import dataclass, asdict

from street_network import StreetNetwork, StreetEdge, IntersectionNode


@dataclass
class InterventionScenario:
    """Represents a specific intervention scenario."""
    name: str
    description: str
    modifications: List[Dict]  # List of modifications to apply
    estimated_cost_per_mile: float  # USD
    evidence_source: str  # Citation for effectiveness
    expected_crash_reduction_pct: float  # Expected % reduction in crashes


# Pre-defined intervention scenarios based on European success
INTERVENTION_SCENARIOS = {
    'vision_zero_speed': InterventionScenario(
        name="Vision Zero Speed Limits",
        description="Reduce urban street speeds to 20 mph (30 km/h)",
        modifications=[{
            'type': 'speed_limit',
            'filter': {'functional_class': [6, 7], 'speed_limit_mph': 25},
            'change': {'speed_limit_mph': 20, 'design_speed_mph': 22}
        }],
        estimated_cost_per_mile=50000,  # Signage, markings, traffic calming
        evidence_source="Helsinki, Oslo: 90% reduction in pedestrian fatalities",
        expected_crash_reduction_pct=60
    ),

    'arterial_speed_reduction': InterventionScenario(
        name="Arterial Speed Reduction",
        description="Reduce arterial speeds from 45+ to 35 mph maximum",
        modifications=[{
            'type': 'speed_limit',
            'filter': {'speed_limit_mph': 45},
            'change': {'speed_limit_mph': 35, 'design_speed_mph': 37}
        }],
        estimated_cost_per_mile=100000,  # Road diet, lane narrowing
        evidence_source="FHWA: 15% crash reduction per 5 mph speed reduction",
        expected_crash_reduction_pct=30
    ),

    'stroad_conversion': InterventionScenario(
        name="Stroad Redesign",
        description="Convert high-speed arterials to either highways or safe streets",
        modifications=[{
            'type': 'stroad_fix',
            'filter': {'is_stroad': True},
            'change': {
                'speed_limit_mph': 30,
                'design_speed_mph': 30,
                'lane_width_feet': 10.0,
                'has_buffer': True,
                'buffer_width_feet': 8.0,
                'is_stroad': False
            }
        }],
        estimated_cost_per_mile=2000000,  # Major reconstruction
        evidence_source="Netherlands: 75% fatality reduction after mode separation",
        expected_crash_reduction_pct=75
    ),

    'complete_sidewalks': InterventionScenario(
        name="Complete Sidewalk Network",
        description="Install sidewalks on all streets lacking them",
        modifications=[{
            'type': 'sidewalk',
            'filter': {'has_sidewalk_north': False, 'has_sidewalk_south': False},
            'change': {
                'has_sidewalk_north': True,
                'has_sidewalk_south': True,
                'sidewalk_width_feet': 6.0
            }
        }],
        estimated_cost_per_mile=500000,  # Sidewalk construction
        evidence_source="FHWA: 88% reduction in pedestrian crashes with sidewalks",
        expected_crash_reduction_pct=65
    ),

    'street_lighting': InterventionScenario(
        name="Complete Street Lighting",
        description="Install adequate lighting on all streets",
        modifications=[{
            'type': 'lighting',
            'filter': {'lighting_quality': ['none', 'poor']},
            'change': {'lighting_quality': 'adequate', 'lighting_spacing_feet': 100}
        }],
        estimated_cost_per_mile=150000,  # LED streetlights installation
        evidence_source="Research: 30-50% reduction in nighttime pedestrian crashes",
        expected_crash_reduction_pct=40
    ),

    'protected_bike_lanes': InterventionScenario(
        name="Protected Bike Lane Network",
        description="Install protected bike lanes on arterials (creates pedestrian buffer)",
        modifications=[{
            'type': 'bike_lane',
            'filter': {'functional_class': [2, 3], 'has_bike_lane': False},
            'change': {
                'has_bike_lane': True,
                'bike_lane_protected': True,
                'has_buffer': True,
                'buffer_width_feet': 6.0
            }
        }],
        estimated_cost_per_mile=800000,  # Protected bike lane installation
        evidence_source="European cities: Physical separation improves pedestrian safety",
        expected_crash_reduction_pct=30
    ),

    'traffic_calming': InterventionScenario(
        name="Comprehensive Traffic Calming",
        description="Add traffic calming to residential streets (bumps, chicanes, etc.)",
        modifications=[{
            'type': 'traffic_calming',
            'filter': {'road_class': 'residential'},
            'change': {
                'design_speed_mph': 20,
                'has_street_trees': True,
                'lane_width_feet': 10.0
            }
        }],
        estimated_cost_per_mile=250000,  # Speed humps, curb extensions, etc.
        evidence_source="UK: 60% reduction in pedestrian casualties with traffic calming",
        expected_crash_reduction_pct=60
    ),

    'protected_intersections': InterventionScenario(
        name="Protected Intersections",
        description="Upgrade high-crash intersections with refuge islands, LPI, etc.",
        modifications=[{
            'type': 'intersection_upgrade',
            'filter': {'crash_count': 2},  # Nodes with 2+ crashes
            'change': {
                'has_leading_pedestrian_interval': True,
                'has_curb_extensions': True,
                'has_refuge_island': True,
                'has_raised_crossing': True
            }
        }],
        estimated_cost_per_mile=500000,  # Per intersection (not per mile)
        evidence_source="Oslo/Helsinki: 50-90% crash reduction at protected intersections",
        expected_crash_reduction_pct=70
    ),

    'comprehensive_vision_zero': InterventionScenario(
        name="Comprehensive Vision Zero",
        description="Full Vision Zero implementation: speed, infrastructure, and enforcement",
        modifications=[
            {
                'type': 'speed_limit',
                'filter': {'functional_class': [6, 7]},
                'change': {'speed_limit_mph': 20, 'design_speed_mph': 20}
            },
            {
                'type': 'speed_limit',
                'filter': {'functional_class': [2, 3, 4]},
                'change': {'speed_limit_mph': 30, 'design_speed_mph': 30}
            },
            {
                'type': 'sidewalk',
                'filter': {'has_sidewalk_north': False, 'has_sidewalk_south': False},
                'change': {'has_sidewalk_north': True, 'has_sidewalk_south': True, 'sidewalk_width_feet': 6.0}
            },
            {
                'type': 'lighting',
                'filter': {'lighting_quality': ['none', 'poor']},
                'change': {'lighting_quality': 'adequate'}
            },
            {
                'type': 'stroad_fix',
                'filter': {'is_stroad': True},
                'change': {
                    'speed_limit_mph': 30,
                    'lane_width_feet': 10.0,
                    'has_buffer': True,
                    'buffer_width_feet': 8.0,
                    'is_stroad': False
                }
            }
        ],
        estimated_cost_per_mile=3000000,  # Comprehensive rebuild
        evidence_source="Netherlands, Norway, Sweden: Near-zero pedestrian deaths",
        expected_crash_reduction_pct=95
    ),
}


class InterventionSimulator:
    """Simulates interventions on street networks."""

    def __init__(self, baseline_network: StreetNetwork):
        """
        Initialize simulator with a baseline network.

        Args:
            baseline_network: Original network before interventions
        """
        self.baseline = baseline_network
        self.scenarios: Dict[str, StreetNetwork] = {}

    def apply_scenario(self, scenario_name: str, scenario: InterventionScenario) -> StreetNetwork:
        """
        Apply an intervention scenario to the network.

        Args:
            scenario_name: Name for this scenario
            scenario: InterventionScenario to apply

        Returns:
            Modified network
        """
        # Deep copy baseline network
        modified_network = copy.deepcopy(self.baseline)

        edges_modified = 0
        nodes_modified = 0

        # Apply each modification in the scenario
        for modification in scenario.modifications:
            mod_type = modification['type']
            filter_criteria = modification.get('filter', {})
            changes = modification['change']

            if mod_type in ['speed_limit', 'sidewalk', 'lighting', 'bike_lane',
                           'traffic_calming', 'stroad_fix']:
                # Edge modifications
                for edge in modified_network.edges.values():
                    if self._matches_filter(edge, filter_criteria):
                        for key, value in changes.items():
                            if hasattr(edge, key):
                                setattr(edge, key, value)
                        edges_modified += 1

            elif mod_type == 'intersection_upgrade':
                # Node modifications
                for node in modified_network.nodes.values():
                    if self._matches_filter(node, filter_criteria):
                        for key, value in changes.items():
                            if hasattr(node, key):
                                setattr(node, key, value)
                        nodes_modified += 1

        # Recalculate risk scores
        modified_network.calculate_all_risk_scores()

        # Store scenario
        self.scenarios[scenario_name] = modified_network

        print(f"Applied '{scenario_name}': {edges_modified} edges, {nodes_modified} nodes modified")

        return modified_network

    def _matches_filter(self, obj, filter_criteria: Dict) -> bool:
        """Check if object matches filter criteria."""
        for key, value in filter_criteria.items():
            if not hasattr(obj, key):
                return False

            obj_value = getattr(obj, key)

            if isinstance(value, list):
                # Match if obj_value is in list or >= minimum in list
                if isinstance(value[0], (int, float)):
                    if obj_value < min(value):
                        return False
                elif obj_value not in value:
                    return False
            elif isinstance(value, (int, float)):
                # For numeric values, match if >= threshold
                if obj_value < value:
                    return False
            else:
                # Exact match
                if obj_value != value:
                    return False

        return True

    def compare_scenarios(self, scenario_names: List[str] = None) -> Dict:
        """
        Compare multiple scenarios to baseline.

        Args:
            scenario_names: List of scenario names to compare. If None, compare all.

        Returns:
            Comparison statistics
        """
        if scenario_names is None:
            scenario_names = list(self.scenarios.keys())

        baseline_stats = self.baseline.get_statistics()

        comparison = {
            'baseline': baseline_stats,
            'scenarios': {}
        }

        for scenario_name in scenario_names:
            if scenario_name not in self.scenarios:
                continue

            scenario_network = self.scenarios[scenario_name]
            scenario_stats = scenario_network.get_statistics()

            # Calculate changes
            changes = {}
            for key in baseline_stats:
                baseline_val = baseline_stats[key]
                scenario_val = scenario_stats[key]

                if isinstance(baseline_val, (int, float)):
                    if baseline_val > 0:
                        pct_change = ((scenario_val - baseline_val) / baseline_val) * 100
                        changes[f"{key}_change_pct"] = pct_change
                    changes[f"{key}_absolute"] = scenario_val
                else:
                    changes[key] = scenario_val

            comparison['scenarios'][scenario_name] = changes

        return comparison

    def generate_report(self, scenario_name: str) -> str:
        """Generate a text report comparing scenario to baseline."""
        if scenario_name not in self.scenarios:
            return f"Scenario '{scenario_name}' not found"

        baseline_stats = self.baseline.get_statistics()
        scenario_stats = self.scenarios[scenario_name].get_statistics()

        report = []
        report.append("=" * 70)
        report.append(f"INTERVENTION SCENARIO REPORT: {scenario_name}")
        report.append("=" * 70)
        report.append("")

        # Get scenario details
        scenario = INTERVENTION_SCENARIOS.get(scenario_name)
        if scenario:
            report.append(f"Description: {scenario.description}")
            report.append(f"Evidence: {scenario.evidence_source}")
            report.append(f"Estimated Cost: ${scenario.estimated_cost_per_mile:,.0f} per mile")
            report.append(f"Expected Crash Reduction: {scenario.expected_crash_reduction_pct}%")
            report.append("")

        report.append("BASELINE vs. SCENARIO COMPARISON")
        report.append("-" * 70)

        # Key metrics
        metrics = [
            ('avg_risk_score', 'Average Risk Score', True),
            ('total_crashes', 'Total Crashes', True),
            ('total_fatalities', 'Total Fatalities', True),
            ('sidewalk_coverage_pct', 'Sidewalk Coverage %', False),
            ('lighting_coverage_pct', 'Adequate Lighting %', False),
            ('stroad_count', 'Stroad Count', True),
            ('high_speed_edge_count', 'High-Speed Streets (35+ mph)', True),
        ]

        for key, label, lower_is_better in metrics:
            baseline_val = baseline_stats.get(key, 0)
            scenario_val = scenario_stats.get(key, 0)

            if baseline_val > 0:
                change = scenario_val - baseline_val
                pct_change = (change / baseline_val) * 100
            else:
                change = scenario_val
                pct_change = 0

            # Format change indicator
            if lower_is_better:
                indicator = "✓" if change < 0 else ("✗" if change > 0 else "→")
            else:
                indicator = "✓" if change > 0 else ("✗" if change < 0 else "→")

            report.append(f"{label:35s}: {baseline_val:10.1f} → {scenario_val:10.1f} "
                         f"({pct_change:+6.1f}%) {indicator}")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)

    def export_scenario_geojson(self, scenario_name: str, filename: str):
        """Export scenario network as GeoJSON."""
        if scenario_name not in self.scenarios:
            print(f"Scenario '{scenario_name}' not found")
            return

        geojson = self.scenarios[scenario_name].to_geojson()

        with open(filename, 'w') as f:
            json.dump(geojson, f, indent=2)

        print(f"Exported '{scenario_name}' to {filename}")


def main():
    """Example usage."""
    import argparse
    from street_network import StreetNetwork

    parser = argparse.ArgumentParser(description='Simulate pedestrian safety interventions')
    parser.add_argument('network_file', help='Input network JSON file')
    parser.add_argument('--scenario', choices=list(INTERVENTION_SCENARIOS.keys()),
                       action='append', help='Scenarios to simulate (can specify multiple)')
    parser.add_argument('--all', action='store_true', help='Run all scenarios')
    parser.add_argument('--output-dir', default='scenarios', help='Output directory for results')

    args = parser.parse_args()

    # Load baseline network
    print(f"Loading baseline network from {args.network_file}...")
    baseline = StreetNetwork.load_from_file(args.network_file)
    baseline.calculate_all_risk_scores()

    # Create simulator
    simulator = InterventionSimulator(baseline)

    # Determine which scenarios to run
    if args.all:
        scenarios_to_run = list(INTERVENTION_SCENARIOS.keys())
    elif args.scenario:
        scenarios_to_run = args.scenario
    else:
        print("No scenarios specified. Use --scenario or --all")
        return

    # Run scenarios
    import os
    os.makedirs(args.output_dir, exist_ok=True)

    for scenario_name in scenarios_to_run:
        print(f"\n{'='*70}")
        print(f"Running scenario: {scenario_name}")
        print(f"{'='*70}")

        scenario = INTERVENTION_SCENARIOS[scenario_name]
        simulator.apply_scenario(scenario_name, scenario)

        # Generate report
        report = simulator.generate_report(scenario_name)
        print(report)

        # Export GeoJSON
        geojson_file = os.path.join(args.output_dir, f"{scenario_name}_geo.json")
        simulator.export_scenario_geojson(scenario_name, geojson_file)

        # Export full network
        network_file = os.path.join(args.output_dir, f"{scenario_name}_network.json")
        simulator.scenarios[scenario_name].export_to_file(network_file)

    # Generate comparison
    print(f"\n{'='*70}")
    print("SCENARIO COMPARISON")
    print(f"{'='*70}")

    comparison = simulator.compare_scenarios(scenarios_to_run)
    comparison_file = os.path.join(args.output_dir, "scenario_comparison.json")

    with open(comparison_file, 'w') as f:
        json.dump(comparison, f, indent=2)

    print(f"Saved comparison to {comparison_file}")


if __name__ == '__main__':
    main()
