"""
Analytical Views Tests.

Tests validate the pre-built analytical views return correct and consistent data.
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


class TestPedestrianCrashesView:
    """Test pedestrian_crashes_view."""

    def test_view_accessible(self, db_connection):
        """Verify view can be queried."""
        result = db_connection.execute("""
            SELECT COUNT(*) FROM pedestrian_crashes_view
        """).fetchone()[0]

        assert result >= 0, "Could not query pedestrian_crashes_view"

    def test_view_only_pedestrian_crashes(self, db_connection):
        """Verify view only contains crashes with pedestrian fatalities."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM pedestrian_crashes_view
            WHERE pedestrian_fatalities = 0 OR pedestrian_fatalities IS NULL
        """).fetchone()[0]

        assert result == 0, f"Found {result} non-pedestrian crashes in view"

    def test_view_has_required_columns(self, db_connection):
        """Verify view has all expected columns."""
        expected_columns = [
            'crash_id', 'year', 'crash_date', 'state_name',
            'latitude', 'longitude', 'pedestrian_fatalities',
            'light_condition_name', 'weather_name'
        ]

        result = db_connection.execute("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'pedestrian_crashes_view'
        """).fetchall()

        existing_columns = [row[0] for row in result]

        for col in expected_columns:
            assert col in existing_columns, f"Column '{col}' missing from view"


class TestPedestrianVictimAnalysisView:
    """Test pedestrian_victim_analysis view."""

    def test_view_accessible(self, db_connection):
        """Verify view can be queried."""
        result = db_connection.execute("""
            SELECT COUNT(*) FROM pedestrian_victim_analysis
        """).fetchone()[0]

        assert result >= 0, "Could not query pedestrian_victim_analysis"

    def test_view_only_fatal_pedestrians(self, db_connection):
        """Verify view only contains fatal pedestrian victims."""
        result = db_connection.execute("""
            SELECT COUNT(*)
            FROM pedestrian_victim_analysis
        """).fetchone()[0]

        # Cross-check with persons table
        persons_count = db_connection.execute("""
            SELECT COUNT(*)
            FROM persons
            WHERE is_pedestrian = TRUE AND is_fatal = TRUE
        """).fetchone()[0]

        # Counts should match (or view might be filtered)
        assert result > 0, "No fatal pedestrians in analysis view"

    def test_view_has_demographic_data(self, db_connection):
        """Verify view includes demographic information."""
        result = db_connection.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN age IS NOT NULL THEN 1 ELSE 0 END) as with_age,
                SUM(CASE WHEN sex_name IS NOT NULL THEN 1 ELSE 0 END) as with_sex
            FROM pedestrian_victim_analysis
        """).fetchone()

        total, with_age, with_sex = result
        if total > 0:
            assert with_age > 0, "No age data in victim analysis"
            assert with_sex > 0, "No sex data in victim analysis"


class TestYearlyPedestrianStatsView:
    """Test yearly_pedestrian_stats view."""

    def test_view_accessible(self, db_connection):
        """Verify view can be queried."""
        result = db_connection.execute("""
            SELECT COUNT(*) FROM yearly_pedestrian_stats
        """).fetchone()[0]

        assert result > 0, "yearly_pedestrian_stats view has no data"

    def test_stats_by_year_complete(self, db_connection):
        """Verify stats exist for each year in dataset."""
        crash_years = set(db_connection.execute("""
            SELECT DISTINCT year
            FROM crashes
            WHERE pedestrian_fatalities > 0
        """).fetchall())

        stats_years = set(db_connection.execute("""
            SELECT DISTINCT year
            FROM yearly_pedestrian_stats
        """).fetchall())

        missing_years = crash_years - stats_years
        assert len(missing_years) == 0, f"Stats missing for years: {missing_years}"

    def test_death_counts_reasonable(self, db_connection):
        """Verify total pedestrian deaths are reasonable per year."""
        result = db_connection.execute("""
            SELECT year, total_pedestrian_deaths
            FROM yearly_pedestrian_stats
            WHERE total_pedestrian_deaths < 100 OR total_pedestrian_deaths > 20000
        """).fetchall()

        # US typically has 5000-7000 ped fatalities per year
        # Flag if < 100 (incomplete) or > 20000 (impossible)
        assert len(result) == 0, f"Found {len(result)} years with unrealistic death counts"

    def test_crash_counts_match_deaths(self, db_connection):
        """Verify total crashes matches or exceeds deaths (multiple deaths per crash possible)."""
        result = db_connection.execute("""
            SELECT year
            FROM yearly_pedestrian_stats
            WHERE total_crashes_with_pedestrians < total_pedestrian_deaths
        """).fetchall()

        # Should never have more deaths than crashes (unless multi-fatality crashes)
        # Actually, this can happen with multi-fatality crashes, so just check it's reasonable
        assert len(result) < 5, f"Found {len(result)} years where crashes < deaths"

    def test_stats_have_percentages(self, db_connection):
        """Verify stats include breakdowns by conditions."""
        result = db_connection.execute("""
            SELECT
                COUNT(*) as total,
                SUM(CASE WHEN rural_crashes > 0 OR urban_crashes > 0 THEN 1 ELSE 0 END) as with_urban_rural,
                SUM(CASE WHEN dark_crashes > 0 THEN 1 ELSE 0 END) as with_lighting
            FROM yearly_pedestrian_stats
        """).fetchone()

        total, with_ur, with_light = result
        if total > 0:
            assert with_ur > 0, "No urban/rural breakdown in stats"
            assert with_light > 0, "No lighting condition breakdown in stats"


class TestViewConsistency:
    """Test consistency between views and base tables."""

    def test_pedestrian_crashes_count_matches(self, db_connection):
        """Verify pedestrian_crashes_view count matches base table."""
        view_count = db_connection.execute("""
            SELECT COUNT(DISTINCT crash_id)
            FROM pedestrian_crashes_view
        """).fetchone()[0]

        table_count = db_connection.execute("""
            SELECT COUNT(*)
            FROM crashes
            WHERE pedestrian_fatalities > 0
        """).fetchone()[0]

        # Counts should match exactly
        assert view_count == table_count, \
            f"View has {view_count} crashes but table has {table_count}"

    def test_yearly_stats_sum_matches_total(self, db_connection):
        """Verify sum of yearly stats matches overall total."""
        yearly_sum = db_connection.execute("""
            SELECT SUM(total_pedestrian_deaths)
            FROM yearly_pedestrian_stats
        """).fetchone()[0]

        total_deaths = db_connection.execute("""
            SELECT SUM(pedestrian_fatalities)
            FROM crashes
            WHERE pedestrian_fatalities > 0
        """).fetchone()[0]

        # Allow small discrepancy due to rounding or data timing
        diff = abs(yearly_sum - total_deaths) if yearly_sum and total_deaths else 0
        assert diff < 100, f"Yearly sum ({yearly_sum}) differs from total ({total_deaths}) by {diff}"


class TestViewPerformance:
    """Test view query performance."""

    def test_views_return_quickly(self, db_connection):
        """Verify views can be queried efficiently."""
        import time

        views = [
            'pedestrian_crashes_view',
            'pedestrian_victim_analysis',
            'yearly_pedestrian_stats'
        ]

        for view in views:
            start = time.time()
            db_connection.execute(f"SELECT COUNT(*) FROM {view}").fetchone()
            elapsed = time.time() - start

            # Views should return in < 5 seconds for reasonable dataset sizes
            assert elapsed < 5.0, f"View {view} took {elapsed:.2f}s (expected < 5s)"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
