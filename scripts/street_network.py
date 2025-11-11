"""
Street Network Model for Pedestrian Safety Simulation

This module provides a graph-based model of street networks with attributes
relevant for pedestrian safety analysis and intervention simulation.

Data Model:
- Nodes: Intersections with attributes (type, signals, crossings, etc.)
- Edges: Street segments with attributes (road type, speed, width, lighting, etc.)
- Crash Data: Historical pedestrian crashes mapped to network elements
"""

import json
import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, asdict
from collections import defaultdict


@dataclass
class IntersectionNode:
    """Represents an intersection in the street network."""
    id: str
    lat: float
    lon: float

    # Infrastructure attributes
    intersection_type: str = "unknown"  # signalized, stop_sign, uncontrolled, roundabout
    has_signals: bool = False
    has_pedestrian_signals: bool = False
    has_leading_pedestrian_interval: bool = False  # LPI gives peds head start
    has_curb_extensions: bool = False  # Bulb-outs reduce crossing distance
    has_refuge_island: bool = False
    has_raised_crossing: bool = False  # Speed table
    crossing_count: int = 0  # Number of marked crosswalks

    # Geometry
    leg_count: int = 4  # Number of approaches (3-way, 4-way, etc.)

    # Risk metrics
    crash_count: int = 0
    crash_fatality_count: int = 0
    risk_score: float = 0.0

    # Connected edges
    connected_edges: List[str] = None

    def __post_init__(self):
        if self.connected_edges is None:
            self.connected_edges = []


@dataclass
class StreetEdge:
    """Represents a street segment between intersections."""
    id: str
    from_node: str
    to_node: str

    # Basic attributes
    name: str = "Unknown Street"
    length_meters: float = 0.0

    # Road classification
    road_class: str = "unknown"  # Interstate, arterial, collector, local, etc.
    functional_class: int = -1  # FARS coding (1=Interstate, 2=Principal Arterial, etc.)
    lanes: int = 2

    # Speed and design
    speed_limit_mph: int = 25
    posted_speed_mph: int = 25  # Sometimes differs from speed limit
    design_speed_mph: int = 30  # What the road geometry encourages
    lane_width_feet: float = 12.0

    # Pedestrian infrastructure
    has_sidewalk_north: bool = False
    has_sidewalk_south: bool = False
    sidewalk_width_feet: float = 0.0
    has_buffer: bool = False  # Between sidewalk and traffic
    buffer_width_feet: float = 0.0
    has_street_trees: bool = False
    has_bike_lane: bool = False
    bike_lane_protected: bool = False

    # Environmental
    lighting_quality: str = "none"  # none, poor, adequate, good
    lighting_spacing_feet: float = 0.0

    # Context
    land_use: str = "unknown"  # residential, commercial, industrial, mixed
    pedestrian_volume: str = "unknown"  # low, medium, high
    vehicle_aadt: int = 0  # Annual Average Daily Traffic

    # Risk factors
    is_stroad: bool = False  # High-speed arterial with pedestrian access
    crash_count: int = 0
    crash_fatality_count: int = 0
    risk_score: float = 0.0

    def calculate_risk_score(self) -> float:
        """
        Calculate pedestrian risk score based on infrastructure attributes.
        Higher score = more dangerous.

        Based on research from:
        - FHWA Pedestrian Safety Guide
        - European road safety audits
        - Vision Zero network analysis
        """
        score = 0.0

        # Speed is the #1 killer - exponential relationship with fatality risk
        if self.speed_limit_mph >= 45:
            score += 10.0  # Extremely dangerous
        elif self.speed_limit_mph >= 35:
            score += 7.0   # Very dangerous
        elif self.speed_limit_mph >= 25:
            score += 3.0   # Moderate risk
        else:
            score += 1.0   # Lower risk

        # Wide lanes encourage speeding
        if self.lane_width_feet >= 12:
            score += 2.0

        # Multiple lanes = higher exposure
        if self.lanes >= 6:
            score += 5.0
        elif self.lanes >= 4:
            score += 3.0
        elif self.lanes >= 3:
            score += 1.5

        # "Stroad" design (high speed + pedestrian access) is deadly
        if self.is_stroad:
            score += 8.0

        # Lack of pedestrian infrastructure
        if not self.has_sidewalk_north and not self.has_sidewalk_south:
            score += 5.0
        elif self.sidewalk_width_feet < 5.0:
            score += 2.0

        if not self.has_buffer:
            score += 3.0

        # Poor lighting is a major factor
        if self.lighting_quality == "none":
            score += 6.0
        elif self.lighting_quality == "poor":
            score += 4.0

        # High traffic volume
        if self.vehicle_aadt > 20000:
            score += 3.0
        elif self.vehicle_aadt > 10000:
            score += 2.0

        # Positive factors reduce risk
        if self.has_bike_lane and self.bike_lane_protected:
            score -= 3.0  # Protected bike lane creates buffer

        if self.has_street_trees:
            score -= 2.0  # Trees slow drivers (psychological narrowing)

        if self.has_buffer and self.buffer_width_feet >= 8:
            score -= 2.0

        # Historical crash data is strongest predictor
        score += self.crash_count * 2.0
        score += self.crash_fatality_count * 10.0

        self.risk_score = max(0.0, score)
        return self.risk_score


class StreetNetwork:
    """Graph representation of a street network with pedestrian safety attributes."""

    def __init__(self):
        self.nodes: Dict[str, IntersectionNode] = {}
        self.edges: Dict[str, StreetEdge] = {}
        self.crashes: List[Dict] = []

    def add_node(self, node: IntersectionNode):
        """Add an intersection node to the network."""
        self.nodes[node.id] = node

    def add_edge(self, edge: StreetEdge):
        """Add a street edge to the network."""
        self.edges[edge.id] = edge

        # Update node connections
        if edge.from_node in self.nodes:
            if edge.id not in self.nodes[edge.from_node].connected_edges:
                self.nodes[edge.from_node].connected_edges.append(edge.id)

        if edge.to_node in self.nodes:
            if edge.id not in self.nodes[edge.to_node].connected_edges:
                self.nodes[edge.to_node].connected_edges.append(edge.id)

    def add_crash(self, crash_data: Dict):
        """Add a crash record and map it to nearest network element."""
        self.crashes.append(crash_data)

        # Map to nearest edge or node
        lat, lon = crash_data.get('lat'), crash_data.get('lon')
        if lat and lon:
            nearest_edge = self.find_nearest_edge(lat, lon, max_distance_meters=50)
            if nearest_edge:
                nearest_edge.crash_count += 1
                if crash_data.get('fatal', False):
                    nearest_edge.crash_fatality_count += 1

    def find_nearest_edge(self, lat: float, lon: float, max_distance_meters: float = 100) -> Optional[StreetEdge]:
        """Find the nearest edge to a given lat/lon point."""
        min_distance = float('inf')
        nearest = None

        for edge in self.edges.values():
            # Get coordinates of edge endpoints
            if edge.from_node not in self.nodes or edge.to_node not in self.nodes:
                continue

            from_node = self.nodes[edge.from_node]
            to_node = self.nodes[edge.to_node]

            # Calculate distance to edge (simplified - point to line segment)
            dist = self._point_to_segment_distance(
                lat, lon,
                from_node.lat, from_node.lon,
                to_node.lat, to_node.lon
            )

            if dist < min_distance:
                min_distance = dist
                nearest = edge

        if min_distance <= max_distance_meters:
            return nearest
        return None

    def _point_to_segment_distance(self, px: float, py: float,
                                   x1: float, y1: float,
                                   x2: float, y2: float) -> float:
        """Calculate distance from point to line segment (in meters)."""
        # Convert to approximate meters (rough estimation)
        # More accurate would use Haversine formula
        meters_per_degree_lat = 111000
        meters_per_degree_lon = 111000 * math.cos(math.radians(px))

        px_m = px * meters_per_degree_lat
        py_m = py * meters_per_degree_lon
        x1_m = x1 * meters_per_degree_lat
        y1_m = y1 * meters_per_degree_lon
        x2_m = x2 * meters_per_degree_lat
        y2_m = y2 * meters_per_degree_lon

        # Vector from point 1 to point 2
        dx = x2_m - x1_m
        dy = y2_m - y1_m

        if dx == 0 and dy == 0:
            # Point 1 and 2 are the same
            return math.sqrt((px_m - x1_m)**2 + (py_m - y1_m)**2)

        # Parameter t determines closest point on line segment
        t = max(0, min(1, ((px_m - x1_m) * dx + (py_m - y1_m) * dy) / (dx**2 + dy**2)))

        # Closest point on segment
        closest_x = x1_m + t * dx
        closest_y = y1_m + t * dy

        # Distance to closest point
        return math.sqrt((px_m - closest_x)**2 + (py_m - closest_y)**2)

    def calculate_all_risk_scores(self):
        """Calculate risk scores for all edges in the network."""
        for edge in self.edges.values():
            edge.calculate_risk_score()

    def get_high_risk_edges(self, threshold: float = 10.0) -> List[StreetEdge]:
        """Get edges with risk score above threshold."""
        return [edge for edge in self.edges.values() if edge.risk_score >= threshold]

    def get_high_risk_nodes(self, threshold: int = 2) -> List[IntersectionNode]:
        """Get intersections with crash count above threshold."""
        return [node for node in self.nodes.values() if node.crash_count >= threshold]

    def to_geojson(self, include_risk_scores: bool = True) -> Dict:
        """Export network to GeoJSON for visualization."""
        features = []

        # Export edges as LineString features
        for edge in self.edges.values():
            if edge.from_node not in self.nodes or edge.to_node not in self.nodes:
                continue

            from_node = self.nodes[edge.from_node]
            to_node = self.nodes[edge.to_node]

            properties = {
                'id': edge.id,
                'name': edge.name,
                'road_class': edge.road_class,
                'speed_limit': edge.speed_limit_mph,
                'lanes': edge.lanes,
                'length_m': edge.length_meters,
                'has_sidewalk': edge.has_sidewalk_north or edge.has_sidewalk_south,
                'lighting': edge.lighting_quality,
                'is_stroad': edge.is_stroad,
                'crashes': edge.crash_count,
                'fatalities': edge.crash_fatality_count,
            }

            if include_risk_scores:
                properties['risk_score'] = edge.risk_score

            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'LineString',
                    'coordinates': [
                        [from_node.lon, from_node.lat],
                        [to_node.lon, to_node.lat]
                    ]
                },
                'properties': properties
            })

        # Export nodes as Point features
        for node in self.nodes.values():
            properties = {
                'id': node.id,
                'type': node.intersection_type,
                'has_signals': node.has_signals,
                'crossings': node.crossing_count,
                'crashes': node.crash_count,
                'fatalities': node.crash_fatality_count,
            }

            if include_risk_scores:
                properties['risk_score'] = node.risk_score

            features.append({
                'type': 'Feature',
                'geometry': {
                    'type': 'Point',
                    'coordinates': [node.lon, node.lat]
                },
                'properties': properties
            })

        return {
            'type': 'FeatureCollection',
            'features': features
        }

    def export_to_file(self, filename: str):
        """Export network to JSON file."""
        data = {
            'nodes': {nid: asdict(node) for nid, node in self.nodes.items()},
            'edges': {eid: asdict(edge) for eid, edge in self.edges.items()},
            'crashes': self.crashes
        }

        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filename: str) -> 'StreetNetwork':
        """Load network from JSON file."""
        with open(filename, 'r') as f:
            data = json.load(f)

        network = cls()

        # Load nodes
        for nid, node_data in data.get('nodes', {}).items():
            network.add_node(IntersectionNode(**node_data))

        # Load edges
        for eid, edge_data in data.get('edges', {}).items():
            network.add_edge(StreetEdge(**edge_data))

        # Load crashes
        network.crashes = data.get('crashes', [])

        return network

    def get_statistics(self) -> Dict:
        """Get summary statistics of the network."""
        total_length = sum(edge.length_meters for edge in self.edges.values())

        edges_with_sidewalks = sum(
            1 for edge in self.edges.values()
            if edge.has_sidewalk_north or edge.has_sidewalk_south
        )

        edges_with_lighting = sum(
            1 for edge in self.edges.values()
            if edge.lighting_quality in ['adequate', 'good']
        )

        stroads = sum(1 for edge in self.edges.values() if edge.is_stroad)

        high_speed_edges = sum(
            1 for edge in self.edges.values()
            if edge.speed_limit_mph >= 35
        )

        return {
            'node_count': len(self.nodes),
            'edge_count': len(self.edges),
            'total_length_km': total_length / 1000,
            'total_crashes': sum(edge.crash_count for edge in self.edges.values()),
            'total_fatalities': sum(edge.crash_fatality_count for edge in self.edges.values()),
            'edges_with_sidewalks': edges_with_sidewalks,
            'sidewalk_coverage_pct': (edges_with_sidewalks / len(self.edges) * 100) if self.edges else 0,
            'edges_with_adequate_lighting': edges_with_lighting,
            'lighting_coverage_pct': (edges_with_lighting / len(self.edges) * 100) if self.edges else 0,
            'stroad_count': stroads,
            'high_speed_edge_count': high_speed_edges,
            'avg_risk_score': sum(e.risk_score for e in self.edges.values()) / len(self.edges) if self.edges else 0,
        }
