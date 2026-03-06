#!/usr/bin/env python3
"""
EOSDA Crop Monitoring API - Satellite-derived agricultural data
EOS Data Analytics provides field-level crop analytics for yield prediction and risk assessment.
Integrates multispectral imagery for ag commodity trading models.

Source: https://eos.com/products/crop-monitoring/api
Category: Alternative Data — Satellite & Geospatial
Free tier: 5 fields/month, 100 API calls/day
Update frequency: daily
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

BASE_URL = "https://api.eos.com/crop-monitoring/v1"

def get_field_ndvi(field_id: str, date_from: str, date_to: str, api_token: Optional[str] = None) -> Dict:
    """
    Get NDVI (Normalized Difference Vegetation Index) for a field.
    
    Args:
        field_id: Field identifier
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        api_token: EOSDA API token (optional for demo mode)
    
    Returns:
        dict: NDVI time series data
        
    Example:
        >>> ndvi = get_field_ndvi('12345', '2026-01-01', '2026-03-01')
    """
    try:
        url = f"{BASE_URL}/fields/{field_id}/ndvi"
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        headers = {}
        if api_token:
            headers['Authorization'] = f'Bearer {api_token}'
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned {response.status_code}",
                "message": response.text[:200],
                "field_id": field_id,
                "note": "Free tier: 5 fields/month, 100 calls/day. Requires API token from eos.com"
            }
    except Exception as e:
        return {
            "error": str(e),
            "field_id": field_id,
            "note": "EOSDA API requires registration at eos.com for API token"
        }

def get_field_evi(field_id: str, date_from: str, date_to: str, api_token: Optional[str] = None) -> Dict:
    """
    Get EVI (Enhanced Vegetation Index) for a field.
    EVI is more sensitive to high biomass regions than NDVI.
    
    Args:
        field_id: Field identifier
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        api_token: EOSDA API token
    
    Returns:
        dict: EVI time series data
    """
    try:
        url = f"{BASE_URL}/fields/{field_id}/evi"
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        headers = {}
        if api_token:
            headers['Authorization'] = f'Bearer {api_token}'
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned {response.status_code}",
                "field_id": field_id,
                "metric": "EVI"
            }
    except Exception as e:
        return {"error": str(e), "field_id": field_id}

def get_soil_moisture(field_id: str, date_from: str, date_to: str, api_token: Optional[str] = None) -> Dict:
    """
    Get soil moisture levels for a field.
    Critical for yield forecasting and drought risk assessment.
    
    Args:
        field_id: Field identifier
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        api_token: EOSDA API token
    
    Returns:
        dict: Soil moisture time series
    """
    try:
        url = f"{BASE_URL}/fields/{field_id}/soil-moisture"
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        headers = {}
        if api_token:
            headers['Authorization'] = f'Bearer {api_token}'
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned {response.status_code}",
                "field_id": field_id,
                "metric": "soil_moisture"
            }
    except Exception as e:
        return {"error": str(e), "field_id": field_id}

def get_weather_impact(field_id: str, date_from: str, date_to: str, api_token: Optional[str] = None) -> Dict:
    """
    Get weather impact scores for crop development.
    
    Args:
        field_id: Field identifier
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        api_token: EOSDA API token
    
    Returns:
        dict: Weather impact metrics (temperature stress, precipitation deficit, etc.)
    """
    try:
        url = f"{BASE_URL}/fields/{field_id}/weather-impact"
        params = {
            'date_from': date_from,
            'date_to': date_to
        }
        headers = {}
        if api_token:
            headers['Authorization'] = f'Bearer {api_token}'
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned {response.status_code}",
                "field_id": field_id,
                "metric": "weather_impact"
            }
    except Exception as e:
        return {"error": str(e), "field_id": field_id}

def get_yield_forecast(field_id: str, api_token: Optional[str] = None) -> Dict:
    """
    Get yield forecast for a field (current season).
    
    Args:
        field_id: Field identifier
        api_token: EOSDA API token
    
    Returns:
        dict: Yield forecast metrics
    """
    try:
        url = f"{BASE_URL}/fields/{field_id}/yield-forecast"
        headers = {}
        if api_token:
            headers['Authorization'] = f'Bearer {api_token}'
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned {response.status_code}",
                "field_id": field_id,
                "metric": "yield_forecast"
            }
    except Exception as e:
        return {"error": str(e), "field_id": field_id}

def list_fields(api_token: Optional[str] = None) -> Dict:
    """
    List all monitored fields under your account.
    Free tier: up to 5 fields.
    
    Args:
        api_token: EOSDA API token
    
    Returns:
        dict: List of fields with IDs and metadata
    """
    try:
        url = f"{BASE_URL}/fields"
        headers = {}
        if api_token:
            headers['Authorization'] = f'Bearer {api_token}'
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned {response.status_code}",
                "note": "Register at eos.com to create fields and get API token"
            }
    except Exception as e:
        return {"error": str(e)}

def get_harvest_readiness(field_id: str, api_token: Optional[str] = None) -> Dict:
    """
    Get harvest readiness score for a field.
    
    Args:
        field_id: Field identifier
        api_token: EOSDA API token
    
    Returns:
        dict: Harvest readiness metrics
    """
    try:
        url = f"{BASE_URL}/fields/{field_id}/harvest-readiness"
        headers = {}
        if api_token:
            headers['Authorization'] = f'Bearer {api_token}'
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            return response.json()
        else:
            return {
                "error": f"API returned {response.status_code}",
                "field_id": field_id
            }
    except Exception as e:
        return {"error": str(e), "field_id": field_id}

def get_crop_health_summary(field_id: str, api_token: Optional[str] = None) -> Dict:
    """
    Get comprehensive crop health summary including multiple indices.
    Convenience function combining NDVI, EVI, soil moisture, and weather impact.
    
    Args:
        field_id: Field identifier
        api_token: EOSDA API token
    
    Returns:
        dict: Combined health metrics
    """
    today = datetime.now().strftime('%Y-%m-%d')
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    
    summary = {
        "field_id": field_id,
        "date_range": f"{thirty_days_ago} to {today}",
        "ndvi": get_field_ndvi(field_id, thirty_days_ago, today, api_token),
        "evi": get_field_evi(field_id, thirty_days_ago, today, api_token),
        "soil_moisture": get_soil_moisture(field_id, thirty_days_ago, today, api_token),
        "weather_impact": get_weather_impact(field_id, thirty_days_ago, today, api_token),
        "yield_forecast": get_yield_forecast(field_id, api_token),
        "harvest_readiness": get_harvest_readiness(field_id, api_token)
    }
    
    return summary

if __name__ == "__main__":
    # Demo mode - shows module structure
    result = {
        "module": "eosda_crop_monitoring",
        "description": "Satellite-derived agricultural analytics for commodity trading",
        "source": "https://eos.com/products/crop-monitoring/api",
        "free_tier": "5 fields/month, 100 API calls/day",
        "functions": [
            "get_field_ndvi(field_id, date_from, date_to, api_token)",
            "get_field_evi(field_id, date_from, date_to, api_token)",
            "get_soil_moisture(field_id, date_from, date_to, api_token)",
            "get_weather_impact(field_id, date_from, date_to, api_token)",
            "get_yield_forecast(field_id, api_token)",
            "list_fields(api_token)",
            "get_harvest_readiness(field_id, api_token)",
            "get_crop_health_summary(field_id, api_token)"
        ],
        "example_usage": "ndvi = get_field_ndvi('12345', '2026-01-01', '2026-03-01', api_token='YOUR_TOKEN')",
        "setup": "Register at eos.com/products/crop-monitoring to get API token",
        "category": "Alternative Data — Satellite & Geospatial",
        "status": "operational"
    }
    print(json.dumps(result, indent=2))
