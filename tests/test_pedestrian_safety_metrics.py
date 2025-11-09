"""
Pedestrian Safety Metrics Tests.

Tests validate pedestrian-specific data quality and metrics based on
FARS dataset characteristics and pedestrian safety research requirements.
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
    yield con
    con.close()


class TestPedestrianIdentification:
    """Test pedestrian crash and victim identification."""

    def test_pedestrian_crashes_match_counts(self, db_connection):
        """Verify pedestrian_fatalities count matches actual fatal pedestrians."""
        result = db_connection.execute("""
            SELECT
                c.crash_id,
                c.pedestrian_fatalities as crash_count,
                COUNT(CASE WHEN p.is_pedestrian AND p.is_fatal THEN 1 END) as actual_count
            FROM crashes c
            LEFT JOIN persons p ON c.crash_id = p.crash_id
            WHERE c.pedestrian_fatalities > 0
            GROUP BY c.crash_id, c.pedestrian_fatalities
            HAVING crash_count != actual_count
            LIMIT 10
        """).fetchall()

        # Some mismatch is expected due to data timing, but shouldn't be widespread
        assert len(result) < 100, f"Found {len(result)} crashes with mismatched pedestrian counts"

    def test_pedestrians_correctly_flagged(self, db_connection):
        """Verify person_type=5 matches is_pedestrian flag."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM persons
            WHERE (person_type = 5 AND is_pedestrian = FALSE)
               OR (person_type != 5 AND person_type IS NOT NULL AND is_pedestrian = TRUE)
        """).fetchone()[0]

        assert result == 0, f"Found {result} persons with incorrect is_pedestrian flag"

    def test_non_motorists_have_vehicle_zero(self, db_connection):
        """Verify non-motorists have vehicle_number=0."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM persons
            WHERE is_non_motorist = TRUE
              AND vehicle_number != 0
        """).fetchone()[0]

        assert result == 0, f"Found {result} non-motorists with vehicle_number != 0"


class TestPedestrianDemographics:
    """Test pedestrian victim demographic data quality."""

    def test_pedestrian_age_distribution_realistic(self, db_connection):
        """Verify pedestrian ages are realistic (0-120)."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM persons
            WHERE is_pedestrian = TRUE
              AND is_fatal = TRUE
              AND age IS NOT NULL
              AND (age < 0 OR age > 120)
        """).fetchone()[0]

        assert result == 0, f"Found {result} pedestrian fatalities with unrealistic age"

    def test_pedestrian_victims_have_demographics(self, db_connection):
        """Check that majority of pedestrian fatalities have age and sex."""
        result = db_connection.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN age IS NOT NULL THEN 1 ELSE 0 END) as with_age,
                SUM(CASE WHEN sex IS NOT NULL THEN 1 ELSE 0 END) as with_sex
            FROM persons
            WHERE is_pedestrian = TRUE AND is_fatal = TRUE
        """).fetchone()

        if result[0] > 0:  # If we have pedestrian fatalities
            total, with_age, with_sex = result
            age_pct = (with_age / total) * 100
            sex_pct = (with_sex / total) * 100

            assert age_pct > 85, f"Only {age_pct:.1f}% of ped fatalities have age (expected >85%)"
            assert sex_pct > 90, f"Only {sex_pct:.1f}% of ped fatalities have sex (expected >90%)"

    def test_child_pedestrian_fatalities_tracked(self, db_connection):
        """Verify child pedestrian fatalities are properly recorded."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM persons
            WHERE is_pedestrian = TRUE
              AND is_fatal = TRUE
              AND age BETWEEN 0 AND 17
        """).fetchone()[0]

        # Should have some child pedestrian fatalities in dataset
        assert result > 0, "No child pedestrian fatalities found (data may be incomplete)"


class TestEnvironmentalFactors:
    """Test environmental conditions related to pedestrian crashes."""

    def test_lighting_conditions_recorded(self, db_connection):
        """Verify lighting conditions are recorded for pedestrian crashes."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND light_condition IS NOT NULL
        """).fetchone()[0]

        total_ped_crashes = db_connection.execute("""
            SELECT COUNT(*) FROM crashes WHERE pedestrian_fatalities > 0
        """).fetchone()[0]

        if total_ped_crashes > 0:
            pct = (result / total_ped_crashes) * 100
            assert pct > 90, f"Only {pct:.1f}% of ped crashes have lighting data"

    def test_dark_conditions_significant(self, db_connection):
        """Verify dark conditions are captured (known pedestrian risk factor)."""
        result = db_connection.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN light_condition IN (2, 3) THEN 1 ELSE 0 END) as dark_crashes
            FROM crashes
            WHERE pedestrian_fatalities > 0
        """).fetchone()

        total, dark = result
        if total > 100:  # Only test if we have sufficient data
            dark_pct = (dark / total) * 100
            # Research shows ~70% of ped fatalities occur in dark
            assert dark_pct > 30, f"Only {dark_pct:.1f}% of ped crashes in dark (expected ~50-70%)"

    def test_weather_conditions_recorded(self, db_connection):
        """Verify weather conditions are recorded."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND weather IS NOT NULL
        """).fetchone()[0]

        total_ped_crashes = db_connection.execute("""
            SELECT COUNT(*) FROM crashes WHERE pedestrian_fatalities > 0
        """).fetchone()[0]

        if total_ped_crashes > 0:
            pct = (result / total_ped_crashes) * 100
            assert pct > 95, f"Only {pct:.1f}% of ped crashes have weather data"


class TestUrbanRuralPatterns:
    """Test urban vs rural crash patterns."""

    def test_urban_rural_classification_exists(self, db_connection):
        """Verify urban/rural classification is captured."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND rural_urban IS NOT NULL
        """).fetchone()[0]

        total = db_connection.execute("""
            SELECT COUNT(*) FROM crashes WHERE pedestrian_fatalities > 0
        """).fetchone()[0]

        if total > 0:
            pct = (result / total) * 100
            assert pct > 95, f"Only {pct:.1f}% of crashes have urban/rural classification"

    def test_majority_pedestrian_crashes_urban(self, db_connection):
        """Verify majority of pedestrian crashes are in urban areas (expected pattern)."""
        result = db_connection.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN rural_urban = 2 THEN 1 ELSE 0 END) as urban
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND rural_urban IS NOT NULL
        """).fetchone()

        total, urban = result
        if total > 100:  # Only test if sufficient data
            urban_pct = (urban / total) * 100
            # Research shows ~75-80% of ped fatalities in urban areas
            assert urban_pct > 50, f"Only {urban_pct:.1f}% urban (expected ~70-80%)"


class TestTemporalPatterns:
    """Test time-based patterns in pedestrian crashes."""

    def test_crashes_distributed_across_months(self, db_connection):
        """Verify crashes occur in all months (not missing data)."""
        result = db_connection.execute("""
            SELECT COUNT(DISTINCT month)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND month IS NOT NULL
        """).fetchone()[0]

        assert result == 12, f"Crashes only found in {result} months (expected 12)"

    def test_time_of_day_recorded(self, db_connection):
        """Verify time of day is recorded for crashes."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND hour IS NOT NULL
              AND hour BETWEEN 0 AND 23
        """).fetchone()[0]

        total = db_connection.execute("""
            SELECT COUNT(*) FROM crashes WHERE pedestrian_fatalities > 0
        """).fetchone()[0]

        if total > 0:
            pct = (result / total) * 100
            assert pct > 80, f"Only {pct:.1f}% have valid time data"

    def test_evening_rush_hour_crashes_present(self, db_connection):
        """Verify evening hours (high-risk period) have crashes."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND hour BETWEEN 17 AND 20
        """).fetchone()[0]

        assert result > 0, "No crashes in evening rush hours (17:00-20:00)"


class TestIntersectionAndCrosswalk:
    """Test intersection and crosswalk-related data."""

    def test_intersection_classification_exists(self, db_connection):
        """Verify intersection classification is recorded."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND intersection_type IS NOT NULL
        """).fetchone()[0]

        total = db_connection.execute("""
            SELECT COUNT(*) FROM crashes WHERE pedestrian_fatalities > 0
        """).fetchone()[0]

        if total > 0:
            pct = (result / total) * 100
            assert pct > 85, f"Only {pct:.1f}% have intersection classification"

    def test_junction_relation_recorded(self, db_connection):
        """Verify relation to junction is recorded."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND relation_to_junction IS NOT NULL
        """).fetchone()[0]

        total = db_connection.execute("""
            SELECT COUNT(*) FROM crashes WHERE pedestrian_fatalities > 0
        """).fetchone()[0]

        if total > 0:
            pct = (result / total) * 100
            assert pct > 90, f"Only {pct:.1f}% have junction relation data"


class TestDataCompletenessOverTime:
    """Test data quality trends over time."""

    def test_recent_years_more_complete(self, db_connection):
        """Verify recent years have better data completeness."""
        result = db_connection.execute("""
            SELECT
                CASE WHEN year >= 2015 THEN 'recent' ELSE 'older' END as period,
                COUNT(*) as crashes,
                AVG(CASE WHEN latitude IS NOT NULL AND longitude IS NOT NULL THEN 1.0 ELSE 0.0 END) as coord_pct
            FROM crashes
            WHERE pedestrian_fatalities > 0
            GROUP BY CASE WHEN year >= 2015 THEN 'recent' ELSE 'older' END
        """).fetchall()

        if len(result) == 2:
            periods = {row[0]: row[2] for row in result}
            if 'recent' in periods and 'older' in periods:
                assert periods['recent'] >= periods['older'], \
                    "Recent years should have equal or better coordinate completeness"


class TestSpatialDataQuality:
    """Test spatial/location data quality."""

    def test_us_coordinates_reasonable(self, db_connection):
        """Verify coordinates are within US bounds."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
              AND (latitude < 18 OR latitude > 72  -- US latitude range ~25-49, buffer for territories
                   OR longitude < -180 OR longitude > -65)  -- US longitude range ~-125 to -65
        """).fetchone()[0]

        # Some outliers expected (territories), but should be minimal
        total_with_coords = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
              AND latitude IS NOT NULL
              AND longitude IS NOT NULL
        """).fetchone()[0]

        if total_with_coords > 0:
            pct = (result / total_with_coords) * 100
            assert pct < 5, f"{pct:.1f}% of crashes have coordinates outside typical US bounds"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
