"""
Time and date utility functions
"""

from datetime import datetime, date, time, timedelta
from typing import Tuple, Optional
import pytz
from astral import LocationInfo
from astral.sun import sun


def classify_time_of_day(crash_time: time, sunrise: time, sunset: time,
                         twilight_minutes: int = 30) -> str:
    """
    Classify time of day based on crash time and solar position

    Args:
        crash_time: Time of crash
        sunrise: Sunrise time
        sunset: Sunset time
        twilight_minutes: Minutes before/after sunrise/sunset for twilight

    Returns:
        'day', 'night', 'dawn', or 'dusk'
    """
    # Convert to minutes since midnight for comparison
    crash_minutes = crash_time.hour * 60 + crash_time.minute
    sunrise_minutes = sunrise.hour * 60 + sunrise.minute
    sunset_minutes = sunset.hour * 60 + sunset.minute

    # Dawn period
    if sunrise_minutes - twilight_minutes <= crash_minutes < sunrise_minutes:
        return 'dawn'

    # Dusk period
    if sunset_minutes <= crash_minutes < sunset_minutes + twilight_minutes:
        return 'dusk'

    # Daytime
    if sunrise_minutes <= crash_minutes < sunset_minutes:
        return 'day'

    # Nighttime
    return 'night'


def get_sunrise_sunset(latitude: float, longitude: float, date_obj: date,
                       timezone: str = 'America/Phoenix') -> Tuple[time, time]:
    """
    Get sunrise and sunset times for a location and date

    Args:
        latitude: Location latitude
        longitude: Location longitude
        date_obj: Date to get sunrise/sunset for
        timezone: Timezone name (e.g., 'America/Phoenix' for Arizona)

    Returns:
        Tuple of (sunrise_time, sunset_time)
    """
    # Create location
    location = LocationInfo(
        name='Location',
        region='',
        timezone=timezone,
        latitude=latitude,
        longitude=longitude
    )

    # Get sun times
    s = sun(location.observer, date=date_obj, tzinfo=pytz.timezone(timezone))

    return s['sunrise'].time(), s['sunset'].time()


def parse_crash_datetime(crash_date: Optional[str], crash_time: Optional[str]) -> Optional[datetime]:
    """
    Parse crash date and time strings into datetime object

    Args:
        crash_date: Date string (YYYY-MM-DD or MM/DD/YYYY)
        crash_time: Time string (HH:MM or HH:MM:SS)

    Returns:
        Combined datetime object or None if parsing fails
    """
    if not crash_date:
        return None

    try:
        # Try different date formats
        date_formats = [
            '%Y-%m-%d',
            '%m/%d/%Y',
            '%Y%m%d',
            '%m-%d-%Y'
        ]

        parsed_date = None
        for fmt in date_formats:
            try:
                parsed_date = datetime.strptime(crash_date, fmt).date()
                break
            except ValueError:
                continue

        if not parsed_date:
            return None

        # Parse time if provided
        if crash_time:
            time_formats = [
                '%H:%M:%S',
                '%H:%M',
                '%I:%M:%S %p',
                '%I:%M %p'
            ]

            parsed_time = None
            for fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(crash_time, fmt).time()
                    break
                except ValueError:
                    continue

            if parsed_time:
                return datetime.combine(parsed_date, parsed_time)

        # Return date with midnight time if no time provided
        return datetime.combine(parsed_date, time(0, 0, 0))

    except Exception as e:
        print(f"Error parsing datetime: {e}")
        return None


def get_time_window(center_time: datetime, window_hours: int = 1) -> Tuple[datetime, datetime]:
    """
    Get time window around a center time

    Args:
        center_time: Center datetime
        window_hours: Hours before and after center time

    Returns:
        Tuple of (start_time, end_time)
    """
    delta = timedelta(hours=window_hours)
    return (center_time - delta, center_time + delta)


def format_duration(seconds: int) -> str:
    """
    Format duration in seconds to human-readable string

    Args:
        seconds: Duration in seconds

    Returns:
        Formatted string (e.g., "2h 30m 15s")
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    parts = []
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 or not parts:
        parts.append(f"{secs}s")

    return " ".join(parts)


# Example usage
if __name__ == '__main__':
    # Test Tucson, AZ
    lat, lon = 32.2226, -110.9747
    test_date = date(2023, 6, 15)

    sunrise, sunset = get_sunrise_sunset(lat, lon, test_date)
    print(f"Sunrise: {sunrise}, Sunset: {sunset}")

    # Test time classification
    test_times = [
        time(6, 0),   # Dawn
        time(12, 0),  # Day
        time(19, 0),  # Dusk
        time(22, 0),  # Night
    ]

    for t in test_times:
        classification = classify_time_of_day(t, sunrise, sunset)
        print(f"{t}: {classification}")

    # Test datetime parsing
    dt = parse_crash_datetime("2023-06-15", "14:30:00")
    print(f"Parsed datetime: {dt}")
