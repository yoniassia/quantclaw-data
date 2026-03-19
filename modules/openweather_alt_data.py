#!/usr/bin/env python3
"""
QuantClaw Data Module: openweather_alt_data

PURPOSE: Accesses global weather data for alternative data applications, 
such as predicting impacts on agriculture and energy commodities.

Data Source: https://openweathermap.org/api
Update Frequency: Real-time data with API calls; data updates vary by endpoint (e.g., current weather is near real-time).
Authentication: Requires a free API key from OpenWeatherMap. Sign up at the data source URL.

CATEGORY: alt_data
"""

import requests
import os
import json
import time
from pathlib import Path

CACHE_DIR = Path('/home/quant/apps/quantclaw-data/cache/openweather_alt_data')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
CACHE_TTL = 3600  # 1 hour

def _cached_get(url, cache_key, params=None, headers=None):
    """
    Helper function to get data with caching.
    
    Args:
        url (str): The URL to fetch.
        cache_key (str): Unique key for caching.
        params (dict, optional): Query parameters.
        headers (dict, optional): HTTP headers.
    
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
        return {'error': f'HTTP request failed: {str(e)}'}
    except Exception as e:
        return {'error': f'Unexpected error: {str(e)}'}

def get_current_weather(city: str, api_key: str) -> dict:
    """
    Get current weather data for a city.
    
    Args:
        city (str): City name.
        api_key (str): OpenWeatherMap API key.
    
    Returns:
        dict: Weather data or error dictionary.
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}"
        cache_key = f"current_weather_{city}"
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def get_five_day_forecast(city: str, api_key: str) -> dict:
    """
    Get 5-day weather forecast for a city.
    
    Args:
        city (str): City name.
        api_key (str): OpenWeatherMap API key.
    
    Returns:
        dict: Forecast data or error dictionary.
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}"
        cache_key = f"five_day_forecast_{city}"
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def get_weather_by_coordinates(lat: float, lon: float, api_key: str) -> dict:
    """
    Get current weather data by latitude and longitude.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        api_key (str): OpenWeatherMap API key.
    
    Returns:
        dict: Weather data or error dictionary.
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}"
        cache_key = f"weather_by_coords_{lat}_{lon}"
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def get_one_call_weather(lat: float, lon: float, api_key: str) -> dict:
    """
    Get One Call API data (current and forecast) by coordinates.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        api_key (str): OpenWeatherMap API key.
    
    Returns:
        dict: One Call data or error dictionary.
    """
    try:
        url = f"https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={api_key}&units=metric"
        cache_key = f"one_call_{lat}_{lon}"
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def get_air_pollution_forecast(lat: float, lon: float, api_key: str) -> dict:
    """
    Get air pollution forecast by coordinates.
    
    Args:
        lat (float): Latitude.
        lon (float): Longitude.
        api_key (str): OpenWeatherMap API key.
    
    Returns:
        dict: Air pollution data or error dictionary.
    """
    try:
        url = f"http://api.openweathermap.org/data/2.5/air_pollution/forecast?lat={lat}&lon={lon}&appid={api_key}"
        cache_key = f"air_pollution_forecast_{lat}_{lon}"
        return _cached_get(url, cache_key)
    except Exception as e:
        return {'error': f'Function error: {str(e)}'}

def main():
    """
    Demo function to showcase key functions.
    """
    api_key = 'your_free_api_key_here'  # Replace with a valid free API key
    demo_city = 'London'
    demo_lat = 51.5074  # London latitude
    demo_lon = -0.1278  # London longitude
    
    print("Demo: Getting current weather for London")
    current_weather = get_current_weather(demo_city, api_key)
    print(json.dumps(current_weather, indent=2))
    
    print("\nDemo: Getting 5-day forecast for London")
    forecast = get_five_day_forecast(demo_city, api_key)
    print(json.dumps(forecast, indent=2))
    
    print("\nDemo: Getting weather by coordinates for London")
    weather_by_coords = get_weather_by_coordinates(demo_lat, demo_lon, api_key)
    print(json.dumps(weather_by_coords, indent=2))

if __name__ == '__main__':
    main()
