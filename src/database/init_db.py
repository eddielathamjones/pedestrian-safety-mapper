"""
Database initialization script for Pedestrian Safety Mapper.

This script creates the DuckDB database, installs spatial extensions,
and sets up all tables, indexes, and views.

Usage:
    python -m src.database.init_db
    python -m src.database.init_db --db-path custom/path/db.duckdb
"""

import argparse
import duckdb
from pathlib import Path
import sys


def create_database(db_path: str = "data/pedestrian_safety.duckdb") -> duckdb.DuckDBPyConnection:
    """
    Create and initialize DuckDB database with spatial extension.

    Args:
        db_path: Path to the database file

    Returns:
        DuckDB connection object
    """
    # Ensure directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"🦆 Creating DuckDB database at: {db_path}")

    # Connect to database (creates if doesn't exist)
    con = duckdb.connect(db_path)

    # Install and load spatial extension (optional if network unavailable)
    print("📦 Installing spatial extension...")
    try:
        con.execute("INSTALL spatial;")
        con.execute("LOAD spatial;")
        print("✅ Spatial extension loaded")
    except Exception as e:
        print(f"⚠️  Warning: Could not install spatial extension: {e}")
        print("   Database will work but spatial queries will be limited")
        print("   Continuing without spatial extension...")

    return con


def create_crashes_table(con: duckdb.DuckDBPyConnection):
    """Create the main crashes fact table."""
    print("📊 Creating 'crashes' table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS crashes (
            -- Primary Key
            crash_id VARCHAR PRIMARY KEY,

            -- Original FARS Identifiers
            state INTEGER,
            state_name VARCHAR,
            st_case INTEGER,
            year INTEGER,

            -- Temporal Information
            crash_date DATE,
            crash_datetime TIMESTAMP,
            month INTEGER,
            month_name VARCHAR,
            day INTEGER,
            day_name VARCHAR,
            day_of_week INTEGER,
            hour INTEGER,
            minute INTEGER,

            -- Spatial Information
            latitude DECIMAL(10, 8),
            longitude DECIMAL(11, 8),
            geom VARCHAR,  -- Will store WKT or be NULL if spatial extension available

            -- Location Details
            county INTEGER,
            county_name VARCHAR,
            city INTEGER,
            city_name VARCHAR,
            rural_urban INTEGER,
            rural_urban_name VARCHAR,

            -- Road Characteristics
            route_type INTEGER,
            route_name VARCHAR,
            functional_system INTEGER,
            functional_system_name VARCHAR,
            road_owner INTEGER,
            road_owner_name VARCHAR,
            national_highway_system BOOLEAN,

            -- Crash Characteristics
            manner_of_collision INTEGER,
            manner_of_collision_name VARCHAR,
            first_harmful_event INTEGER,
            first_harmful_event_name VARCHAR,
            relation_to_junction INTEGER,
            relation_to_junction_name VARCHAR,
            intersection_type INTEGER,
            intersection_type_name VARCHAR,
            relation_to_roadway INTEGER,
            relation_to_roadway_name VARCHAR,

            -- Work Zone
            work_zone INTEGER,
            work_zone_name VARCHAR,

            -- Environmental Conditions
            light_condition INTEGER,
            light_condition_name VARCHAR,
            weather INTEGER,
            weather_name VARCHAR,

            -- Special Circumstances
            school_bus_related BOOLEAN,
            rail_crossing VARCHAR,

            -- Notification & Response Times
            notification_hour INTEGER,
            notification_minute INTEGER,
            arrival_hour INTEGER,
            arrival_minute INTEGER,
            hospital_arrival_hour INTEGER,
            hospital_arrival_minute INTEGER,

            -- Crash Severity
            total_fatalities INTEGER,
            pedestrian_fatalities INTEGER,
            total_vehicles INTEGER,
            total_persons INTEGER,

            -- Metadata
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            data_source VARCHAR
        );
    """)

    print("  ✓ Crashes table created")


def create_persons_table(con: duckdb.DuckDBPyConnection):
    """Create the persons dimension table."""
    print("👥 Creating 'persons' table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS persons (
            -- Primary Key
            person_id VARCHAR PRIMARY KEY,

            -- Foreign Key
            crash_id VARCHAR,

            -- FARS Identifiers
            state INTEGER,
            st_case INTEGER,
            vehicle_number INTEGER,
            person_number INTEGER,
            year INTEGER,

            -- Person Type
            person_type INTEGER,
            person_type_name VARCHAR,
            is_pedestrian BOOLEAN,
            is_bicyclist BOOLEAN,
            is_non_motorist BOOLEAN,

            -- Demographics
            age INTEGER,
            age_name VARCHAR,
            sex INTEGER,
            sex_name VARCHAR,
            hispanic_origin INTEGER,
            race INTEGER,

            -- Injury Severity
            injury_severity INTEGER,
            injury_severity_name VARCHAR,
            is_fatal BOOLEAN,

            -- Death Details
            death_date DATE,
            death_time TIME,
            hours_to_death INTEGER,
            minutes_to_death INTEGER,
            died_at_scene BOOLEAN,

            -- Medical Response
            transported_by INTEGER,
            transported_by_name VARCHAR,
            ems_arrival_time TIME,
            hospital_arrival_time TIME,

            -- Occupant Details
            seating_position INTEGER,
            seating_position_name VARCHAR,
            restraint_system_use INTEGER,
            restraint_system_use_name VARCHAR,
            restraint_misuse INTEGER,
            helmet_use INTEGER,
            airbag_deployment INTEGER,
            airbag_deployment_name VARCHAR,
            ejection INTEGER,
            ejection_name VARCHAR,

            -- Impairment
            drinking BOOLEAN,
            alcohol_test_result DECIMAL(5, 3),
            drug_involvement BOOLEAN,

            -- Work-Related
            work_related_injury BOOLEAN,

            -- Metadata
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("  ✓ Persons table created")


def create_pedestrian_details_table(con: duckdb.DuckDBPyConnection):
    """Create the pedestrian-specific details table."""
    print("🚶 Creating 'pedestrian_details' table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS pedestrian_details (
            -- Primary Key
            ped_detail_id VARCHAR PRIMARY KEY,

            -- Foreign Keys
            person_id VARCHAR,
            crash_id VARCHAR,

            -- FARS Identifiers
            state INTEGER,
            st_case INTEGER,
            year INTEGER,

            -- Demographics
            age INTEGER,
            sex INTEGER,
            sex_name VARCHAR,

            -- Pedestrian Type
            person_type INTEGER,
            person_type_name VARCHAR,

            -- Crossing Behavior
            crosswalk_present BOOLEAN,
            pedestrian_in_crosswalk BOOLEAN,
            school_zone BOOLEAN,

            -- Crash Type Classification
            pedestrian_crash_type INTEGER,
            pedestrian_crash_type_name VARCHAR,
            bicyclist_crash_type INTEGER,
            bicyclist_crash_type_name VARCHAR,

            -- Location at Impact
            pedestrian_location INTEGER,
            pedestrian_location_name VARCHAR,
            bicyclist_location INTEGER,
            bicyclist_location_name VARCHAR,

            -- Position on Road
            pedestrian_position INTEGER,
            pedestrian_position_name VARCHAR,
            bicyclist_position INTEGER,
            bicyclist_position_name VARCHAR,

            -- Movement Direction
            pedestrian_direction INTEGER,
            pedestrian_direction_name VARCHAR,
            bicyclist_direction INTEGER,
            bicyclist_direction_name VARCHAR,

            -- Motorist Direction & Maneuver
            motorist_direction INTEGER,
            motorist_direction_name VARCHAR,
            motorist_maneuver INTEGER,
            motorist_maneuver_name VARCHAR,

            -- Pedestrian Action
            pedestrian_scenario INTEGER,
            pedestrian_scenario_name VARCHAR,

            -- Crash Group
            pedestrian_crash_group INTEGER,
            pedestrian_crash_group_name VARCHAR,
            bicyclist_crash_group INTEGER,
            bicyclist_crash_group_name VARCHAR,

            -- Metadata
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("  ✓ Pedestrian details table created")


def create_non_motorist_factors_table(con: duckdb.DuckDBPyConnection):
    """Create the non-motorist contributing factors table."""
    print("⚠️  Creating 'non_motorist_factors' table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS non_motorist_factors (
            -- Primary Key
            factor_id VARCHAR PRIMARY KEY,

            -- Foreign Keys
            person_id VARCHAR,
            crash_id VARCHAR,

            -- FARS Identifiers
            state INTEGER,
            st_case INTEGER,
            vehicle_number INTEGER,
            person_number INTEGER,

            -- Contributing Factor
            contributing_factor INTEGER,
            contributing_factor_name VARCHAR,

            -- Metadata
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("  ✓ Non-motorist factors table created")


def create_vehicles_table(con: duckdb.DuckDBPyConnection):
    """Create the vehicles dimension table."""
    print("🚗 Creating 'vehicles' table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS vehicles (
            -- Primary Key
            vehicle_id VARCHAR PRIMARY KEY,

            -- Foreign Key
            crash_id VARCHAR,

            -- FARS Identifiers
            state INTEGER,
            st_case INTEGER,
            vehicle_number INTEGER,
            year INTEGER,

            -- Vehicle Characteristics
            make INTEGER,
            make_name VARCHAR,
            model INTEGER,
            model_name VARCHAR,
            model_year INTEGER,
            body_type INTEGER,
            body_type_name VARCHAR,
            vehicle_type VARCHAR,

            -- Impact Details
            initial_impact_point INTEGER,
            initial_impact_point_name VARCHAR,

            -- Vehicle Maneuver
            vehicle_maneuver INTEGER,
            vehicle_maneuver_name VARCHAR,

            -- Speed & Control
            travel_speed INTEGER,
            speed_limit INTEGER,
            rollover BOOLEAN,
            fire BOOLEAN,

            -- Special Use
            emergency_vehicle BOOLEAN,
            special_use INTEGER,

            -- Driver Information
            driver_age INTEGER,
            driver_sex INTEGER,
            driver_drinking BOOLEAN,
            driver_drug_involvement BOOLEAN,

            -- Metadata
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("  ✓ Vehicles table created")


def create_environment_table(con: duckdb.DuckDBPyConnection):
    """Create the environment dimension table."""
    print("🌤️  Creating 'environment' table...")

    con.execute("""
        CREATE TABLE IF NOT EXISTS environment (
            -- Primary Key
            env_id VARCHAR PRIMARY KEY,

            -- Foreign Key
            crash_id VARCHAR,

            -- Temporal
            year INTEGER,
            month INTEGER,
            hour INTEGER,

            -- Lighting
            light_condition INTEGER,
            light_condition_name VARCHAR,
            is_dark BOOLEAN,
            is_dawn_dusk BOOLEAN,

            -- Weather
            atmospheric_condition INTEGER,
            atmospheric_condition_name VARCHAR,
            is_rain BOOLEAN,
            is_snow BOOLEAN,
            is_fog BOOLEAN,
            is_clear BOOLEAN,

            -- Road Surface
            road_surface_condition INTEGER,
            road_surface_condition_name VARCHAR,

            -- Metadata
            ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    print("  ✓ Environment table created")


def create_indexes(con: duckdb.DuckDBPyConnection):
    """Create indexes for query performance."""
    print("🔍 Creating indexes...")

    indexes = [
        # Crashes indexes
        ("idx_crashes_year", "crashes", "year"),
        ("idx_crashes_state", "crashes", "state"),
        ("idx_crashes_date", "crashes", "crash_date"),

        # Persons indexes
        ("idx_persons_crash", "persons", "crash_id"),
        ("idx_persons_type", "persons", "person_type"),
        ("idx_persons_year", "persons", "year"),
        ("idx_persons_age", "persons", "age"),

        # Pedestrian details indexes
        ("idx_peddetails_person", "pedestrian_details", "person_id"),
        ("idx_peddetails_crash", "pedestrian_details", "crash_id"),
        ("idx_peddetails_crashtype", "pedestrian_details", "pedestrian_crash_type"),
        ("idx_peddetails_year", "pedestrian_details", "year"),

        # Non-motorist factors indexes
        ("idx_nmfactors_person", "non_motorist_factors", "person_id"),
        ("idx_nmfactors_crash", "non_motorist_factors", "crash_id"),

        # Vehicles indexes
        ("idx_vehicles_crash", "vehicles", "crash_id"),
        ("idx_vehicles_year", "vehicles", "year"),

        # Environment indexes
        ("idx_env_crash", "environment", "crash_id"),
        ("idx_env_light", "environment", "light_condition"),
    ]

    for idx_name, table, column in indexes:
        try:
            con.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column});")
            print(f"  ✓ Created index: {idx_name}")
        except Exception as e:
            print(f"  ⚠️  Warning: Could not create index {idx_name}: {e}")


def create_views(con: duckdb.DuckDBPyConnection):
    """Create analytical views."""
    print("👁️  Creating analytical views...")

    # Pedestrian crashes view
    con.execute("""
        CREATE OR REPLACE VIEW pedestrian_crashes_view AS
        SELECT
            c.crash_id,
            c.year,
            c.crash_date,
            c.state_name,
            c.county_name,
            c.city_name,
            c.latitude,
            c.longitude,
            c.geom,
            c.pedestrian_fatalities,
            c.rural_urban_name,
            c.light_condition_name,
            c.weather_name,
            c.functional_system_name,
            e.is_dark,
            e.is_rain,
            e.is_snow,
            COUNT(DISTINCT p.person_id) as total_pedestrians_involved
        FROM crashes c
        LEFT JOIN persons p ON c.crash_id = p.crash_id AND p.is_pedestrian = TRUE
        LEFT JOIN environment e ON c.crash_id = e.env_id
        WHERE c.pedestrian_fatalities > 0
        GROUP BY ALL;
    """)
    print("  ✓ Created view: pedestrian_crashes_view")

    # Pedestrian victim analysis view
    con.execute("""
        CREATE OR REPLACE VIEW pedestrian_victim_analysis AS
        SELECT
            p.person_id,
            p.crash_id,
            c.year,
            c.crash_date,
            c.state_name,
            c.latitude,
            c.longitude,
            c.geom,
            p.age,
            p.sex_name,
            p.hispanic_origin,
            pd.pedestrian_crash_type_name,
            pd.pedestrian_location_name,
            pd.pedestrian_scenario_name,
            pd.crosswalk_present,
            pd.pedestrian_in_crosswalk,
            pd.school_zone,
            c.light_condition_name,
            c.weather_name,
            c.rural_urban_name,
            p.hours_to_death,
            p.died_at_scene
        FROM persons p
        JOIN crashes c ON p.crash_id = c.crash_id
        LEFT JOIN pedestrian_details pd ON p.person_id = pd.person_id
        WHERE p.is_pedestrian = TRUE AND p.is_fatal = TRUE;
    """)
    print("  ✓ Created view: pedestrian_victim_analysis")

    # Yearly statistics view
    con.execute("""
        CREATE OR REPLACE VIEW yearly_pedestrian_stats AS
        SELECT
            year,
            COUNT(DISTINCT crash_id) as total_crashes_with_pedestrians,
            SUM(pedestrian_fatalities) as total_pedestrian_deaths,
            AVG(pedestrian_fatalities) as avg_deaths_per_crash,
            COUNT(DISTINCT CASE WHEN rural_urban = 1 THEN crash_id END) as rural_crashes,
            COUNT(DISTINCT CASE WHEN rural_urban = 2 THEN crash_id END) as urban_crashes,
            COUNT(DISTINCT CASE WHEN light_condition IN (2,3) THEN crash_id END) as dark_crashes,
            COUNT(DISTINCT CASE WHEN weather != 1 THEN crash_id END) as adverse_weather_crashes
        FROM crashes
        WHERE pedestrian_fatalities > 0
        GROUP BY year
        ORDER BY year;
    """)
    print("  ✓ Created view: yearly_pedestrian_stats")


def get_database_info(con: duckdb.DuckDBPyConnection):
    """Print database information and statistics."""
    print("\n" + "="*60)
    print("📊 DATABASE INFORMATION")
    print("="*60)

    # List tables
    tables = con.execute("SHOW TABLES;").fetchall()
    print(f"\n📋 Tables ({len(tables)}):")
    for table in tables:
        print(f"  • {table[0]}")

    # List views
    views = con.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_type = 'VIEW';
    """).fetchall()
    print(f"\n👁️  Views ({len(views)}):")
    for view in views:
        print(f"  • {view[0]}")

    print("\n" + "="*60)
    print("✅ Database initialization complete!")
    print("="*60)


def main():
    """Main function to initialize the database."""
    parser = argparse.ArgumentParser(
        description="Initialize DuckDB database for Pedestrian Safety Mapper"
    )
    parser.add_argument(
        "--db-path",
        default="data/pedestrian_safety.duckdb",
        help="Path to the database file (default: data/pedestrian_safety.duckdb)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of database (drops existing)"
    )

    args = parser.parse_args()

    # Check if database exists
    db_file = Path(args.db_path)
    if db_file.exists() and not args.force:
        print(f"⚠️  Database already exists at: {args.db_path}")
        print("   Use --force to recreate, or connect to existing database")
        response = input("   Continue with existing database? [y/N]: ")
        if response.lower() != 'y':
            print("❌ Initialization cancelled")
            sys.exit(0)
    elif db_file.exists() and args.force:
        print(f"🗑️  Removing existing database: {args.db_path}")
        db_file.unlink()

    try:
        # Create database and connection
        con = create_database(args.db_path)

        # Create all tables
        print("\n" + "="*60)
        print("Creating database schema...")
        print("="*60 + "\n")

        create_crashes_table(con)
        create_persons_table(con)
        create_pedestrian_details_table(con)
        create_non_motorist_factors_table(con)
        create_vehicles_table(con)
        create_environment_table(con)

        # Create indexes
        print()
        create_indexes(con)

        # Create views
        print()
        create_views(con)

        # Display database info
        get_database_info(con)

        # Close connection
        con.close()

        print(f"\n💾 Database saved to: {args.db_path}")
        print("\n🚀 Next steps:")
        print("   1. Run data ingestion: python -m src.database.ingest_data")
        print("   2. Query the database: python -m src.database.query_examples")

    except Exception as e:
        print(f"\n❌ Error initializing database: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
