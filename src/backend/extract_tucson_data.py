#!/usr/bin/env python3
"""
Extract Tucson pedestrian fatality data from FARS database (1975-2022)
Filters for Pima County (Tucson area) pedestrian incidents with precise location data
"""

import csv
import json
import zipfile
import os
from pathlib import Path
from collections import defaultdict

# Configuration
STATE_CODE = "4"  # Arizona
CITY_CODE = "530"  # Tucson
COUNTY_CODE = "19"  # Pima County
START_YEAR = 1975
END_YEAR = 2022
DATA_DIR = Path(__file__).parent.parent.parent / "data" / "raw"
OUTPUT_DIR = Path(__file__).parent.parent.parent / "data" / "processed"

# Key fields to extract for visualization
FIELDS_TO_EXTRACT = [
    'STATE', 'ST_CASE', 'YEAR', 'MONTH', 'DAY', 'DAY_WEEK', 'HOUR', 'MINUTE',
    'LATITUDE', 'LONGITUD', 'TWAY_ID', 'TWAY_ID2', 'ROUTE',
    'FUNC_SYS', 'FUNC_SYSNAME', 'RUR_URB', 'RUR_URBNAME',
    'RELJCT1', 'RELJCT1NAME', 'TYP_INT', 'TYP_INTNAME',
    'REL_ROAD', 'REL_ROADNAME', 'LGT_COND', 'LGT_CONDNAME',
    'WEATHER', 'WEATHERNAME', 'HARM_EV', 'HARM_EVNAME',
    'MAN_COLL', 'MAN_COLLNAME', 'SP_JUR', 'SP_JURNAME',
    'NHS', 'NHSNAME', 'RD_OWNER', 'RD_OWNERNAME',
    'PEDS', 'FATALS', 'PERSONS', 'VE_TOTAL',
    'COUNTY', 'COUNTYNAME', 'CITY', 'CITYNAME'
]


def find_accident_csv(zip_path):
    """Find the accident CSV file in the zip archive (handles naming variations)"""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        for name in zf.namelist():
            if 'accident' in name.lower() and name.endswith(('.csv', '.CSV')):
                return name
    return None


def extract_year_data(year):
    """Extract Tucson pedestrian data for a specific year"""
    year_dir = DATA_DIR / str(year)

    # Find the main CSV zip file
    csv_zip = None
    for file in year_dir.glob("FARS*NationalCSV.zip"):
        if "Auxiliary" not in file.name and "PuertoRico" not in file.name:
            csv_zip = file
            break

    if not csv_zip or not csv_zip.exists():
        print(f"  ⚠ No CSV data found for {year}")
        return []

    try:
        with zipfile.ZipFile(csv_zip, 'r') as zf:
            accident_file = find_accident_csv(csv_zip)
            if not accident_file:
                print(f"  ⚠ No accident.csv found in {year}")
                return []

            # Read and filter data
            with zf.open(accident_file) as f:
                # Read as text, handle encoding issues
                text_data = f.read().decode('utf-8', errors='ignore')
                lines = text_data.strip().split('\n')
                reader = csv.DictReader(lines)

                incidents = []
                for row in reader:
                    # Filter for Tucson pedestrian incidents
                    state = row.get('STATE', '')
                    city = row.get('CITY', '')
                    peds = row.get('PEDS', '0')

                    # Check if this is a Tucson pedestrian incident
                    if state == STATE_CODE and city == CITY_CODE and peds and int(peds) > 0:
                        # Extract only needed fields
                        incident = {}
                        for field in FIELDS_TO_EXTRACT:
                            incident[field] = row.get(field, '')

                        # Add year if not present
                        if not incident.get('YEAR'):
                            incident['YEAR'] = str(year)

                        incidents.append(incident)

                if incidents:
                    print(f"  ✓ {year}: Found {len(incidents)} pedestrian fatalities")
                else:
                    print(f"  ○ {year}: No pedestrian fatalities")

                return incidents

    except Exception as e:
        print(f"  ✗ Error processing {year}: {e}")
        return []


def main():
    """Extract all Tucson pedestrian data and save to processed files"""
    print("=" * 60)
    print("Extracting Tucson Pedestrian Fatality Data (1975-2022)")
    print("=" * 60)

    all_incidents = []
    year_stats = {}

    # Process each year
    for year in range(START_YEAR, END_YEAR + 1):
        incidents = extract_year_data(year)
        all_incidents.extend(incidents)
        year_stats[year] = len(incidents)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Save as CSV
    csv_output = OUTPUT_DIR / "tucson_pedestrian_fatalities.csv"
    if all_incidents:
        with open(csv_output, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS_TO_EXTRACT)
            writer.writeheader()
            writer.writerows(all_incidents)
        print(f"\n✓ Saved {len(all_incidents)} incidents to {csv_output}")

    # Save as GeoJSON for mapping
    geojson_output = OUTPUT_DIR / "tucson_pedestrian_fatalities.geojson"
    features = []

    for incident in all_incidents:
        try:
            lat = float(incident.get('LATITUDE', 0))
            lon = float(incident.get('LONGITUD', 0))

            # Skip if no valid coordinates
            if lat == 0 or lon == 0:
                continue

            feature = {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [lon, lat]
                },
                "properties": incident
            }
            features.append(feature)
        except (ValueError, TypeError):
            continue

    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    with open(geojson_output, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, indent=2)

    print(f"✓ Saved {len(features)} incidents with coordinates to {geojson_output}")

    # Generate statistics
    stats_output = OUTPUT_DIR / "tucson_statistics.json"

    # Calculate additional statistics
    road_type_stats = defaultdict(int)
    intersection_stats = defaultdict(int)
    hour_stats = defaultdict(int)
    lighting_stats = defaultdict(int)

    for incident in all_incidents:
        road_type = incident.get('FUNC_SYSNAME', 'Unknown')
        intersection_type = incident.get('TYP_INTNAME', 'Unknown')
        hour = incident.get('HOUR', 'Unknown')
        lighting = incident.get('LGT_CONDNAME', 'Unknown')

        road_type_stats[road_type] += 1
        intersection_stats[intersection_type] += 1
        hour_stats[hour] += 1
        lighting_stats[lighting] += 1

    statistics = {
        "total_incidents": len(all_incidents),
        "total_with_coordinates": len(features),
        "years_covered": f"{START_YEAR}-{END_YEAR}",
        "by_year": year_stats,
        "by_road_type": dict(road_type_stats),
        "by_intersection_type": dict(intersection_stats),
        "by_hour": dict(hour_stats),
        "by_lighting_condition": dict(lighting_stats)
    }

    with open(stats_output, 'w', encoding='utf-8') as f:
        json.dump(statistics, f, indent=2)

    print(f"✓ Saved statistics to {stats_output}")

    # Print summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Total pedestrian fatalities: {len(all_incidents)}")
    print(f"Incidents with GPS coordinates: {len(features)}")
    print(f"Years with data: {sum(1 for count in year_stats.values() if count > 0)}")
    print(f"Date range: {START_YEAR}-{END_YEAR}")
    print("\nTop 5 years with most fatalities:")
    top_years = sorted(year_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    for year, count in top_years:
        if count > 0:
            print(f"  {year}: {count} fatalities")

    print("\nTop road types:")
    top_roads = sorted(road_type_stats.items(), key=lambda x: x[1], reverse=True)[:5]
    for road_type, count in top_roads:
        print(f"  {road_type}: {count} incidents")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
