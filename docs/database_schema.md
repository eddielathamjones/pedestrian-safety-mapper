# DuckDB Database Schema Design
## Pedestrian Safety Mapper - FARS Data

**Last Updated**: November 9, 2025
**Database**: DuckDB 1.1.3 with Spatial Extension
**Data Source**: NHTSA FARS (1975-2022)

---

## Design Principles

1. **Pedestrian-Focused**: Schema optimized for pedestrian fatality analysis
2. **Denormalized for Analytics**: Prioritize query performance over storage
3. **Spatial-First**: All crashes include geometry for mapping
4. **Time-Series Ready**: Optimized for temporal analysis
5. **Star Schema**: Fact table (crashes) with dimension tables

---

## Schema Overview

```
┌─────────────────┐
│     crashes     │◄─────┐
│   (Fact Table)  │      │
└────────┬────────┘      │
         │               │
    ┌────┴────┬──────────┼──────────┬──────────┐
    │         │          │          │          │
┌───▼───┐ ┌──▼──┐ ┌─────▼─────┐ ┌──▼──┐ ┌────▼────┐
│persons│ │peds │ │environment│ │veh. │ │location │
└───────┘ └─────┘ └───────────┘ └─────┘ └─────────┘
```

---

## Core Tables

### 1. `crashes` - Main Fact Table

Primary table containing all crash-level information with spatial data.

```sql
CREATE TABLE crashes (
    -- Primary Key
    crash_id VARCHAR PRIMARY KEY,  -- Format: {YEAR}_{STATE}_{ST_CASE}

    -- Original FARS Identifiers
    state INTEGER,
    state_name VARCHAR,
    st_case INTEGER,  -- FARS case number
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

    -- Spatial Information (PRIMARY FOCUS)
    latitude DECIMAL(10, 8),
    longitude DECIMAL(11, 8),
    geom GEOMETRY,  -- Point geometry (SRID 4326 - WGS84)

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

    -- School Bus Involved
    school_bus_related BOOLEAN,

    -- Railroad Crossing
    rail_crossing VARCHAR,

    -- Notification & Response Times
    notification_hour INTEGER,
    notification_minute INTEGER,
    arrival_hour INTEGER,
    arrival_minute INTEGER,
    hospital_arrival_hour INTEGER,
    hospital_arrival_minute INTEGER,

    -- Crash Severity (CRITICAL METRICS)
    total_fatalities INTEGER,
    pedestrian_fatalities INTEGER,  -- Derived from person records
    total_vehicles INTEGER,
    total_persons INTEGER,

    -- Metadata
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR  -- e.g., 'FARS2022NationalCSV'
);

-- Indexes for performance
CREATE INDEX idx_crashes_year ON crashes(year);
CREATE INDEX idx_crashes_state ON crashes(state);
CREATE INDEX idx_crashes_date ON crashes(crash_date);
CREATE INDEX idx_crashes_pedestrians ON crashes(pedestrian_fatalities) WHERE pedestrian_fatalities > 0;
CREATE INDEX idx_crashes_geom ON crashes USING RTREE(geom);  -- Spatial index
```

---

### 2. `persons` - All Crash Victims

Contains individual-level data for all persons involved in crashes.

```sql
CREATE TABLE persons (
    -- Primary Key
    person_id VARCHAR PRIMARY KEY,  -- Format: {crash_id}_{VEH_NO}_{PER_NO}

    -- Foreign Key
    crash_id VARCHAR REFERENCES crashes(crash_id),

    -- FARS Identifiers
    state INTEGER,
    st_case INTEGER,
    vehicle_number INTEGER,  -- 0 = non-motorist
    person_number INTEGER,
    year INTEGER,

    -- Person Type (CRITICAL)
    person_type INTEGER,
    person_type_name VARCHAR,
    is_pedestrian BOOLEAN,  -- Derived: person_type = 5
    is_bicyclist BOOLEAN,   -- Derived: person_type = 6
    is_non_motorist BOOLEAN, -- Derived: vehicle_number = 0

    -- Demographics
    age INTEGER,
    age_name VARCHAR,
    sex INTEGER,
    sex_name VARCHAR,
    hispanic_origin INTEGER,
    race INTEGER,

    -- Injury Severity (PRIMARY METRIC)
    injury_severity INTEGER,
    injury_severity_name VARCHAR,
    is_fatal BOOLEAN,  -- Derived: injury_severity = 4

    -- Death Details (for fatalities)
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

    -- Occupant Details (if in vehicle)
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

-- Indexes
CREATE INDEX idx_persons_crash ON persons(crash_id);
CREATE INDEX idx_persons_type ON persons(person_type);
CREATE INDEX idx_persons_pedestrian ON persons(is_pedestrian) WHERE is_pedestrian = TRUE;
CREATE INDEX idx_persons_fatal ON persons(is_fatal) WHERE is_fatal = TRUE;
CREATE INDEX idx_persons_age ON persons(age);
CREATE INDEX idx_persons_year ON persons(year);
```

---

### 3. `pedestrian_details` - Pedestrian-Specific Data

Extended details for pedestrian victims from pbtype table.

```sql
CREATE TABLE pedestrian_details (
    -- Primary Key
    ped_detail_id VARCHAR PRIMARY KEY,  -- Same as person_id

    -- Foreign Key
    person_id VARCHAR REFERENCES persons(person_id),
    crash_id VARCHAR REFERENCES crashes(crash_id),

    -- FARS Identifiers
    state INTEGER,
    st_case INTEGER,
    year INTEGER,

    -- Pedestrian Demographics
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

    -- Crash Type Classification (CRITICAL FOR ANALYSIS)
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

-- Indexes
CREATE INDEX idx_peddetails_person ON pedestrian_details(person_id);
CREATE INDEX idx_peddetails_crash ON pedestrian_details(crash_id);
CREATE INDEX idx_peddetails_crashtype ON pedestrian_details(pedestrian_crash_type);
CREATE INDEX idx_peddetails_location ON pedestrian_details(pedestrian_location);
CREATE INDEX idx_peddetails_year ON pedestrian_details(year);
```

---

### 4. `non_motorist_factors` - Contributing Factors

Non-motorist contributing circumstances from nmcrash table.

```sql
CREATE TABLE non_motorist_factors (
    -- Primary Key
    factor_id VARCHAR PRIMARY KEY,  -- {person_id}_{sequence}

    -- Foreign Keys
    person_id VARCHAR REFERENCES persons(person_id),
    crash_id VARCHAR REFERENCES crashes(crash_id),

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

-- Indexes
CREATE INDEX idx_nmfactors_person ON non_motorist_factors(person_id);
CREATE INDEX idx_nmfactors_crash ON non_motorist_factors(crash_id);
CREATE INDEX idx_nmfactors_factor ON non_motorist_factors(contributing_factor);
```

---

### 5. `vehicles` - Vehicle Information

Vehicles involved in crashes (especially those hitting pedestrians).

```sql
CREATE TABLE vehicles (
    -- Primary Key
    vehicle_id VARCHAR PRIMARY KEY,  -- {crash_id}_{VEH_NO}

    -- Foreign Key
    crash_id VARCHAR REFERENCES crashes(crash_id),

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
    vehicle_type VARCHAR,  -- From VPIC decode

    -- Impact Details
    initial_impact_point INTEGER,
    initial_impact_point_name VARCHAR,

    -- Vehicle Maneuver
    vehicle_maneuver INTEGER,
    vehicle_maneuver_name VARCHAR,

    -- Speed & Control
    travel_speed INTEGER,  -- MPH
    speed_limit INTEGER,   -- MPH
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

-- Indexes
CREATE INDEX idx_vehicles_crash ON vehicles(crash_id);
CREATE INDEX idx_vehicles_type ON vehicles(body_type);
CREATE INDEX idx_vehicles_year ON vehicles(year);
CREATE INDEX idx_vehicles_speed ON vehicles(travel_speed);
```

---

### 6. `environment` - Environmental Factors

Denormalized table combining weather, lighting, and road conditions for analysis.

```sql
CREATE TABLE environment (
    -- Primary Key
    env_id VARCHAR PRIMARY KEY,  -- Same as crash_id

    -- Foreign Key
    crash_id VARCHAR REFERENCES crashes(crash_id),

    -- Temporal
    year INTEGER,
    month INTEGER,
    hour INTEGER,

    -- Lighting
    light_condition INTEGER,
    light_condition_name VARCHAR,
    is_dark BOOLEAN,  -- Derived
    is_dawn_dusk BOOLEAN,  -- Derived

    -- Weather
    atmospheric_condition INTEGER,
    atmospheric_condition_name VARCHAR,
    is_rain BOOLEAN,
    is_snow BOOLEAN,
    is_fog BOOLEAN,
    is_clear BOOLEAN,

    -- Road Surface (from roadway table if available)
    road_surface_condition INTEGER,
    road_surface_condition_name VARCHAR,

    -- Metadata
    ingestion_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_env_crash ON environment(crash_id);
CREATE INDEX idx_env_light ON environment(light_condition);
CREATE INDEX idx_env_weather ON environment(atmospheric_condition);
CREATE INDEX idx_env_dark ON environment(is_dark) WHERE is_dark = TRUE;
```

---

## Analytical Views

Pre-computed views for common queries.

### 1. `pedestrian_crashes_view`

All crashes involving pedestrian fatalities with key details.

```sql
CREATE VIEW pedestrian_crashes_view AS
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
GROUP BY c.crash_id, c.year, c.crash_date, c.state_name, c.county_name,
         c.city_name, c.latitude, c.longitude, c.geom, c.pedestrian_fatalities,
         c.rural_urban_name, c.light_condition_name, c.weather_name,
         c.functional_system_name, e.is_dark, e.is_rain, e.is_snow;
```

### 2. `pedestrian_victim_analysis`

Detailed view of pedestrian victims for demographic analysis.

```sql
CREATE VIEW pedestrian_victim_analysis AS
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
```

### 3. `yearly_pedestrian_stats`

Annual statistics for trend analysis.

```sql
CREATE VIEW yearly_pedestrian_stats AS
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
```

---

## Spatial Queries Examples

```sql
-- Find all pedestrian crashes within 5km of a point (e.g., city center)
SELECT crash_id, state_name, crash_date, pedestrian_fatalities
FROM crashes
WHERE pedestrian_fatalities > 0
  AND ST_Distance_Sphere(
      geom,
      ST_GeomFromText('POINT(-118.2437 34.0522)', 4326)
  ) <= 5000;

-- Density analysis: crashes per grid cell (0.1 degree squares)
SELECT
    FLOOR(latitude * 10) / 10 as lat_grid,
    FLOOR(longitude * 10) / 10 as lon_grid,
    COUNT(*) as crash_count,
    SUM(pedestrian_fatalities) as total_deaths
FROM crashes
WHERE pedestrian_fatalities > 0
GROUP BY lat_grid, lon_grid
HAVING crash_count > 5
ORDER BY total_deaths DESC;
```

---

## Data Size Estimates

Based on 48 years of FARS data (1975-2022):

| Table | Estimated Rows | Storage (Parquet) |
|-------|---------------|-------------------|
| crashes | ~2.5M total, ~500K with peds | 150-200 MB |
| persons | ~8M total, ~50K pedestrians | 400-500 MB |
| pedestrian_details | ~50K | 10-15 MB |
| non_motorist_factors | ~100K | 5-10 MB |
| vehicles | ~5M | 300-400 MB |
| environment | ~2.5M | 50-75 MB |
| **Total** | **~18M rows** | **~1.2 GB** |

DuckDB with compression: **~500-800 MB** on disk

---

## Next Steps

1. ✅ Schema designed
2. ⏳ Create database initialization script
3. ⏳ Build ETL pipeline
4. ⏳ Load sample data (2022)
5. ⏳ Validate schema with test queries
6. ⏳ Load historical data (1975-2021)
7. ⏳ Create materialized tables for common queries
8. ⏳ Export to GeoJSON for web mapping

---

## Notes

- **SRID 4326**: Using WGS84 (standard GPS coordinates) for all spatial data
- **Denormalization**: Some redundancy for query performance (e.g., year in multiple tables)
- **Boolean Flags**: Derived fields for common filters (is_pedestrian, is_dark, etc.)
- **Naming Convention**: All names use descriptive text from FARS lookup tables
- **Indexes**: Focused on common query patterns (year, state, spatial, pedestrian filters)
