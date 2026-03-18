#!/usr/bin/env python3

"""
QuantClaw Data Module: openweathermap_weather_data

Purpose: Accesses global weather data for financial forecasting in agriculture and energy.

Data Source URL: https://api.openweathermap.org/

Update Frequency: Real-time data, cached for 1 hour.

Auth Info: Requires a free API key from OpenWeatherMap. Obtain one at https://openweathermap.org/api.
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/openweathermap_weather_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.
    
    Args:
        url (str): The URL to fetch.
        cache_key (str): Unique key for caching.
        params (dict): Query parameters.
        headers (dict): HTTP headers.
    
    Returns:
        dict: The JSON response data.
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

def get_current_weather(city: str, api_key: str) -> dict:
    """
    Get current weather data for a given city.
    
    Args:
        city (str): The city name.
        api_key (str): The OpenWeatherMap API key.
    
    Returns:
        dict: Weather data or error dictionary.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {'q': city, 'appid': api_key, 'units': 'metric'}
    cache_key = f"current_weather_{city}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f"Failed to get current weather: {str(e)}"}

def get_current_weather_by_coords(lat: float, lon: float, api_key: str) -> dict:
    """
    Get current weather data for given coordinates.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        api_key (str): The OpenWeatherMap API key.
    
    Returns:
        dict: Weather data or error dictionary.
    """
    url = "https://api.openweathermap.org/data/2.5/weather"
    params = {'lat': lat, 'lon': lon, 'appid': api_key, 'units': 'metric'}
    cache_key = f"current_weather_coords_{lat}_{lon}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f"Failed to get current weather by coords: {str(e)}"}

def get_5_day_forecast(city: str, api_key: str) -> dict:
    """
    Get 5-day weather forecast for a given city.
    
    Args:
        city (str): The city name.
        api_key (str): The OpenWeatherMap API key.
    
    Returns:
        dict: Forecast data or error dictionary.
    """
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {'q': city, 'appid': api_key, 'units': 'metric'}
    cache_key = f"5_day_forecast_{city}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f"Failed to get 5-day forecast: {str(e)}"}

def get_5_day_forecast_by_coords(lat: float, lon: float, api_key: str) -> dict:
    """
    Get 5-day weather forecast for given coordinates.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        api_key (str): The OpenWeatherMap API key.
    
    Returns:
        dict: Forecast data or error dictionary.
    """
    url = "https://api.openweathermap.org/data/2.5/forecast"
    params = {'lat': lat, 'lon': lon, 'appid': api_key, 'units': 'metric'}
    cache_key = f"5_day_forecast_coords_{lat}_{lon}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f"Failed to get 5-day forecast by coords: {str(e)}"}

def get_uv_index(lat: float, lon: float, api_key: str) -> dict:
    """
    Get current UV index for given coordinates.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        api_key (str): The OpenWeatherMap API key.
    
    Returns:
        dict: UV index data or error dictionary.
    """
    url = "https://api.openweathermap.org/data/2.5/uvi"
    params = {'lat': lat, 'lon': lon, 'appid': api_key}
    cache_key = f"uv_index_{lat}_{lon}"
    try:
        return _cached_get(url, cache_key, params=params)
    except Exception as e:
        return {'error': f"Failed to get UV index: {str(e)}"}

def main():
    """
    Demonstrate key functions.
    """
    api_key = os.getenv('OPENWEATHER_API_KEY')  # Expect API key in environment variable
    if not api_key:
        print("Error: OPENWEATHER_API_KEY environment variable not set.")
        return
    
    # Demo 1: Get current weather for London
    london_weather = get_current_weather('London', api_key)
    print("Current weather for London:", london_weather)
    
    # Demo 2: Get 5-day forecast for London
    london_forecast = get_5_day_forecast('London', api_key)
    print("5-day forecast for London:", london_forecast)
    
    # Demo 3: Get UV index for a specific location (e.g., New York: 40.7128, -74.0060)
    uv_data = get_uv_index(40.7128, -74.0060, api_key)
    print("UV index for New York:", uv_data)

if __name__ == '__main__':
    main()
