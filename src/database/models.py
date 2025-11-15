"""
SQLAlchemy ORM models for FARS Multi-Sensory Database

These models correspond to the database schema defined in sql/schema.sql
Use these for ORM-based queries and data manipulation
"""

from datetime import datetime, date, time
from typing import Optional

from sqlalchemy import (
    Column, Integer, String, DECIMAL, Boolean, DateTime, Date, Time,
    Text, TIMESTAMP, ForeignKey, CheckConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry

Base = declarative_base()


class Crash(Base):
    """Main crashes table"""
    __tablename__ = 'crashes'

    crash_id = Column(String(50), primary_key=True)
    state = Column(String(2))
    city = Column(String(100))
    county = Column(String(100))

    # Location
    latitude = Column(DECIMAL(10, 7))
    longitude = Column(DECIMAL(10, 7))
    geom = Column(Geometry('POINT', srid=4326))
    intersection = Column(String(200))

    # Temporal
    crash_date = Column(Date)
    crash_time = Column(Time)
    crash_datetime = Column(TIMESTAMP)
    time_of_day = Column(String(20))

    # Victim information
    victim_name = Column(String(100))
    victim_age = Column(Integer)
    victim_gender = Column(String(10))

    # Crash characteristics
    severity = Column(String(20))
    vehicle_type = Column(String(50))
    vehicle_speed = Column(Integer)
    vehicle_direction = Column(Integer)

    # Infrastructure
    has_crosswalk = Column(Boolean)
    has_signal = Column(Boolean)
    has_sidewalk = Column(Boolean)
    distance_to_crosswalk = Column(DECIMAL(10, 2))

    # Metadata
    data_complete = Column(Boolean, default=False)
    last_updated = Column(TIMESTAMP, default=datetime.utcnow)
    notes = Column(Text)

    # Relationships
    streetview_images = relationship("StreetviewImage", back_populates="crash", cascade="all, delete-orphan")
    sound_data = relationship("SoundData", back_populates="crash", cascade="all, delete-orphan")
    air_quality = relationship("AirQuality", back_populates="crash", cascade="all, delete-orphan")
    weather = relationship("Weather", back_populates="crash", cascade="all, delete-orphan")
    lighting = relationship("Lighting", back_populates="crash", cascade="all, delete-orphan")
    analysis_results = relationship("AnalysisResults", back_populates="crash", cascade="all, delete-orphan")


class StreetviewImage(Base):
    """Street view images table"""
    __tablename__ = 'streetview_images'

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    crash_id = Column(String(50), ForeignKey('crashes.crash_id', ondelete='CASCADE'))

    # Image metadata
    image_url = Column(Text)
    local_path = Column(String(500))
    source = Column(String(50))

    # Capture info
    captured_at = Column(TIMESTAMP)
    compass_angle = Column(Integer)
    camera_latitude = Column(DECIMAL(10, 7))
    camera_longitude = Column(DECIMAL(10, 7))
    camera_geom = Column(Geometry('POINT', srid=4326))

    # Analysis results
    has_crosswalk_detected = Column(Boolean)
    has_signal_detected = Column(Boolean)
    has_sidewalk_detected = Column(Boolean)
    green_view_index = Column(DECIMAL(5, 2))
    road_width_pixels = Column(Integer)
    vehicle_count = Column(Integer)

    # Metadata
    download_date = Column(TIMESTAMP, default=datetime.utcnow)
    file_size_kb = Column(Integer)

    # Relationship
    crash = relationship("Crash", back_populates="streetview_images")


class SoundData(Base):
    """Sound data table"""
    __tablename__ = 'sound_data'

    sound_id = Column(Integer, primary_key=True, autoincrement=True)
    crash_id = Column(String(50), ForeignKey('crashes.crash_id', ondelete='CASCADE'))

    # Recording info
    source = Column(String(50))
    recording_url = Column(Text)
    local_path = Column(String(500))

    # Temporal
    recorded_at = Column(TIMESTAMP)
    duration_seconds = Column(Integer)

    # Measurements
    mean_loudness_db = Column(DECIMAL(5, 2))
    peak_loudness_db = Column(DECIMAL(5, 2))
    traffic_intensity = Column(DECIMAL(8, 2))
    spectral_brightness = Column(DECIMAL(8, 2))
    num_acoustic_events = Column(Integer)
    events_per_minute = Column(DECIMAL(5, 2))

    # Metadata
    sample_rate = Column(Integer)
    channels = Column(Integer)
    download_date = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    crash = relationship("Crash", back_populates="sound_data")


class AirQuality(Base):
    """Air quality table"""
    __tablename__ = 'air_quality'

    aq_id = Column(Integer, primary_key=True, autoincrement=True)
    crash_id = Column(String(50), ForeignKey('crashes.crash_id', ondelete='CASCADE'))

    # Source
    source = Column(String(50))
    sensor_id = Column(String(100))
    sensor_distance_meters = Column(DECIMAL(10, 2))

    # Temporal
    measurement_time = Column(TIMESTAMP)

    # Measurements
    pm2_5 = Column(DECIMAL(6, 2))
    pm10 = Column(DECIMAL(6, 2))
    no2 = Column(DECIMAL(6, 2))
    o3 = Column(DECIMAL(6, 2))
    co = Column(DECIMAL(6, 2))
    aqi = Column(Integer)
    aqi_category = Column(String(50))

    # Environmental
    temperature_f = Column(DECIMAL(5, 2))
    humidity = Column(DECIMAL(5, 2))
    pressure = Column(DECIMAL(7, 2))

    # Metadata
    data_quality = Column(String(20))
    retrieved_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    crash = relationship("Crash", back_populates="air_quality")


class Weather(Base):
    """Weather table"""
    __tablename__ = 'weather'

    weather_id = Column(Integer, primary_key=True, autoincrement=True)
    crash_id = Column(String(50), ForeignKey('crashes.crash_id', ondelete='CASCADE'))

    # Source
    source = Column(String(50))
    observation_time = Column(TIMESTAMP)

    # Measurements
    temperature_f = Column(DECIMAL(5, 2))
    feels_like_f = Column(DECIMAL(5, 2))
    humidity = Column(DECIMAL(5, 2))
    precipitation_inches = Column(DECIMAL(5, 3))
    wind_speed_mph = Column(DECIMAL(5, 2))
    wind_direction = Column(Integer)
    visibility_miles = Column(DECIMAL(5, 2))
    cloud_cover = Column(DECIMAL(5, 2))
    uv_index = Column(DECIMAL(3, 1))

    # Conditions
    conditions = Column(String(100))
    weather_description = Column(Text)

    # Derived flags
    is_precipitation = Column(Boolean)
    is_extreme_heat = Column(Boolean)
    is_extreme_cold = Column(Boolean)
    poor_visibility = Column(Boolean)

    # Metadata
    retrieved_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    crash = relationship("Crash", back_populates="weather")


class Lighting(Base):
    """Lighting table"""
    __tablename__ = 'lighting'

    lighting_id = Column(Integer, primary_key=True, autoincrement=True)
    crash_id = Column(String(50), ForeignKey('crashes.crash_id', ondelete='CASCADE'))

    # Street lights
    streetlights_within_50m = Column(Integer)
    streetlights_within_100m = Column(Integer)
    nearest_streetlight_distance_m = Column(DECIMAL(10, 2))

    # Satellite nighttime brightness
    viirs_nighttime_radiance = Column(DECIMAL(10, 4))

    # Temporal lighting
    sunrise_time = Column(Time)
    sunset_time = Column(Time)
    lighting_condition = Column(String(20))

    # Metadata
    source = Column(String(50))
    retrieved_at = Column(TIMESTAMP, default=datetime.utcnow)

    # Relationship
    crash = relationship("Crash", back_populates="lighting")


class AnalysisResults(Base):
    """Analysis results table"""
    __tablename__ = 'analysis_results'

    analysis_id = Column(Integer, primary_key=True, autoincrement=True)
    crash_id = Column(String(50), ForeignKey('crashes.crash_id', ondelete='CASCADE'))

    # Visual analysis
    cv_has_crosswalk = Column(Boolean)
    cv_has_signal = Column(Boolean)
    cv_has_sidewalk = Column(Boolean)
    cv_road_width_pixels = Column(Integer)
    cv_vehicle_count = Column(Integer)
    cv_green_view_index = Column(DECIMAL(5, 2))
    cv_confidence = Column(DECIMAL(4, 3))

    # Composite scores
    infrastructure_grade = Column(String(2))
    environmental_stress_score = Column(DECIMAL(5, 2))
    pedestrian_safety_score = Column(DECIMAL(5, 2))

    # Multi-sensory flags
    high_noise = Column(Boolean)
    poor_air_quality = Column(Boolean)
    extreme_temperature = Column(Boolean)
    insufficient_lighting = Column(Boolean)
    missing_infrastructure = Column(Boolean)

    # Metadata
    analysis_version = Column(String(20))
    analyzed_at = Column(TIMESTAMP, default=datetime.utcnow)
    notes = Column(Text)

    # Relationship
    crash = relationship("Crash", back_populates="analysis_results")


# ============================================================================
# Additional Data Source Models
# ============================================================================

class TrafficData(Base):
    """Traffic data model"""
    __tablename__ = 'traffic_data'

    traffic_id = Column(Integer, primary_key=True, autoincrement=True)
    crash_id = Column(String(50), ForeignKey('crashes.crash_id', ondelete='CASCADE'))

    aadt = Column(Integer)
    peak_hour_volume = Column(Integer)
    pedestrian_volume = Column(Integer)
    bicycle_volume = Column(Integer)

    posted_speed_limit = Column(Integer)
    observed_85th_percentile_speed = Column(Integer)
    observed_mean_speed = Column(Integer)

    source = Column(String(100))
    measurement_date = Column(Date)
    measurement_type = Column(String(50))
    retrieved_at = Column(TIMESTAMP, default=datetime.utcnow)


class Demographics(Base):
    """Demographics model"""
    __tablename__ = 'demographics'

    demo_id = Column(Integer, primary_key=True, autoincrement=True)
    crash_id = Column(String(50), ForeignKey('crashes.crash_id', ondelete='CASCADE'))
    census_tract = Column(String(20))
    census_block_group = Column(String(20))

    total_population = Column(Integer)
    population_density = Column(DECIMAL(10, 2))

    median_income = Column(Integer)
    per_capita_income = Column(Integer)
    poverty_rate = Column(DECIMAL(5, 2))
    unemployment_rate = Column(DECIMAL(5, 2))
    gini_index = Column(DECIMAL(4, 3))

    percent_no_vehicle = Column(DECIMAL(5, 2))
    percent_walk_to_work = Column(DECIMAL(5, 2))
    percent_transit_to_work = Column(DECIMAL(5, 2))
    percent_bike_to_work = Column(DECIMAL(5, 2))
    mean_commute_time = Column(DECIMAL(5, 2))

    median_age = Column(DECIMAL(5, 2))
    percent_under_18 = Column(DECIMAL(5, 2))
    percent_over_65 = Column(DECIMAL(5, 2))
    percent_minority = Column(DECIMAL(5, 2))
    percent_limited_english = Column(DECIMAL(5, 2))

    social_vulnerability_index = Column(DECIMAL(4, 2))

    source = Column(String(100))
    year = Column(Integer)
    retrieved_at = Column(TIMESTAMP, default=datetime.utcnow)


class OSMInfrastructure(Base):
    """OpenStreetMap infrastructure model"""
    __tablename__ = 'osm_infrastructure'

    osm_id = Column(Integer, primary_key=True, autoincrement=True)
    crash_id = Column(String(50), ForeignKey('crashes.crash_id', ondelete='CASCADE'))

    road_class = Column(String(50))
    road_name = Column(String(200))
    number_of_lanes = Column(Integer)
    lane_width_meters = Column(DECIMAL(5, 2))
    road_width_meters = Column(DECIMAL(6, 2))
    surface_type = Column(String(50))
    max_speed_kph = Column(Integer)
    max_speed_mph = Column(Integer)

    has_sidewalk = Column(Boolean)
    sidewalk_both_sides = Column(Boolean)
    has_bike_lane = Column(Boolean)
    bike_lane_protected = Column(Boolean)
    has_median = Column(Boolean)
    has_buffer = Column(Boolean)
    is_one_way = Column(Boolean)
    is_lit = Column(Boolean)

    distance_to_crosswalk_m = Column(DECIMAL(8, 2))
    distance_to_signal_m = Column(DECIMAL(8, 2))
    distance_to_transit_m = Column(DECIMAL(8, 2))
    distance_to_school_m = Column(DECIMAL(8, 2))

    is_intersection = Column(Boolean)
    intersection_type = Column(String(50))
    number_of_approaches = Column(Integer)
    has_pedestrian_signal = Column(Boolean)
    has_crosswalk_marking = Column(Boolean)

    osm_way_id = Column(Integer)
    osm_node_id = Column(Integer)
    retrieved_at = Column(TIMESTAMP, default=datetime.utcnow)
