-- FARS Multi-Sensory Database - Useful Views
-- Create views for common query patterns and analysis

-- ============================================================================
-- Comprehensive Crash View
-- ============================================================================

-- View combining all data sources for each crash
CREATE OR REPLACE VIEW vw_crash_complete AS
SELECT
    -- Basic crash info
    c.crash_id,
    c.state,
    c.city,
    c.county,
    c.latitude,
    c.longitude,
    c.geom,
    c.intersection,
    c.crash_date,
    c.crash_time,
    c.crash_datetime,
    c.time_of_day,
    c.severity,
    c.vehicle_type,
    c.vehicle_speed,

    -- Sound data
    s.mean_loudness_db,
    s.peak_loudness_db,
    s.traffic_intensity as sound_traffic_intensity,
    s.source as sound_source,

    -- Air quality
    aq.pm2_5,
    aq.pm10,
    aq.aqi,
    aq.aqi_category,
    aq.source as aq_source,
    aq.sensor_distance_meters,

    -- Weather
    w.temperature_f,
    w.feels_like_f,
    w.humidity,
    w.precipitation_inches,
    w.wind_speed_mph,
    w.visibility_miles,
    w.conditions as weather_conditions,
    w.is_precipitation,
    w.is_extreme_heat,
    w.is_extreme_cold,
    w.poor_visibility,

    -- Lighting
    l.lighting_condition,
    l.streetlights_within_50m,
    l.streetlights_within_100m,
    l.viirs_nighttime_radiance,

    -- Computer vision analysis
    ar.cv_has_crosswalk,
    ar.cv_has_sidewalk,
    ar.cv_has_signal,
    ar.cv_green_view_index,
    ar.infrastructure_grade,
    ar.environmental_stress_score,
    ar.pedestrian_safety_score,

    -- Flags
    ar.high_noise,
    ar.poor_air_quality,
    ar.extreme_temperature,
    ar.insufficient_lighting,
    ar.missing_infrastructure,

    -- Metadata
    c.data_complete,
    c.last_updated

FROM crashes c
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id;

-- ============================================================================
-- High Risk Locations View
-- ============================================================================

-- Crashes with multiple environmental stressors
CREATE OR REPLACE VIEW vw_high_risk_crashes AS
SELECT
    crash_id,
    intersection,
    city,
    state,
    crash_date,
    latitude,
    longitude,
    geom,

    -- Environmental factors
    mean_loudness_db,
    pm2_5,
    aqi_category,
    temperature_f,
    weather_conditions,
    lighting_condition,
    streetlights_within_50m,

    -- Infrastructure
    cv_has_crosswalk,
    cv_has_sidewalk,
    cv_has_signal,
    infrastructure_grade,

    -- Scores
    environmental_stress_score,
    pedestrian_safety_score,

    -- Count number of risk factors
    (
        CASE WHEN high_noise THEN 1 ELSE 0 END +
        CASE WHEN poor_air_quality THEN 1 ELSE 0 END +
        CASE WHEN extreme_temperature THEN 1 ELSE 0 END +
        CASE WHEN insufficient_lighting THEN 1 ELSE 0 END +
        CASE WHEN missing_infrastructure THEN 1 ELSE 0 END
    ) as risk_factor_count

FROM vw_crash_complete
WHERE
    high_noise OR
    poor_air_quality OR
    extreme_temperature OR
    insufficient_lighting OR
    missing_infrastructure
ORDER BY risk_factor_count DESC, environmental_stress_score DESC;

-- ============================================================================
-- Infrastructure Deficiency View
-- ============================================================================

-- Crashes at locations with missing critical infrastructure
CREATE OR REPLACE VIEW vw_infrastructure_deficient AS
SELECT
    c.crash_id,
    c.intersection,
    c.city,
    c.county,
    c.state,
    c.latitude,
    c.longitude,
    c.geom,
    c.crash_date,
    c.severity,

    -- What's missing
    CASE WHEN ar.cv_has_crosswalk = FALSE THEN 'Missing' ELSE 'Present' END as crosswalk_status,
    CASE WHEN ar.cv_has_sidewalk = FALSE THEN 'Missing' ELSE 'Present' END as sidewalk_status,
    CASE WHEN ar.cv_has_signal = FALSE THEN 'Missing' ELSE 'Present' END as signal_status,
    CASE WHEN l.streetlights_within_50m < 1 THEN 'Insufficient' ELSE 'Adequate' END as lighting_status,

    -- Analysis
    ar.infrastructure_grade,
    ar.pedestrian_safety_score,

    -- Count deficiencies
    (
        CASE WHEN ar.cv_has_crosswalk = FALSE THEN 1 ELSE 0 END +
        CASE WHEN ar.cv_has_sidewalk = FALSE THEN 1 ELSE 0 END +
        CASE WHEN ar.cv_has_signal = FALSE THEN 1 ELSE 0 END +
        CASE WHEN l.streetlights_within_50m < 1 THEN 1 ELSE 0 END
    ) as deficiency_count

FROM crashes c
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
WHERE
    ar.cv_has_crosswalk = FALSE OR
    ar.cv_has_sidewalk = FALSE OR
    ar.cv_has_signal = FALSE OR
    l.streetlights_within_50m < 1
ORDER BY deficiency_count DESC, c.crash_date DESC;

-- ============================================================================
-- Environmental Justice View
-- ============================================================================

-- Aggregate environmental conditions by county
CREATE OR REPLACE VIEW vw_county_environmental_summary AS
SELECT
    c.county,
    c.state,
    COUNT(DISTINCT c.crash_id) as total_crashes,

    -- Air quality
    ROUND(AVG(aq.pm2_5)::numeric, 2) as avg_pm25,
    ROUND(AVG(aq.aqi)::numeric, 1) as avg_aqi,
    COUNT(CASE WHEN aq.aqi_category IN ('Unhealthy', 'Very Unhealthy', 'Hazardous') THEN 1 END) as poor_aq_days,

    -- Sound
    ROUND(AVG(s.mean_loudness_db)::numeric, 1) as avg_noise_db,
    COUNT(CASE WHEN s.mean_loudness_db > 75 THEN 1 END) as high_noise_count,

    -- Temperature extremes
    COUNT(CASE WHEN w.is_extreme_heat THEN 1 END) as extreme_heat_count,
    COUNT(CASE WHEN w.is_extreme_cold THEN 1 END) as extreme_cold_count,

    -- Infrastructure
    COUNT(CASE WHEN ar.cv_has_crosswalk = FALSE THEN 1 END) as no_crosswalk_count,
    COUNT(CASE WHEN ar.cv_has_sidewalk = FALSE THEN 1 END) as no_sidewalk_count,
    ROUND(AVG(l.streetlights_within_50m)::numeric, 1) as avg_streetlights,

    -- Scores
    ROUND(AVG(ar.environmental_stress_score)::numeric, 1) as avg_stress_score,
    ROUND(AVG(ar.pedestrian_safety_score)::numeric, 1) as avg_safety_score,
    ROUND(AVG(
        CASE ar.infrastructure_grade
            WHEN 'A' THEN 4.0
            WHEN 'B' THEN 3.0
            WHEN 'C' THEN 2.0
            WHEN 'D' THEN 1.0
            WHEN 'F' THEN 0.0
        END
    )::numeric, 2) as avg_infrastructure_gpa

FROM crashes c
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
WHERE c.county IS NOT NULL
GROUP BY c.county, c.state
HAVING COUNT(DISTINCT c.crash_id) >= 3
ORDER BY total_crashes DESC;

-- ============================================================================
-- Temporal Patterns View
-- ============================================================================

-- Hourly crash patterns with environmental context
CREATE OR REPLACE VIEW vw_hourly_patterns AS
SELECT
    EXTRACT(HOUR FROM c.crash_time) as hour_of_day,
    COUNT(*) as crash_count,

    -- Environmental averages
    ROUND(AVG(s.mean_loudness_db)::numeric, 1) as avg_sound_db,
    ROUND(AVG(w.temperature_f)::numeric, 1) as avg_temp_f,
    ROUND(AVG(aq.pm2_5)::numeric, 2) as avg_pm25,
    ROUND(AVG(w.visibility_miles)::numeric, 2) as avg_visibility,

    -- Condition counts
    COUNT(CASE WHEN l.lighting_condition = 'dark' THEN 1 END) as dark_count,
    COUNT(CASE WHEN w.is_precipitation THEN 1 END) as precipitation_count,
    COUNT(CASE WHEN ar.missing_infrastructure THEN 1 END) as poor_infrastructure_count,

    -- Average scores
    ROUND(AVG(ar.environmental_stress_score)::numeric, 1) as avg_stress_score

FROM crashes c
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
WHERE c.crash_time IS NOT NULL
GROUP BY EXTRACT(HOUR FROM c.crash_time)
ORDER BY hour_of_day;

-- ============================================================================
-- Data Quality View
-- ============================================================================

-- Track data completeness for each crash
CREATE OR REPLACE VIEW vw_data_completeness AS
SELECT
    c.crash_id,
    c.intersection,
    c.city,
    c.state,
    c.crash_date,
    c.data_complete,

    -- Data availability flags
    CASE WHEN sv.image_count > 0 THEN TRUE ELSE FALSE END as has_streetview,
    CASE WHEN s.crash_id IS NOT NULL THEN TRUE ELSE FALSE END as has_sound,
    CASE WHEN aq.crash_id IS NOT NULL THEN TRUE ELSE FALSE END as has_air_quality,
    CASE WHEN w.crash_id IS NOT NULL THEN TRUE ELSE FALSE END as has_weather,
    CASE WHEN l.crash_id IS NOT NULL THEN TRUE ELSE FALSE END as has_lighting,
    CASE WHEN ar.crash_id IS NOT NULL THEN TRUE ELSE FALSE END as has_analysis,

    -- Image count
    COALESCE(sv.image_count, 0) as streetview_image_count,

    -- Completeness percentage
    ROUND(
        100.0 * (
            CASE WHEN sv.image_count > 0 THEN 1 ELSE 0 END +
            CASE WHEN s.crash_id IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN aq.crash_id IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN w.crash_id IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN l.crash_id IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN ar.crash_id IS NOT NULL THEN 1 ELSE 0 END
        ) / 6.0,
        1
    ) as completeness_percentage

FROM crashes c
LEFT JOIN (
    SELECT crash_id, COUNT(*) as image_count
    FROM streetview_images
    GROUP BY crash_id
) sv ON c.crash_id = sv.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM sound_data) s ON c.crash_id = s.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM air_quality) aq ON c.crash_id = aq.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM weather) w ON c.crash_id = w.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM lighting) l ON c.crash_id = l.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM analysis_results) ar ON c.crash_id = ar.crash_id
ORDER BY completeness_percentage DESC, c.crash_date DESC;

-- ============================================================================
-- Crash Hotspot View
-- ============================================================================

-- Identify areas with clusters of crashes (within 500m)
CREATE OR REPLACE VIEW vw_crash_hotspots AS
SELECT
    c1.crash_id,
    c1.intersection,
    c1.city,
    c1.county,
    c1.state,
    c1.latitude,
    c1.longitude,
    c1.geom,
    COUNT(DISTINCT c2.crash_id) as nearby_crashes_500m,

    -- Average conditions in hotspot
    ROUND(AVG(ar2.environmental_stress_score)::numeric, 1) as avg_area_stress,
    ROUND(AVG(ar2.pedestrian_safety_score)::numeric, 1) as avg_area_safety,
    COUNT(CASE WHEN ar2.infrastructure_grade IN ('D', 'F') THEN 1 END) as poor_infrastructure_nearby

FROM crashes c1
LEFT JOIN crashes c2 ON
    c1.crash_id != c2.crash_id AND
    c1.geom IS NOT NULL AND
    c2.geom IS NOT NULL AND
    ST_DWithin(c1.geom::geography, c2.geom::geography, 500)
LEFT JOIN analysis_results ar2 ON c2.crash_id = ar2.crash_id
WHERE c1.geom IS NOT NULL
GROUP BY c1.crash_id, c1.intersection, c1.city, c1.county, c1.state, c1.latitude, c1.longitude, c1.geom
HAVING COUNT(DISTINCT c2.crash_id) >= 2
ORDER BY nearby_crashes_500m DESC;

-- ============================================================================
-- Monthly Trends View
-- ============================================================================

-- Monthly aggregation of crashes and environmental conditions
CREATE OR REPLACE VIEW vw_monthly_trends AS
SELECT
    DATE_TRUNC('month', c.crash_date)::date as month,
    EXTRACT(YEAR FROM c.crash_date) as year,
    EXTRACT(MONTH FROM c.crash_date) as month_num,
    COUNT(*) as crash_count,

    -- Environmental averages
    ROUND(AVG(aq.pm2_5)::numeric, 2) as avg_pm25,
    ROUND(AVG(aq.aqi)::numeric, 1) as avg_aqi,
    ROUND(AVG(s.mean_loudness_db)::numeric, 1) as avg_noise,
    ROUND(AVG(w.temperature_f)::numeric, 1) as avg_temperature,

    -- Condition counts
    COUNT(CASE WHEN w.is_precipitation THEN 1 END) as precipitation_crashes,
    COUNT(CASE WHEN w.is_extreme_heat OR w.is_extreme_cold THEN 1 END) as extreme_temp_crashes,
    COUNT(CASE WHEN aq.aqi_category IN ('Unhealthy', 'Very Unhealthy', 'Hazardous') THEN 1 END) as poor_aq_crashes,

    -- Infrastructure
    COUNT(CASE WHEN ar.infrastructure_grade IN ('D', 'F') THEN 1 END) as poor_infrastructure_count,
    ROUND(AVG(ar.pedestrian_safety_score)::numeric, 1) as avg_safety_score

FROM crashes c
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
WHERE c.crash_date IS NOT NULL
GROUP BY DATE_TRUNC('month', c.crash_date), EXTRACT(YEAR FROM c.crash_date), EXTRACT(MONTH FROM c.crash_date)
ORDER BY month DESC;

-- ============================================================================
-- Summary Statistics View
-- ============================================================================

-- Overall database statistics
CREATE OR REPLACE VIEW vw_database_summary AS
SELECT
    COUNT(DISTINCT c.crash_id) as total_crashes,
    COUNT(DISTINCT c.state) as states_covered,
    COUNT(DISTINCT c.county) as counties_covered,
    COUNT(DISTINCT c.city) as cities_covered,
    MIN(c.crash_date) as earliest_crash,
    MAX(c.crash_date) as latest_crash,

    -- Data coverage
    COUNT(DISTINCT sv.crash_id) as crashes_with_streetview,
    COUNT(DISTINCT s.crash_id) as crashes_with_sound,
    COUNT(DISTINCT aq.crash_id) as crashes_with_air_quality,
    COUNT(DISTINCT w.crash_id) as crashes_with_weather,
    COUNT(DISTINCT l.crash_id) as crashes_with_lighting,
    COUNT(DISTINCT ar.crash_id) as crashes_with_analysis,

    -- Percentages
    ROUND(100.0 * COUNT(DISTINCT sv.crash_id) / NULLIF(COUNT(DISTINCT c.crash_id), 0), 1) as streetview_coverage_pct,
    ROUND(100.0 * COUNT(DISTINCT s.crash_id) / NULLIF(COUNT(DISTINCT c.crash_id), 0), 1) as sound_coverage_pct,
    ROUND(100.0 * COUNT(DISTINCT aq.crash_id) / NULLIF(COUNT(DISTINCT c.crash_id), 0), 1) as aq_coverage_pct,
    ROUND(100.0 * COUNT(DISTINCT w.crash_id) / NULLIF(COUNT(DISTINCT c.crash_id), 0), 1) as weather_coverage_pct,
    ROUND(100.0 * COUNT(DISTINCT l.crash_id) / NULLIF(COUNT(DISTINCT c.crash_id), 0), 1) as lighting_coverage_pct,
    ROUND(100.0 * COUNT(DISTINCT ar.crash_id) / NULLIF(COUNT(DISTINCT c.crash_id), 0), 1) as analysis_coverage_pct,

    -- Complete records
    COUNT(CASE WHEN c.data_complete THEN 1 END) as complete_records,
    ROUND(100.0 * COUNT(CASE WHEN c.data_complete THEN 1 END) / NULLIF(COUNT(DISTINCT c.crash_id), 0), 1) as complete_pct

FROM crashes c
LEFT JOIN streetview_images sv ON c.crash_id = sv.crash_id
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id;

-- ============================================================================
-- Grant permissions (adjust as needed for your database users)
-- ============================================================================

-- Example: GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_readonly_user;
-- Example: GRANT SELECT ON ALL TABLES IN SCHEMA public TO your_app_user;
