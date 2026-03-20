#!/usr/bin/env python3

"""
QuantClaw Data Module: openweather_finance

PURPOSE: Provides weather data for alternative data applications, such as forecasting impacts on agriculture and energy markets.

Data Source URL: https://api.openweathermap.org
Update Frequency: Real-time via API calls, with cached responses valid for 1 hour.
Auth Info: Requires a free-tier API key from OpenWeatherMap. Set the environment variable 'OPENWEATHER_API_KEY' for access. Use only free endpoints.

CATEGORY: alt_data
"""

import requests
import os
import json
import time
from pathlib import Path

# Cache configuration
CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/openweather_finance')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour in seconds

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to perform a GET request with caching.

    Args:
        url (str): The API endpoint URL.
        cache_key (str): A unique key for caching the response.
        params (dict, optional): Query parameters for the request.
        headers (dict, optional): Headers for the request.

    Returns:
        dict: The JSON response data, or cached data if available and not expired.
    """
    cache_file = CACHE_DIR / f'{cache_key}.json'
    if cache_file.exists() and (time.time() - cache_file.stat().st_mtime) < CACHE_TTL:
        return json.loads(cache_file.read_text())
    
    try:
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        cache_file.write_text(json.dumps(data, indent=2))
        return data
    except requests.exceptions.RequestException as e:
        return {'error': str(e)}

def get_current_weather(city: str) -> dict:
    """
    Retrieve current weather data for a given city.

    Args:
        city (str): The city name.

    Returns:
        dict: Weather data as a dictionary, or an error dictionary if the request fails.
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return {'error': 'API key not set in environment variable OPENWEATHER_API_KEY'}
    
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'q': city, 'appid': api_key, 'units': 'metric'}
    cache_key = f'current_weather_{city}'
    
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to get current weather: {str(e)}'}

def get_forecast(city: str) -> dict:
    """
    Retrieve 5-day weather forecast for a given city.

    Args:
        city (str): The city name.

    Returns:
        dict: Forecast data as a dictionary, or an error dictionary if the request fails.
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return {'error': 'API key not set in environment variable OPENWEATHER_API_KEY'}
    
    url = 'https://api.openweathermap.org/data/2.5/forecast'
    params = {'q': city, 'appid': api_key, 'units': 'metric'}
    cache_key = f'forecast_{city}'
    
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to get forecast: {str(e)}'}

def get_weather_by_coords(lat: float, lon: float) -> dict:
    """
    Retrieve current weather data for given coordinates.

    Args:
        lat (float): Latitude.
        lon (float): Longitude.

    Returns:
        dict: Weather data as a dictionary, or an error dictionary if the request fails.
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return {'error': 'API key not set in environment variable OPENWEATHER_API_KEY'}
    
    url = 'https://api.openweathermap.org/data/2.5/weather'
    params = {'lat': lat, 'lon': lon, 'appid': api_key, 'units': 'metric'}
    cache_key = f'weather_by_coords_{lat}_{lon}'
    
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to get weather by coordinates: {str(e)}'}

def get_hourly_forecast(city: str) -> dict:
    """
    Retrieve hourly forecast data for a given city (using 5-day forecast endpoint).

    Args:
        city (str): The city name.

    Returns:
        dict: Hourly forecast data as a dictionary, or an error dictionary if the request fails.
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return {'error': 'API key not set in environment variable OPENWEATHER_API_KEY'}
    
    url = 'https://api.openweathermap.org/data/2.5/forecast'
    params = {'q': city, 'appid': api_key, 'units': 'metric', 'cnt': 24}  # Limit to 24 hours for hourly
    cache_key = f'hourly_forecast_{city}'
    
    try:
        data = _cached_get(url, cache_key, params=params)
        # Extract hourly data if available
        if 'list' in data:
            return {'hourly': data['list']}  # Return only the list for hourly
        return data
    except Exception as e:
        return {'error': f'Failed to get hourly forecast: {str(e)}'}

def get_air_pollution(city: str) -> dict:
    """
    Retrieve current air pollution data for a given city.

    Args:
        city (str): The city name.

    Returns:
        dict: Air pollution data as a dictionary, or an error dictionary if the request fails.
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')
    if not api_key:
        return {'error': 'API key not set in environment variable OPENWEATHER_API_KEY'}
    
    url = 'http://api.openweathermap.org/data/2.5/air_pollution'  # Note: Free tier might require coordinates, but assuming city works via geocoding
    params = {'q': city, 'appid': api_key}
    cache_key = f'air_pollution_{city}'
    
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f'Failed to get air pollution: {str(e)}'}

def main():
    """
    Demonstrate key functions from the module.
    """
    import sys
    
    if len(sys.argv) > 1:
        city = sys.argv[1]
    else:
        city = 'London'  # Default city for demo
    
    print("Demonstrating get_current_weather:")
    result = get_current_weather(city)
    print(result)  # Output the dictionary
    
    print("\nDemonstrating get_forecast:")
    result = get_forecast(city)
    print(result)  # Output the dictionary
    
    print("\nDemonstrating get_weather_by_coords for London (approx: 51.5074, -0.1278):")
    result = get_weather_by_coords(51.5074, -0.1278)
    print(result)  # Output the dictionary

if __name__ == '__main__':
    main()
