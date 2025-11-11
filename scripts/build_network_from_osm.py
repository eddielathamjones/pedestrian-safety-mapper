"""
Build Street Network from OpenStreetMap Data

Downloads OSM data for a given area and constructs a StreetNetwork object
with pedestrian safety attributes inferred from OSM tags.

Requires: osmnx library
Install: pip install osmnx
"""

import os
import sys
import json
from typing import Dict, Tuple, Optional
import math

try:
    import osmnx as ox
    import networkx as nx
except ImportError:
    print("Error: osmnx not installed. Install with: pip install osmnx")
    sys.exit(1)

from street_network import StreetNetwork, IntersectionNode, StreetEdge


# OSM highway tag mapping to functional class
HIGHWAY_TO_FUNCTIONAL_CLASS = {
    'motorway': 1,        # Interstate
    'motorway_link': 1,
    'trunk': 2,           # Principal Arterial
    'trunk_link': 2,
    'primary': 2,
    'primary_link': 2,
    'secondary': 3,       # Minor Arterial
    'secondary_link': 3,
    'tertiary': 4,        # Major Collector
    'tertiary_link': 4,
    'residential': 6,     # Local
    'living_street': 7,
    'service': 7,
    'unclassified': 6,
}

# Default speed limits by road type (mph)
DEFAULT_SPEEDS = {
    'motorway': 65,
    'trunk': 55,
    'primary': 45,
    'secondary': 35,
    'tertiary': 30,
    'residential': 25,
    'living_street': 15,
    'service': 15,
    'unclassified': 25,
}


def download_osm_network(place_name: str = None,
                         bbox: Tuple[float, float, float, float] = None,
                         point: Tuple[float, float] = None,
                         distance: float = 1000) -> nx.MultiDiGraph:
    """
    Download street network from OpenStreetMap.

    Args:
        place_name: Name of place (e.g., "Berkeley, California, USA")
        bbox: Bounding box as (north, south, east, west)
        point: Center point as (lat, lon) with distance radius
        distance: Radius in meters if using point

    Returns:
        NetworkX MultiDiGraph from OSMnx
    """
    print("Downloading OSM data...")

    if place_name:
        G = ox.graph_from_place(place_name, network_type='drive')
    elif bbox:
        north, south, east, west = bbox
        G = ox.graph_from_bbox(north, south, east, west, network_type='drive')
    elif point:
        lat, lon = point
        G = ox.graph_from_point((lat, lon), dist=distance, network_type='drive')
    else:
        raise ValueError("Must provide place_name, bbox, or point")

    print(f"Downloaded network with {len(G.nodes)} nodes and {len(G.edges)} edges")
    return G


def infer_lighting_quality(edge_data: Dict) -> str:
    """
    Infer lighting quality from OSM tags.

    OSM 'lit' tag: yes, no, automatic, limited
    """
    lit = edge_data.get('lit', None)

    if lit == 'yes' or lit == 'automatic':
        return 'adequate'
    elif lit == 'limited':
        return 'poor'
    elif lit == 'no':
        return 'none'
    else:
        # Heuristic: assume urban arterials have lighting
        highway = edge_data.get('highway', '')
        if highway in ['primary', 'secondary', 'tertiary']:
            return 'adequate'
        return 'unknown'


def infer_sidewalk_presence(edge_data: Dict) -> Tuple[bool, bool]:
    """
    Infer sidewalk presence from OSM tags.

    Returns: (has_north, has_south)
    OSM tags: sidewalk=both, left, right, no, none
    """
    sidewalk = edge_data.get('sidewalk', 'no')

    if sidewalk == 'both':
        return True, True
    elif sidewalk in ['left', 'right']:
        return True, False  # Simplified - don't know actual orientation
    elif sidewalk in ['no', 'none']:
        # Heuristic: residential streets often have sidewalks not tagged
        highway = edge_data.get('highway', '')
        if highway in ['residential', 'tertiary']:
            return True, True  # Assume present if not explicitly marked 'no'
        return False, False
    else:
        # Unknown - use heuristics
        highway = edge_data.get('highway', '')
        if highway in ['residential', 'tertiary', 'secondary', 'primary']:
            return True, True
        return False, False


def infer_is_stroad(highway_type: str, speed_limit: int, lanes: int) -> bool:
    """
    Determine if this is a "stroad" - high-speed arterial with pedestrian access.

    Stroads are the most dangerous design: combine high speeds with frequent
    pedestrian crossings, driveways, and intersections.

    Characteristics:
    - Principal or minor arterial classification
    - 4+ lanes
    - 35+ mph speed limit
    - Has adjacent land use (not limited access)
    """
    is_arterial = highway_type in ['trunk', 'primary', 'secondary']
    high_speed = speed_limit >= 35
    multi_lane = lanes >= 4

    # If it's a limited access road (motorway), it's not a stroad
    if highway_type in ['motorway', 'motorway_link']:
        return False

    return is_arterial and high_speed and multi_lane


def calculate_edge_length(G: nx.MultiDiGraph, u: int, v: int, key: int) -> float:
    """Calculate edge length in meters."""
    edge_data = G[u][v][key]
    if 'length' in edge_data:
        return edge_data['length']

    # Calculate from node coordinates
    node_u = G.nodes[u]
    node_v = G.nodes[v]

    # Haversine distance
    lat1, lon1 = node_u['y'], node_u['x']
    lat2, lon2 = node_v['y'], node_v['x']

    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

    return R * c


def build_street_network(osm_graph: nx.MultiDiGraph) -> StreetNetwork:
    """
    Convert OSMnx graph to StreetNetwork object.

    Extracts relevant attributes and infers pedestrian safety characteristics.
    """
    print("Building street network model...")
    network = StreetNetwork()

    # Add nodes (intersections)
    for node_id, node_data in osm_graph.nodes(data=True):
        node = IntersectionNode(
            id=str(node_id),
            lat=node_data['y'],
            lon=node_data['x'],
            intersection_type='uncontrolled',  # TODO: infer from OSM tags
            has_signals=node_data.get('highway') == 'traffic_signals',
        )
        network.add_node(node)

    # Add edges (street segments)
    for u, v, key, edge_data in osm_graph.edges(keys=True, data=True):
        edge_id = f"{u}_{v}_{key}"

        # Extract basic attributes
        highway_type = edge_data.get('highway', 'unclassified')
        if isinstance(highway_type, list):
            highway_type = highway_type[0]

        name = edge_data.get('name', 'Unnamed Street')
        if isinstance(name, list):
            name = ', '.join(name)

        # Get or infer number of lanes
        lanes = edge_data.get('lanes', 2)
        if isinstance(lanes, list):
            lanes = int(lanes[0])
        elif isinstance(lanes, str):
            lanes = int(lanes) if lanes.isdigit() else 2
        else:
            lanes = int(lanes)

        # Get or infer speed limit
        maxspeed = edge_data.get('maxspeed', None)
        if maxspeed:
            if isinstance(maxspeed, list):
                maxspeed = maxspeed[0]
            # Parse speed (could be "30 mph", "50", "50 km/h")
            if isinstance(maxspeed, str):
                if 'mph' in maxspeed:
                    speed_limit = int(maxspeed.replace('mph', '').strip())
                elif 'km/h' in maxspeed:
                    speed_limit = int(int(maxspeed.replace('km/h', '').strip()) * 0.621371)
                elif maxspeed.isdigit():
                    speed_limit = int(maxspeed)
                else:
                    speed_limit = DEFAULT_SPEEDS.get(highway_type, 25)
            else:
                speed_limit = int(maxspeed)
        else:
            speed_limit = DEFAULT_SPEEDS.get(highway_type, 25)

        # Infer lane width (US standard is 10-12 feet, varies by road type)
        if highway_type in ['motorway', 'trunk']:
            lane_width = 12.0
        elif highway_type in ['primary', 'secondary']:
            lane_width = 11.0
        else:
            lane_width = 10.0

        # Calculate length
        length_m = calculate_edge_length(osm_graph, u, v, key)

        # Infer pedestrian infrastructure
        has_sidewalk_n, has_sidewalk_s = infer_sidewalk_presence(edge_data)
        lighting = infer_lighting_quality(edge_data)

        # Bike infrastructure
        has_bike_lane = 'cycleway' in edge_data or edge_data.get('bicycle') == 'designated'
        bike_lane_protected = edge_data.get('cycleway:right') == 'track' or \
                              edge_data.get('cycleway:left') == 'track'

        # Determine if it's a stroad
        functional_class = HIGHWAY_TO_FUNCTIONAL_CLASS.get(highway_type, 6)
        is_stroad = infer_is_stroad(highway_type, speed_limit, lanes)

        # Create edge
        edge = StreetEdge(
            id=edge_id,
            from_node=str(u),
            to_node=str(v),
            name=name,
            length_meters=length_m,
            road_class=highway_type,
            functional_class=functional_class,
            lanes=lanes,
            speed_limit_mph=speed_limit,
            posted_speed_mph=speed_limit,
            design_speed_mph=speed_limit + 5,  # Heuristic: actual speeds often 5+ over
            lane_width_feet=lane_width,
            has_sidewalk_north=has_sidewalk_n,
            has_sidewalk_south=has_sidewalk_s,
            sidewalk_width_feet=5.0 if (has_sidewalk_n or has_sidewalk_s) else 0.0,
            has_bike_lane=has_bike_lane,
            bike_lane_protected=bike_lane_protected,
            lighting_quality=lighting,
            is_stroad=is_stroad,
        )

        network.add_edge(edge)

    print(f"Built network with {len(network.nodes)} nodes and {len(network.edges)} edges")
    return network


def main():
    """Example usage."""
    import argparse

    parser = argparse.ArgumentParser(description='Build street network from OpenStreetMap')
    parser.add_argument('--place', type=str, help='Place name (e.g., "Berkeley, California, USA")')
    parser.add_argument('--lat', type=float, help='Center latitude')
    parser.add_argument('--lon', type=float, help='Center longitude')
    parser.add_argument('--radius', type=float, default=1000, help='Radius in meters (default: 1000)')
    parser.add_argument('--output', type=str, default='network.json', help='Output filename')

    args = parser.parse_args()

    # Download OSM data
    if args.place:
        G = download_osm_network(place_name=args.place)
    elif args.lat and args.lon:
        G = download_osm_network(point=(args.lat, args.lon), distance=args.radius)
    else:
        print("Error: Must provide --place or --lat/--lon")
        sys.exit(1)

    # Build network
    network = build_street_network(G)

    # Calculate risk scores
    print("Calculating risk scores...")
    network.calculate_all_risk_scores()

    # Print statistics
    stats = network.get_statistics()
    print("\n" + "="*60)
    print("NETWORK STATISTICS")
    print("="*60)
    for key, value in stats.items():
        print(f"{key}: {value}")

    # Find high-risk segments
    high_risk = network.get_high_risk_edges(threshold=15.0)
    print(f"\nHigh-risk segments (score >= 15.0): {len(high_risk)}")
    if high_risk:
        print("\nTop 5 highest risk segments:")
        sorted_risk = sorted(high_risk, key=lambda e: e.risk_score, reverse=True)[:5]
        for edge in sorted_risk:
            print(f"  - {edge.name}: {edge.risk_score:.1f}")
            print(f"    {edge.speed_limit_mph} mph, {edge.lanes} lanes, lighting: {edge.lighting_quality}")

    # Export
    print(f"\nExporting network to {args.output}...")
    network.export_to_file(args.output)

    # Also export GeoJSON for visualization
    geojson_file = args.output.replace('.json', '_geo.json')
    print(f"Exporting GeoJSON to {geojson_file}...")
    geojson = network.to_geojson()
    with open(geojson_file, 'w') as f:
        json.dump(geojson, f)

    print("\nDone!")


if __name__ == '__main__':
    main()
