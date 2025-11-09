"""
Data ingestion pipeline for FARS data into DuckDB.

This script extracts, transforms, and loads FARS CSV data from ZIP files
into the DuckDB database.

Usage:
    # Ingest single year
    python -m src.database.ingest_data --year 2022

    # Ingest range of years
    python -m src.database.ingest_data --start-year 2020 --end-year 2022

    # Ingest all available years
    python -m src.database.ingest_data --all

    # Custom database path
    python -m src.database.ingest_data --year 2022 --db-path custom/db.duckdb
"""

import argparse
import duckdb
import pandas as pd
from pathlib import Path
import zipfile
import tempfile
import shutil
from typing import Optional, List, Tuple
from tqdm import tqdm
import sys
from datetime import datetime


class FARSIngester:
    """Handles ingestion of FARS data into DuckDB."""

    def __init__(self, db_path: str = "data/pedestrian_safety.duckdb"):
        """
        Initialize the ingester.

        Args:
            db_path: Path to DuckDB database file
        """
        self.db_path = db_path
        self.con = None
        self.stats = {
            'crashes_inserted': 0,
            'persons_inserted': 0,
            'pedestrian_details_inserted': 0,
            'nm_factors_inserted': 0,
            'vehicles_inserted': 0,
            'environment_inserted': 0,
            'errors': []
        }

    def connect(self):
        """Connect to the database."""
        if not Path(self.db_path).exists():
            raise FileNotFoundError(
                f"Database not found at {self.db_path}. "
                "Run 'python -m src.database.init_db' first."
            )
        self.con = duckdb.connect(self.db_path)
        try:
            self.con.execute("LOAD spatial;")
        except Exception:
            pass  # Spatial extension not available, continue anyway

    def close(self):
        """Close database connection."""
        if self.con:
            self.con.close()

    def find_data_files(self, year: int, region: str = "National") -> Optional[Path]:
        """
        Find the CSV ZIP file for a given year and region.

        Args:
            year: Year to search for
            region: Region (National or PuertoRico)

        Returns:
            Path to ZIP file or None if not found
        """
        data_dir = Path("data/raw") / str(year)
        if not data_dir.exists():
            return None

        # Look for CSV format
        pattern = f"FARS{year}{region}CSV.zip"
        zip_files = list(data_dir.glob(pattern))

        if zip_files:
            return zip_files[0]

        return None

    def extract_zip(self, zip_path: Path, temp_dir: Path) -> Path:
        """
        Extract ZIP file to temporary directory.

        Args:
            zip_path: Path to ZIP file
            temp_dir: Temporary directory for extraction

        Returns:
            Path to extracted CSV directory
        """
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Find the extracted directory
        extracted_dirs = [d for d in temp_dir.iterdir() if d.is_dir()]
        if extracted_dirs:
            return extracted_dirs[0]

        return temp_dir

    def create_crash_id(self, row: pd.Series) -> str:
        """Create unique crash ID."""
        return f"{row['YEAR']}_{row['STATE']:02d}_{row['ST_CASE']}"

    def create_person_id(self, row: pd.Series, crash_id: str) -> str:
        """Create unique person ID."""
        veh_no = row.get('VEH_NO', 0)
        per_no = row.get('PER_NO', 1)
        return f"{crash_id}_{veh_no}_{per_no}"

    def create_vehicle_id(self, row: pd.Series, crash_id: str) -> str:
        """Create unique vehicle ID."""
        veh_no = row.get('VEH_NO', 1)
        return f"{crash_id}_{veh_no}"

    def safe_int(self, value, default=None):
        """Safely convert value to int."""
        try:
            if pd.isna(value):
                return default
            return int(value)
        except (ValueError, TypeError):
            return default

    def safe_float(self, value, default=None):
        """Safely convert value to float."""
        try:
            if pd.isna(value):
                return default
            return float(value)
        except (ValueError, TypeError):
            return default

    def safe_bool(self, value, true_values=[1, '1', 'Yes', 'True']):
        """Safely convert value to boolean."""
        if pd.isna(value):
            return False
        return value in true_values

    def ingest_crashes(self, csv_dir: Path, year: int) -> int:
        """
        Ingest crash-level data.

        Args:
            csv_dir: Directory containing CSV files
            year: Year of data

        Returns:
            Number of records inserted
        """
        accident_file = csv_dir / "accident.csv"
        if not accident_file.exists():
            # Try uppercase
            accident_file = csv_dir / "ACCIDENT.CSV"

        if not accident_file.exists():
            raise FileNotFoundError(f"accident.csv not found in {csv_dir}")

        print(f"  📁 Reading accident.csv...")
        df = pd.read_csv(accident_file, encoding='latin-1', low_memory=False)

        print(f"  🔄 Processing {len(df)} crash records...")

        # Create crash_id
        df['crash_id'] = df.apply(lambda row: self.create_crash_id(row), axis=1)

        # Create crash_date and datetime
        df['crash_date'] = pd.to_datetime(
            df[['YEAR', 'MONTH', 'DAY']].rename(columns={'YEAR': 'year', 'MONTH': 'month', 'DAY': 'day'}),
            errors='coerce'
        )

        # Count pedestrian fatalities (will be updated from person records)
        df['pedestrian_fatalities'] = df.get('PEDS', 0)

        # Prepare data for insertion
        crashes_data = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="  Processing crashes"):
            crash = {
                'crash_id': row['crash_id'],
                'state': self.safe_int(row.get('STATE')),
                'state_name': row.get('STATENAME', ''),
                'st_case': self.safe_int(row.get('ST_CASE')),
                'year': year,
                'crash_date': row['crash_date'],
                'crash_datetime': None,  # Will be computed if needed
                'month': self.safe_int(row.get('MONTH')),
                'month_name': row.get('MONTHNAME', ''),
                'day': self.safe_int(row.get('DAY')),
                'day_name': row.get('DAYNAME', ''),
                'day_of_week': self.safe_int(row.get('DAY_WEEK')),
                'hour': self.safe_int(row.get('HOUR')),
                'minute': self.safe_int(row.get('MINUTE')),
                'latitude': self.safe_float(row.get('LATITUDE')),
                'longitude': self.safe_float(row.get('LONGITUD')),
                'county': self.safe_int(row.get('COUNTY')),
                'county_name': row.get('COUNTYNAME', ''),
                'city': self.safe_int(row.get('CITY')),
                'city_name': row.get('CITYNAME', ''),
                'rural_urban': self.safe_int(row.get('RUR_URB')),
                'rural_urban_name': row.get('RUR_URBNAME', ''),
                'route_type': self.safe_int(row.get('ROUTE')),
                'route_name': row.get('ROUTENAME', ''),
                'functional_system': self.safe_int(row.get('FUNC_SYS')),
                'functional_system_name': row.get('FUNC_SYSNAME', ''),
                'road_owner': self.safe_int(row.get('RD_OWNER')),
                'road_owner_name': row.get('RD_OWNERNAME', ''),
                'national_highway_system': self.safe_bool(row.get('NHS'), [1, '1']),
                'manner_of_collision': self.safe_int(row.get('MAN_COLL')),
                'manner_of_collision_name': row.get('MAN_COLLNAME', ''),
                'first_harmful_event': self.safe_int(row.get('HARM_EV')),
                'first_harmful_event_name': row.get('HARM_EVNAME', ''),
                'relation_to_junction': self.safe_int(row.get('RELJCT1')),
                'relation_to_junction_name': row.get('RELJCT1NAME', ''),
                'intersection_type': self.safe_int(row.get('TYP_INT')),
                'intersection_type_name': row.get('TYP_INTNAME', ''),
                'relation_to_roadway': self.safe_int(row.get('REL_ROAD')),
                'relation_to_roadway_name': row.get('REL_ROADNAME', ''),
                'work_zone': self.safe_int(row.get('WRK_ZONE')),
                'work_zone_name': row.get('WRK_ZONENAME', ''),
                'light_condition': self.safe_int(row.get('LGT_COND')),
                'light_condition_name': row.get('LGT_CONDNAME', ''),
                'weather': self.safe_int(row.get('WEATHER')),
                'weather_name': row.get('WEATHERNAME', ''),
                'school_bus_related': self.safe_bool(row.get('SCH_BUS'), [1, '1']),
                'rail_crossing': row.get('RAIL', ''),
                'notification_hour': self.safe_int(row.get('NOT_HOUR')),
                'notification_minute': self.safe_int(row.get('NOT_MIN')),
                'arrival_hour': self.safe_int(row.get('ARR_HOUR')),
                'arrival_minute': self.safe_int(row.get('ARR_MIN')),
                'hospital_arrival_hour': self.safe_int(row.get('HOSP_HR')),
                'hospital_arrival_minute': self.safe_int(row.get('HOSP_MN')),
                'total_fatalities': self.safe_int(row.get('FATALS'), 0),
                'pedestrian_fatalities': self.safe_int(row.get('PEDS'), 0),
                'total_vehicles': self.safe_int(row.get('VE_TOTAL'), 0),
                'total_persons': self.safe_int(row.get('PERSONS'), 0),
                'data_source': f"FARS{year}NationalCSV"
            }
            crashes_data.append(crash)

        # Insert into database
        print(f"  💾 Inserting {len(crashes_data)} crash records...")
        crashes_df = pd.DataFrame(crashes_data)

        # Insert data into database
        self.con.execute("BEGIN TRANSACTION;")
        try:
            # Add missing columns with defaults
            crashes_df['geom'] = None
            crashes_df['ingestion_timestamp'] = None  # Will use database DEFAULT

            # Ensure column order matches table definition
            column_order = [
                'crash_id', 'state', 'state_name', 'st_case', 'year',
                'crash_date', 'crash_datetime', 'month', 'month_name', 'day', 'day_name', 'day_of_week',
                'hour', 'minute', 'latitude', 'longitude', 'geom',
                'county', 'county_name', 'city', 'city_name',
                'rural_urban', 'rural_urban_name',
                'route_type', 'route_name',
                'functional_system', 'functional_system_name',
                'road_owner', 'road_owner_name', 'national_highway_system',
                'manner_of_collision', 'manner_of_collision_name',
                'first_harmful_event', 'first_harmful_event_name',
                'relation_to_junction', 'relation_to_junction_name',
                'intersection_type', 'intersection_type_name',
                'relation_to_roadway', 'relation_to_roadway_name',
                'work_zone', 'work_zone_name',
                'light_condition', 'light_condition_name',
                'weather', 'weather_name',
                'school_bus_related', 'rail_crossing',
                'notification_hour', 'notification_minute',
                'arrival_hour', 'arrival_minute',
                'hospital_arrival_hour', 'hospital_arrival_minute',
                'total_fatalities', 'pedestrian_fatalities', 'total_vehicles', 'total_persons',
                'ingestion_timestamp', 'data_source'
            ]
            crashes_df = crashes_df[column_order]

            self.con.execute("""
                INSERT INTO crashes
                SELECT * FROM crashes_df
            """)

            # Update geometry for records with valid coordinates (if spatial extension available)
            try:
                self.con.execute("""
                    UPDATE crashes
                    SET geom = CAST(ST_AsText(ST_Point(longitude, latitude)) AS VARCHAR)
                    WHERE latitude IS NOT NULL
                      AND longitude IS NOT NULL
                      AND latitude BETWEEN -90 AND 90
                      AND longitude BETWEEN -180 AND 180
                      AND year = ?
                """, [year])
            except Exception:
                print("  ⚠️  Skipping geometry creation (spatial extension not available)")

            self.con.execute("COMMIT;")
            print(f"  ✅ Inserted {len(crashes_data)} crash records")
        except Exception as e:
            self.con.execute("ROLLBACK;")
            raise e

        self.stats['crashes_inserted'] += len(crashes_data)
        return len(crashes_data)

    def ingest_persons(self, csv_dir: Path, year: int) -> int:
        """Ingest person-level data."""
        person_files = [
            csv_dir / "person.csv",
            csv_dir / "PERSON.CSV",
            csv_dir / "MIPER.CSV"  # Michigan format for older years
        ]

        person_file = None
        for pf in person_files:
            if pf.exists():
                person_file = pf
                break

        if not person_file:
            print(f"  ⚠️  Warning: No person file found, skipping persons")
            return 0

        print(f"  📁 Reading {person_file.name}...")
        df = pd.read_csv(person_file, encoding='latin-1', low_memory=False)

        print(f"  🔄 Processing {len(df)} person records...")

        persons_data = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="  Processing persons"):
            crash_id = f"{year}_{row['STATE']:02d}_{row['ST_CASE']}"
            person_id = self.create_person_id(row, crash_id)

            person_type = self.safe_int(row.get('PER_TYP'))
            is_pedestrian = person_type == 5
            is_bicyclist = person_type == 6
            is_non_motorist = self.safe_int(row.get('VEH_NO')) == 0

            injury_severity = self.safe_int(row.get('INJ_SEV'))
            is_fatal = injury_severity == 4

            person = {
                'person_id': person_id,
                'crash_id': crash_id,
                'state': self.safe_int(row.get('STATE')),
                'st_case': self.safe_int(row.get('ST_CASE')),
                'vehicle_number': self.safe_int(row.get('VEH_NO')),
                'person_number': self.safe_int(row.get('PER_NO')),
                'year': year,
                'person_type': person_type,
                'person_type_name': row.get('PER_TYPNAME', ''),
                'is_pedestrian': is_pedestrian,
                'is_bicyclist': is_bicyclist,
                'is_non_motorist': is_non_motorist,
                'age': self.safe_int(row.get('AGE')),
                'age_name': row.get('AGENAME', ''),
                'sex': self.safe_int(row.get('SEX')),
                'sex_name': row.get('SEXNAME', ''),
                'hispanic_origin': self.safe_int(row.get('HISPANIC')),
                'race': self.safe_int(row.get('RACE')),
                'injury_severity': injury_severity,
                'injury_severity_name': row.get('INJ_SEVNAME', ''),
                'is_fatal': is_fatal,
                'death_date': None,  # Could be computed from DEATH_DA, DEATH_MO, DEATH_YR
                'death_time': None,  # Could be computed from DEATH_HR, DEATH_MN
                'hours_to_death': self.safe_int(row.get('LAG_HRS')),
                'minutes_to_death': self.safe_int(row.get('LAG_MINS')),
                'died_at_scene': self.safe_bool(row.get('DOA'), [1, '1']),
                'transported_by': self.safe_int(row.get('HOSPITAL')),
                'transported_by_name': row.get('HOSPITALNAME', ''),
                'ems_arrival_time': None,  # Could be computed from ARR_HOUR, ARR_MIN
                'hospital_arrival_time': None,  # Could be computed from HOSP_HR, HOSP_MN
                'seating_position': self.safe_int(row.get('SEAT_POS')),
                'seating_position_name': row.get('SEAT_POSNAME', ''),
                'restraint_system_use': self.safe_int(row.get('REST_USE')),
                'restraint_system_use_name': row.get('REST_USENAME', ''),
                'restraint_misuse': self.safe_int(row.get('REST_MIS')),
                'helmet_use': self.safe_int(row.get('HELM_USE')),
                'airbag_deployment': self.safe_int(row.get('AIR_BAG')),
                'airbag_deployment_name': row.get('AIR_BAGNAME', ''),
                'ejection': self.safe_int(row.get('EJECTION')),
                'ejection_name': row.get('EJECTIONNAME', ''),
                'drinking': self.safe_bool(row.get('DRINKING'), [1, '1']),
                'alcohol_test_result': self.safe_float(row.get('ALC_RES')) if self.safe_float(row.get('ALC_RES'), 0) < 10 else None,  # Filter out special codes (e.g., 996 = Test Not Given)
                'drug_involvement': self.safe_bool(row.get('DRUGS'), [1, '1']),
                'work_related_injury': self.safe_bool(row.get('WORK_INJ'), [1, '1'])
            }
            persons_data.append(person)

        # Insert into database
        print(f"  💾 Inserting {len(persons_data)} person records...")
        persons_df = pd.DataFrame(persons_data)

        # Add ingestion_timestamp
        persons_df['ingestion_timestamp'] = None

        # Ensure column order matches table definition
        column_order = [
            'person_id', 'crash_id', 'state', 'st_case', 'vehicle_number', 'person_number', 'year',
            'person_type', 'person_type_name', 'is_pedestrian', 'is_bicyclist', 'is_non_motorist',
            'age', 'age_name', 'sex', 'sex_name', 'hispanic_origin', 'race',
            'injury_severity', 'injury_severity_name', 'is_fatal',
            'death_date', 'death_time', 'hours_to_death', 'minutes_to_death', 'died_at_scene',
            'transported_by', 'transported_by_name', 'ems_arrival_time', 'hospital_arrival_time',
            'seating_position', 'seating_position_name',
            'restraint_system_use', 'restraint_system_use_name', 'restraint_misuse',
            'helmet_use', 'airbag_deployment', 'airbag_deployment_name',
            'ejection', 'ejection_name',
            'drinking', 'alcohol_test_result', 'drug_involvement',
            'work_related_injury', 'ingestion_timestamp'
        ]
        persons_df = persons_df[column_order]

        self.con.execute("INSERT INTO persons SELECT * FROM persons_df")

        print(f"  ✅ Inserted {len(persons_data)} person records")
        self.stats['persons_inserted'] += len(persons_data)
        return len(persons_data)

    def ingest_pedestrian_details(self, csv_dir: Path, year: int) -> int:
        """Ingest pedestrian-specific details from pbtype table."""
        pbtype_file = csv_dir / "pbtype.csv"
        if not pbtype_file.exists():
            pbtype_file = csv_dir / "PBTYPE.CSV"

        if not pbtype_file.exists():
            print(f"  ⚠️  Warning: No pbtype file found, skipping pedestrian details")
            return 0

        print(f"  📁 Reading pbtype.csv...")
        df = pd.read_csv(pbtype_file, encoding='latin-1', low_memory=False)

        print(f"  🔄 Processing {len(df)} pedestrian detail records...")

        ped_data = []
        for _, row in tqdm(df.iterrows(), total=len(df), desc="  Processing ped details"):
            crash_id = f"{year}_{row['STATE']:02d}_{row['ST_CASE']}"
            veh_no = self.safe_int(row.get('VEH_NO'), 0)
            per_no = self.safe_int(row.get('PER_NO'), 1)
            person_id = f"{crash_id}_{veh_no}_{per_no}"

            ped_detail = {
                'ped_detail_id': person_id,
                'person_id': person_id,
                'crash_id': crash_id,
                'state': self.safe_int(row.get('STATE')),
                'st_case': self.safe_int(row.get('ST_CASE')),
                'year': year,
                'age': self.safe_int(row.get('PBAGE')),
                'sex': self.safe_int(row.get('PBSEX')),
                'sex_name': row.get('PBSEXNAME', ''),
                'person_type': self.safe_int(row.get('PBPTYPE')),
                'person_type_name': row.get('PBPTYPENAME', ''),
                'crosswalk_present': self.safe_bool(row.get('PBCWALK')),
                'pedestrian_in_crosswalk': self.safe_bool(row.get('PBSWALK')),
                'school_zone': self.safe_bool(row.get('PBSZONE')),
                'pedestrian_crash_type': self.safe_int(row.get('PEDCTYPE')),
                'pedestrian_crash_type_name': row.get('PEDCTYPENAME', ''),
                'bicyclist_crash_type': self.safe_int(row.get('BIKECTYPE')),
                'bicyclist_crash_type_name': row.get('BIKECTYPENAME', ''),
                'pedestrian_location': self.safe_int(row.get('PEDLOC')),
                'pedestrian_location_name': row.get('PEDLOCNAME', ''),
                'bicyclist_location': self.safe_int(row.get('BIKELOC')),
                'bicyclist_location_name': row.get('BIKELOCNAME', ''),
                'pedestrian_position': self.safe_int(row.get('PEDPOS')),
                'pedestrian_position_name': row.get('PEDPOSNAME', ''),
                'bicyclist_position': self.safe_int(row.get('BIKEPOS')),
                'bicyclist_position_name': row.get('BIKEPOSNAME', ''),
                'pedestrian_direction': self.safe_int(row.get('PEDDIR')),
                'pedestrian_direction_name': row.get('PEDDIRNAME', ''),
                'bicyclist_direction': self.safe_int(row.get('BIKEDIR')),
                'bicyclist_direction_name': row.get('BIKEDIRNAME', ''),
                'motorist_direction': self.safe_int(row.get('MOTDIR')),
                'motorist_direction_name': row.get('MOTDIRNAME', ''),
                'motorist_maneuver': self.safe_int(row.get('MOTMAN')),
                'motorist_maneuver_name': row.get('MOTMANNAME', ''),
                'pedestrian_scenario': self.safe_int(row.get('PEDLEG')),
                'pedestrian_scenario_name': row.get('PEDLEGNAME', ''),
                'pedestrian_crash_group': self.safe_int(row.get('PEDCGP')),
                'pedestrian_crash_group_name': row.get('PEDCGPNAME', ''),
                'bicyclist_crash_group': self.safe_int(row.get('BIKECGP')),
                'bicyclist_crash_group_name': row.get('BIKECGPNAME', '')
            }
            ped_data.append(ped_detail)

        # Insert into database
        print(f"  💾 Inserting {len(ped_data)} pedestrian detail records...")
        ped_df = pd.DataFrame(ped_data)

        # Add ingestion_timestamp
        ped_df['ingestion_timestamp'] = None

        # Ensure column order matches table definition
        column_order = [
            'ped_detail_id', 'person_id', 'crash_id',
            'state', 'st_case', 'year',
            'age', 'sex', 'sex_name',
            'person_type', 'person_type_name',
            'crosswalk_present', 'pedestrian_in_crosswalk', 'school_zone',
            'pedestrian_crash_type', 'pedestrian_crash_type_name',
            'bicyclist_crash_type', 'bicyclist_crash_type_name',
            'pedestrian_location', 'pedestrian_location_name',
            'bicyclist_location', 'bicyclist_location_name',
            'pedestrian_position', 'pedestrian_position_name',
            'bicyclist_position', 'bicyclist_position_name',
            'pedestrian_direction', 'pedestrian_direction_name',
            'bicyclist_direction', 'bicyclist_direction_name',
            'motorist_direction', 'motorist_direction_name',
            'motorist_maneuver', 'motorist_maneuver_name',
            'pedestrian_scenario', 'pedestrian_scenario_name',
            'pedestrian_crash_group', 'pedestrian_crash_group_name',
            'bicyclist_crash_group', 'bicyclist_crash_group_name',
            'ingestion_timestamp'
        ]
        ped_df = ped_df[column_order]

        self.con.execute("INSERT INTO pedestrian_details SELECT * FROM ped_df")

        print(f"  ✅ Inserted {len(ped_data)} pedestrian detail records")
        self.stats['pedestrian_details_inserted'] += len(ped_data)
        return len(ped_data)

    def ingest_year(self, year: int, region: str = "National") -> bool:
        """
        Ingest all data for a single year.

        Args:
            year: Year to ingest
            region: Region (National or PuertoRico)

        Returns:
            True if successful, False otherwise
        """
        print(f"\n{'='*60}")
        print(f"📅 Ingesting FARS {year} - {region}")
        print(f"{'='*60}")

        # Find data file
        zip_path = self.find_data_files(year, region)
        if not zip_path:
            print(f"❌ No data found for {year} {region}")
            self.stats['errors'].append(f"{year}: Data file not found")
            return False

        print(f"📦 Found data: {zip_path.name}")

        # Create temporary directory for extraction
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            try:
                # Extract ZIP
                print(f"📂 Extracting ZIP file...")
                csv_dir = self.extract_zip(zip_path, temp_path)
                print(f"  ✓ Extracted to {csv_dir}")

                # Ingest data tables
                self.ingest_crashes(csv_dir, year)
                self.ingest_persons(csv_dir, year)
                self.ingest_pedestrian_details(csv_dir, year)
                # Could add: vehicles, environment, nm_factors

                print(f"\n✅ Successfully ingested {year} {region}")
                return True

            except Exception as e:
                print(f"\n❌ Error ingesting {year} {region}: {e}")
                import traceback
                traceback.print_exc()
                self.stats['errors'].append(f"{year}: {str(e)}")
                return False

    def print_stats(self):
        """Print ingestion statistics."""
        print(f"\n{'='*60}")
        print("📊 INGESTION STATISTICS")
        print(f"{'='*60}")
        print(f"Crashes inserted:            {self.stats['crashes_inserted']:,}")
        print(f"Persons inserted:            {self.stats['persons_inserted']:,}")
        print(f"Pedestrian details inserted: {self.stats['pedestrian_details_inserted']:,}")
        print(f"Errors:                      {len(self.stats['errors'])}")
        if self.stats['errors']:
            print("\nErrors:")
            for error in self.stats['errors']:
                print(f"  • {error}")
        print(f"{'='*60}\n")


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Ingest FARS data into DuckDB")
    parser.add_argument("--year", type=int, help="Single year to ingest")
    parser.add_argument("--start-year", type=int, help="Start year for range")
    parser.add_argument("--end-year", type=int, help="End year for range")
    parser.add_argument("--all", action="store_true", help="Ingest all available years")
    parser.add_argument(
        "--db-path",
        default="data/pedestrian_safety.duckdb",
        help="Path to database file"
    )
    parser.add_argument(
        "--region",
        default="National",
        choices=["National", "PuertoRico"],
        help="Region to ingest"
    )

    args = parser.parse_args()

    # Determine years to ingest
    years = []
    if args.year:
        years = [args.year]
    elif args.start_year and args.end_year:
        years = list(range(args.start_year, args.end_year + 1))
    elif args.all:
        # Find all available years
        data_dir = Path("data/raw")
        if data_dir.exists():
            years = sorted([int(d.name) for d in data_dir.iterdir() if d.is_dir() and d.name.isdigit()])
    else:
        print("❌ Please specify --year, --start-year/--end-year, or --all")
        sys.exit(1)

    print(f"🚀 Starting FARS data ingestion")
    print(f"   Years: {years[0]}-{years[-1]} ({len(years)} years)")
    print(f"   Database: {args.db_path}")
    print(f"   Region: {args.region}\n")

    # Create ingester
    ingester = FARSIngester(args.db_path)

    try:
        ingester.connect()
        print("✅ Connected to database\n")

        # Ingest each year
        for year in years:
            success = ingester.ingest_year(year, args.region)
            if not success:
                print(f"⚠️  Continuing with next year...")

        # Print final statistics
        ingester.print_stats()

    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    finally:
        ingester.close()

    print("✅ Ingestion complete!")


if __name__ == "__main__":
    main()
