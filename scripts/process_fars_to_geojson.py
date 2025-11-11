import os
import zipfile
import pandas as pd
import json
from pathlib import Path
import glob

def extract_zip_files(year_dir):
    """
    Extracts all ZIP files in the specified year directory.

    Args:
        year_dir (str): Path to the year directory containing ZIP files
    """
    zip_files = glob.glob(os.path.join(year_dir, "*.zip"))

    for zip_file in zip_files:
        extract_dir = os.path.join(year_dir, "extracted")
        os.makedirs(extract_dir, exist_ok=True)

        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"Extracted {os.path.basename(zip_file)}")
        except Exception as e:
            print(f"Error extracting {zip_file}: {e}")

def process_fars_year(year, base_dir="data/raw"):
    """
    Processes FARS data for a specific year and extracts pedestrian fatality locations.

    Args:
        year (int): Year to process
        base_dir (str): Base directory containing FARS data

    Returns:
        list: List of features for GeoJSON
    """
    year_dir = os.path.join(base_dir, str(year))
    extract_dir = os.path.join(year_dir, "extracted")

    # Extract ZIP files if not already extracted
    if not os.path.exists(extract_dir):
        print(f"Extracting files for year {year}...")
        extract_zip_files(year_dir)

    features = []

    # Look for ACCIDENT and PERSON CSV files
    accident_files = glob.glob(os.path.join(extract_dir, "*accident*.csv"), recursive=True) + \
                     glob.glob(os.path.join(extract_dir, "*ACCIDENT*.csv"), recursive=True)
    person_files = glob.glob(os.path.join(extract_dir, "*person*.csv"), recursive=True) + \
                   glob.glob(os.path.join(extract_dir, "*PERSON*.csv"), recursive=True)

    if not accident_files or not person_files:
        print(f"Could not find required CSV files for year {year}")
        return features

    try:
        # Read accident data (contains location information)
        accident_df = pd.read_csv(accident_files[0], encoding='latin-1', low_memory=False)

        # Read person data (contains pedestrian information)
        person_df = pd.read_csv(person_files[0], encoding='latin-1', low_memory=False)

        # Standardize column names to uppercase
        accident_df.columns = accident_df.columns.str.upper()
        person_df.columns = person_df.columns.str.upper()

        # Filter for pedestrians (PER_TYP = 5 typically indicates pedestrian)
        pedestrians = person_df[person_df['PER_TYP'] == 5]

        # Merge with accident data to get location information
        merged = pedestrians.merge(accident_df, on='ST_CASE', how='left')

        # Extract coordinates (column names vary by year, try different options)
        lat_cols = ['LATITUDE', 'LAT', 'LATITUD']
        lon_cols = ['LONGITUD', 'LONG', 'LONGITUDE']

        lat_col = None
        lon_col = None

        for col in lat_cols:
            if col in merged.columns:
                lat_col = col
                break

        for col in lon_cols:
            if col in merged.columns:
                lon_col = col
                break

        if lat_col and lon_col:
            # Filter out invalid coordinates
            valid_coords = merged[
                (merged[lat_col].notna()) &
                (merged[lon_col].notna()) &
                (merged[lat_col] != 0) &
                (merged[lon_col] != 0) &
                (merged[lat_col] >= -90) &
                (merged[lat_col] <= 90) &
                (merged[lon_col] >= -180) &
                (merged[lon_col] <= 180)
            ]

            # Create GeoJSON features
            for _, row in valid_coords.iterrows():
                # FARS stores coordinates in DDMMSS format, convert to decimal degrees
                lat = row[lat_col]
                lon = row[lon_col]

                # Convert from DDMMSS to decimal degrees if needed
                if abs(lat) > 90:  # Likely in DDMMSS format
                    lat = convert_ddmmss_to_decimal(lat)
                if abs(lon) > 180:  # Likely in DDMMSS format
                    lon = convert_ddmmss_to_decimal(lon)

                # Ensure longitude is negative for US coordinates
                if lon > 0:
                    lon = -lon

                feature = {
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lon, lat]
                    },
                    "properties": {
                        "year": year,
                        "state": int(row.get('STATE', 0)),
                        "case": int(row.get('ST_CASE', 0)),
                        "county": int(row.get('COUNTY', 0)) if 'COUNTY' in row else None,
                        "age": int(row.get('AGE', 0)) if 'AGE' in row else None,
                        "sex": int(row.get('SEX', 0)) if 'SEX' in row else None,
                        "injury_severity": int(row.get('INJ_SEV', 0)) if 'INJ_SEV' in row else None
                    }
                }
                features.append(feature)

        print(f"Processed {len(features)} pedestrian fatalities for year {year}")

    except Exception as e:
        print(f"Error processing year {year}: {e}")

    return features

def convert_ddmmss_to_decimal(ddmmss):
    """
    Converts coordinates from DDMMSS format to decimal degrees.

    Args:
        ddmmss (float): Coordinate in DDMMSS format

    Returns:
        float: Coordinate in decimal degrees
    """
    try:
        ddmmss_str = str(int(ddmmss)).zfill(6)
        degrees = int(ddmmss_str[:-4])
        minutes = int(ddmmss_str[-4:-2])
        seconds = int(ddmmss_str[-2:])

        decimal = degrees + minutes/60 + seconds/3600
        return decimal
    except:
        return ddmmss

def create_geojson(years, output_file="data/pedestrian_fatalities.geojson", base_dir="data/raw"):
    """
    Creates a GeoJSON file from FARS data for multiple years.

    Args:
        years (list): List of years to process
        output_file (str): Path to output GeoJSON file
        base_dir (str): Base directory containing FARS data
    """
    all_features = []

    for year in years:
        print(f"\nProcessing year {year}...")
        features = process_fars_year(year, base_dir)
        all_features.extend(features)

    # Create GeoJSON structure
    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    # Write to file
    with open(output_file, 'w') as f:
        json.dump(geojson, f, indent=2)

    print(f"\nCreated GeoJSON with {len(all_features)} features")
    print(f"Output saved to: {output_file}")

if __name__ == "__main__":
    # Process available years
    # Start with a few recent years for testing
    years_to_process = [2020, 2005, 1987]

    # Create GeoJSON
    create_geojson(years_to_process)
