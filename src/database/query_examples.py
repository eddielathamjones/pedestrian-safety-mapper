"""
Example queries for the Pedestrian Safety Mapper database.

This script demonstrates common analytical queries for pedestrian safety analysis.

Usage:
    python -m src.database.query_examples
"""

import duckdb
import pandas as pd
from pathlib import Path


def connect_db(db_path: str = "data/pedestrian_safety.duckdb") -> duckdb.DuckDBPyConnection:
    """Connect to the database."""
    if not Path(db_path).exists():
        raise FileNotFoundError(f"Database not found at {db_path}")

    con = duckdb.connect(db_path, read_only=True)
    try:
        con.execute("LOAD spatial;")
    except Exception:
        pass  # Spatial extension not available
    return con


def example_1_yearly_trends(con):
    """Example: Yearly pedestrian fatality trends."""
    print("\n" + "="*70)
    print("📈 Example 1: Yearly Pedestrian Fatality Trends")
    print("="*70)

    query = """
        SELECT *
        FROM yearly_pedestrian_stats
        ORDER BY year DESC
        LIMIT 10;
    """

    result = con.execute(query).df()
    print(result.to_string())


def example_2_state_rankings(con):
    """Example: States with most pedestrian fatalities."""
    print("\n" + "="*70)
    print("🗺️  Example 2: States with Most Pedestrian Fatalities (Last 5 Years)")
    print("="*70)

    query = """
        SELECT
            state_name,
            COUNT(DISTINCT crash_id) as total_crashes,
            SUM(pedestrian_fatalities) as total_deaths,
            ROUND(AVG(pedestrian_fatalities), 2) as avg_deaths_per_crash
        FROM crashes
        WHERE pedestrian_fatalities > 0
          AND year >= (SELECT MAX(year) - 4 FROM crashes)
        GROUP BY state_name
        ORDER BY total_deaths DESC
        LIMIT 15;
    """

    result = con.execute(query).df()
    print(result.to_string())


def example_3_time_of_day_analysis(con):
    """Example: Pedestrian crashes by time of day."""
    print("\n" + "="*70)
    print("🕐 Example 3: Pedestrian Crashes by Time of Day")
    print("="*70)

    query = """
        SELECT
            hour,
            COUNT(*) as crash_count,
            SUM(pedestrian_fatalities) as total_deaths,
            ROUND(AVG(pedestrian_fatalities), 2) as avg_deaths
        FROM crashes
        WHERE pedestrian_fatalities > 0
          AND hour IS NOT NULL
        GROUP BY hour
        ORDER BY hour;
    """

    result = con.execute(query).df()
    print(result.to_string())


def example_4_lighting_conditions(con):
    """Example: Impact of lighting conditions."""
    print("\n" + "="*70)
    print("💡 Example 4: Pedestrian Crashes by Lighting Condition")
    print("="*70)

    query = """
        SELECT
            light_condition_name,
            COUNT(*) as crash_count,
            SUM(pedestrian_fatalities) as total_deaths,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct_of_crashes
        FROM crashes
        WHERE pedestrian_fatalities > 0
          AND light_condition_name IS NOT NULL
        GROUP BY light_condition_name
        ORDER BY crash_count DESC;
    """

    result = con.execute(query).df()
    print(result.to_string())


def example_5_urban_vs_rural(con):
    """Example: Urban vs rural comparison."""
    print("\n" + "="*70)
    print("🏙️  Example 5: Urban vs Rural Pedestrian Crashes")
    print("="*70)

    query = """
        SELECT
            rural_urban_name,
            COUNT(*) as crash_count,
            SUM(pedestrian_fatalities) as total_deaths,
            ROUND(AVG(pedestrian_fatalities), 2) as avg_deaths_per_crash,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct_of_crashes
        FROM crashes
        WHERE pedestrian_fatalities > 0
          AND rural_urban_name IS NOT NULL
        GROUP BY rural_urban_name
        ORDER BY crash_count DESC;
    """

    result = con.execute(query).df()
    print(result.to_string())


def example_6_pedestrian_demographics(con):
    """Example: Pedestrian victim demographics."""
    print("\n" + "="*70)
    print("👤 Example 6: Pedestrian Victim Demographics (Age Groups)")
    print("="*70)

    query = """
        SELECT
            CASE
                WHEN age < 15 THEN '0-14'
                WHEN age BETWEEN 15 AND 24 THEN '15-24'
                WHEN age BETWEEN 25 AND 34 THEN '25-34'
                WHEN age BETWEEN 35 AND 44 THEN '35-44'
                WHEN age BETWEEN 45 AND 54 THEN '45-54'
                WHEN age BETWEEN 55 AND 64 THEN '55-64'
                WHEN age >= 65 THEN '65+'
                ELSE 'Unknown'
            END as age_group,
            COUNT(*) as victim_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM persons
        WHERE is_pedestrian = TRUE
          AND is_fatal = TRUE
          AND age IS NOT NULL
        GROUP BY age_group
        ORDER BY
            CASE age_group
                WHEN '0-14' THEN 1
                WHEN '15-24' THEN 2
                WHEN '25-34' THEN 3
                WHEN '35-44' THEN 4
                WHEN '45-54' THEN 5
                WHEN '55-64' THEN 6
                WHEN '65+' THEN 7
                ELSE 8
            END;
    """

    result = con.execute(query).df()
    print(result.to_string())


def example_7_crosswalk_analysis(con):
    """Example: Crosswalk-related crashes."""
    print("\n" + "="*70)
    print("🚸 Example 7: Crosswalk-Related Crashes")
    print("="*70)

    query = """
        SELECT
            CASE
                WHEN crosswalk_present AND pedestrian_in_crosswalk THEN 'In Crosswalk'
                WHEN crosswalk_present AND NOT pedestrian_in_crosswalk THEN 'Crosswalk Present, Not Used'
                WHEN NOT crosswalk_present THEN 'No Crosswalk'
                ELSE 'Unknown'
            END as crosswalk_status,
            COUNT(*) as victim_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM pedestrian_details
        GROUP BY crosswalk_status
        ORDER BY victim_count DESC;
    """

    result = con.execute(query).df()
    print(result.to_string())


def example_8_spatial_query(con):
    """Example: Spatial query (crashes near a point)."""
    print("\n" + "="*70)
    print("📍 Example 8: Crashes Near Los Angeles (within 25km)")
    print("="*70)

    query = """
        SELECT
            crash_id,
            year,
            crash_date,
            city_name,
            pedestrian_fatalities,
            latitude,
            longitude,
            ROUND(ST_Distance_Sphere(
                geom,
                ST_Point(-118.2437, 34.0522)
            ) / 1000.0, 2) as distance_km
        FROM crashes
        WHERE pedestrian_fatalities > 0
          AND geom IS NOT NULL
          AND ST_Distance_Sphere(
              geom,
              ST_Point(-118.2437, 34.0522)
          ) <= 25000
        ORDER BY distance_km
        LIMIT 10;
    """

    result = con.execute(query).df()
    print(result.to_string())


def example_9_crash_type_classification(con):
    """Example: Most common pedestrian crash types."""
    print("\n" + "="*70)
    print("🚦 Example 9: Most Common Pedestrian Crash Types")
    print("="*70)

    query = """
        SELECT
            pedestrian_crash_type_name,
            COUNT(*) as crash_count,
            ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as pct
        FROM pedestrian_details
        WHERE pedestrian_crash_type_name IS NOT NULL
          AND pedestrian_crash_type_name != 'Not a Cyclist'
        GROUP BY pedestrian_crash_type_name
        ORDER BY crash_count DESC
        LIMIT 15;
    """

    result = con.execute(query).df()
    print(result.to_string())


def example_10_monthly_seasonality(con):
    """Example: Monthly crash patterns (seasonality)."""
    print("\n" + "="*70)
    print("📅 Example 10: Monthly Crash Patterns (Seasonality)")
    print("="*70)

    query = """
        SELECT
            month_name,
            COUNT(*) as crash_count,
            SUM(pedestrian_fatalities) as total_deaths,
            ROUND(AVG(pedestrian_fatalities), 2) as avg_deaths
        FROM crashes
        WHERE pedestrian_fatalities > 0
          AND month_name IS NOT NULL
        GROUP BY month, month_name
        ORDER BY month;
    """

    result = con.execute(query).df()
    print(result.to_string())


def main():
    """Run all example queries."""
    print("🦆 Pedestrian Safety Mapper - Query Examples")
    print("="*70)

    try:
        con = connect_db()
        print("✅ Connected to database\n")

        # Check if data exists
        row_count = con.execute("SELECT COUNT(*) FROM crashes WHERE pedestrian_fatalities > 0").fetchone()[0]
        if row_count == 0:
            print("⚠️  No pedestrian crash data found in database.")
            print("   Run: python -m src.database.ingest_data --year 2022")
            return

        print(f"📊 Found {row_count:,} pedestrian crashes in database\n")

        # Run examples
        example_1_yearly_trends(con)
        example_2_state_rankings(con)
        example_3_time_of_day_analysis(con)
        example_4_lighting_conditions(con)
        example_5_urban_vs_rural(con)
        example_6_pedestrian_demographics(con)
        example_7_crosswalk_analysis(con)
        example_8_spatial_query(con)
        example_9_crash_type_classification(con)
        example_10_monthly_seasonality(con)

        con.close()

        print("\n" + "="*70)
        print("✅ All example queries complete!")
        print("="*70)

    except FileNotFoundError as e:
        print(f"❌ {e}")
        print("   Run: python -m src.database.init_db")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
