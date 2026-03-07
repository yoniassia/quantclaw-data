#!/usr/bin/env python3
"""
OpenSky Network API Module — Flight Tracking Alternative Data

Real-time and historical aviation data from OpenSky Network's global sensor network.
Tracks aircraft positions, flights, arrivals, departures, and flight paths.
Useful for analyzing air traffic patterns, travel demand, fuel consumption correlations.

Data Source: https://opensky-network.org/api
API Documentation: https://opensky-network.org/apidoc/rest.html

Free Tier: Anonymous access up to 100 calls/minute
Update Frequency: Real-time (updates every 10 seconds)
Coverage: Global aircraft tracking

Author: QUANTCLAW DATA NightBuilder
Built: 2026-03-07
"""

import sys
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import time

# OpenSky Network API Configuration
OPENSKY_BASE_URL = "https://opensky-network.org/api"

# Rate limiting - 100 calls/min for anonymous
RATE_LIMIT_DELAY = 0.6  # seconds between calls (conservative)
_last_call_time = 0

def _rate_limit():
    """Enforce rate limiting between API calls"""
    global _last_call_time
    elapsed = time.time() - _last_call_time
    if elapsed < RATE_LIMIT_DELAY:
        time.sleep(RATE_LIMIT_DELAY - elapsed)
    _last_call_time = time.time()

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Make HTTP request to OpenSky Network API with error handling
    
    Args:
        endpoint: API endpoint path (e.g., '/states/all')
        params: Optional query parameters
    
    Returns:
        dict: JSON response from API
    
    Raises:
        Exception: On HTTP errors or invalid responses
    """
    _rate_limit()
    
    url = f"{OPENSKY_BASE_URL}{endpoint}"
    
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        if response.status_code == 404:
            return None  # No data found
        raise Exception(f"OpenSky API HTTP error: {e}")
    except requests.exceptions.Timeout:
        raise Exception("OpenSky API request timed out")
    except requests.exceptions.RequestException as e:
        raise Exception(f"OpenSky API request failed: {e}")
    except json.JSONDecodeError:
        raise Exception("OpenSky API returned invalid JSON")

def get_all_states(time_secs: Optional[int] = None, 
                   icao24: Optional[str] = None,
                   bbox: Optional[Tuple[float, float, float, float]] = None) -> Dict:
    """
    Retrieve state vectors for all aircraft currently tracked by OpenSky Network.
    
    State vectors contain position, velocity, altitude, and metadata for each aircraft.
    
    Args:
        time_secs: Unix timestamp (seconds since epoch). Default: current time
        icao24: ICAO24 transponder address (hex string, lowercase) to filter single aircraft
        bbox: Bounding box (lat_min, lon_min, lat_max, lon_max) to filter by area
    
    Returns:
        dict: {
            'time': int (Unix timestamp),
            'states': list of state vectors, each containing:
                [icao24, callsign, origin_country, time_position, last_contact,
                 longitude, latitude, baro_altitude, on_ground, velocity,
                 true_track, vertical_rate, sensors, geo_altitude, squawk, spi, position_source]
        }
        Returns None if no data available
    
    Example:
        >>> states = get_all_states()
        >>> print(f"Tracking {len(states['states'])} aircraft")
    """
    params = {}
    
    if time_secs is not None:
        params['time'] = time_secs
    
    if icao24 is not None:
        params['icao24'] = icao24.lower()
    
    if bbox is not None:
        params['lamin'] = bbox[0]
        params['lomin'] = bbox[1]
        params['lamax'] = bbox[2]
        params['lomax'] = bbox[3]
    
    result = _make_request('/states/all', params)
    
    if result is None:
        return {'time': time_secs or int(time.time()), 'states': []}
    
    return result

def get_flights_by_aircraft(icao24: str, begin: int, end: int) -> List[Dict]:
    """
    Retrieve flights for a specific aircraft within a time interval.
    
    Args:
        icao24: ICAO24 transponder address (hex string) of the aircraft
        begin: Unix timestamp (seconds) - start of time interval
        end: Unix timestamp (seconds) - end of time interval
    
    Returns:
        list: Flight records, each containing:
            {
                'icao24': str,
                'firstSeen': int (Unix timestamp),
                'estDepartureAirport': str (ICAO code),
                'lastSeen': int (Unix timestamp),
                'estArrivalAirport': str (ICAO code),
                'callsign': str,
                'estDepartureAirportHorizDistance': int (meters),
                'estDepartureAirportVertDistance': int (meters),
                'estArrivalAirportHorizDistance': int (meters),
                'estArrivalAirportVertDistance': int (meters),
                'departureAirportCandidatesCount': int,
                'arrivalAirportCandidatesCount': int
            }
        Returns empty list if no flights found
    
    Example:
        >>> # Get flights for specific aircraft in last 24 hours
        >>> end_time = int(time.time())
        >>> begin_time = end_time - 86400
        >>> flights = get_flights_by_aircraft('a12b34', begin_time, end_time)
    """
    icao24 = icao24.lower()
    params = {'begin': begin, 'end': end}
    
    result = _make_request(f'/flights/aircraft', params={'icao24': icao24, **params})
    
    if result is None:
        return []
    
    return result if isinstance(result, list) else []

def get_arrivals_by_airport(airport_icao: str, begin: int, end: int) -> List[Dict]:
    """
    Retrieve flights arriving at a specific airport within a time interval.
    
    Args:
        airport_icao: ICAO airport code (e.g., 'KJFK' for JFK, 'EDDF' for Frankfurt)
        begin: Unix timestamp (seconds) - start of time interval
        end: Unix timestamp (seconds) - end of time interval
    
    Returns:
        list: Arrival flight records (same structure as get_flights_by_aircraft)
        Returns empty list if no arrivals found
    
    Example:
        >>> # Get arrivals at JFK in last hour
        >>> end_time = int(time.time())
        >>> begin_time = end_time - 3600
        >>> arrivals = get_arrivals_by_airport('KJFK', begin_time, end_time)
    """
    airport_icao = airport_icao.upper()
    params = {'airport': airport_icao, 'begin': begin, 'end': end}
    
    result = _make_request('/flights/arrival', params)
    
    if result is None:
        return []
    
    return result if isinstance(result, list) else []

def get_departures_by_airport(airport_icao: str, begin: int, end: int) -> List[Dict]:
    """
    Retrieve flights departing from a specific airport within a time interval.
    
    Args:
        airport_icao: ICAO airport code (e.g., 'KJFK' for JFK, 'EDDF' for Frankfurt)
        begin: Unix timestamp (seconds) - start of time interval
        end: Unix timestamp (seconds) - end of time interval
    
    Returns:
        list: Departure flight records (same structure as get_flights_by_aircraft)
        Returns empty list if no departures found
    
    Example:
        >>> # Get departures from Frankfurt in last 2 hours
        >>> end_time = int(time.time())
        >>> begin_time = end_time - 7200
        >>> departures = get_departures_by_airport('EDDF', begin_time, end_time)
    """
    airport_icao = airport_icao.upper()
    params = {'airport': airport_icao, 'begin': begin, 'end': end}
    
    result = _make_request('/flights/departure', params)
    
    if result is None:
        return []
    
    return result if isinstance(result, list) else []

def get_track_by_aircraft(icao24: str, time_secs: Optional[int] = None) -> Dict:
    """
    Retrieve trajectory (waypoints) for a specific aircraft.
    
    Returns the flight path as a series of waypoints showing the aircraft's
    movement over time.
    
    Args:
        icao24: ICAO24 transponder address (hex string) of the aircraft
        time_secs: Unix timestamp (seconds). Default: current time
    
    Returns:
        dict: {
            'icao24': str,
            'callsign': str,
            'startTime': int (Unix timestamp),
            'endTime': int (Unix timestamp),
            'path': list of waypoints, each containing:
                [time, latitude, longitude, baro_altitude, true_track, on_ground]
        }
        Returns None if no track data available
    
    Example:
        >>> track = get_track_by_aircraft('a12b34')
        >>> if track and track.get('path'):
        >>>     print(f"Flight path has {len(track['path'])} waypoints")
    """
    icao24 = icao24.lower()
    params = {'icao24': icao24}
    
    if time_secs is not None:
        params['time'] = time_secs
    
    result = _make_request('/tracks/all', params)
    
    return result

# Utility functions for common use cases

def get_aircraft_count() -> int:
    """
    Get current count of tracked aircraft worldwide.
    
    Returns:
        int: Number of aircraft currently being tracked
    """
    states = get_all_states()
    if states and 'states' in states:
        return len(states['states'])
    return 0

def get_aircraft_in_region(lat_min: float, lon_min: float, 
                           lat_max: float, lon_max: float) -> List:
    """
    Get all aircraft currently in a geographic region.
    
    Args:
        lat_min: Minimum latitude
        lon_min: Minimum longitude
        lat_max: Maximum latitude
        lon_max: Maximum longitude
    
    Returns:
        list: State vectors for aircraft in the bounding box
    """
    bbox = (lat_min, lon_min, lat_max, lon_max)
    states = get_all_states(bbox=bbox)
    if states and 'states' in states:
        return states['states']
    return []

if __name__ == "__main__":
    # Test module functionality
    print("OpenSky Network API Module - Testing")
    print("=" * 50)
    
    try:
        # Test 1: Get all current aircraft states
        print("\n1. Fetching current aircraft states...")
        states = get_all_states()
        if states and 'states' in states:
            count = len(states['states'])
            print(f"✓ Success: Tracking {count} aircraft")
            if count > 0:
                # Show sample aircraft
                sample = states['states'][0]
                print(f"  Sample: ICAO24={sample[0]}, Callsign={sample[1]}, Country={sample[2]}")
        else:
            print("✗ No aircraft data returned")
        
        # Test 2: Get aircraft count
        print("\n2. Getting aircraft count...")
        count = get_aircraft_count()
        print(f"✓ Current aircraft count: {count}")
        
        # Test 3: Regional query (example: North America)
        print("\n3. Testing regional query (North America)...")
        na_aircraft = get_aircraft_in_region(25.0, -125.0, 50.0, -65.0)
        print(f"✓ Aircraft in North America: {len(na_aircraft)}")
        
        print("\n" + "=" * 50)
        print("Module Status: OPERATIONAL")
        print(json.dumps({
            "module": "opensky_network_api",
            "status": "operational",
            "functions": 9,
            "api_base": OPENSKY_BASE_URL,
            "rate_limit": "100 calls/min (anonymous)"
        }, indent=2))
        
    except Exception as e:
        print(f"\n✗ Error during testing: {e}")
        sys.exit(1)
