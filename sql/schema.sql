-- FARS Multi-Sensory Pedestrian Crash Database Schema
-- This schema supports comprehensive environmental and infrastructure analysis
-- of pedestrian crash locations

-- Enable PostGIS extension for geographic data
CREATE EXTENSION IF NOT EXISTS postgis;

-- ============================================================================
-- Core Tables
-- ============================================================================

-- Main crashes table
CREATE TABLE crashes (
    crash_id VARCHAR(50) PRIMARY KEY,
    state VARCHAR(2),
    city VARCHAR(100),
    county VARCHAR(100),

    -- Location
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    geom GEOMETRY(Point, 4326),  -- PostGIS geometry column
    intersection VARCHAR(200),

    -- Temporal
    crash_date DATE,
    crash_time TIME,
    crash_datetime TIMESTAMP,
    time_of_day VARCHAR(20), -- 'day', 'night', 'dawn', 'dusk'

    -- Victim information (if available/consented)
    victim_name VARCHAR(100),
    victim_age INTEGER,
    victim_gender VARCHAR(10),

    -- Crash characteristics
    severity VARCHAR(20),
    vehicle_type VARCHAR(50),
    vehicle_speed INTEGER,
    vehicle_direction INTEGER, -- degrees, 0-360

    -- Infrastructure (from visual analysis)
    has_crosswalk BOOLEAN,
    has_signal BOOLEAN,
    has_sidewalk BOOLEAN,
    distance_to_crosswalk DECIMAL(10, 2), -- feet

    -- Metadata
    data_complete BOOLEAN DEFAULT FALSE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    -- Constraints
    CHECK (latitude BETWEEN -90 AND 90),
    CHECK (longitude BETWEEN -180 AND 180),
    CHECK (vehicle_direction BETWEEN 0 AND 360 OR vehicle_direction IS NULL)
);

-- Create index on geography for spatial queries
CREATE INDEX idx_crashes_geom ON crashes USING GIST(geom);
CREATE INDEX idx_crashes_datetime ON crashes(crash_datetime);
CREATE INDEX idx_crashes_state ON crashes(state);
CREATE INDEX idx_crashes_complete ON crashes(data_complete);

-- ============================================================================
-- Street View Images
-- ============================================================================

CREATE TABLE streetview_images (
    image_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Image metadata
    image_url TEXT,
    local_path VARCHAR(500),
    source VARCHAR(50), -- 'mapillary', 'google', etc.

    -- Capture info
    captured_at TIMESTAMP,
    compass_angle INTEGER, -- 0-360
    camera_latitude DECIMAL(10, 7),
    camera_longitude DECIMAL(10, 7),
    camera_geom GEOMETRY(Point, 4326),

    -- Analysis results (populated later by computer vision)
    has_crosswalk_detected BOOLEAN,
    has_signal_detected BOOLEAN,
    has_sidewalk_detected BOOLEAN,
    green_view_index DECIMAL(5, 2),
    road_width_pixels INTEGER,
    vehicle_count INTEGER,

    -- Metadata
    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_size_kb INTEGER,

    -- Constraints
    CHECK (compass_angle BETWEEN 0 AND 360 OR compass_angle IS NULL),
    CHECK (green_view_index BETWEEN 0 AND 100 OR green_view_index IS NULL)
);

CREATE INDEX idx_streetview_crash ON streetview_images(crash_id);
CREATE INDEX idx_streetview_source ON streetview_images(source);
CREATE INDEX idx_streetview_geom ON streetview_images USING GIST(camera_geom);

-- ============================================================================
-- Sound Data
-- ============================================================================

CREATE TABLE sound_data (
    sound_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Recording info
    source VARCHAR(50), -- 'aporee', 'field_recording', 'modeled'
    recording_url TEXT,
    local_path VARCHAR(500),

    -- Temporal
    recorded_at TIMESTAMP,
    duration_seconds INTEGER,

    -- Measurements
    mean_loudness_db DECIMAL(5, 2),
    peak_loudness_db DECIMAL(5, 2),
    traffic_intensity DECIMAL(8, 2),
    spectral_brightness DECIMAL(8, 2),
    num_acoustic_events INTEGER,
    events_per_minute DECIMAL(5, 2),

    -- Metadata
    sample_rate INTEGER,
    channels INTEGER,
    download_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (duration_seconds > 0 OR duration_seconds IS NULL),
    CHECK (channels IN (1, 2) OR channels IS NULL)
);

CREATE INDEX idx_sound_crash ON sound_data(crash_id);
CREATE INDEX idx_sound_source ON sound_data(source);

-- ============================================================================
-- Air Quality
-- ============================================================================

CREATE TABLE air_quality (
    aq_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Source
    source VARCHAR(50), -- 'purpleair', 'epa', 'openaq'
    sensor_id VARCHAR(100),
    sensor_distance_meters DECIMAL(10, 2),

    -- Temporal
    measurement_time TIMESTAMP,

    -- Measurements
    pm2_5 DECIMAL(6, 2),
    pm10 DECIMAL(6, 2),
    no2 DECIMAL(6, 2),
    o3 DECIMAL(6, 2),
    co DECIMAL(6, 2),
    aqi INTEGER,
    aqi_category VARCHAR(50), -- 'Good', 'Moderate', 'Unhealthy for Sensitive Groups', 'Unhealthy', 'Very Unhealthy', 'Hazardous'

    -- Environmental
    temperature_f DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    pressure DECIMAL(7, 2),

    -- Metadata
    data_quality VARCHAR(20),
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (aqi BETWEEN 0 AND 500 OR aqi IS NULL),
    CHECK (humidity BETWEEN 0 AND 100 OR humidity IS NULL)
);

CREATE INDEX idx_aq_crash ON air_quality(crash_id);
CREATE INDEX idx_aq_source ON air_quality(source);
CREATE INDEX idx_aq_time ON air_quality(measurement_time);

-- ============================================================================
-- Weather
-- ============================================================================

CREATE TABLE weather (
    weather_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Source
    source VARCHAR(50), -- 'visualcrossing', 'noaa', 'openweather'

    -- Temporal (matched to crash time)
    observation_time TIMESTAMP,

    -- Measurements
    temperature_f DECIMAL(5, 2),
    feels_like_f DECIMAL(5, 2),
    humidity DECIMAL(5, 2),
    precipitation_inches DECIMAL(5, 3),
    wind_speed_mph DECIMAL(5, 2),
    wind_direction INTEGER,
    visibility_miles DECIMAL(5, 2),
    cloud_cover DECIMAL(5, 2),
    uv_index DECIMAL(3, 1),

    -- Conditions
    conditions VARCHAR(100), -- 'Clear', 'Rain', 'Fog', etc.
    weather_description TEXT,

    -- Derived flags
    is_precipitation BOOLEAN,
    is_extreme_heat BOOLEAN, -- > 100°F
    is_extreme_cold BOOLEAN, -- < 32°F
    poor_visibility BOOLEAN, -- < 2 miles

    -- Metadata
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (wind_direction BETWEEN 0 AND 360 OR wind_direction IS NULL),
    CHECK (humidity BETWEEN 0 AND 100 OR humidity IS NULL),
    CHECK (cloud_cover BETWEEN 0 AND 100 OR cloud_cover IS NULL)
);

CREATE INDEX idx_weather_crash ON weather(crash_id);
CREATE INDEX idx_weather_source ON weather(source);
CREATE INDEX idx_weather_conditions ON weather(conditions);

-- ============================================================================
-- Lighting
-- ============================================================================

CREATE TABLE lighting (
    lighting_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Street lights
    streetlights_within_50m INTEGER,
    streetlights_within_100m INTEGER,
    nearest_streetlight_distance_m DECIMAL(10, 2),

    -- Satellite nighttime brightness
    viirs_nighttime_radiance DECIMAL(10, 4),

    -- Temporal lighting
    sunrise_time TIME,
    sunset_time TIME,
    lighting_condition VARCHAR(20), -- 'daylight', 'dark', 'dawn', 'dusk'

    -- Metadata
    source VARCHAR(50),
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (streetlights_within_50m >= 0 OR streetlights_within_50m IS NULL),
    CHECK (streetlights_within_100m >= 0 OR streetlights_within_100m IS NULL)
);

CREATE INDEX idx_lighting_crash ON lighting(crash_id);
CREATE INDEX idx_lighting_condition ON lighting(lighting_condition);

-- ============================================================================
-- Analysis Results
-- ============================================================================

CREATE TABLE analysis_results (
    analysis_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Visual analysis (computer vision)
    cv_has_crosswalk BOOLEAN,
    cv_has_signal BOOLEAN,
    cv_has_sidewalk BOOLEAN,
    cv_road_width_pixels INTEGER,
    cv_vehicle_count INTEGER,
    cv_green_view_index DECIMAL(5, 2),
    cv_confidence DECIMAL(4, 3),

    -- Composite scores
    infrastructure_grade VARCHAR(2), -- A-F
    environmental_stress_score DECIMAL(5, 2), -- 0-100
    pedestrian_safety_score DECIMAL(5, 2), -- 0-100

    -- Multi-sensory flags
    high_noise BOOLEAN,
    poor_air_quality BOOLEAN,
    extreme_temperature BOOLEAN,
    insufficient_lighting BOOLEAN,
    missing_infrastructure BOOLEAN,

    -- Metadata
    analysis_version VARCHAR(20),
    analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    notes TEXT,

    -- Constraints
    CHECK (cv_green_view_index BETWEEN 0 AND 100 OR cv_green_view_index IS NULL),
    CHECK (cv_confidence BETWEEN 0 AND 1 OR cv_confidence IS NULL),
    CHECK (environmental_stress_score BETWEEN 0 AND 100 OR environmental_stress_score IS NULL),
    CHECK (pedestrian_safety_score BETWEEN 0 AND 100 OR pedestrian_safety_score IS NULL),
    CHECK (infrastructure_grade IN ('A', 'B', 'C', 'D', 'F') OR infrastructure_grade IS NULL)
);

CREATE INDEX idx_analysis_crash ON analysis_results(crash_id);
CREATE INDEX idx_analysis_grade ON analysis_results(infrastructure_grade);
CREATE INDEX idx_analysis_safety_score ON analysis_results(pedestrian_safety_score);

-- ============================================================================
-- Functions and Triggers
-- ============================================================================

-- Function to automatically update geom column when lat/lon changes
CREATE OR REPLACE FUNCTION update_crash_geom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
        NEW.geom = ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update geom on insert or update
CREATE TRIGGER trigger_update_crash_geom
    BEFORE INSERT OR UPDATE OF latitude, longitude ON crashes
    FOR EACH ROW
    EXECUTE FUNCTION update_crash_geom();

-- Function to update camera_geom for street view images
CREATE OR REPLACE FUNCTION update_streetview_geom()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.camera_latitude IS NOT NULL AND NEW.camera_longitude IS NOT NULL THEN
        NEW.camera_geom = ST_SetSRID(ST_MakePoint(NEW.camera_longitude, NEW.camera_latitude), 4326);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for street view image geometry
CREATE TRIGGER trigger_update_streetview_geom
    BEFORE INSERT OR UPDATE OF camera_latitude, camera_longitude ON streetview_images
    FOR EACH ROW
    EXECUTE FUNCTION update_streetview_geom();

-- Function to automatically update last_updated timestamp
CREATE OR REPLACE FUNCTION update_last_updated()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update last_updated
CREATE TRIGGER trigger_update_crash_timestamp
    BEFORE UPDATE ON crashes
    FOR EACH ROW
    EXECUTE FUNCTION update_last_updated();

-- ============================================================================
-- Additional Data Source Tables
-- ============================================================================

-- Traffic data from counts, sensors, and models
CREATE TABLE traffic_data (
    traffic_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Traffic volumes
    aadt INTEGER, -- Annual Average Daily Traffic
    peak_hour_volume INTEGER,
    pedestrian_volume INTEGER,
    bicycle_volume INTEGER,

    -- Speed
    posted_speed_limit INTEGER,
    observed_85th_percentile_speed INTEGER,
    observed_mean_speed INTEGER,

    -- Source and timing
    source VARCHAR(100),
    measurement_date DATE,
    measurement_type VARCHAR(50), -- 'count', 'model', 'sensor'
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (aadt >= 0 OR aadt IS NULL),
    CHECK (posted_speed_limit > 0 OR posted_speed_limit IS NULL)
);

CREATE INDEX idx_traffic_crash ON traffic_data(crash_id);
CREATE INDEX idx_traffic_source ON traffic_data(source);

-- Demographics and socioeconomic data from Census/ACS
CREATE TABLE demographics (
    demo_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,
    census_tract VARCHAR(20),
    census_block_group VARCHAR(20),

    -- Population
    total_population INTEGER,
    population_density DECIMAL(10, 2), -- per square mile

    -- Economics
    median_income INTEGER,
    per_capita_income INTEGER,
    poverty_rate DECIMAL(5, 2),
    unemployment_rate DECIMAL(5, 2),
    gini_index DECIMAL(4, 3), -- Income inequality

    -- Transportation
    percent_no_vehicle DECIMAL(5, 2),
    percent_walk_to_work DECIMAL(5, 2),
    percent_transit_to_work DECIMAL(5, 2),
    percent_bike_to_work DECIMAL(5, 2),
    mean_commute_time DECIMAL(5, 2),

    -- Demographics
    median_age DECIMAL(5, 2),
    percent_under_18 DECIMAL(5, 2),
    percent_over_65 DECIMAL(5, 2),
    percent_minority DECIMAL(5, 2),
    percent_limited_english DECIMAL(5, 2),

    -- Vulnerability
    social_vulnerability_index DECIMAL(4, 2), -- CDC SVI

    -- Source
    source VARCHAR(100),
    year INTEGER,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (poverty_rate BETWEEN 0 AND 100 OR poverty_rate IS NULL),
    CHECK (unemployment_rate BETWEEN 0 AND 100 OR unemployment_rate IS NULL)
);

CREATE INDEX idx_demo_crash ON demographics(crash_id);
CREATE INDEX idx_demo_tract ON demographics(census_tract);
CREATE INDEX idx_demo_svi ON demographics(social_vulnerability_index);

-- Land use and built environment characteristics
CREATE TABLE land_use (
    land_use_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Density metrics
    building_density_per_acre DECIMAL(8, 2),
    population_density_per_sq_mi DECIMAL(10, 2),
    employment_density_per_sq_mi DECIMAL(10, 2),

    -- Coverage metrics
    impervious_surface_percent DECIMAL(5, 2),
    tree_canopy_percent DECIMAL(5, 2),
    green_space_percent DECIMAL(5, 2),

    -- Land use classification
    zoning_category VARCHAR(50),
    primary_land_use VARCHAR(50), -- 'residential', 'commercial', 'industrial', etc.
    is_mixed_use BOOLEAN,
    walkability_score DECIMAL(5, 2), -- 0-100 if available

    -- Activity generators within 0.25 miles (400m)
    schools_nearby INTEGER,
    transit_stops_nearby INTEGER,
    parks_nearby INTEGER,
    retail_establishments_nearby INTEGER,
    restaurants_nearby INTEGER,
    healthcare_facilities_nearby INTEGER,

    -- Source
    source VARCHAR(100),
    data_year INTEGER,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (impervious_surface_percent BETWEEN 0 AND 100 OR impervious_surface_percent IS NULL),
    CHECK (tree_canopy_percent BETWEEN 0 AND 100 OR tree_canopy_percent IS NULL)
);

CREATE INDEX idx_landuse_crash ON land_use(crash_id);
CREATE INDEX idx_landuse_type ON land_use(primary_land_use);
CREATE INDEX idx_landuse_mixed ON land_use(is_mixed_use);

-- OpenStreetMap infrastructure data
CREATE TABLE osm_infrastructure (
    osm_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Road characteristics
    road_class VARCHAR(50), -- 'motorway', 'primary', 'secondary', 'residential', etc.
    road_name VARCHAR(200),
    number_of_lanes INTEGER,
    lane_width_meters DECIMAL(5, 2),
    road_width_meters DECIMAL(6, 2),
    surface_type VARCHAR(50), -- 'asphalt', 'concrete', 'gravel', etc.
    max_speed_kph INTEGER,
    max_speed_mph INTEGER,

    -- Infrastructure presence
    has_sidewalk BOOLEAN,
    sidewalk_both_sides BOOLEAN,
    has_bike_lane BOOLEAN,
    bike_lane_protected BOOLEAN,
    has_median BOOLEAN,
    has_buffer BOOLEAN,
    is_one_way BOOLEAN,
    is_lit BOOLEAN, -- Street lighting per OSM

    -- Nearby features (distances in meters)
    distance_to_crosswalk_m DECIMAL(8, 2),
    distance_to_signal_m DECIMAL(8, 2),
    distance_to_transit_m DECIMAL(8, 2),
    distance_to_school_m DECIMAL(8, 2),

    -- Intersection characteristics (if applicable)
    is_intersection BOOLEAN,
    intersection_type VARCHAR(50), -- 'signalized', 'stop', 'yield', 'uncontrolled', 'roundabout'
    number_of_approaches INTEGER,
    has_pedestrian_signal BOOLEAN,
    has_crosswalk_marking BOOLEAN,

    -- OSM metadata
    osm_way_id BIGINT,
    osm_node_id BIGINT,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (number_of_lanes > 0 OR number_of_lanes IS NULL),
    CHECK (number_of_approaches >= 3 OR number_of_approaches IS NULL)
);

CREATE INDEX idx_osm_crash ON osm_infrastructure(crash_id);
CREATE INDEX idx_osm_road_class ON osm_infrastructure(road_class);
CREATE INDEX idx_osm_intersection ON osm_infrastructure(is_intersection);
CREATE INDEX idx_osm_way_id ON osm_infrastructure(osm_way_id);

-- Historical changes and interventions
CREATE TABLE historical_changes (
    change_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- What changed
    change_type VARCHAR(100), -- 'crosswalk_added', 'signal_installed', 'speed_limit_reduced', etc.
    change_date DATE,
    change_description TEXT,

    -- Before/after conditions
    condition_before TEXT,
    condition_after TEXT,

    -- Relationship to crash
    days_after_crash INTEGER, -- negative if before crash, positive if after
    was_response_to_crash BOOLEAN,
    intervention_cost DECIMAL(12, 2), -- if known

    -- Source and documentation
    source VARCHAR(100),
    documentation_url TEXT,
    verified BOOLEAN DEFAULT FALSE,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_changes_crash ON historical_changes(crash_id);
CREATE INDEX idx_changes_type ON historical_changes(change_type);
CREATE INDEX idx_changes_date ON historical_changes(change_date);

-- Transit accessibility data
CREATE TABLE transit_access (
    transit_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Nearby transit
    nearest_stop_distance_m DECIMAL(8, 2),
    stops_within_400m INTEGER, -- Quarter mile
    stops_within_800m INTEGER, -- Half mile

    -- Service quality
    routes_available INTEGER,
    weekday_frequency DECIMAL(6, 2), -- trips per hour
    weekend_frequency DECIMAL(6, 2),
    hours_of_service DECIMAL(5, 2), -- hours per day

    -- Stop characteristics
    nearest_stop_name VARCHAR(200),
    nearest_stop_amenities TEXT, -- 'shelter', 'bench', 'lighting', etc.
    has_accessible_stop BOOLEAN,

    -- Source
    source VARCHAR(100), -- GTFS feed source
    gtfs_stop_id VARCHAR(100),
    service_date DATE,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_transit_crash ON transit_access(crash_id);
CREATE INDEX idx_transit_distance ON transit_access(nearest_stop_distance_m);

-- Crime and safety data
CREATE TABLE crime_data (
    crime_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Crime within radius (typically 500m)
    search_radius_m DECIMAL(8, 2),
    time_window_months INTEGER, -- Crime in last N months before crash

    -- Crime counts by type
    violent_crime_count INTEGER,
    property_crime_count INTEGER,
    total_crime_count INTEGER,

    -- Crime density
    crime_density_per_sq_km DECIMAL(8, 2),

    -- Safety perception
    safety_score DECIMAL(5, 2), -- 0-100 if available from surveys

    -- Source
    source VARCHAR(100),
    data_start_date DATE,
    data_end_date DATE,
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_crime_crash ON crime_data(crash_id);

-- School zones and education facilities
CREATE TABLE schools (
    school_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- School information
    school_name VARCHAR(200),
    school_type VARCHAR(50), -- 'elementary', 'middle', 'high', 'college'
    enrollment INTEGER,
    distance_to_crash_m DECIMAL(8, 2),

    -- School zone
    in_school_zone BOOLEAN,
    school_zone_speed_limit INTEGER,
    has_crossing_guard BOOLEAN,
    has_school_zone_signage BOOLEAN,

    -- Timing
    school_hours_start TIME,
    school_hours_end TIME,
    crash_during_school_hours BOOLEAN,

    -- Source
    source VARCHAR(100),
    nces_id VARCHAR(20), -- National Center for Education Statistics ID
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_schools_crash ON schools(crash_id);
CREATE INDEX idx_schools_zone ON schools(in_school_zone);

-- Elevation and terrain data
CREATE TABLE terrain (
    terrain_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Elevation
    elevation_meters DECIMAL(8, 2),
    elevation_feet DECIMAL(8, 2),

    -- Slope
    slope_degrees DECIMAL(5, 2),
    slope_percent DECIMAL(5, 2),
    slope_category VARCHAR(20), -- 'flat', 'mild', 'moderate', 'steep'

    -- Aspect (direction of slope)
    aspect_degrees DECIMAL(5, 2), -- 0-360
    aspect_cardinal VARCHAR(3), -- N, NE, E, SE, S, SW, W, NW

    -- Viewshed analysis
    viewshed_area_sq_m DECIMAL(12, 2), -- Visible area from point
    visibility_score DECIMAL(5, 2), -- Relative visibility (0-100)

    -- Source
    source VARCHAR(100), -- 'USGS NED', 'LiDAR', etc.
    resolution_meters DECIMAL(6, 2),
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Constraints
    CHECK (slope_degrees BETWEEN 0 AND 90 OR slope_degrees IS NULL),
    CHECK (aspect_degrees BETWEEN 0 AND 360 OR aspect_degrees IS NULL)
);

CREATE INDEX idx_terrain_crash ON terrain(crash_id);
CREATE INDEX idx_terrain_slope ON terrain(slope_category);

-- Parking data
CREATE TABLE parking (
    parking_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- On-street parking
    on_street_parking_present BOOLEAN,
    parking_side VARCHAR(20), -- 'both', 'left', 'right', 'none'
    parking_type VARCHAR(50), -- 'parallel', 'angled', 'perpendicular'

    -- Parking restrictions
    parking_time_limit VARCHAR(50),
    parking_cost_per_hour DECIMAL(6, 2),
    has_parking_meters BOOLEAN,

    -- Nearby parking facilities
    parking_lots_within_100m INTEGER,
    parking_garages_within_200m INTEGER,

    -- Parking occupancy (if available)
    estimated_occupancy_percent DECIMAL(5, 2),

    -- Source
    source VARCHAR(100),
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_parking_crash ON parking(crash_id);

-- Events and special circumstances
CREATE TABLE special_events (
    event_id SERIAL PRIMARY KEY,
    crash_id VARCHAR(50) REFERENCES crashes(crash_id) ON DELETE CASCADE,

    -- Event details
    event_name VARCHAR(200),
    event_type VARCHAR(100), -- 'concert', 'sports', 'festival', 'parade', etc.
    event_start_time TIMESTAMP,
    event_end_time TIMESTAMP,
    expected_attendance INTEGER,

    -- Location relative to crash
    event_distance_m DECIMAL(8, 2),
    crash_during_event BOOLEAN,
    crash_within_1hr_of_event BOOLEAN,

    -- Impact
    road_closures TEXT,
    detour_routes TEXT,
    increased_pedestrian_activity BOOLEAN,

    -- Source
    source VARCHAR(100),
    retrieved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_crash ON special_events(crash_id);
CREATE INDEX idx_events_during ON special_events(crash_during_event);
