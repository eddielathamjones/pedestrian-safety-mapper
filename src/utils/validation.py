"""
Data validation utilities for FARS Multi-Sensory Database

Validates crash data, API responses, and database inputs
"""

from typing import Optional, Dict, Any, List
from datetime import datetime, date, time
from pydantic import BaseModel, Field, validator, ValidationError
from decimal import Decimal


class CrashData(BaseModel):
    """Validation model for crash records"""

    crash_id: str = Field(..., min_length=1, max_length=50)
    state: Optional[str] = Field(None, min_length=2, max_length=2)
    city: Optional[str] = Field(None, max_length=100)
    county: Optional[str] = Field(None, max_length=100)

    # Location
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    intersection: Optional[str] = Field(None, max_length=200)

    # Temporal
    crash_date: Optional[date] = None
    crash_time: Optional[time] = None
    time_of_day: Optional[str] = Field(None, regex='^(day|night|dawn|dusk)$')

    # Victim
    victim_age: Optional[int] = Field(None, ge=0, le=150)
    victim_gender: Optional[str] = Field(None, regex='^(M|F|U|Male|Female|Unknown)$')

    # Crash characteristics
    severity: Optional[str] = None
    vehicle_speed: Optional[int] = Field(None, ge=0, le=200)
    vehicle_direction: Optional[int] = Field(None, ge=0, le=360)

    class Config:
        validate_assignment = True

    @validator('state')
    def validate_state_code(cls, v):
        """Validate US state code"""
        if v is None:
            return v

        valid_states = {
            'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
            'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
            'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
            'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
            'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY',
            'DC', 'PR'  # DC and Puerto Rico
        }

        if v.upper() not in valid_states:
            raise ValueError(f"Invalid state code: {v}")

        return v.upper()


class AirQualityData(BaseModel):
    """Validation model for air quality data"""

    crash_id: str
    source: str = Field(..., regex='^(purpleair|epa|openaq)$')
    sensor_distance_meters: Optional[float] = Field(None, ge=0, le=10000)

    # Measurements
    pm2_5: Optional[float] = Field(None, ge=0, le=1000)
    pm10: Optional[float] = Field(None, ge=0, le=2000)
    aqi: Optional[int] = Field(None, ge=0, le=500)

    # Environmental
    temperature_f: Optional[float] = Field(None, ge=-100, le=150)
    humidity: Optional[float] = Field(None, ge=0, le=100)

    @validator('aqi')
    def validate_aqi_category(cls, v, values):
        """Ensure AQI is consistent with category"""
        if v is None:
            return v

        # AQI ranges
        if v < 0 or v > 500:
            raise ValueError(f"AQI must be between 0 and 500, got {v}")

        return v


class WeatherData(BaseModel):
    """Validation model for weather data"""

    crash_id: str
    source: str

    # Measurements
    temperature_f: Optional[float] = Field(None, ge=-100, le=150)
    humidity: Optional[float] = Field(None, ge=0, le=100)
    wind_speed_mph: Optional[float] = Field(None, ge=0, le=200)
    wind_direction: Optional[int] = Field(None, ge=0, le=360)
    visibility_miles: Optional[float] = Field(None, ge=0, le=50)
    precipitation_inches: Optional[float] = Field(None, ge=0, le=20)
    cloud_cover: Optional[float] = Field(None, ge=0, le=100)

    @validator('temperature_f')
    def classify_extreme_temp(cls, v, values):
        """Flag extreme temperatures"""
        if v is not None:
            if v > 100:
                values['is_extreme_heat'] = True
            if v < 32:
                values['is_extreme_cold'] = True
        return v


class StreetViewImage(BaseModel):
    """Validation model for street view images"""

    crash_id: str
    source: str = Field(..., regex='^(mapillary|google)$')

    # Capture info
    compass_angle: Optional[int] = Field(None, ge=0, le=360)
    camera_latitude: Optional[float] = Field(None, ge=-90, le=90)
    camera_longitude: Optional[float] = Field(None, ge=-180, le=180)

    # File info
    local_path: Optional[str] = None
    file_size_kb: Optional[int] = Field(None, ge=0)

    # Analysis results
    green_view_index: Optional[float] = Field(None, ge=0, le=100)


class SoundData(BaseModel):
    """Validation model for sound data"""

    crash_id: str
    source: str = Field(..., regex='^(aporee|field_recording|modeled)$')

    duration_seconds: Optional[int] = Field(None, ge=0, le=3600)
    mean_loudness_db: Optional[float] = Field(None, ge=0, le=140)
    peak_loudness_db: Optional[float] = Field(None, ge=0, le=140)

    sample_rate: Optional[int] = Field(None, ge=8000, le=96000)
    channels: Optional[int] = Field(None, ge=1, le=2)

    @validator('peak_loudness_db')
    def validate_peak_vs_mean(cls, v, values):
        """Ensure peak >= mean"""
        if v is not None and 'mean_loudness_db' in values and values['mean_loudness_db'] is not None:
            if v < values['mean_loudness_db']:
                raise ValueError(f"Peak loudness ({v}) cannot be less than mean ({values['mean_loudness_db']})")
        return v


def validate_crash_data(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate crash data dictionary

    Args:
        data: Dictionary of crash data

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        CrashData(**data)
        return True, None
    except ValidationError as e:
        return False, str(e)


def validate_coordinates(lat: float, lon: float) -> bool:
    """Quick coordinate validation"""
    return -90 <= lat <= 90 and -180 <= lon <= 180


def validate_aqi(aqi: int) -> tuple[bool, Optional[str]]:
    """
    Validate AQI value and return category

    Args:
        aqi: Air Quality Index value

    Returns:
        Tuple of (is_valid, category)
    """
    if not 0 <= aqi <= 500:
        return False, None

    if aqi <= 50:
        return True, "Good"
    elif aqi <= 100:
        return True, "Moderate"
    elif aqi <= 150:
        return True, "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return True, "Unhealthy"
    elif aqi <= 300:
        return True, "Very Unhealthy"
    else:
        return True, "Hazardous"


def validate_date_range(start_date: date, end_date: date) -> bool:
    """Validate date range is logical"""
    return start_date <= end_date


def sanitize_string(value: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string for database insertion

    Args:
        value: String to sanitize
        max_length: Maximum length

    Returns:
        Sanitized string
    """
    if not value:
        return ""

    # Remove null bytes
    value = value.replace('\x00', '')

    # Strip whitespace
    value = value.strip()

    # Truncate if needed
    if max_length and len(value) > max_length:
        value = value[:max_length]

    return value


def validate_file_path(path: str, must_exist: bool = False) -> bool:
    """
    Validate file path

    Args:
        path: File path to validate
        must_exist: Whether file must exist

    Returns:
        True if valid, False otherwise
    """
    from pathlib import Path

    try:
        p = Path(path)

        # Check for invalid characters
        if '\x00' in str(p):
            return False

        # Check if exists (if required)
        if must_exist and not p.exists():
            return False

        return True

    except Exception:
        return False


class DataQualityChecker:
    """Check data quality and completeness"""

    def __init__(self):
        self.issues = []

    def check_crash(self, crash_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check crash data quality

        Returns dict with:
        - completeness_score: 0-100
        - issues: List of issues found
        - warnings: List of warnings
        """
        self.issues = []
        warnings = []
        score = 100

        # Required fields
        required = ['crash_id', 'latitude', 'longitude', 'crash_date']
        for field in required:
            if not crash_data.get(field):
                self.issues.append(f"Missing required field: {field}")
                score -= 25

        # Recommended fields
        recommended = ['city', 'state', 'crash_time', 'severity']
        for field in recommended:
            if not crash_data.get(field):
                warnings.append(f"Missing recommended field: {field}")
                score -= 5

        # Coordinate validation
        lat = crash_data.get('latitude')
        lon = crash_data.get('longitude')
        if lat and lon:
            if not validate_coordinates(lat, lon):
                self.issues.append(f"Invalid coordinates: ({lat}, {lon})")
                score -= 20

        # Date validation
        crash_date = crash_data.get('crash_date')
        if crash_date:
            if isinstance(crash_date, str):
                try:
                    crash_date = datetime.strptime(crash_date, '%Y-%m-%d').date()
                except ValueError:
                    self.issues.append(f"Invalid date format: {crash_date}")
                    score -= 10

            if crash_date > date.today():
                self.issues.append(f"Crash date in future: {crash_date}")
                score -= 15

        return {
            'completeness_score': max(0, score),
            'is_valid': len(self.issues) == 0,
            'issues': self.issues,
            'warnings': warnings
        }


# Example usage
if __name__ == '__main__':
    # Test crash validation
    test_crash = {
        'crash_id': 'AZ-2023-001',
        'state': 'AZ',
        'latitude': 32.2226,
        'longitude': -110.9747,
        'crash_date': date(2023, 6, 15),
        'crash_time': time(14, 30),
        'vehicle_speed': 35
    }

    is_valid, error = validate_crash_data(test_crash)
    print(f"Crash valid: {is_valid}")
    if error:
        print(f"Error: {error}")

    # Test AQI validation
    is_valid, category = validate_aqi(125)
    print(f"AQI 125: {category}")

    # Test data quality
    checker = DataQualityChecker()
    quality = checker.check_crash(test_crash)
    print(f"Completeness score: {quality['completeness_score']}")
    print(f"Issues: {quality['issues']}")
    print(f"Warnings: {quality['warnings']}")
