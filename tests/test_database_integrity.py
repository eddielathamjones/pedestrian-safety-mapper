"""
Database Integrity Tests for Pedestrian Safety Mapper.

Tests validate:
- Table existence and structure
- Row counts and data presence
- Primary key uniqueness
- Foreign key relationships
- Required field completeness
"""

import pytest
import duckdb
from pathlib import Path


@pytest.fixture(scope="module")
def db_connection():
    """Create database connection for tests."""
    db_path = "data/pedestrian_safety.duckdb"
    if not Path(db_path).exists():
        pytest.skip(f"Database not found at {db_path}")

    con = duckdb.connect(db_path, read_only=True)
    try:
        con.execute("LOAD spatial;")
    except Exception:
        pass  # Spatial extension optional

    yield con
    con.close()


class TestDatabaseStructure:
    """Test database tables and schema."""

    def test_all_tables_exist(self, db_connection):
        """Verify all expected tables exist."""
        expected_tables = [
            'crashes', 'persons', 'pedestrian_details',
            'non_motorist_factors', 'vehicles', 'environment'
        ]

        result = db_connection.execute("SHOW TABLES;").fetchall()
        existing_tables = [row[0] for row in result]

        for table in expected_tables:
            assert table in existing_tables, f"Table '{table}' not found in database"

    def test_all_views_exist(self, db_connection):
        """Verify all analytical views exist."""
        expected_views = [
            'pedestrian_crashes_view',
            'pedestrian_victim_analysis',
            'yearly_pedestrian_stats'
        ]

        result = db_connection.execute("""
            SELECT table_name
            FROM information_schema.tables
            WHERE table_type = 'VIEW';
        """).fetchall()
        existing_views = [row[0] for row in result]

        for view in expected_views:
            assert view in existing_views, f"View '{view}' not found in database"

    def test_crashes_table_has_data(self, db_connection):
        """Verify crashes table contains data."""
        count = db_connection.execute("SELECT COUNT(*) FROM crashes").fetchone()[0]
        assert count > 0, "Crashes table is empty"

    def test_persons_table_has_data(self, db_connection):
        """Verify persons table contains data."""
        count = db_connection.execute("SELECT COUNT(*) FROM persons").fetchone()[0]
        assert count > 0, "Persons table is empty"


class TestPrimaryKeyUniqueness:
    """Test primary key constraints and uniqueness."""

    def test_crashes_primary_key_unique(self, db_connection):
        """Verify crash_id is unique."""
        result = db_connection.execute("""
            SELECT crash_id, COUNT(*) as cnt
            FROM crashes
            GROUP BY crash_id
            HAVING COUNT(*) > 1
        """).fetchall()

        assert len(result) == 0, f"Found {len(result)} duplicate crash_id values"

    def test_persons_primary_key_unique(self, db_connection):
        """Verify person_id is unique."""
        result = db_connection.execute("""
            SELECT person_id, COUNT(*) as cnt
            FROM persons
            GROUP BY person_id
            HAVING COUNT(*) > 1
        """).fetchall()

        assert len(result) == 0, f"Found {len(result)} duplicate person_id values"

    def test_crash_id_format(self, db_connection):
        """Verify crash_id follows expected format: {YEAR}_{STATE}_{CASE}."""
        result = db_connection.execute("""
            SELECT crash_id
            FROM crashes
            WHERE crash_id !~ '^[0-9]{4}_[0-9]{2}_[0-9]+$'
            LIMIT 10
        """).fetchall()

        assert len(result) == 0, f"Found {len(result)} crash_ids with invalid format"


class TestForeignKeyRelationships:
    """Test referential integrity between tables."""

    def test_persons_crash_id_references_crashes(self, db_connection):
        """Verify all person crash_ids exist in crashes table."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM persons p
            WHERE NOT EXISTS (
                SELECT 1 FROM crashes c WHERE c.crash_id = p.crash_id
            )
        """).fetchone()[0]

        assert result == 0, f"Found {result} orphaned person records"

    def test_pedestrian_details_person_id_references_persons(self, db_connection):
        """Verify all pedestrian detail person_ids exist in persons table."""
        # Skip if no pedestrian_details
        count = db_connection.execute("SELECT COUNT(*) FROM pedestrian_details").fetchone()[0]
        if count == 0:
            pytest.skip("No pedestrian_details data available")

        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM pedestrian_details pd
            WHERE NOT EXISTS (
                SELECT 1 FROM persons p WHERE p.person_id = pd.person_id
            )
        """).fetchone()[0]

        assert result == 0, f"Found {result} orphaned pedestrian detail records"


class TestRequiredFieldCompleteness:
    """Test that critical fields are populated."""

    def test_crashes_have_state(self, db_connection):
        """Verify all crashes have a state."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE state IS NULL
        """).fetchone()[0]

        assert result == 0, f"Found {result} crashes without state"

    def test_crashes_have_year(self, db_connection):
        """Verify all crashes have a year."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE year IS NULL
        """).fetchone()[0]

        assert result == 0, f"Found {result} crashes without year"

    def test_crashes_have_fatalities_count(self, db_connection):
        """Verify all crashes have fatality count (can be 0)."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE total_fatalities IS NULL
        """).fetchone()[0]

        assert result == 0, f"Found {result} crashes without total_fatalities"

    def test_persons_have_injury_severity(self, db_connection):
        """Verify all persons have injury severity."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM persons
            WHERE injury_severity IS NULL
        """).fetchone()[0]

        assert result == 0, f"Found {result} persons without injury_severity"


class TestDataRanges:
    """Test data values are within expected ranges."""

    def test_year_range(self, db_connection):
        """Verify years are within FARS data range (1975-present)."""
        result = db_connection.execute("""
            SELECT MIN(year) as min_year, MAX(year) as max_year
            FROM crashes
        """).fetchone()

        min_year, max_year = result
        assert min_year >= 1975, f"Found year {min_year} before FARS start (1975)"
        assert max_year <= 2025, f"Found year {max_year} in the future"

    def test_state_codes_valid(self, db_connection):
        """Verify state codes are valid (1-56)."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE state < 1 OR state > 56
        """).fetchone()[0]

        assert result == 0, f"Found {result} crashes with invalid state codes"

    def test_month_range(self, db_connection):
        """Verify months are 1-12."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE month < 1 OR month > 12
        """).fetchone()[0]

        assert result == 0, f"Found {result} crashes with invalid month"

    def test_hour_range(self, db_connection):
        """Verify hours are 0-23 or 99 (unknown)."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE hour IS NOT NULL
              AND hour NOT BETWEEN 0 AND 23
              AND hour != 99
        """).fetchone()[0]

        assert result == 0, f"Found {result} crashes with invalid hour"

    def test_latitude_range(self, db_connection):
        """Verify latitudes are within valid range (-90 to 90)."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE latitude IS NOT NULL
              AND (latitude < -90 OR latitude > 90)
        """).fetchone()[0]

        assert result == 0, f"Found {result} crashes with invalid latitude"

    def test_longitude_range(self, db_connection):
        """Verify longitudes are within valid range (-180 to 180)."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE longitude IS NOT NULL
              AND (longitude < -180 OR longitude > 180)
        """).fetchone()[0]

        assert result == 0, f"Found {result} crashes with invalid longitude"


class TestDataQuality:
    """Test data quality metrics."""

    def test_coordinate_completeness(self, db_connection):
        """Check percentage of crashes with coordinates."""
        result = db_connection.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1 ELSE 0 END) as with_coords
            FROM crashes
        """).fetchone()

        total, with_coords = result
        if total > 0:
            pct = (with_coords / total) * 100
            assert pct > 80, f"Only {pct:.1f}% of crashes have coordinates (expected >80%)"

    def test_pedestrian_crashes_identifiable(self, db_connection):
        """Verify pedestrian crashes are properly identified."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
        """).fetchone()[0]

        assert result > 0, "No pedestrian crashes found in database"

    def test_persons_per_crash_reasonable(self, db_connection):
        """Verify person counts per crash are reasonable (<100)."""
        result = db_connection.execute("""
            SELECT crash_id, COUNT(*) as person_count
            FROM persons
            GROUP BY crash_id
            HAVING COUNT(*) > 100
        """).fetchall()

        assert len(result) == 0, f"Found {len(result)} crashes with >100 persons (likely data error)"

    def test_fatal_injury_consistency(self, db_connection):
        """Verify is_fatal flag matches injury_severity=4."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM persons
            WHERE (is_fatal = TRUE AND injury_severity != 4)
               OR (is_fatal = FALSE AND injury_severity = 4)
        """).fetchone()[0]

        assert result == 0, f"Found {result} persons with inconsistent fatal injury flags"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
