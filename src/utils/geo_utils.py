"""
Geospatial utility functions
"""

import math
from typing import Tuple, Optional
from shapely.geometry import Point
from pyproj import Geod


def validate_coordinates(latitude: float, longitude: float) -> bool:
    """
    Validate latitude and longitude coordinates

    Args:
        latitude: Latitude in decimal degrees
        longitude: Longitude in decimal degrees

    Returns:
        True if valid, False otherwise
    """
    if not (-90 <= latitude <= 90):
        return False
    if not (-180 <= longitude <= 180):
        return False
    return True


def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float,
                       unit: str = 'meters') -> float:
    """
    Calculate distance between two points using Vincenty formula (WGS84 ellipsoid)

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates
        unit: Output unit - 'meters', 'kilometers', 'miles', 'feet'

    Returns:
        Distance in specified unit
    """
    # Use pyproj Geod for accurate ellipsoidal calculations
    geod = Geod(ellps='WGS84')
    _, _, distance = geod.inv(lon1, lat1, lon2, lat2)

    # Convert to desired unit
    conversions = {
        'meters': 1,
        'kilometers': 0.001,
        'miles': 0.000621371,
        'feet': 3.28084
    }

    if unit not in conversions:
        raise ValueError(f"Unknown unit: {unit}. Use: {list(conversions.keys())}")

    return distance * conversions[unit]


def get_bounding_box(latitude: float, longitude: float, radius_meters: float) -> Tuple[float, float, float, float]:
    """
    Get bounding box around a point

    Args:
        latitude: Center latitude
        longitude: Center longitude
        radius_meters: Radius in meters

    Returns:
        Tuple of (min_lat, min_lon, max_lat, max_lon)
    """
    # Approximate degrees per meter at given latitude
    lat_degree = 1 / 111320.0  # meters per degree latitude (constant)
    lon_degree = 1 / (111320.0 * math.cos(math.radians(latitude)))  # varies with latitude

    lat_offset = radius_meters * lat_degree
    lon_offset = radius_meters * lon_degree

    return (
        latitude - lat_offset,   # min_lat
        longitude - lon_offset,  # min_lon
        latitude + lat_offset,   # max_lat
        longitude + lon_offset   # max_lon
    )


def point_to_geom(longitude: float, latitude: float) -> Point:
    """
    Create a Shapely Point geometry

    Args:
        longitude: X coordinate
        latitude: Y coordinate

    Returns:
        Shapely Point object
    """
    return Point(longitude, latitude)


def point_to_wkt(longitude: float, latitude: float) -> str:
    """
    Create a WKT (Well-Known Text) representation of a point

    Args:
        longitude: X coordinate
        latitude: Y coordinate

    Returns:
        WKT string
    """
    return f"POINT({longitude} {latitude})"


def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate bearing (compass direction) from point 1 to point 2

    Args:
        lat1, lon1: Starting point
        lat2, lon2: Ending point

    Returns:
        Bearing in degrees (0-360, where 0/360 is North)
    """
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    lon_diff = math.radians(lon2 - lon1)

    x = math.sin(lon_diff) * math.cos(lat2_rad)
    y = (math.cos(lat1_rad) * math.sin(lat2_rad) -
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(lon_diff))

    bearing = math.degrees(math.atan2(x, y))
    return (bearing + 360) % 360  # Normalize to 0-360


def cardinal_direction(bearing: float) -> str:
    """
    Convert bearing to cardinal direction

    Args:
        bearing: Bearing in degrees (0-360)

    Returns:
        Cardinal direction string (N, NE, E, SE, S, SW, W, NW)
    """
    directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    index = round(bearing / 45) % 8
    return directions[index]


# Example usage
if __name__ == '__main__':
    # Test coordinates (Tucson, AZ)
    lat, lon = 32.2226, -110.9747

    print(f"Valid coordinates: {validate_coordinates(lat, lon)}")

    # Bounding box within 1km
    bbox = get_bounding_box(lat, lon, 1000)
    print(f"Bounding box (1km): {bbox}")

    # Distance calculation
    lat2, lon2 = 32.2526, -110.9647  # ~3.5 km away
    dist = calculate_distance(lat, lon, lat2, lon2, unit='kilometers')
    print(f"Distance: {dist:.2f} km")

    # Bearing
    bearing = calculate_bearing(lat, lon, lat2, lon2)
    print(f"Bearing: {bearing:.1f}° ({cardinal_direction(bearing)})")
