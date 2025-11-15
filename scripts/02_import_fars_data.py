#!/usr/bin/env python3
"""
FARS Data Import Script

Import FARS crash data into the database.

This script:
1. Reads FARS CSV/SAS files from data/raw/
2. Filters to pedestrian crashes
3. Extracts coordinates and crash details
4. Validates and cleans data
5. Inserts into crashes table

Usage:
    python scripts/02_import_fars_data.py --year 2022 --state AZ

    # Import all years for a state
    python scripts/02_import_fars_data.py --state AZ --all-years

    # Import from specific file
    python scripts/02_import_fars_data.py --file data/raw/2022/accidents.csv

    # Dry run (validate without inserting)
    python scripts/02_import_fars_data.py --year 2022 --dry-run
"""

import sys
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import csv

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pandas as pd
import numpy as np
from loguru import logger
from tqdm import tqdm

from src.database import Database
from src.utils.validation import validate_crash_data, DataQualityChecker
from src.utils.geo_utils import validate_coordinates
from src.utils.time_utils import parse_crash_datetime, classify_time_of_day, get_sunrise_sunset


class FARSImporter:
    """Import FARS data into database"""

    def __init__(self, db: Database, dry_run: bool = False):
        """
        Initialize importer

        Args:
            db: Database connection
            dry_run: If True, validate but don't insert
        """
        self.db = db
        self.dry_run = dry_run
        self.quality_checker = DataQualityChecker()

        # Statistics
        self.stats = {
            'total_rows': 0,
            'pedestrian_crashes': 0,
            'valid_crashes': 0,
            'invalid_crashes': 0,
            'inserted': 0,
            'skipped': 0,
            'errors': 0
        }

    def read_fars_file(self, file_path: Path) -> pd.DataFrame:
        """
        Read FARS data file (CSV or SAS)

        Args:
            file_path: Path to FARS file

        Returns:
            DataFrame with crash data
        """
        logger.info(f"Reading FARS file: {file_path}")

        if file_path.suffix.lower() == '.csv':
            # Read CSV
            df = pd.read_csv(file_path, low_memory=False)
        elif file_path.suffix.lower() in ['.sas7bdat', '.xpt']:
            # Read SAS
            df = pd.read_sas(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        logger.info(f"Read {len(df):,} rows from {file_path.name}")
        self.stats['total_rows'] += len(df)

        return df

    def filter_pedestrian_crashes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Filter to pedestrian-involved crashes

        FARS coding:
        - PERSON_TYPE == 5 (pedestrian) or 6 (pedalcyclist)
        - Or use HARM_EV (harmful event) codes

        Args:
            df: Full FARS DataFrame

        Returns:
            Filtered DataFrame with pedestrian crashes
        """
        # This is simplified - actual FARS filtering depends on file structure
        # FARS has multiple files: ACCIDENT, PERSON, VEHICLE, etc.

        # Check which columns are available
        if 'PERSON_TYPE' in df.columns:
            # Filter to pedestrian victims
            ped_df = df[df['PERSON_TYPE'] == 5].copy()
        elif 'HARM_EV' in df.columns:
            # Filter by harmful event (pedestrian involved)
            ped_df = df[df['HARM_EV'].isin([8, 9])].copy()  # 8=pedestrian, 9=pedalcyclist
        else:
            logger.warning("Cannot filter pedestrians - unknown FARS format")
            ped_df = df.copy()

        logger.info(f"Filtered to {len(ped_df):,} pedestrian-involved crashes")
        self.stats['pedestrian_crashes'] += len(ped_df)

        return ped_df

    def extract_crash_data(self, row: pd.Series, year: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """
        Extract crash data from FARS row

        Args:
            row: FARS data row
            year: Year of crash (if not in row)

        Returns:
            Dictionary with crash data, or None if invalid
        """
        try:
            # FARS column names vary by year - this is a generic mapping
            # You'll need to adjust based on actual FARS data structure

            # Extract coordinates
            # FARS uses different column names over the years:
            # Old: LATITUDE, LONGITUD
            # New: LAT, LONG
            lat = None
            lon = None

            for lat_col in ['LATITUDE', 'LAT', 'TWAY_LAT']:
                if lat_col in row.index and pd.notna(row[lat_col]):
                    lat = float(row[lat_col])
                    break

            for lon_col in ['LONGITUD', 'LONG', 'LONGITUDE', 'TWAY_LONG']:
                if lon_col in row.index and pd.notna(row[lon_col]):
                    lon = float(row[lon_col])
                    break

            # FARS sometimes stores coords as integers (scaled)
            # e.g., 32.2226 stored as 322226
            if lat and abs(lat) > 180:
                lat = lat / 10000.0
            if lon and abs(lon) > 180:
                lon = lon / 10000.0

            # Validate coordinates
            if not lat or not lon or not validate_coordinates(lat, lon):
                return None

            # Generate crash ID
            crash_year = year or row.get('YEAR', 'XXXX')
            state = row.get('STATE', row.get('STATENAME', 'XX'))
            case_num = row.get('ST_CASE', row.get('CASENUM', '0'))
            crash_id = f"{state}-{crash_year}-{case_num}"

            # Extract date/time
            crash_date = None
            crash_time = None

            if 'YEAR' in row.index and 'MONTH' in row.index and 'DAY' in row.index:
                year_val = int(row['YEAR']) if pd.notna(row['YEAR']) else crash_year
                month_val = int(row['MONTH']) if pd.notna(row['MONTH']) else 1
                day_val = int(row['DAY']) if pd.notna(row['DAY']) else 1

                try:
                    crash_date = f"{year_val}-{month_val:02d}-{day_val:02d}"
                except:
                    pass

            if 'HOUR' in row.index and 'MINUTE' in row.index:
                hour_val = int(row['HOUR']) if pd.notna(row['HOUR']) else 0
                minute_val = int(row['MINUTE']) if pd.notna(row['MINUTE']) else 0

                if 0 <= hour_val < 24:
                    crash_time = f"{hour_val:02d}:{minute_val:02d}:00"

            # Parse datetime
            crash_datetime = parse_crash_datetime(crash_date, crash_time)

            # Classify time of day
            time_of_day = None
            if crash_datetime and lat and lon:
                try:
                    sunrise, sunset = get_sunrise_sunset(lat, lon, crash_datetime.date())
                    time_of_day = classify_time_of_day(
                        crash_datetime.time(),
                        sunrise,
                        sunset
                    )
                except:
                    pass

            # Build crash dict
            crash_data = {
                'crash_id': crash_id,
                'state': str(state)[:2] if state else None,
                'county': row.get('COUNTY', row.get('COUNTYNAME')),
                'city': row.get('CITY', row.get('CITYNAME')),

                # Location
                'latitude': lat,
                'longitude': lon,

                # Temporal
                'crash_date': crash_date,
                'crash_time': crash_time,
                'crash_datetime': crash_datetime,
                'time_of_day': time_of_day,

                # Victim (if available)
                'victim_age': int(row['AGE']) if 'AGE' in row.index and pd.notna(row['AGE']) else None,
                'victim_gender': row.get('SEX'),

                # Crash characteristics
                'severity': 'Fatal',  # FARS only includes fatal crashes
                'vehicle_speed': int(row['TRAV_SP']) if 'TRAV_SP' in row.index and pd.notna(row['TRAV_SP']) else None,

                # Metadata
                'data_complete': False,
                'notes': f"Imported from FARS {crash_year}"
            }

            return crash_data

        except Exception as e:
            logger.error(f"Error extracting crash data: {e}")
            return None

    def validate_and_insert(self, crash_data: Dict[str, Any]) -> bool:
        """
        Validate crash data and insert into database

        Args:
            crash_data: Crash data dictionary

        Returns:
            True if inserted successfully, False otherwise
        """
        # Validate data
        quality = self.quality_checker.check_crash(crash_data)

        if not quality['is_valid']:
            self.stats['invalid_crashes'] += 1
            logger.warning(f"Invalid crash {crash_data['crash_id']}: {quality['issues']}")
            return False

        self.stats['valid_crashes'] += 1

        # Skip if completeness too low
        if quality['completeness_score'] < 50:
            self.stats['skipped'] += 1
            logger.debug(f"Skipping {crash_data['crash_id']} - low completeness ({quality['completeness_score']}%)")
            return False

        # Insert into database
        if not self.dry_run:
            try:
                with self.db.get_connection() as conn:
                    cursor = conn.cursor()

                    # Insert crash
                    cursor.execute("""
                        INSERT INTO crashes (
                            crash_id, state, county, city,
                            latitude, longitude,
                            crash_date, crash_time, crash_datetime, time_of_day,
                            victim_age, victim_gender,
                            severity, vehicle_speed,
                            data_complete, notes
                        ) VALUES (
                            %s, %s, %s, %s,
                            %s, %s,
                            %s, %s, %s, %s,
                            %s, %s,
                            %s, %s,
                            %s, %s
                        )
                        ON CONFLICT (crash_id) DO NOTHING
                    """, (
                        crash_data['crash_id'],
                        crash_data['state'],
                        crash_data['county'],
                        crash_data['city'],
                        crash_data['latitude'],
                        crash_data['longitude'],
                        crash_data['crash_date'],
                        crash_data['crash_time'],
                        crash_data['crash_datetime'],
                        crash_data['time_of_day'],
                        crash_data['victim_age'],
                        crash_data['victim_gender'],
                        crash_data['severity'],
                        crash_data['vehicle_speed'],
                        crash_data['data_complete'],
                        crash_data['notes']
                    ))

                    cursor.close()

                self.stats['inserted'] += 1
                return True

            except Exception as e:
                self.stats['errors'] += 1
                logger.error(f"Error inserting crash {crash_data['crash_id']}: {e}")
                return False
        else:
            # Dry run - just count as inserted
            self.stats['inserted'] += 1
            return True

    def import_file(self, file_path: Path, year: Optional[int] = None, state_filter: Optional[str] = None):
        """
        Import FARS data from file

        Args:
            file_path: Path to FARS file
            year: Year of data
            state_filter: Only import crashes from this state (e.g., 'AZ')
        """
        # Read file
        df = self.read_fars_file(file_path)

        # Filter to pedestrians
        df = self.filter_pedestrian_crashes(df)

        # Filter by state if specified
        if state_filter:
            if 'STATE' in df.columns:
                df = df[df['STATE'] == state_filter]
            elif 'STATENAME' in df.columns:
                df = df[df['STATENAME'].str.upper() == state_filter.upper()]

            logger.info(f"Filtered to {len(df):,} crashes in {state_filter}")

        # Process each row
        logger.info(f"Processing {len(df):,} crashes...")

        for idx, row in tqdm(df.iterrows(), total=len(df), desc="Importing crashes"):
            crash_data = self.extract_crash_data(row, year=year)

            if crash_data:
                self.validate_and_insert(crash_data)

    def print_stats(self):
        """Print import statistics"""
        print("\n" + "=" * 60)
        print("IMPORT STATISTICS")
        print("=" * 60)
        print(f"Total rows read:           {self.stats['total_rows']:,}")
        print(f"Pedestrian crashes:        {self.stats['pedestrian_crashes']:,}")
        print(f"Valid crashes:             {self.stats['valid_crashes']:,}")
        print(f"Invalid crashes:           {self.stats['invalid_crashes']:,}")
        print(f"Skipped (low quality):     {self.stats['skipped']:,}")
        print(f"Successfully inserted:     {self.stats['inserted']:,}")
        print(f"Errors:                    {self.stats['errors']:,}")
        print("=" * 60)

        if self.stats['valid_crashes'] > 0:
            success_rate = (self.stats['inserted'] / self.stats['valid_crashes']) * 100
            print(f"Success rate: {success_rate:.1f}%")


def main():
    """Main import function"""
    parser = argparse.ArgumentParser(
        description='Import FARS data into database'
    )
    parser.add_argument(
        '--year',
        type=int,
        help='Year of FARS data to import'
    )
    parser.add_argument(
        '--state',
        type=str,
        help='Filter to specific state (e.g., AZ, CA)'
    )
    parser.add_argument(
        '--file',
        type=str,
        help='Specific FARS file to import'
    )
    parser.add_argument(
        '--all-years',
        action='store_true',
        help='Import all available years for specified state'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate data without inserting into database'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of crashes to import (for testing)'
    )

    args = parser.parse_args()

    # Setup logging
    logger.add(
        project_root / 'logs' / 'fars_import.log',
        rotation="10 MB",
        level="DEBUG"
    )

    logger.info("=" * 60)
    logger.info("FARS Data Import")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("DRY RUN MODE - No data will be inserted")

    # Connect to database
    try:
        db = Database()
        if not args.dry_run and not db.test_connection():
            logger.error("Database connection failed")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    # Create importer
    importer = FARSImporter(db, dry_run=args.dry_run)

    # Determine files to import
    if args.file:
        # Import specific file
        file_path = Path(args.file)
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            sys.exit(1)

        importer.import_file(file_path, year=args.year, state_filter=args.state)

    elif args.year:
        # Import specific year
        year_dir = project_root / 'data' / 'raw' / str(args.year)
        if not year_dir.exists():
            logger.error(f"Year directory not found: {year_dir}")
            sys.exit(1)

        # Find FARS files
        files = list(year_dir.glob("*ACCIDENT*.CSV")) + list(year_dir.glob("*PERSON*.CSV"))
        if not files:
            logger.error(f"No FARS files found in {year_dir}")
            sys.exit(1)

        for file_path in files:
            importer.import_file(file_path, year=args.year, state_filter=args.state)

    else:
        logger.error("Must specify --year or --file")
        sys.exit(1)

    # Print statistics
    importer.print_stats()

    # Close database
    db.close()

    logger.info("Import complete!")


if __name__ == '__main__':
    # Ensure logs directory exists
    (project_root / 'logs').mkdir(exist_ok=True)
    main()
