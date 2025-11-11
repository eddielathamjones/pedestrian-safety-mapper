#!/usr/bin/env python3
"""
Flask API for Tucson Pedestrian Safety Mapper
Serves GeoJSON data and statistics with filtering capabilities
"""

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import json
from pathlib import Path
from collections import defaultdict
from datetime import datetime

app = Flask(__name__, static_folder='../../src/frontend', static_url_path='')
CORS(app)  # Enable CORS for frontend

# Data paths
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "processed"
GEOJSON_FILE = DATA_DIR / "tucson_pedestrian_fatalities.geojson"
STATS_FILE = DATA_DIR / "tucson_statistics.json"

# Load data into memory (for faster access)
with open(GEOJSON_FILE, 'r') as f:
    GEOJSON_DATA = json.load(f)

with open(STATS_FILE, 'r') as f:
    STATS_DATA = json.load(f)


@app.route('/')
def index():
    """Serve the main application page"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/edgy')
def index_edgy():
    """Serve the edgy/confrontational version"""
    return send_from_directory(app.static_folder, 'index-edgy.html')


@app.route('/zine')
def zine():
    """Serve the print-ready 12-page zine"""
    return send_from_directory(app.static_folder, 'zine.html')


@app.route('/api/incidents')
def get_incidents():
    """
    Get all incidents with optional filtering
    Query params:
        - year_start: Start year (inclusive)
        - year_end: End year (inclusive)
        - road_type: Filter by functional system name
        - hour_start: Start hour (0-23)
        - hour_end: End hour (0-23)
        - lighting: Filter by lighting condition
        - intersection_type: Filter by intersection type
    """
    # Get query parameters
    year_start = request.args.get('year_start', type=int)
    year_end = request.args.get('year_end', type=int)
    road_type = request.args.get('road_type')
    hour_start = request.args.get('hour_start', type=int)
    hour_end = request.args.get('hour_end', type=int)
    lighting = request.args.get('lighting')
    intersection_type = request.args.get('intersection_type')

    # Filter features
    filtered_features = []
    for feature in GEOJSON_DATA['features']:
        props = feature['properties']

        # Year filter
        if year_start and int(props.get('YEAR', 0)) < year_start:
            continue
        if year_end and int(props.get('YEAR', 9999)) > year_end:
            continue

        # Road type filter
        if road_type and props.get('FUNC_SYSNAME') != road_type:
            continue

        # Hour filter
        try:
            hour = int(props.get('HOUR', -1))
            if hour_start is not None and hour < hour_start:
                continue
            if hour_end is not None and hour > hour_end:
                continue
        except (ValueError, TypeError):
            pass

        # Lighting filter
        if lighting and props.get('LGT_CONDNAME') != lighting:
            continue

        # Intersection type filter
        if intersection_type and props.get('TYP_INTNAME') != intersection_type:
            continue

        filtered_features.append(feature)

    return jsonify({
        "type": "FeatureCollection",
        "features": filtered_features,
        "count": len(filtered_features)
    })


@app.route('/api/statistics')
def get_statistics():
    """Get overall statistics"""
    return jsonify(STATS_DATA)


@app.route('/api/statistics/temporal')
def get_temporal_stats():
    """Get temporal statistics (by year, month, day, hour)"""
    year_counts = defaultdict(int)
    month_counts = defaultdict(int)
    day_week_counts = defaultdict(int)
    hour_counts = defaultdict(int)

    for feature in GEOJSON_DATA['features']:
        props = feature['properties']

        year = props.get('YEAR')
        month = props.get('MONTH')
        day_week = props.get('DAY_WEEK')
        hour = props.get('HOUR')

        if year:
            year_counts[year] += 1
        if month:
            month_counts[month] += 1
        if day_week:
            day_week_counts[day_week] += 1
        if hour:
            hour_counts[hour] += 1

    return jsonify({
        "by_year": dict(sorted(year_counts.items())),
        "by_month": dict(sorted(month_counts.items())),
        "by_day_of_week": dict(sorted(day_week_counts.items())),
        "by_hour": dict(sorted(hour_counts.items()))
    })


@app.route('/api/statistics/road_types')
def get_road_type_stats():
    """Get statistics by road functional class"""
    road_type_counts = defaultdict(int)
    road_type_by_year = defaultdict(lambda: defaultdict(int))

    for feature in GEOJSON_DATA['features']:
        props = feature['properties']
        road_type = props.get('FUNC_SYSNAME', 'Unknown')
        year = props.get('YEAR')

        road_type_counts[road_type] += 1
        if year:
            road_type_by_year[year][road_type] += 1

    return jsonify({
        "total_by_type": dict(road_type_counts),
        "by_year": {year: dict(types) for year, types in road_type_by_year.items()}
    })


@app.route('/api/statistics/intersections')
def get_intersection_stats():
    """Get statistics by intersection type and location"""
    intersection_counts = defaultdict(int)
    location_counts = defaultdict(int)
    intersection_lighting = defaultdict(lambda: defaultdict(int))

    for feature in GEOJSON_DATA['features']:
        props = feature['properties']

        int_type = props.get('TYP_INTNAME', 'Unknown')
        location = props.get('REL_ROADNAME', 'Unknown')
        lighting = props.get('LGT_CONDNAME', 'Unknown')

        intersection_counts[int_type] += 1
        location_counts[location] += 1
        intersection_lighting[int_type][lighting] += 1

    return jsonify({
        "by_intersection_type": dict(intersection_counts),
        "by_road_location": dict(location_counts),
        "lighting_by_intersection": {k: dict(v) for k, v in intersection_lighting.items()}
    })


@app.route('/api/statistics/lighting')
def get_lighting_stats():
    """Get statistics by lighting conditions"""
    lighting_counts = defaultdict(int)
    lighting_by_hour = defaultdict(lambda: defaultdict(int))

    for feature in GEOJSON_DATA['features']:
        props = feature['properties']
        lighting = props.get('LGT_CONDNAME', 'Unknown')
        hour = props.get('HOUR')

        lighting_counts[lighting] += 1
        if hour:
            lighting_by_hour[hour][lighting] += 1

    return jsonify({
        "by_lighting": dict(lighting_counts),
        "by_hour": {hour: dict(conditions) for hour, conditions in lighting_by_hour.items()}
    })


@app.route('/api/hot_spots')
def get_hot_spots():
    """
    Identify high-risk corridors and intersections
    Returns streets with multiple incidents
    """
    street_incidents = defaultdict(list)

    for feature in GEOJSON_DATA['features']:
        props = feature['properties']
        street = props.get('TWAY_ID', '').strip()

        if street:
            street_incidents[street].append({
                'year': props.get('YEAR'),
                'coordinates': feature['geometry']['coordinates'],
                'road_type': props.get('FUNC_SYSNAME'),
                'lighting': props.get('LGT_CONDNAME'),
                'hour': props.get('HOUR')
            })

    # Filter streets with 3+ incidents
    hot_spots = {
        street: {
            'count': len(incidents),
            'incidents': incidents
        }
        for street, incidents in street_incidents.items()
        if len(incidents) >= 3
    }

    # Sort by incident count
    sorted_hot_spots = dict(sorted(hot_spots.items(), key=lambda x: x[1]['count'], reverse=True))

    return jsonify({
        "hot_spot_count": len(sorted_hot_spots),
        "hot_spots": sorted_hot_spots
    })


@app.route('/api/trends')
def get_trends():
    """
    Calculate trends over time
    Returns year-over-year changes and moving averages
    """
    year_counts = defaultdict(int)

    for feature in GEOJSON_DATA['features']:
        year = feature['properties'].get('YEAR')
        if year:
            year_counts[year] += 1

    sorted_years = sorted(year_counts.items())

    # Calculate year-over-year change
    yoy_change = []
    for i in range(1, len(sorted_years)):
        prev_year, prev_count = sorted_years[i-1]
        curr_year, curr_count = sorted_years[i]
        change = curr_count - prev_count
        pct_change = (change / prev_count * 100) if prev_count > 0 else 0

        yoy_change.append({
            'year': curr_year,
            'count': curr_count,
            'change': change,
            'pct_change': round(pct_change, 1)
        })

    # Calculate 3-year moving average
    moving_avg = []
    years = [y for y, _ in sorted_years]
    counts = [c for _, c in sorted_years]

    for i in range(2, len(counts)):
        avg = sum(counts[i-2:i+1]) / 3
        moving_avg.append({
            'year': years[i],
            'moving_avg': round(avg, 1)
        })

    return jsonify({
        "annual_counts": dict(sorted_years),
        "year_over_year": yoy_change,
        "moving_average_3yr": moving_avg
    })


@app.route('/api/health')
def health_check():
    """API health check"""
    return jsonify({
        "status": "healthy",
        "data_loaded": len(GEOJSON_DATA['features']),
        "timestamp": datetime.now().isoformat()
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Tucson Pedestrian Safety Mapper - Backend API")
    print("=" * 60)
    print(f"Data loaded: {len(GEOJSON_DATA['features'])} incidents")
    print(f"Server starting on http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
