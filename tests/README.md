# Pedestrian Safety Mapper - Test Suite

Comprehensive test suite for validating data integrity, pedestrian safety metrics, and analytical views in the DuckDB database.

## Overview

This test suite validates the Pedestrian Safety Mapper database against known FARS (Fatality Analysis Reporting System) data characteristics and pedestrian safety research patterns.

## Test Categories

### 1. Database Integrity Tests (`test_database_integrity.py`)

Tests fundamental database structure and data quality:

- **Table Structure**: Verifies all expected tables and views exist
- **Primary Keys**: Ensures crash_id and person_id uniqueness
- **Foreign Keys**: Validates referential integrity between tables
- **Required Fields**: Checks completeness of critical fields
- **Data Ranges**: Validates years, state codes, coordinates, dates
- **Data Quality**: Assesses coordinate completeness, person counts, consistency

**Key Validations**:
- ✓ All 6 core tables exist
- ✓ All 3 analytical views exist
- ✓ Primary keys are unique
- ✓ Foreign key relationships are valid
- ✓ Years within FARS range (1975-present)
- ✓ Geographic coordinates within valid bounds
- ✓ >80% of crashes have coordinates

### 2. Pedestrian Safety Metrics Tests (`test_pedestrian_safety_metrics.py`)

Tests pedestrian-specific data based on traffic safety research:

- **Pedestrian Identification**: Validates person_type=5 and is_pedestrian flags
- **Demographics**: Checks age/sex completeness and reasonableness
- **Environmental Factors**: Tests lighting, weather data completeness
- **Urban/Rural Patterns**: Validates expected urban concentration (~70-80%)
- **Temporal Patterns**: Tests time of day, monthly distribution
- **Intersection Data**: Validates crosswalk and junction data
- **Spatial Quality**: Ensures coordinates are within US bounds

**Key Validations**:
- ✓ Pedestrian flag consistency (person_type=5)
- ✓ >85% have demographic data
- ✓ Dark conditions represent ~50-70% (known risk factor)
- ✓ Majority of crashes are urban (expected pattern)
- ✓ Crashes distributed across all months
- ✓ Evening rush hour crashes present

### 3. Analytical Views Tests (`test_analytical_views.py`)

Tests pre-built analytical views for correctness:

- **View Accessibility**: Ensures all views can be queried
- **Data Filtering**: Validates views contain only expected records
- **Column Completeness**: Checks all expected columns present
- **Consistency**: Verifies view counts match base table counts
- **Performance**: Tests query performance (<5 seconds)

**Views Tested**:
- `pedestrian_crashes_view` - All crashes with pedestrian fatalities
- `pedestrian_victim_analysis` - Fatal pedestrian victim details
- `yearly_pedestrian_stats` - Annual trends and statistics

## Running Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-cov

# Ensure database exists with data
python -m src.database.init_db
python -m src.database.ingest_data --year 2022
```

### Run All Tests

```bash
# From project root
pytest tests/ -v

# With coverage report
pytest tests/ --cov=src/database --cov-report=html

# Run specific test file
pytest tests/test_database_integrity.py -v
```

### Run Specific Test Classes

```bash
# Test only primary key uniqueness
pytest tests/test_database_integrity.py::TestPrimaryKeyUniqueness -v

# Test only pedestrian identification
pytest tests/test_pedestrian_safety_metrics.py::TestPedestrianIdentification -v
```

### Run Specific Tests

```bash
# Test coordinate completeness
pytest tests/test_database_integrity.py::TestDataQuality::test_coordinate_completeness -v

# Test urban/rural pattern
pytest tests/test_pedestrian_safety_metrics.py::TestUrbanRuralPatterns::test_majority_pedestrian_crashes_urban -v
```

## Test Output Examples

### Successful Test Run

```
tests/test_database_integrity.py::TestDatabaseStructure::test_all_tables_exist PASSED
tests/test_database_integrity.py::TestPrimaryKeyUniqueness::test_crashes_primary_key_unique PASSED
tests/test_pedestrian_safety_metrics.py::TestPedestrianIdentification::test_pedestrians_correctly_flagged PASSED

================================ 45 passed in 12.34s ================================
```

### Failed Test Example

```
FAILED tests/test_database_integrity.py::TestDataQuality::test_coordinate_completeness
AssertionError: Only 65.3% of crashes have coordinates (expected >80%)
```

## Expected Test Results

Based on FARS data characteristics:

| Test Category | Expected Pass Rate | Notes |
|---------------|-------------------|-------|
| Database Structure | 100% | All tables/views should exist |
| Primary Keys | 100% | No duplicates allowed |
| Foreign Keys | 100% | All references must be valid |
| Data Ranges | >95% | Some outliers expected |
| Coordinate Completeness | >80% | Improves in recent years |
| Pedestrian Demographics | >85% | Age/sex should be recorded |
| Dark Conditions | 50-70% | Known pedestrian risk pattern |
| Urban Crashes | 70-80% | Expected distribution |

## Test Data Requirements

Tests are designed to work with:
- **Minimum**: 1 year of data (e.g., 2022)
- **Recommended**: 5+ years for trend analysis
- **Optimal**: Full FARS dataset (1975-2022)

## Understanding Test Failures

### Common Reasons for Failures

1. **Incomplete Data Ingestion**: Only partial year loaded
   - Solution: Re-run ingestion for full year

2. **Missing Tables**: pedestrian_details not populated
   - Solution: Fix column mapping in ingest_data.py

3. **Coordinate Completeness**: <80% have lat/lon
   - Expected for older years (pre-2010)
   - Check if spatial extension is loaded

4. **Urban/Rural Pattern**: Not ~70% urban
   - May vary by state/region
   - Check if specific geographic subset

5. **View Consistency**: Counts don't match
   - May indicate aggregation issue
   - Check view definitions in init_db.py

## Adding New Tests

### Test Structure

```python
class TestNewFeature:
    """Test description."""

    def test_specific_aspect(self, db_connection):
        """Test what this validates."""
        result = db_connection.execute("""
            YOUR SQL QUERY HERE
        """).fetchone()[0]

        assert result meets_expectation, "Failure message"
```

### Best Practices

1. **Descriptive Names**: Use clear test and class names
2. **Single Assertion**: One primary assertion per test
3. **Clear Messages**: Provide helpful failure messages
4. **Known Patterns**: Base on FARS documentation/research
5. **Reasonable Thresholds**: Allow for data variation

## Research-Based Test Thresholds

Tests are based on pedestrian safety research:

- **Dark Conditions**: ~70% of pedestrian fatalities occur in dark/dawn/dusk
  - Source: NHTSA Traffic Safety Facts
  - Test threshold: >30% (conservative)

- **Urban Crashes**: ~75% of pedestrian fatalities in urban areas
  - Source: FARS Encyclopedia
  - Test threshold: >50% (conservative)

- **Evening Hours**: Peak risk 18:00-21:00
  - Source: Pedestrian safety research
  - Test: Crashes present in evening hours

- **Demographics**: >90% should have age/sex recorded
  - Source: FARS data quality standards
  - Test threshold: >85% age, >90% sex

## Continuous Integration

To integrate with CI/CD:

```yaml
# .github/workflows/tests.yml
name: Database Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Initialize database
        run: python -m src.database.init_db
      - name: Ingest test data
        run: python -m src.database.ingest_data --year 2022
      - name: Run tests
        run: pytest tests/ -v --cov
```

## Documentation References

- [FARS Analytical User's Manual](https://crashstats.nhtsa.dot.gov/Api/Public/ViewPublication/812827)
- [FARS Encyclopedia](https://www-fars.nhtsa.dot.gov//QueryTool/QuerySection/Report.aspx)
- [Pedestrian Safety Guide](https://safety.fhwa.dot.gov/ped_bike/)

## Contact

For questions about tests or to report issues:
- Create issue on GitHub
- Review FARS documentation for expected patterns
- Check test logs for specific failure details
