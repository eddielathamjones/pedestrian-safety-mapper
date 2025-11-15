-- FARS Multi-Sensory Database - Example Queries
-- Collection of useful queries for analyzing pedestrian crash data

-- ============================================================================
-- Multi-Sensory Environmental Stressor Analysis
-- ============================================================================

-- Find crashes with multiple environmental stressors
-- (high noise, poor air quality, extreme temperature, inadequate lighting, missing infrastructure)
SELECT
    c.crash_id,
    c.intersection,
    c.city,
    c.state,
    c.crash_date,
    s.mean_loudness_db as sound_db,
    aq.pm2_5,
    aq.aqi_category,
    w.temperature_f,
    l.streetlights_within_50m,
    ar.cv_has_crosswalk,
    ar.cv_has_sidewalk,
    ar.infrastructure_grade,
    ar.environmental_stress_score
FROM crashes c
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
WHERE
    (s.mean_loudness_db > 75 OR s.mean_loudness_db IS NULL) AND
    (aq.pm2_5 > 35 OR aq.aqi_category IN ('Unhealthy', 'Very Unhealthy', 'Hazardous')) AND
    (w.temperature_f > 100 OR w.temperature_f < 32) AND
    (l.streetlights_within_50m < 2 OR l.streetlights_within_50m IS NULL) AND
    (ar.cv_has_crosswalk = FALSE OR ar.cv_has_sidewalk = FALSE)
ORDER BY c.crash_date DESC;

-- ============================================================================
-- Environmental Justice Analysis
-- ============================================================================

-- Compare environmental conditions and infrastructure across counties
SELECT
    c.county,
    c.state,
    COUNT(*) as crash_count,
    ROUND(AVG(aq.pm2_5)::numeric, 2) as avg_pm25,
    ROUND(AVG(aq.aqi)::numeric, 1) as avg_aqi,
    ROUND(AVG(s.mean_loudness_db)::numeric, 1) as avg_noise_db,
    SUM(CASE WHEN ar.cv_has_crosswalk = FALSE THEN 1 ELSE 0 END) as no_crosswalk_count,
    SUM(CASE WHEN ar.cv_has_sidewalk = FALSE THEN 1 ELSE 0 END) as no_sidewalk_count,
    ROUND(AVG(l.streetlights_within_50m)::numeric, 1) as avg_streetlights,
    ROUND(AVG(ar.environmental_stress_score)::numeric, 1) as avg_stress_score,
    ROUND(AVG(ar.pedestrian_safety_score)::numeric, 1) as avg_safety_score
FROM crashes c
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
WHERE c.county IS NOT NULL
GROUP BY c.county, c.state
HAVING COUNT(*) >= 5  -- Only counties with at least 5 crashes
ORDER BY crash_count DESC;

-- ============================================================================
-- Temporal Pattern Analysis
-- ============================================================================

-- Crashes by hour of day with environmental conditions
SELECT
    EXTRACT(HOUR FROM c.crash_time) as hour_of_day,
    COUNT(*) as crashes,
    ROUND(AVG(s.mean_loudness_db)::numeric, 1) as avg_sound_db,
    ROUND(AVG(w.temperature_f)::numeric, 1) as avg_temp,
    ROUND(AVG(aq.pm2_5)::numeric, 2) as avg_pm25,
    SUM(CASE WHEN l.lighting_condition = 'dark' THEN 1 ELSE 0 END) as dark_conditions,
    SUM(CASE WHEN w.is_precipitation THEN 1 ELSE 0 END) as precipitation_count
FROM crashes c
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
WHERE c.crash_time IS NOT NULL
GROUP BY hour_of_day
ORDER BY hour_of_day;

-- Day vs night crash comparison
SELECT
    c.time_of_day,
    COUNT(*) as crash_count,
    ROUND(AVG(w.visibility_miles)::numeric, 2) as avg_visibility,
    ROUND(AVG(l.streetlights_within_50m)::numeric, 1) as avg_streetlights,
    SUM(CASE WHEN ar.insufficient_lighting THEN 1 ELSE 0 END) as poor_lighting_count,
    SUM(CASE WHEN ar.cv_has_crosswalk = FALSE THEN 1 ELSE 0 END) as no_crosswalk
FROM crashes c
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
WHERE c.time_of_day IN ('day', 'night')
GROUP BY c.time_of_day;

-- ============================================================================
-- Infrastructure Analysis
-- ============================================================================

-- Crashes without critical infrastructure
SELECT
    c.crash_id,
    c.intersection,
    c.city,
    c.state,
    c.crash_date,
    ar.cv_has_crosswalk,
    ar.cv_has_sidewalk,
    ar.cv_has_signal,
    l.streetlights_within_50m,
    ar.infrastructure_grade,
    c.severity
FROM crashes c
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
WHERE
    (ar.cv_has_crosswalk = FALSE OR
     ar.cv_has_sidewalk = FALSE OR
     ar.cv_has_signal = FALSE OR
     l.streetlights_within_50m < 1)
ORDER BY
    CASE c.severity
        WHEN 'Fatal' THEN 1
        WHEN 'Serious' THEN 2
        ELSE 3
    END,
    c.crash_date DESC;

-- Infrastructure grade distribution
SELECT
    infrastructure_grade,
    COUNT(*) as crash_count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) as percentage,
    ROUND(AVG(pedestrian_safety_score)::numeric, 1) as avg_safety_score
FROM analysis_results
WHERE infrastructure_grade IS NOT NULL
GROUP BY infrastructure_grade
ORDER BY infrastructure_grade;

-- ============================================================================
-- Air Quality Impact Analysis
-- ============================================================================

-- Crashes during poor air quality events
SELECT
    c.crash_id,
    c.intersection,
    c.crash_date,
    aq.aqi,
    aq.aqi_category,
    aq.pm2_5,
    aq.pm10,
    aq.sensor_distance_meters,
    w.temperature_f,
    w.humidity
FROM crashes c
INNER JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
WHERE aq.aqi_category IN ('Unhealthy', 'Very Unhealthy', 'Hazardous')
ORDER BY aq.aqi DESC;

-- Average air quality by season
SELECT
    EXTRACT(MONTH FROM c.crash_date) as month,
    CASE
        WHEN EXTRACT(MONTH FROM c.crash_date) IN (12, 1, 2) THEN 'Winter'
        WHEN EXTRACT(MONTH FROM c.crash_date) IN (3, 4, 5) THEN 'Spring'
        WHEN EXTRACT(MONTH FROM c.crash_date) IN (6, 7, 8) THEN 'Summer'
        ELSE 'Fall'
    END as season,
    COUNT(*) as crash_count,
    ROUND(AVG(aq.pm2_5)::numeric, 2) as avg_pm25,
    ROUND(AVG(aq.aqi)::numeric, 1) as avg_aqi,
    ROUND(AVG(w.temperature_f)::numeric, 1) as avg_temp
FROM crashes c
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
WHERE EXTRACT(MONTH FROM c.crash_date) IS NOT NULL
GROUP BY month, season
ORDER BY month;

-- ============================================================================
-- Weather Pattern Analysis
-- ============================================================================

-- Crashes during adverse weather
SELECT
    w.conditions,
    COUNT(*) as crash_count,
    ROUND(AVG(w.visibility_miles)::numeric, 2) as avg_visibility,
    ROUND(AVG(w.wind_speed_mph)::numeric, 1) as avg_wind_speed,
    SUM(CASE WHEN w.is_precipitation THEN 1 ELSE 0 END) as with_precipitation
FROM crashes c
INNER JOIN weather w ON c.crash_id = w.crash_id
WHERE w.conditions IS NOT NULL
GROUP BY w.conditions
HAVING COUNT(*) >= 3
ORDER BY crash_count DESC;

-- ============================================================================
-- Geospatial Analysis
-- ============================================================================

-- Find crashes within a specific radius of a point (example: downtown Tucson)
-- Replace the coordinates with your area of interest
SELECT
    c.crash_id,
    c.intersection,
    c.crash_date,
    ST_Distance(
        c.geom::geography,
        ST_SetSRID(ST_MakePoint(-110.9747, 32.2226), 4326)::geography
    ) / 1609.34 as distance_miles,
    ar.infrastructure_grade,
    ar.environmental_stress_score
FROM crashes c
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
WHERE ST_DWithin(
    c.geom::geography,
    ST_SetSRID(ST_MakePoint(-110.9747, 32.2226), 4326)::geography,
    8046.72  -- 5 miles in meters
)
ORDER BY distance_miles;

-- Crash density hotspots (crashes within 500m of each other)
SELECT
    c1.crash_id,
    c1.intersection,
    c1.latitude,
    c1.longitude,
    COUNT(DISTINCT c2.crash_id) as nearby_crashes
FROM crashes c1
LEFT JOIN crashes c2 ON
    c1.crash_id != c2.crash_id AND
    ST_DWithin(c1.geom::geography, c2.geom::geography, 500)  -- 500 meters
WHERE c1.geom IS NOT NULL
GROUP BY c1.crash_id, c1.intersection, c1.latitude, c1.longitude
HAVING COUNT(DISTINCT c2.crash_id) >= 3
ORDER BY nearby_crashes DESC;

-- ============================================================================
-- Data Completeness Analysis
-- ============================================================================

-- Check data completeness across all tables
SELECT
    COUNT(DISTINCT c.crash_id) as total_crashes,
    COUNT(DISTINCT CASE WHEN c.data_complete THEN c.crash_id END) as complete_crashes,
    COUNT(DISTINCT sv.crash_id) as with_streetview,
    COUNT(DISTINCT s.crash_id) as with_sound,
    COUNT(DISTINCT aq.crash_id) as with_air_quality,
    COUNT(DISTINCT w.crash_id) as with_weather,
    COUNT(DISTINCT l.crash_id) as with_lighting,
    COUNT(DISTINCT ar.crash_id) as with_analysis,
    ROUND(100.0 * COUNT(DISTINCT sv.crash_id) / COUNT(DISTINCT c.crash_id), 1) as streetview_pct,
    ROUND(100.0 * COUNT(DISTINCT s.crash_id) / COUNT(DISTINCT c.crash_id), 1) as sound_pct,
    ROUND(100.0 * COUNT(DISTINCT aq.crash_id) / COUNT(DISTINCT c.crash_id), 1) as air_quality_pct,
    ROUND(100.0 * COUNT(DISTINCT w.crash_id) / COUNT(DISTINCT c.crash_id), 1) as weather_pct,
    ROUND(100.0 * COUNT(DISTINCT l.crash_id) / COUNT(DISTINCT c.crash_id), 1) as lighting_pct,
    ROUND(100.0 * COUNT(DISTINCT ar.crash_id) / COUNT(DISTINCT c.crash_id), 1) as analysis_pct
FROM crashes c
LEFT JOIN streetview_images sv ON c.crash_id = sv.crash_id
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id;

-- Crashes missing specific data types
SELECT
    c.crash_id,
    c.intersection,
    c.city,
    c.state,
    c.crash_date,
    CASE WHEN sv.crash_id IS NULL THEN 'Missing' ELSE 'Present' END as streetview,
    CASE WHEN s.crash_id IS NULL THEN 'Missing' ELSE 'Present' END as sound,
    CASE WHEN aq.crash_id IS NULL THEN 'Missing' ELSE 'Present' END as air_quality,
    CASE WHEN w.crash_id IS NULL THEN 'Missing' ELSE 'Present' END as weather,
    CASE WHEN l.crash_id IS NULL THEN 'Missing' ELSE 'Present' END as lighting,
    CASE WHEN ar.crash_id IS NULL THEN 'Missing' ELSE 'Present' END as analysis
FROM crashes c
LEFT JOIN (SELECT DISTINCT crash_id FROM streetview_images) sv ON c.crash_id = sv.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM sound_data) s ON c.crash_id = s.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM air_quality) aq ON c.crash_id = aq.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM weather) w ON c.crash_id = w.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM lighting) l ON c.crash_id = l.crash_id
LEFT JOIN (SELECT DISTINCT crash_id FROM analysis_results) ar ON c.crash_id = ar.crash_id
WHERE
    sv.crash_id IS NULL OR
    s.crash_id IS NULL OR
    aq.crash_id IS NULL OR
    w.crash_id IS NULL OR
    l.crash_id IS NULL OR
    ar.crash_id IS NULL
ORDER BY c.crash_date DESC
LIMIT 100;

-- ============================================================================
-- Comprehensive Crash Profile
-- ============================================================================

-- Get complete multi-sensory profile for a specific crash
-- Replace 'CRASH_ID_HERE' with actual crash ID
SELECT
    -- Basic info
    c.crash_id,
    c.intersection,
    c.city,
    c.state,
    c.crash_date,
    c.crash_time,
    c.time_of_day,
    c.severity,

    -- Sound
    s.mean_loudness_db,
    s.peak_loudness_db,
    s.traffic_intensity,

    -- Air quality
    aq.pm2_5,
    aq.aqi,
    aq.aqi_category,

    -- Weather
    w.temperature_f,
    w.conditions,
    w.visibility_miles,
    w.is_precipitation,

    -- Lighting
    l.lighting_condition,
    l.streetlights_within_50m,

    -- Infrastructure
    ar.cv_has_crosswalk,
    ar.cv_has_sidewalk,
    ar.cv_has_signal,
    ar.infrastructure_grade,

    -- Scores
    ar.environmental_stress_score,
    ar.pedestrian_safety_score,

    -- Flags
    ar.high_noise,
    ar.poor_air_quality,
    ar.extreme_temperature,
    ar.insufficient_lighting,
    ar.missing_infrastructure
FROM crashes c
LEFT JOIN sound_data s ON c.crash_id = s.crash_id
LEFT JOIN air_quality aq ON c.crash_id = aq.crash_id
LEFT JOIN weather w ON c.crash_id = w.crash_id
LEFT JOIN lighting l ON c.crash_id = l.crash_id
LEFT JOIN analysis_results ar ON c.crash_id = ar.crash_id
WHERE c.crash_id = 'CRASH_ID_HERE';
