#!/usr/bin/env python3
"""
USGS Earthquake & Natural Hazards Data Module

U.S. Geological Survey real-time earthquake and water monitoring data
- Recent earthquake events (magnitude, location, depth)
- Significant earthquakes with tsunami warnings
- Earthquake statistics and trends
- Water level monitoring from USGS gauges
- Geospatial analysis for disaster response

Data Source: https://earthquake.usgs.gov/fdsnws/event/1/
Water Services: https://waterservices.usgs.gov/nwis/
Refresh: Real-time (earthquakes updated within minutes)
Coverage: Global earthquake monitoring, US water gauges
Free tier: Yes, no authentication required

Author: QUANTCLAW DATA NightBuilder
Phase: USGS_001
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta

# USGS API Configuration
EARTHQUAKE_BASE_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
WATER_BASE_URL = "https://waterservices.usgs.gov/nwis/iv"


def _fetch_usgs_data(url: str, params: Dict[str, str]) -> Dict:
    """
    Internal helper to fetch data from USGS APIs
    
    Args:
        url: Base URL for the API endpoint
        params: Query parameters
        
    Returns:
        Parsed JSON response
        
    Raises:
        urllib.error.URLError: Network errors
        json.JSONDecodeError: Invalid JSON response
    """
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{url}?{query_string}"
    
    try:
        with urllib.request.urlopen(full_url, timeout=30) as response:
            data = response.read()
            return json.loads(data)
    except urllib.error.HTTPError as e:
        raise Exception(f"USGS API HTTP error {e.code}: {e.reason}")
    except urllib.error.URLError as e:
        raise Exception(f"USGS API connection error: {e.reason}")
    except json.JSONDecodeError as e:
        raise Exception(f"USGS API returned invalid JSON: {e}")


def get_recent_earthquakes(min_magnitude: float = 4.0, days: int = 7) -> Dict[str, Union[int, List[Dict]]]:
    """
    Get recent earthquakes above specified magnitude
    
    Args:
        min_magnitude: Minimum earthquake magnitude (default 4.0)
        days: Number of days to look back (default 7)
        
    Returns:
        Dictionary containing:
        - count: Number of earthquakes
        - earthquakes: List of earthquake events with details
        
    Example:
        >>> data = get_recent_earthquakes(min_magnitude=5.0, days=7)
        >>> print(f"Found {data['count']} earthquakes")
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    params = {
        'format': 'geojson',
        'minmagnitude': str(min_magnitude),
        'starttime': start_time.strftime('%Y-%m-%d'),
        'endtime': end_time.strftime('%Y-%m-%d'),
        'orderby': 'time'
    }
    
    result = _fetch_usgs_data(EARTHQUAKE_BASE_URL, params)
    
    earthquakes = []
    for feature in result.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        coords = geom.get('coordinates', [0, 0, 0])
        
        earthquakes.append({
            'id': feature.get('id'),
            'magnitude': props.get('mag'),
            'place': props.get('place'),
            'time': datetime.fromtimestamp(props.get('time', 0) / 1000).isoformat(),
            'longitude': coords[0],
            'latitude': coords[1],
            'depth_km': coords[2],
            'tsunami': bool(props.get('tsunami')),
            'felt': props.get('felt'),
            'significance': props.get('sig'),
            'url': props.get('url')
        })
    
    return {
        'count': len(earthquakes),
        'earthquakes': earthquakes,
        'query': {
            'min_magnitude': min_magnitude,
            'days': days,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }
    }


def get_earthquakes_near(lat: float, lon: float, radius_km: float = 100, days: int = 30, min_magnitude: float = 2.5) -> Dict[str, Union[int, List[Dict]]]:
    """
    Get earthquakes near a specific location
    
    Args:
        lat: Latitude of center point
        lon: Longitude of center point
        radius_km: Search radius in kilometers (default 100)
        days: Number of days to look back (default 30)
        min_magnitude: Minimum magnitude (default 2.5)
        
    Returns:
        Dictionary containing earthquakes near the location
        
    Example:
        >>> # Earthquakes near Tokyo
        >>> data = get_earthquakes_near(35.6762, 139.6503, radius_km=200)
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    params = {
        'format': 'geojson',
        'latitude': str(lat),
        'longitude': str(lon),
        'maxradiuskm': str(radius_km),
        'minmagnitude': str(min_magnitude),
        'starttime': start_time.strftime('%Y-%m-%d'),
        'endtime': end_time.strftime('%Y-%m-%d'),
        'orderby': 'time-asc'
    }
    
    result = _fetch_usgs_data(EARTHQUAKE_BASE_URL, params)
    
    earthquakes = []
    for feature in result.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        coords = geom.get('coordinates', [0, 0, 0])
        
        earthquakes.append({
            'id': feature.get('id'),
            'magnitude': props.get('mag'),
            'place': props.get('place'),
            'time': datetime.fromtimestamp(props.get('time', 0) / 1000).isoformat(),
            'longitude': coords[0],
            'latitude': coords[1],
            'depth_km': coords[2],
            'type': props.get('type'),
            'status': props.get('status')
        })
    
    return {
        'count': len(earthquakes),
        'center': {'latitude': lat, 'longitude': lon},
        'radius_km': radius_km,
        'earthquakes': earthquakes
    }


def get_earthquake_count(min_magnitude: float = 2.5, days: int = 30) -> Dict[str, Union[int, Dict]]:
    """
    Get count of earthquakes by magnitude range
    
    Args:
        min_magnitude: Minimum magnitude threshold (default 2.5)
        days: Number of days to look back (default 30)
        
    Returns:
        Dictionary with total count and breakdown by magnitude
        
    Example:
        >>> stats = get_earthquake_count(min_magnitude=2.5, days=7)
        >>> print(f"Total: {stats['total_count']}")
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    params = {
        'format': 'geojson',
        'minmagnitude': str(min_magnitude),
        'starttime': start_time.strftime('%Y-%m-%d'),
        'endtime': end_time.strftime('%Y-%m-%d')
    }
    
    result = _fetch_usgs_data(EARTHQUAKE_BASE_URL, params)
    
    # Count by magnitude ranges
    magnitude_ranges = {
        '2.5-3.9': 0,
        '4.0-4.9': 0,
        '5.0-5.9': 0,
        '6.0-6.9': 0,
        '7.0+': 0
    }
    
    total = 0
    for feature in result.get('features', []):
        mag = feature.get('properties', {}).get('mag', 0)
        total += 1
        
        if mag >= 7.0:
            magnitude_ranges['7.0+'] += 1
        elif mag >= 6.0:
            magnitude_ranges['6.0-6.9'] += 1
        elif mag >= 5.0:
            magnitude_ranges['5.0-5.9'] += 1
        elif mag >= 4.0:
            magnitude_ranges['4.0-4.9'] += 1
        else:
            magnitude_ranges['2.5-3.9'] += 1
    
    return {
        'total_count': total,
        'magnitude_breakdown': magnitude_ranges,
        'period_days': days,
        'min_magnitude': min_magnitude,
        'start_time': start_time.isoformat(),
        'end_time': end_time.isoformat()
    }


def get_significant_earthquakes(days: int = 30) -> Dict[str, Union[int, List[Dict]]]:
    """
    Get significant earthquakes (USGS significance > 600 or magnitude > 6.0)
    
    Args:
        days: Number of days to look back (default 30)
        
    Returns:
        Dictionary containing significant earthquake events
        
    Example:
        >>> events = get_significant_earthquakes(days=7)
        >>> for eq in events['earthquakes']:
        ...     print(f"M{eq['magnitude']} - {eq['place']}")
    """
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    params = {
        'format': 'geojson',
        'minmagnitude': '6.0',  # Significant threshold
        'starttime': start_time.strftime('%Y-%m-%d'),
        'endtime': end_time.strftime('%Y-%m-%d'),
        'orderby': 'magnitude'
    }
    
    result = _fetch_usgs_data(EARTHQUAKE_BASE_URL, params)
    
    earthquakes = []
    for feature in result.get('features', []):
        props = feature.get('properties', {})
        geom = feature.get('geometry', {})
        coords = geom.get('coordinates', [0, 0, 0])
        
        earthquakes.append({
            'id': feature.get('id'),
            'magnitude': props.get('mag'),
            'place': props.get('place'),
            'time': datetime.fromtimestamp(props.get('time', 0) / 1000).isoformat(),
            'longitude': coords[0],
            'latitude': coords[1],
            'depth_km': coords[2],
            'tsunami': bool(props.get('tsunami')),
            'felt': props.get('felt'),
            'significance': props.get('sig'),
            'alert': props.get('alert'),
            'status': props.get('status'),
            'url': props.get('url'),
            'title': props.get('title')
        })
    
    return {
        'count': len(earthquakes),
        'earthquakes': earthquakes,
        'period_days': days
    }


def get_water_level(site: str = '01646500', period: str = 'P7D') -> Dict[str, Union[str, List[Dict]]]:
    """
    Get water level data from USGS gauge station
    
    Args:
        site: USGS site number (default '01646500' - Potomac River at Washington DC)
        period: ISO 8601 period (P7D = 7 days, P1D = 1 day)
        
    Returns:
        Dictionary containing water level measurements
        
    Example:
        >>> # Potomac River water levels
        >>> data = get_water_level(site='01646500', period='P1D')
        >>> print(f"Site: {data['site_name']}")
    """
    params = {
        'format': 'json',
        'sites': site,
        'parameterCd': '00065',  # Gage height
        'period': period
    }
    
    result = _fetch_usgs_data(WATER_BASE_URL, params)
    
    # Parse the nested USGS water services JSON structure
    time_series = result.get('value', {}).get('timeSeries', [])
    
    if not time_series:
        return {
            'site': site,
            'error': 'No data available for this site',
            'measurements': []
        }
    
    site_info = time_series[0].get('sourceInfo', {})
    values = time_series[0].get('values', [{}])[0].get('value', [])
    
    measurements = []
    for val in values:
        measurements.append({
            'datetime': val.get('dateTime'),
            'value': float(val.get('value', 0)),
            'qualifiers': val.get('qualifiers', [])
        })
    
    return {
        'site': site,
        'site_name': site_info.get('siteName'),
        'latitude': site_info.get('geoLocation', {}).get('geogLocation', {}).get('latitude'),
        'longitude': site_info.get('geoLocation', {}).get('geogLocation', {}).get('longitude'),
        'variable': time_series[0].get('variable', {}).get('variableName'),
        'unit': time_series[0].get('variable', {}).get('unit', {}).get('unitCode'),
        'measurement_count': len(measurements),
        'measurements': measurements
    }


def get_earthquake_stats(year: Optional[int] = None) -> Dict[str, Union[int, Dict]]:
    """
    Get earthquake statistics for a specific year or current year
    
    Args:
        year: Year for statistics (default current year)
        
    Returns:
        Dictionary with earthquake statistics
        
    Example:
        >>> stats = get_earthquake_stats(2024)
        >>> print(f"Total earthquakes: {stats['total_count']}")
    """
    if year is None:
        year = datetime.utcnow().year
    
    start_time = f"{year}-01-01"
    end_time = f"{year}-12-31"
    
    params = {
        'format': 'geojson',
        'minmagnitude': '2.5',
        'starttime': start_time,
        'endtime': end_time
    }
    
    result = _fetch_usgs_data(EARTHQUAKE_BASE_URL, params)
    
    magnitude_counts = {
        '2.5-3.9': 0,
        '4.0-4.9': 0,
        '5.0-5.9': 0,
        '6.0-6.9': 0,
        '7.0-7.9': 0,
        '8.0+': 0
    }
    
    tsunami_events = 0
    total = 0
    max_magnitude = 0
    
    for feature in result.get('features', []):
        props = feature.get('properties', {})
        mag = props.get('mag', 0)
        total += 1
        
        if mag > max_magnitude:
            max_magnitude = mag
        
        if props.get('tsunami'):
            tsunami_events += 1
        
        if mag >= 8.0:
            magnitude_counts['8.0+'] += 1
        elif mag >= 7.0:
            magnitude_counts['7.0-7.9'] += 1
        elif mag >= 6.0:
            magnitude_counts['6.0-6.9'] += 1
        elif mag >= 5.0:
            magnitude_counts['5.0-5.9'] += 1
        elif mag >= 4.0:
            magnitude_counts['4.0-4.9'] += 1
        else:
            magnitude_counts['2.5-3.9'] += 1
    
    return {
        'year': year,
        'total_count': total,
        'magnitude_breakdown': magnitude_counts,
        'max_magnitude': max_magnitude,
        'tsunami_events': tsunami_events,
        'start_time': start_time,
        'end_time': end_time
    }


# Export all public functions
__all__ = [
    'get_recent_earthquakes',
    'get_earthquakes_near',
    'get_earthquake_count',
    'get_significant_earthquakes',
    'get_water_level',
    'get_earthquake_stats'
]


if __name__ == "__main__":
    # Test the module
    print("Testing USGS EarthExplorer Module...")
    print("\n1. Recent earthquakes (M5.0+, last 7 days):")
    recent = get_recent_earthquakes(min_magnitude=5.0, days=7)
    print(f"   Found {recent['count']} earthquakes")
    
    print("\n2. Earthquake count (last 30 days):")
    count = get_earthquake_count(min_magnitude=2.5, days=30)
    print(f"   Total: {count['total_count']}")
    print(f"   Breakdown: {count['magnitude_breakdown']}")
    
    print("\nModule test complete!")
