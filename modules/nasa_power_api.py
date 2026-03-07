#!/usr/bin/env python3
"""
NASA POWER API — Satellite & Geospatial Climate Data Module

Provides solar and meteorological data from NASA POWER
(Prediction Of Worldwide Energy Resources) for:
- Agriculture commodity trading (weather pattern analysis)
- Solar/renewable energy sector analysis
- Climate risk modeling for portfolios
- Extreme weather impact assessment

Source: https://power.larc.nasa.gov/docs/services/api/
Category: Alternative Data — Satellite & Geospatial
Free tier: True (no API key required, public access)
Update frequency: Daily
Coverage: Global, 1981-present
Resolution: 0.5° x 0.625° (latitude x longitude)
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

# NASA POWER API Configuration
NASA_POWER_BASE_URL = "https://power.larc.nasa.gov/api/temporal/daily/point"

# ========== PARAMETER REGISTRY ==========

# Solar & Radiation Parameters
SOLAR_PARAMS = {
    'ALLSKY_SFC_SW_DWN': 'All Sky Surface Shortwave Downward Irradiance (kW-hr/m^2/day)',
    'CLRSKY_SFC_SW_DWN': 'Clear Sky Surface Shortwave Downward Irradiance (kW-hr/m^2/day)',
    'ALLSKY_SFC_PAR_TOT': 'All Sky Surface PAR Total (W/m^2)',
    'ALLSKY_SFC_UVA': 'All Sky Surface UVA Irradiance (W/m^2)',
    'ALLSKY_SFC_UVB': 'All Sky Surface UVB Irradiance (W/m^2)',
}

# Temperature & Humidity Parameters
TEMPERATURE_PARAMS = {
    'T2M': 'Temperature at 2 Meters (C)',
    'T2M_MAX': 'Temperature at 2 Meters Maximum (C)',
    'T2M_MIN': 'Temperature at 2 Meters Minimum (C)',
    'T2MDEW': 'Dew/Frost Point at 2 Meters (C)',
    'RH2M': 'Relative Humidity at 2 Meters (%)',
    'QV2M': 'Specific Humidity at 2 Meters (g/kg)',
}

# Wind Parameters
WIND_PARAMS = {
    'WS2M': 'Wind Speed at 2 Meters (m/s)',
    'WS10M': 'Wind Speed at 10 Meters (m/s)',
    'WS50M': 'Wind Speed at 50 Meters (m/s)',
    'WD2M': 'Wind Direction at 2 Meters (Degrees)',
    'WD10M': 'Wind Direction at 10 Meters (Degrees)',
    'WD50M': 'Wind Direction at 50 Meters (Degrees)',
}

# Precipitation Parameters
PRECIPITATION_PARAMS = {
    'PRECTOTCORR': 'Precipitation Corrected (mm/day)',
    'PRECTOTCORR_SUM': 'Precipitation Corrected Sum (mm)',
    'CLOUD_AMT': 'Cloud Amount (%)',
}

# Agricultural Parameters
AGRO_PARAMS = {
    'T2M': 'Temperature at 2 Meters (C)',
    'T2M_MAX': 'Max Temperature (C)',
    'T2M_MIN': 'Min Temperature (C)',
    'PRECTOTCORR': 'Precipitation (mm/day)',
    'RH2M': 'Relative Humidity (%)',
    'WS2M': 'Wind Speed (m/s)',
    'ALLSKY_SFC_SW_DWN': 'Solar Irradiance (kW-hr/m^2/day)',
}

# Community identifiers
COMMUNITIES = {
    'AG': 'Agroclimatology',
    'RE': 'Renewable Energy',
    'SB': 'Sustainable Buildings',
}


def _format_date(date_input) -> str:
    """
    Convert date to NASA POWER API format (YYYYMMDD)
    
    Args:
        date_input: datetime object or string in YYYY-MM-DD format
    
    Returns:
        String in YYYYMMDD format
    """
    if isinstance(date_input, str):
        # Handle YYYY-MM-DD format
        date_obj = datetime.strptime(date_input, '%Y-%m-%d')
    elif isinstance(date_input, datetime):
        date_obj = date_input
    else:
        raise ValueError(f"Invalid date format: {date_input}. Use YYYY-MM-DD string or datetime object")
    
    return date_obj.strftime('%Y%m%d')


def _fetch_nasa_power(
    parameters: List[str],
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
    community: str = 'AG'
) -> Dict:
    """
    Core NASA POWER API fetcher (helper function)
    
    Args:
        parameters: List of parameter codes (e.g., ['T2M', 'PRECTOTCORR'])
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        start_date: Start date (YYYY-MM-DD or YYYYMMDD)
        end_date: End date (YYYY-MM-DD or YYYYMMDD)
        community: Data community (AG, RE, SB)
    
    Returns:
        Dict with NASA POWER response data
    """
    try:
        # Validate coordinates
        if not (-90 <= latitude <= 90):
            raise ValueError(f"Latitude must be between -90 and 90, got {latitude}")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"Longitude must be between -180 and 180, got {longitude}")
        
        # Format dates
        start_fmt = _format_date(start_date)
        end_fmt = _format_date(end_date)
        
        # Build request
        params = {
            'parameters': ','.join(parameters),
            'community': community,
            'longitude': longitude,
            'latitude': latitude,
            'start': start_fmt,
            'end': end_fmt,
            'format': 'JSON'
        }
        
        response = requests.get(NASA_POWER_BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        if 'properties' not in data or 'parameter' not in data.get('properties', {}):
            return {
                'success': False,
                'error': 'No parameter data in response',
                'raw_response': data
            }
        
        return {
            'success': True,
            'data': data,
            'location': {
                'latitude': latitude,
                'longitude': longitude
            },
            'period': {
                'start': start_date,
                'end': end_date
            },
            'parameters_requested': parameters,
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'location': {'latitude': latitude, 'longitude': longitude}
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'location': {'latitude': latitude, 'longitude': longitude}
        }


def _extract_timeseries(data: Dict, param_codes: List[str]) -> Dict[str, List[Dict]]:
    """
    Extract and format time series data from NASA POWER response
    
    Args:
        data: NASA POWER API response data
        param_codes: List of parameter codes to extract
    
    Returns:
        Dict mapping parameter codes to time series arrays
    """
    timeseries = {}
    
    # NASA POWER data is in properties.parameter
    if 'properties' not in data or 'parameter' not in data['properties']:
        return timeseries
    
    param_data_root = data['properties']['parameter']
    
    for param in param_codes:
        if param in param_data_root:
            param_data = param_data_root[param]
            
            # Convert to list of {date, value} dicts
            series = []
            for date_str, value in param_data.items():
                if date_str.isdigit() and len(date_str) == 8:  # YYYYMMDD format
                    try:
                        date_obj = datetime.strptime(date_str, '%Y%m%d')
                        series.append({
                            'date': date_obj.strftime('%Y-%m-%d'),
                            'value': value
                        })
                    except ValueError:
                        continue
            
            series.sort(key=lambda x: x['date'])
            timeseries[param] = series
    
    return timeseries


def _calculate_stats(series: List[Dict]) -> Dict:
    """
    Calculate statistics for a time series
    
    Args:
        series: List of {date, value} dicts
    
    Returns:
        Dict with min, max, mean, latest stats
    """
    if not series:
        return {}
    
    values = [item['value'] for item in series if isinstance(item['value'], (int, float))]
    
    if not values:
        return {}
    
    return {
        'latest': values[-1],
        'latest_date': series[-1]['date'],
        'min': min(values),
        'max': max(values),
        'mean': sum(values) / len(values),
        'count': len(values)
    }


def get_solar_radiation(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str
) -> Dict:
    """
    Get solar irradiance and radiation data
    
    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dict with solar radiation time series and statistics
    
    Example:
        >>> data = get_solar_radiation(40.78, -73.96, '2026-01-01', '2026-02-01')
        >>> print(data['stats']['ALLSKY_SFC_SW_DWN'])
    """
    params = ['ALLSKY_SFC_SW_DWN', 'CLRSKY_SFC_SW_DWN', 'ALLSKY_SFC_PAR_TOT']
    
    result = _fetch_nasa_power(params, latitude, longitude, start_date, end_date, community='RE')
    
    if not result['success']:
        return result
    
    # Extract time series
    timeseries = _extract_timeseries(result['data'], params)
    
    # Calculate statistics for each parameter
    stats = {}
    for param, series in timeseries.items():
        stats[param] = _calculate_stats(series)
    
    return {
        'success': True,
        'location': result['location'],
        'period': result['period'],
        'timeseries': timeseries,
        'stats': stats,
        'parameter_descriptions': {k: SOLAR_PARAMS[k] for k in params if k in SOLAR_PARAMS},
        'timestamp': result['timestamp']
    }


def get_temperature_data(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str
) -> Dict:
    """
    Get temperature and humidity data
    
    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dict with temperature/humidity time series and statistics
    
    Example:
        >>> data = get_temperature_data(40.78, -73.96, '2026-01-01', '2026-02-01')
        >>> print(f"Avg temp: {data['stats']['T2M']['mean']:.1f}°C")
    """
    params = ['T2M', 'T2M_MAX', 'T2M_MIN', 'T2MDEW', 'RH2M']
    
    result = _fetch_nasa_power(params, latitude, longitude, start_date, end_date, community='AG')
    
    if not result['success']:
        return result
    
    timeseries = _extract_timeseries(result['data'], params)
    
    stats = {}
    for param, series in timeseries.items():
        stats[param] = _calculate_stats(series)
    
    # Calculate temperature range
    insights = []
    if 'T2M_MAX' in stats and 'T2M_MIN' in stats and stats['T2M_MAX'] and stats['T2M_MIN']:
        if 'mean' in stats['T2M_MAX'] and 'mean' in stats['T2M_MIN']:
            temp_range = stats['T2M_MAX']['mean'] - stats['T2M_MIN']['mean']
            insights.append(f"Average daily temperature range: {temp_range:.1f}°C")
    
    if 'T2M' in stats and stats['T2M'] and 'mean' in stats['T2M']:
        avg_temp = stats['T2M']['mean']
        if avg_temp > 30:
            insights.append("High temperature conditions (>30°C avg)")
        elif avg_temp < 0:
            insights.append("Freezing conditions (<0°C avg)")
    
    return {
        'success': True,
        'location': result['location'],
        'period': result['period'],
        'timeseries': timeseries,
        'stats': stats,
        'insights': insights,
        'parameter_descriptions': {k: TEMPERATURE_PARAMS[k] for k in params if k in TEMPERATURE_PARAMS},
        'timestamp': result['timestamp']
    }


def get_wind_data(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str
) -> Dict:
    """
    Get wind speed and direction data at multiple heights
    
    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dict with wind data time series and statistics
    
    Example:
        >>> data = get_wind_data(40.78, -73.96, '2026-01-01', '2026-02-01')
        >>> print(f"Avg wind speed: {data['stats']['WS10M']['mean']:.1f} m/s")
    """
    params = ['WS2M', 'WS10M', 'WS50M', 'WD10M']
    
    result = _fetch_nasa_power(params, latitude, longitude, start_date, end_date, community='RE')
    
    if not result['success']:
        return result
    
    timeseries = _extract_timeseries(result['data'], params)
    
    stats = {}
    for param, series in timeseries.items():
        stats[param] = _calculate_stats(series)
    
    # Wind energy insights
    insights = []
    if 'WS50M' in stats and stats['WS50M'] and 'mean' in stats['WS50M']:
        avg_wind_50m = stats['WS50M']['mean']
        if avg_wind_50m > 6.0:
            insights.append(f"Good wind energy potential at 50m: {avg_wind_50m:.1f} m/s avg")
        elif avg_wind_50m < 3.0:
            insights.append(f"Low wind energy potential: {avg_wind_50m:.1f} m/s avg")
    
    return {
        'success': True,
        'location': result['location'],
        'period': result['period'],
        'timeseries': timeseries,
        'stats': stats,
        'insights': insights,
        'parameter_descriptions': {k: WIND_PARAMS[k] for k in params if k in WIND_PARAMS},
        'timestamp': result['timestamp']
    }


def get_precipitation(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str
) -> Dict:
    """
    Get precipitation and cloud cover data
    
    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dict with precipitation time series and statistics
    
    Example:
        >>> data = get_precipitation(40.78, -73.96, '2026-01-01', '2026-02-01')
        >>> total_rain = sum(p['value'] for p in data['timeseries']['PRECTOTCORR'])
        >>> print(f"Total rainfall: {total_rain:.1f} mm")
    """
    params = ['PRECTOTCORR', 'CLOUD_AMT']
    
    result = _fetch_nasa_power(params, latitude, longitude, start_date, end_date, community='AG')
    
    if not result['success']:
        return result
    
    timeseries = _extract_timeseries(result['data'], params)
    
    stats = {}
    for param, series in timeseries.items():
        stats[param] = _calculate_stats(series)
    
    # Calculate total precipitation
    insights = []
    if 'PRECTOTCORR' in timeseries and timeseries['PRECTOTCORR']:
        total_precip = sum(p['value'] for p in timeseries['PRECTOTCORR'] if isinstance(p['value'], (int, float)))
        insights.append(f"Total precipitation: {total_precip:.1f} mm")
        
        # Count rainy days (>1mm threshold)
        rainy_days = sum(1 for p in timeseries['PRECTOTCORR'] if isinstance(p['value'], (int, float)) and p['value'] > 1.0)
        insights.append(f"Rainy days (>1mm): {rainy_days}")
    
    if 'CLOUD_AMT' in stats and stats['CLOUD_AMT'] and 'mean' in stats['CLOUD_AMT']:
        avg_cloud = stats['CLOUD_AMT']['mean']
        if avg_cloud > 70:
            insights.append("Very cloudy conditions (>70% avg)")
        elif avg_cloud < 30:
            insights.append("Mostly clear conditions (<30% avg)")
    
    return {
        'success': True,
        'location': result['location'],
        'period': result['period'],
        'timeseries': timeseries,
        'stats': stats,
        'insights': insights,
        'parameter_descriptions': {k: PRECIPITATION_PARAMS[k] for k in params if k in PRECIPITATION_PARAMS},
        'timestamp': result['timestamp']
    }


def get_climate_summary(
    latitude: float,
    longitude: float,
    year: int
) -> Dict:
    """
    Get annual climate summary for a location
    
    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        year: Year (1981-present)
    
    Returns:
        Dict with annual climate statistics
    
    Example:
        >>> summary = get_climate_summary(40.78, -73.96, 2025)
        >>> print(f"Annual avg temp: {summary['annual_stats']['temperature']['mean']:.1f}°C")
    """
    start_date = f"{year}-01-01"
    end_date = f"{year}-12-31"
    
    params = ['T2M', 'T2M_MAX', 'T2M_MIN', 'PRECTOTCORR', 'ALLSKY_SFC_SW_DWN', 'WS10M']
    
    result = _fetch_nasa_power(params, latitude, longitude, start_date, end_date, community='AG')
    
    if not result['success']:
        return result
    
    timeseries = _extract_timeseries(result['data'], params)
    
    # Calculate annual statistics
    annual_stats = {}
    
    if 'T2M' in timeseries and timeseries['T2M']:
        temp_series = [p['value'] for p in timeseries['T2M'] if isinstance(p['value'], (int, float))]
        if temp_series:
            annual_stats['temperature'] = {
                'mean': sum(temp_series) / len(temp_series),
                'min': min(temp_series),
                'max': max(temp_series),
                'unit': '°C'
            }
    
    if 'PRECTOTCORR' in timeseries and timeseries['PRECTOTCORR']:
        precip_series = [p['value'] for p in timeseries['PRECTOTCORR'] if isinstance(p['value'], (int, float))]
        if precip_series:
            total_precip = sum(precip_series)
            annual_stats['precipitation'] = {
                'total': total_precip,
                'average_daily': total_precip / len(precip_series),
                'unit': 'mm'
            }
    
    if 'ALLSKY_SFC_SW_DWN' in timeseries and timeseries['ALLSKY_SFC_SW_DWN']:
        solar_series = [p['value'] for p in timeseries['ALLSKY_SFC_SW_DWN'] if isinstance(p['value'], (int, float))]
        if solar_series:
            annual_stats['solar_radiation'] = {
                'mean': sum(solar_series) / len(solar_series),
                'total': sum(solar_series),
                'unit': 'kW-hr/m^2/day'
            }
    
    return {
        'success': True,
        'location': result['location'],
        'year': year,
        'annual_stats': annual_stats,
        'data_completeness': {param: len(timeseries[param]) for param in params if param in timeseries},
        'timestamp': result['timestamp']
    }


def get_agro_climatology(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str
) -> Dict:
    """
    Get comprehensive agricultural weather data
    Combines temperature, precipitation, humidity, wind, and solar for crop modeling
    
    Args:
        latitude: Latitude (-90 to 90)
        longitude: Longitude (-180 to 180)
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
    
    Returns:
        Dict with comprehensive agricultural climate data
    
    Example:
        >>> agro = get_agro_climatology(40.78, -73.96, '2026-01-01', '2026-02-01')
        >>> print(agro['agricultural_insights'])
    """
    params = list(AGRO_PARAMS.keys())
    
    result = _fetch_nasa_power(params, latitude, longitude, start_date, end_date, community='AG')
    
    if not result['success']:
        return result
    
    timeseries = _extract_timeseries(result['data'], params)
    
    stats = {}
    for param, series in timeseries.items():
        stats[param] = _calculate_stats(series)
    
    # Agricultural insights
    insights = []
    
    # Temperature stress analysis
    if 'T2M_MAX' in stats and stats['T2M_MAX'] and 'max' in stats['T2M_MAX']:
        max_temp = stats['T2M_MAX']['max']
        if max_temp > 35:
            insights.append(f"Heat stress risk: max temp {max_temp:.1f}°C")
    
    if 'T2M_MIN' in stats and stats['T2M_MIN'] and 'min' in stats['T2M_MIN']:
        min_temp = stats['T2M_MIN']['min']
        if min_temp < 0:
            insights.append(f"Frost risk: min temp {min_temp:.1f}°C")
    
    # Drought/flood analysis
    if 'PRECTOTCORR' in timeseries and timeseries['PRECTOTCORR']:
        precip_values = [p['value'] for p in timeseries['PRECTOTCORR'] if isinstance(p['value'], (int, float))]
        if precip_values:
            total_precip = sum(precip_values)
            days = len(precip_values)
            
            if total_precip < 25 and days >= 30:
                insights.append(f"Drought conditions: only {total_precip:.1f}mm in {days} days")
            elif total_precip > 200 and days >= 30:
                insights.append(f"Excessive rainfall: {total_precip:.1f}mm in {days} days")
    
    # Humidity stress
    if 'RH2M' in stats and stats['RH2M'] and 'mean' in stats['RH2M']:
        avg_humidity = stats['RH2M']['mean']
        if avg_humidity > 80:
            insights.append("High humidity - disease risk")
        elif avg_humidity < 30:
            insights.append("Low humidity - drought stress")
    
    if not insights:
        insights.append("Normal agricultural conditions")
    
    return {
        'success': True,
        'location': result['location'],
        'period': result['period'],
        'timeseries': timeseries,
        'stats': stats,
        'agricultural_insights': insights,
        'parameter_descriptions': AGRO_PARAMS,
        'timestamp': result['timestamp']
    }


def list_all_parameters() -> Dict:
    """
    List all available parameters organized by category
    
    Returns:
        Dict with all parameters and descriptions
    """
    all_params = {
        'Solar & Radiation': SOLAR_PARAMS,
        'Temperature & Humidity': TEMPERATURE_PARAMS,
        'Wind': WIND_PARAMS,
        'Precipitation': PRECIPITATION_PARAMS,
        'Agricultural': AGRO_PARAMS,
    }
    
    total_count = sum(len(params) for params in all_params.values())
    
    return {
        'success': True,
        'total_parameters': total_count,
        'categories': all_params,
        'communities': COMMUNITIES,
        'module': 'nasa_power_api',
        'source': NASA_POWER_BASE_URL
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("NASA POWER API - Satellite & Geospatial Climate Data")
    print("=" * 70)
    
    # List available parameters
    params_info = list_all_parameters()
    print(f"\nTotal Parameters: {params_info['total_parameters']}")
    print("\nCategories:")
    for category, params in params_info['categories'].items():
        print(f"  {category}: {len(params)} parameters")
    
    print("\n" + json.dumps(params_info, indent=2))
