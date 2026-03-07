#!/usr/bin/env python3
"""
OpenWeatherMap Climate API — Weather & Climate Data for Trading

Provides current weather, forecasts, air quality, and historical climate data.
Key use cases:
- Commodity trading (weather impacts crops, energy demand)
- Climate risk analysis for portfolios
- ESG climate metrics
- Supply chain disruption modeling

Source: https://openweathermap.org/api
Category: ESG & Climate
Free tier: 60 calls/min, 1M calls/month with API key
Update frequency: Real-time (current), hourly (forecast)
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Tuple
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# OpenWeatherMap API Configuration
OWM_BASE_URL = "https://api.openweathermap.org/data/2.5"
OWM_API_KEY = os.environ.get("OPENWEATHERMAP_API_KEY", "")

# ========== COMMODITY WEATHER SENSITIVITY MAP ==========
COMMODITY_REGIONS = {
    'wheat': {
        'us': {'lat': 38.5, 'lon': -97.5, 'name': 'Kansas (US Wheat Belt)'},
        'russia': {'lat': 52.5, 'lon': 52.0, 'name': 'Southern Russia'},
        'ukraine': {'lat': 49.0, 'lon': 32.0, 'name': 'Central Ukraine'},
    },
    'corn': {
        'us': {'lat': 40.5, 'lon': -89.5, 'name': 'Iowa (US Corn Belt)'},
        'brazil': {'lat': -15.8, 'lon': -47.9, 'name': 'Central Brazil'},
        'argentina': {'lat': -34.6, 'lon': -58.4, 'name': 'Argentina Pampas'},
    },
    'soybeans': {
        'us': {'lat': 40.5, 'lon': -89.5, 'name': 'Illinois (US)'},
        'brazil': {'lat': -23.5, 'lon': -46.6, 'name': 'São Paulo Region'},
        'argentina': {'lat': -31.4, 'lon': -64.2, 'name': 'Córdoba Province'},
    },
    'coffee': {
        'brazil': {'lat': -19.9, 'lon': -43.9, 'name': 'Minas Gerais'},
        'colombia': {'lat': 4.6, 'lon': -74.1, 'name': 'Colombia Coffee Region'},
        'vietnam': {'lat': 12.2, 'lon': 109.2, 'name': 'Central Highlands Vietnam'},
    },
    'natural_gas': {
        'us': {'lat': 32.8, 'lon': -96.8, 'name': 'Texas (Heating Demand)'},
        'europe': {'lat': 50.1, 'lon': 8.7, 'name': 'Germany (EU Demand Center)'},
    },
    'cotton': {
        'us': {'lat': 33.6, 'lon': -101.8, 'name': 'Texas Cotton Belt'},
        'india': {'lat': 17.4, 'lon': 78.5, 'name': 'Hyderabad Region'},
    },
}

# Weather risk thresholds
WEATHER_THRESHOLDS = {
    'extreme_heat': 35.0,  # Celsius
    'extreme_cold': -20.0,
    'heavy_rain': 50.0,  # mm per day
    'drought_days': 14,  # consecutive days without rain
    'high_wind': 15.0,  # m/s
}


def _get_api_key_or_error() -> Tuple[Optional[str], Optional[str]]:
    """
    Helper to get API key or return friendly error message
    
    Returns:
        Tuple of (api_key, error_message)
    """
    if not OWM_API_KEY:
        error_msg = (
            "❌ OPENWEATHERMAP_API_KEY not found in environment.\n\n"
            "To get a FREE API key:\n"
            "1. Visit https://openweathermap.org/price (Free tier: 60 calls/min)\n"
            "2. Click 'Get API Key' and sign up\n"
            "3. Add to .env file: OPENWEATHERMAP_API_KEY=your_key_here\n"
            "4. Free tier includes: Current weather, 5-day forecast, Air pollution\n\n"
            "Then re-run this function."
        )
        return None, error_msg
    return OWM_API_KEY, None


def _parse_location(location: Union[str, Tuple[float, float]]) -> Dict:
    """
    Parse location input (city name or lat/lon tuple)
    
    Args:
        location: Either "City,CountryCode" string or (lat, lon) tuple
    
    Returns:
        Dict with query parameters for API
    """
    if isinstance(location, tuple) and len(location) == 2:
        return {'lat': location[0], 'lon': location[1]}
    else:
        return {'q': str(location)}


def get_current_weather(location: Union[str, Tuple[float, float]], 
                       units: str = 'metric',
                       api_key: Optional[str] = None) -> Dict:
    """
    Get current weather conditions for a location
    
    Args:
        location: City name ("London,UK") or (lat, lon) tuple
        units: 'metric' (°C, m/s), 'imperial' (°F, mph), or 'standard' (K)
        api_key: Optional API key (uses env var if not provided)
    
    Returns:
        Dict with current weather data including temp, humidity, wind, pressure
    
    Example:
        >>> weather = get_current_weather("London,UK")
        >>> weather = get_current_weather((51.5074, -0.1278))  # London coords
    """
    key, error = _get_api_key_or_error()
    if error and not api_key:
        return {'success': False, 'error': error}
    
    api_key = api_key or key
    
    try:
        url = f"{OWM_BASE_URL}/weather"
        params = {
            'appid': api_key,
            'units': units,
            **_parse_location(location)
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Extract key metrics
        result = {
            'success': True,
            'location': {
                'name': data.get('name', 'Unknown'),
                'country': data.get('sys', {}).get('country', ''),
                'lat': data.get('coord', {}).get('lat'),
                'lon': data.get('coord', {}).get('lon'),
            },
            'current': {
                'temp': data['main']['temp'],
                'feels_like': data['main']['feels_like'],
                'temp_min': data['main']['temp_min'],
                'temp_max': data['main']['temp_max'],
                'pressure': data['main']['pressure'],
                'humidity': data['main']['humidity'],
                'wind_speed': data.get('wind', {}).get('speed', 0),
                'wind_deg': data.get('wind', {}).get('deg', 0),
                'clouds': data.get('clouds', {}).get('all', 0),
                'visibility': data.get('visibility', 0),
                'weather': data['weather'][0]['main'],
                'description': data['weather'][0]['description'],
            },
            'rain_1h': data.get('rain', {}).get('1h', 0),
            'snow_1h': data.get('snow', {}).get('1h', 0),
            'timestamp': datetime.fromtimestamp(data['dt']).isoformat(),
            'sunrise': datetime.fromtimestamp(data['sys']['sunrise']).isoformat(),
            'sunset': datetime.fromtimestamp(data['sys']['sunset']).isoformat(),
        }
        
        # Add risk flags
        result['risk_flags'] = []
        if result['current']['temp'] > WEATHER_THRESHOLDS['extreme_heat']:
            result['risk_flags'].append('EXTREME_HEAT')
        if result['current']['temp'] < WEATHER_THRESHOLDS['extreme_cold']:
            result['risk_flags'].append('EXTREME_COLD')
        if result['current']['wind_speed'] > WEATHER_THRESHOLDS['high_wind']:
            result['risk_flags'].append('HIGH_WIND')
        if result['rain_1h'] > 10:
            result['risk_flags'].append('HEAVY_RAIN')
        
        return result
        
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return {'success': False, 'error': 'Invalid API key. Check OPENWEATHERMAP_API_KEY.'}
        return {'success': False, 'error': f'HTTP {e.response.status_code}: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}'}


def get_forecast_5day(location: Union[str, Tuple[float, float]], 
                      units: str = 'metric',
                      api_key: Optional[str] = None) -> Dict:
    """
    Get 5-day weather forecast with 3-hour intervals (40 data points)
    
    Args:
        location: City name or (lat, lon) tuple
        units: Temperature units
        api_key: Optional API key
    
    Returns:
        Dict with 5-day forecast including temp, precipitation, wind trends
    
    Example:
        >>> forecast = get_forecast_5day("Chicago,US")
    """
    key, error = _get_api_key_or_error()
    if error and not api_key:
        return {'success': False, 'error': error}
    
    api_key = api_key or key
    
    try:
        url = f"{OWM_BASE_URL}/forecast"
        params = {
            'appid': api_key,
            'units': units,
            **_parse_location(location)
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        # Process forecast list
        forecasts = []
        daily_summary = {}
        
        for item in data['list']:
            dt = datetime.fromtimestamp(item['dt'])
            day = dt.date().isoformat()
            
            forecast_point = {
                'datetime': dt.isoformat(),
                'temp': item['main']['temp'],
                'feels_like': item['main']['feels_like'],
                'temp_min': item['main']['temp_min'],
                'temp_max': item['main']['temp_max'],
                'pressure': item['main']['pressure'],
                'humidity': item['main']['humidity'],
                'weather': item['weather'][0]['main'],
                'description': item['weather'][0]['description'],
                'wind_speed': item.get('wind', {}).get('speed', 0),
                'clouds': item.get('clouds', {}).get('all', 0),
                'rain_3h': item.get('rain', {}).get('3h', 0),
                'snow_3h': item.get('snow', {}).get('3h', 0),
                'pop': item.get('pop', 0) * 100,  # Probability of precipitation
            }
            forecasts.append(forecast_point)
            
            # Aggregate daily stats
            if day not in daily_summary:
                daily_summary[day] = {
                    'temp_min': forecast_point['temp_min'],
                    'temp_max': forecast_point['temp_max'],
                    'total_rain': 0,
                    'avg_humidity': [],
                    'max_wind': 0,
                }
            
            daily_summary[day]['temp_min'] = min(daily_summary[day]['temp_min'], forecast_point['temp_min'])
            daily_summary[day]['temp_max'] = max(daily_summary[day]['temp_max'], forecast_point['temp_max'])
            daily_summary[day]['total_rain'] += forecast_point['rain_3h']
            daily_summary[day]['avg_humidity'].append(forecast_point['humidity'])
            daily_summary[day]['max_wind'] = max(daily_summary[day]['max_wind'], forecast_point['wind_speed'])
        
        # Finalize daily summary
        for day in daily_summary:
            daily_summary[day]['avg_humidity'] = sum(daily_summary[day]['avg_humidity']) / len(daily_summary[day]['avg_humidity'])
        
        # Trading insights
        insights = []
        total_rain = sum(d['total_rain'] for d in daily_summary.values())
        if total_rain > 100:  # Heavy rain expected
            insights.append(f'Heavy rainfall expected: {total_rain:.1f}mm over 5 days')
        
        temps = [f['temp'] for f in forecasts]
        if max(temps) > WEATHER_THRESHOLDS['extreme_heat']:
            insights.append(f'Extreme heat expected: {max(temps):.1f}°C')
        if min(temps) < WEATHER_THRESHOLDS['extreme_cold']:
            insights.append(f'Extreme cold expected: {min(temps):.1f}°C')
        
        return {
            'success': True,
            'location': {
                'name': data['city']['name'],
                'country': data['city']['country'],
                'lat': data['city']['coord']['lat'],
                'lon': data['city']['coord']['lon'],
            },
            'forecast_3h': forecasts[:16],  # Next 48 hours
            'daily_summary': daily_summary,
            'insights': insights if insights else ['Normal conditions expected'],
            'forecast_count': len(forecasts),
            'timestamp': datetime.now().isoformat(),
        }
        
    except requests.HTTPError as e:
        return {'success': False, 'error': f'HTTP {e.response.status_code}: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}'}


def get_air_pollution(lat: float, lon: float, api_key: Optional[str] = None) -> Dict:
    """
    Get air quality index (AQI) and pollutant concentrations
    
    Args:
        lat: Latitude
        lon: Longitude
        api_key: Optional API key
    
    Returns:
        Dict with AQI (1-5 scale), CO, NO, NO2, O3, SO2, PM2.5, PM10, NH3
    
    Example:
        >>> aqi = get_air_pollution(51.5074, -0.1278)  # London
    """
    key, error = _get_api_key_or_error()
    if error and not api_key:
        return {'success': False, 'error': error}
    
    api_key = api_key or key
    
    try:
        url = f"{OWM_BASE_URL}/air_pollution"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('list'):
            return {'success': False, 'error': 'No air pollution data available'}
        
        pollution = data['list'][0]
        aqi = pollution['main']['aqi']
        components = pollution['components']
        
        # AQI interpretation
        aqi_levels = {
            1: 'Good',
            2: 'Fair',
            3: 'Moderate',
            4: 'Poor',
            5: 'Very Poor'
        }
        
        # Health implications for trading (ESG, supply chain)
        health_impact = []
        if aqi >= 4:
            health_impact.append('Poor air quality may impact outdoor work, logistics')
        if components.get('pm2_5', 0) > 35:
            health_impact.append(f'High PM2.5: {components["pm2_5"]:.1f} μg/m³')
        if components.get('pm10', 0) > 50:
            health_impact.append(f'High PM10: {components["pm10"]:.1f} μg/m³')
        
        return {
            'success': True,
            'location': {'lat': lat, 'lon': lon},
            'aqi': aqi,
            'aqi_level': aqi_levels.get(aqi, 'Unknown'),
            'components': {
                'co': components.get('co', 0),  # Carbon monoxide (μg/m³)
                'no': components.get('no', 0),  # Nitric oxide
                'no2': components.get('no2', 0),  # Nitrogen dioxide
                'o3': components.get('o3', 0),  # Ozone
                'so2': components.get('so2', 0),  # Sulphur dioxide
                'pm2_5': components.get('pm2_5', 0),  # Fine particles
                'pm10': components.get('pm10', 0),  # Coarse particles
                'nh3': components.get('nh3', 0),  # Ammonia
            },
            'health_impact': health_impact if health_impact else ['Air quality acceptable'],
            'timestamp': datetime.fromtimestamp(pollution['dt']).isoformat(),
        }
        
    except requests.HTTPError as e:
        return {'success': False, 'error': f'HTTP {e.response.status_code}: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}'}


def get_historical_weather(lat: float, lon: float, date: str, 
                          api_key: Optional[str] = None) -> Dict:
    """
    Get historical weather data (PREMIUM FEATURE - not available on free tier)
    
    Args:
        lat: Latitude
        lon: Longitude
        date: Date string 'YYYY-MM-DD'
        api_key: Optional API key
    
    Returns:
        Dict with error message explaining premium requirement
    
    Note:
        Historical weather is NOT available on OpenWeatherMap free tier.
        Requires 'History' subscription.
        For backtesting, use archived forecast data or alternative sources.
    """
    return {
        'success': False,
        'error': 'Historical weather data requires OpenWeatherMap Premium subscription',
        'message': (
            'The free tier does NOT include historical weather data.\n'
            'Alternatives:\n'
            '1. Use archived forecast data (collect forecasts daily)\n'
            '2. Use NOAA Climate Data: https://www.ncdc.noaa.gov/cdo-web/\n'
            '3. Use Visual Crossing Weather API (1000 free records/day)\n'
            '4. Upgrade to OpenWeatherMap History subscription'
        ),
        'requested': {'lat': lat, 'lon': lon, 'date': date}
    }


def get_weather_alerts(lat: float, lon: float, api_key: Optional[str] = None) -> Dict:
    """
    Get severe weather alerts (OneCall API - requires separate subscription)
    
    Args:
        lat: Latitude
        lon: Longitude
        api_key: Optional API key
    
    Returns:
        Dict with weather alerts if any
    
    Note:
        Weather alerts are part of OneCall API 3.0, which requires
        separate subscription ($0 for first 1000 calls/day, then paid).
    """
    key, error = _get_api_key_or_error()
    if error and not api_key:
        return {'success': False, 'error': error}
    
    api_key = api_key or key
    
    try:
        # Try OneCall 3.0 (may require separate subscription)
        url = "https://api.openweathermap.org/data/3.0/onecall"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': api_key,
            'exclude': 'minutely,hourly,daily'  # Only get alerts
        }
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        alerts = data.get('alerts', [])
        
        if not alerts:
            return {
                'success': True,
                'location': {'lat': lat, 'lon': lon},
                'alerts': [],
                'message': 'No active weather alerts',
                'timestamp': datetime.now().isoformat(),
            }
        
        # Process alerts
        processed_alerts = []
        for alert in alerts:
            processed_alerts.append({
                'event': alert.get('event', ''),
                'start': datetime.fromtimestamp(alert['start']).isoformat(),
                'end': datetime.fromtimestamp(alert['end']).isoformat(),
                'sender': alert.get('sender_name', ''),
                'description': alert.get('description', '')[:200],  # Truncate
                'tags': alert.get('tags', []),
            })
        
        return {
            'success': True,
            'location': {'lat': lat, 'lon': lon},
            'alerts': processed_alerts,
            'alert_count': len(processed_alerts),
            'timestamp': datetime.now().isoformat(),
        }
        
    except requests.HTTPError as e:
        if e.response.status_code == 401:
            return {
                'success': False,
                'error': 'OneCall API 3.0 requires separate subscription',
                'message': (
                    'Weather alerts are part of OneCall API.\n'
                    'Sign up at: https://openweathermap.org/api/one-call-3\n'
                    'Free tier: 1,000 calls/day'
                ),
            }
        return {'success': False, 'error': f'HTTP {e.response.status_code}: {str(e)}'}
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}'}


def analyze_commodity_weather_risk(commodity: str, region: str = 'us', 
                                   api_key: Optional[str] = None) -> Dict:
    """
    Analyze weather risk for specific commodity in key production region
    
    Args:
        commodity: Commodity name ('wheat', 'corn', 'soybeans', 'coffee', 
                   'natural_gas', 'cotton')
        region: Region code ('us', 'brazil', 'russia', 'europe', etc.)
        api_key: Optional API key
    
    Returns:
        Dict with current weather, forecast, and commodity-specific risk assessment
    
    Example:
        >>> risk = analyze_commodity_weather_risk('wheat', 'us')
        >>> risk = analyze_commodity_weather_risk('coffee', 'brazil')
    """
    commodity = commodity.lower()
    region = region.lower()
    
    # Validate commodity and region
    if commodity not in COMMODITY_REGIONS:
        available = ', '.join(COMMODITY_REGIONS.keys())
        return {
            'success': False,
            'error': f'Unknown commodity: {commodity}',
            'available_commodities': available
        }
    
    if region not in COMMODITY_REGIONS[commodity]:
        available = ', '.join(COMMODITY_REGIONS[commodity].keys())
        return {
            'success': False,
            'error': f'Unknown region for {commodity}: {region}',
            'available_regions': available
        }
    
    # Get region coordinates
    region_info = COMMODITY_REGIONS[commodity][region]
    lat, lon = region_info['lat'], region_info['lon']
    
    # Fetch current weather and forecast
    current = get_current_weather((lat, lon), api_key=api_key)
    forecast = get_forecast_5day((lat, lon), api_key=api_key)
    
    if not current['success'] or not forecast['success']:
        return {
            'success': False,
            'error': 'Failed to fetch weather data',
            'current_error': current.get('error'),
            'forecast_error': forecast.get('error'),
        }
    
    # Commodity-specific risk analysis
    risk_factors = []
    severity = 'LOW'
    
    temp = current['current']['temp']
    humidity = current['current']['humidity']
    
    # Crop-specific thresholds
    if commodity in ['wheat', 'corn', 'soybeans', 'cotton']:
        # Extreme heat during growing season
        if temp > 35:
            risk_factors.append(f'EXTREME HEAT: {temp}°C - crop stress, reduced yields')
            severity = 'HIGH'
        elif temp > 30:
            risk_factors.append(f'High temperatures: {temp}°C - monitor for stress')
            severity = 'MEDIUM'
        
        # Excessive rain (flooding)
        total_rain = sum(forecast['daily_summary'][day]['total_rain'] 
                        for day in forecast['daily_summary'])
        if total_rain > 100:
            risk_factors.append(f'HEAVY RAIN FORECAST: {total_rain:.1f}mm - flooding risk')
            severity = 'HIGH'
        elif total_rain < 10:
            risk_factors.append(f'Low precipitation: {total_rain:.1f}mm - drought risk')
            severity = 'MEDIUM' if severity == 'LOW' else severity
        
        # Humidity extremes (disease risk)
        if humidity > 85:
            risk_factors.append(f'High humidity: {humidity}% - fungal disease risk')
    
    elif commodity == 'coffee':
        # Coffee is sensitive to frost and excessive rain
        if temp < 5:
            risk_factors.append(f'FROST RISK: {temp}°C - potential crop damage')
            severity = 'HIGH'
        
        total_rain = sum(forecast['daily_summary'][day]['total_rain'] 
                        for day in forecast['daily_summary'])
        if total_rain > 150:
            risk_factors.append(f'Excessive rain: {total_rain:.1f}mm - harvest delays')
            severity = 'MEDIUM'
    
    elif commodity == 'natural_gas':
        # Natural gas demand driven by heating/cooling needs
        if temp < 0:
            risk_factors.append(f'COLD SNAP: {temp}°C - increased heating demand')
            severity = 'HIGH'
        elif temp > 35:
            risk_factors.append(f'Heat wave: {temp}°C - increased cooling demand')
            severity = 'MEDIUM'
    
    # Check for extreme events in forecast
    for risk in forecast.get('insights', []):
        if 'Extreme' in risk or 'Heavy' in risk:
            risk_factors.append(f'FORECAST: {risk}')
            severity = 'HIGH' if 'Extreme' in risk else 'MEDIUM'
    
    if not risk_factors:
        risk_factors.append('Normal weather conditions - no significant risks')
    
    return {
        'success': True,
        'commodity': commodity,
        'region': region,
        'region_name': region_info['name'],
        'location': {'lat': lat, 'lon': lon},
        'current_weather': {
            'temp': temp,
            'humidity': humidity,
            'wind_speed': current['current']['wind_speed'],
            'weather': current['current']['weather'],
            'description': current['current']['description'],
        },
        'risk_assessment': {
            'severity': severity,
            'risk_factors': risk_factors,
            'overall_risk': severity,
        },
        'forecast_summary': forecast.get('insights', []),
        'trading_implications': _get_trading_implications(commodity, severity, risk_factors),
        'timestamp': datetime.now().isoformat(),
    }


def _get_trading_implications(commodity: str, severity: str, risk_factors: List[str]) -> List[str]:
    """
    Generate trading implications based on weather risks
    
    Args:
        commodity: Commodity name
        severity: Risk severity level
        risk_factors: List of identified risks
    
    Returns:
        List of trading implications
    """
    implications = []
    
    if severity == 'HIGH':
        implications.append(f'⚠️ High risk to {commodity} supply - expect price volatility')
        
        if commodity in ['wheat', 'corn', 'soybeans']:
            implications.append('Consider bullish positioning on crop futures')
            implications.append('Monitor USDA crop reports for yield revisions')
        elif commodity == 'coffee':
            implications.append('Potential supply disruption - monitor Brazilian crop reports')
        elif commodity == 'natural_gas':
            implications.append('Demand spike expected - bullish for NG futures')
    
    elif severity == 'MEDIUM':
        implications.append(f'Moderate weather risk to {commodity} - increased monitoring')
        implications.append('Volatility may increase as weather window narrows')
    
    else:
        implications.append(f'Normal conditions for {commodity} production')
        implications.append('Weather not a significant price driver currently')
    
    # Specific risk-based implications
    for risk in risk_factors:
        if 'FROST' in risk.upper():
            implications.append('Frost damage can cause 20-40% yield loss - major bullish catalyst')
        elif 'FLOOD' in risk.upper() or 'HEAVY RAIN' in risk.upper():
            implications.append('Flooding delays planting/harvest, reduces quality - bullish bias')
        elif 'DROUGHT' in risk.upper():
            implications.append('Drought stress reduces yields - long-term bullish if persistent')
        elif 'EXTREME HEAT' in risk.upper():
            implications.append('Heat stress during pollination = permanent yield loss')
    
    return implications


def get_weather_snapshot(lat: float, lon: float, api_key: Optional[str] = None) -> Dict:
    """
    Get comprehensive weather snapshot: current + forecast + air quality
    
    Args:
        lat: Latitude
        lon: Longitude
        api_key: Optional API key
    
    Returns:
        Dict with complete weather picture for trading analysis
    """
    current = get_current_weather((lat, lon), api_key=api_key)
    forecast = get_forecast_5day((lat, lon), api_key=api_key)
    aqi = get_air_pollution(lat, lon, api_key=api_key)
    
    return {
        'success': True,
        'location': {'lat': lat, 'lon': lon},
        'current': current if current['success'] else {'error': current.get('error')},
        'forecast': forecast if forecast['success'] else {'error': forecast.get('error')},
        'air_quality': aqi if aqi['success'] else {'error': aqi.get('error')},
        'timestamp': datetime.now().isoformat(),
    }


def list_available_commodities() -> Dict:
    """
    List all commodities and regions available for risk analysis
    
    Returns:
        Dict with commodity-region mapping
    """
    commodities_list = {}
    
    for commodity, regions in COMMODITY_REGIONS.items():
        commodities_list[commodity] = {
            'regions': list(regions.keys()),
            'region_details': [
                {'code': code, 'name': info['name'], 'coords': (info['lat'], info['lon'])}
                for code, info in regions.items()
            ]
        }
    
    return {
        'success': True,
        'commodities': commodities_list,
        'total_commodities': len(COMMODITY_REGIONS),
        'total_regions': sum(len(regions) for regions in COMMODITY_REGIONS.values()),
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("OpenWeatherMap Climate API - Weather Data for Trading")
    print("=" * 70)
    
    # Check API key
    key, error = _get_api_key_or_error()
    if error:
        print("\n" + error)
        print("\n⚠️  Module will import but functions will fail without API key")
    else:
        print(f"\n✅ API key configured: {key[:8]}...{key[-4:]}")
    
    # Show available commodities
    print("\n" + "=" * 70)
    print("Available Commodity Risk Analysis:")
    print("=" * 70)
    
    commodities = list_available_commodities()
    for commodity, info in commodities['commodities'].items():
        print(f"\n{commodity.upper()}")
        for region in info['region_details']:
            print(f"  {region['code']}: {region['name']} {region['coords']}")
    
    print("\n" + "=" * 70)
    print("Example Usage:")
    print("=" * 70)
    print("""
# Get current weather
weather = get_current_weather("Chicago,US")

# Get 5-day forecast
forecast = get_forecast_5day((41.8781, -87.6298))

# Check air quality
aqi = get_air_pollution(40.7128, -74.0060)  # New York

# Analyze commodity risk
risk = analyze_commodity_weather_risk('wheat', 'us')

# Complete snapshot
snapshot = get_weather_snapshot(51.5074, -0.1278)  # London
""")
    
    print("\n" + "=" * 70)
    print("Module Status: READY")
    print("=" * 70)
