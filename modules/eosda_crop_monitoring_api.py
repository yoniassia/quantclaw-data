#!/usr/bin/env python3
"""
EOSDA Crop Monitoring API — Satellite-Derived Agricultural Data

EOS Data Analytics provides satellite-derived crop monitoring data for agricultural
commodity trading and risk assessment. Key metrics include:
- NDVI (Normalized Difference Vegetation Index) for crop health
- Soil moisture levels
- Weather conditions at field level
- Crop calendars for planting/harvest timing
- Field-level statistics and analytics

Source: https://eos.com/products/crop-monitoring/api
Category: Alternative Data — Satellite & Geospatial
Free tier: True (requires EOSDA_API_KEY env var)
Update frequency: Daily
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# EOSDA API Configuration
EOSDA_BASE_URL = "https://api.eos.com/crop-monitoring/v1"
EOSDA_API_KEY = os.environ.get("EOSDA_API_KEY", "")


def _make_request(endpoint: str, params: Optional[Dict] = None, api_key: Optional[str] = None) -> Dict:
    """
    Internal helper for EOSDA API requests
    
    Args:
        endpoint: API endpoint path (e.g., '/fields/123/ndvi')
        params: Query parameters
        api_key: Optional API key override
    
    Returns:
        Dict with response data or error
    """
    try:
        headers = {}
        key = api_key or EOSDA_API_KEY
        
        if not key:
            return {
                "success": False,
                "error": "EOSDA_API_KEY not set. Get your free API key from https://eos.com/products/crop-monitoring/api",
                "data": None
            }
        
        headers["Authorization"] = f"Bearer {key}"
        
        url = f"{EOSDA_BASE_URL}{endpoint}"
        response = requests.get(url, headers=headers, params=params or {}, timeout=15)
        
        # Check for auth errors
        if response.status_code == 401:
            return {
                "success": False,
                "error": "Invalid API key. Check EOSDA_API_KEY in .env",
                "data": None
            }
        
        if response.status_code == 403:
            return {
                "success": False,
                "error": "API access forbidden. Check your subscription tier.",
                "data": None
            }
        
        if response.status_code == 429:
            return {
                "success": False,
                "error": "Rate limit exceeded. Upgrade your EOSDA plan or wait.",
                "data": None
            }
        
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "error": None,
            "data": data
        }
    
    except requests.exceptions.Timeout:
        return {
            "success": False,
            "error": "Request timeout after 15 seconds",
            "data": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "data": None
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Invalid JSON response from API",
            "data": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "data": None
        }


def get_ndvi(
    lat: float,
    lon: float,
    date_from: str,
    date_to: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get NDVI (Normalized Difference Vegetation Index) time series for location
    
    NDVI measures vegetation health and density (range -1 to 1, higher = healthier crops).
    Critical for yield prediction and crop stress detection.
    
    Args:
        lat: Latitude (decimal degrees)
        lon: Longitude (decimal degrees)
        date_from: Start date (YYYY-MM-DD format)
        date_to: End date (YYYY-MM-DD format)
        api_key: Optional EOSDA API key override
    
    Returns:
        Dict with NDVI time series, statistics, and trend analysis
    
    Example:
        >>> result = get_ndvi(40.7128, -74.0060, "2026-01-01", "2026-03-01")
        >>> if result['success']:
        ...     print(f"Average NDVI: {result['statistics']['mean']:.3f}")
    """
    params = {
        "lat": lat,
        "lon": lon,
        "date_from": date_from,
        "date_to": date_to
    }
    
    # For demonstration, we'll construct a realistic endpoint path
    # In production, you might need to first create a field or use a field_id
    endpoint = f"/ndvi"
    
    response = _make_request(endpoint, params=params, api_key=api_key)
    
    if not response["success"]:
        return response
    
    data = response["data"]
    
    # Calculate statistics if we have time series data
    statistics = {}
    trend_analysis = []
    
    if isinstance(data, dict) and "values" in data:
        values = [float(v["ndvi"]) for v in data["values"] if "ndvi" in v]
        
        if values:
            statistics = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1],
                "count": len(values)
            }
            
            # Trend analysis
            if len(values) >= 2:
                recent_change = values[-1] - values[0]
                statistics["period_change"] = recent_change
                
                if recent_change < -0.1:
                    trend_analysis.append("Significant vegetation decline detected")
                elif recent_change > 0.1:
                    trend_analysis.append("Strong vegetation growth detected")
                else:
                    trend_analysis.append("Stable vegetation conditions")
            
            # Health assessment
            if statistics["latest"] < 0.2:
                trend_analysis.append("WARNING: Very low NDVI - potential crop stress or bare soil")
            elif statistics["latest"] < 0.4:
                trend_analysis.append("Low vegetation density - early growth or stressed crops")
            elif statistics["latest"] < 0.6:
                trend_analysis.append("Moderate vegetation - typical for growing crops")
            elif statistics["latest"] < 0.8:
                trend_analysis.append("Healthy vegetation - good crop conditions")
            else:
                trend_analysis.append("Very high NDVI - peak vegetation/biomass")
    
    return {
        "success": True,
        "location": {"lat": lat, "lon": lon},
        "date_range": {"from": date_from, "to": date_to},
        "ndvi_data": data,
        "statistics": statistics,
        "trend_analysis": trend_analysis,
        "timestamp": datetime.now().isoformat()
    }


def get_soil_moisture(
    lat: float,
    lon: float,
    date_from: str,
    date_to: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get soil moisture data for location over time period
    
    Soil moisture is critical for crop yield prediction, drought monitoring,
    and irrigation planning. Measured as volumetric water content (%).
    
    Args:
        lat: Latitude (decimal degrees)
        lon: Longitude (decimal degrees)
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        api_key: Optional EOSDA API key override
    
    Returns:
        Dict with soil moisture time series and drought risk assessment
    
    Example:
        >>> result = get_soil_moisture(40.7128, -74.0060, "2026-01-01", "2026-03-01")
        >>> if result['success']:
        ...     print(f"Current moisture: {result['statistics']['latest']:.1f}%")
    """
    params = {
        "lat": lat,
        "lon": lon,
        "date_from": date_from,
        "date_to": date_to
    }
    
    endpoint = "/soil-moisture"
    response = _make_request(endpoint, params=params, api_key=api_key)
    
    if not response["success"]:
        return response
    
    data = response["data"]
    
    # Calculate statistics
    statistics = {}
    risk_assessment = []
    
    if isinstance(data, dict) and "values" in data:
        values = [float(v["moisture"]) for v in data["values"] if "moisture" in v]
        
        if values:
            statistics = {
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "latest": values[-1],
                "count": len(values)
            }
            
            # Drought risk assessment
            latest_moisture = statistics["latest"]
            if latest_moisture < 10:
                risk_assessment.append("SEVERE DROUGHT RISK: Soil moisture critically low")
            elif latest_moisture < 20:
                risk_assessment.append("HIGH DROUGHT RISK: Crops likely stressed")
            elif latest_moisture < 30:
                risk_assessment.append("MODERATE DROUGHT RISK: Monitor irrigation needs")
            elif latest_moisture < 50:
                risk_assessment.append("Adequate soil moisture for most crops")
            else:
                risk_assessment.append("High soil moisture - potential waterlogging risk")
            
            # Trend
            if len(values) >= 2:
                change = values[-1] - values[0]
                statistics["period_change"] = change
                
                if change < -10:
                    risk_assessment.append("Rapid soil moisture depletion detected")
                elif change > 10:
                    risk_assessment.append("Soil moisture increasing - recent precipitation")
    
    return {
        "success": True,
        "location": {"lat": lat, "lon": lon},
        "date_range": {"from": date_from, "to": date_to},
        "soil_moisture_data": data,
        "statistics": statistics,
        "risk_assessment": risk_assessment,
        "timestamp": datetime.now().isoformat()
    }


def get_weather(
    lat: float,
    lon: float,
    date_from: str,
    date_to: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get weather conditions for agricultural area
    
    Includes temperature, precipitation, solar radiation, and other
    meteorological data relevant to crop growth and commodity pricing.
    
    Args:
        lat: Latitude (decimal degrees)
        lon: Longitude (decimal degrees)
        date_from: Start date (YYYY-MM-DD)
        date_to: End date (YYYY-MM-DD)
        api_key: Optional EOSDA API key override
    
    Returns:
        Dict with weather time series and agricultural impacts
    
    Example:
        >>> result = get_weather(40.7128, -74.0060, "2026-01-01", "2026-03-01")
        >>> if result['success']:
        ...     print(f"Total precipitation: {result['statistics']['total_precip']:.1f}mm")
    """
    params = {
        "lat": lat,
        "lon": lon,
        "date_from": date_from,
        "date_to": date_to
    }
    
    endpoint = "/weather"
    response = _make_request(endpoint, params=params, api_key=api_key)
    
    if not response["success"]:
        return response
    
    data = response["data"]
    
    # Calculate weather statistics
    statistics = {}
    impact_analysis = []
    
    if isinstance(data, dict) and "values" in data:
        weather_values = data["values"]
        
        # Extract temperature and precipitation
        temps = [float(v.get("temp", 0)) for v in weather_values if "temp" in v]
        precip = [float(v.get("precipitation", 0)) for v in weather_values if "precipitation" in v]
        
        if temps:
            statistics["avg_temp"] = sum(temps) / len(temps)
            statistics["max_temp"] = max(temps)
            statistics["min_temp"] = min(temps)
            
            # Temperature stress analysis
            if statistics["max_temp"] > 35:
                impact_analysis.append("HEAT STRESS: Extreme temperatures detected - crop damage risk")
            elif statistics["max_temp"] > 30:
                impact_analysis.append("High temperatures - monitor for heat stress")
            
            if statistics["min_temp"] < 0:
                impact_analysis.append("FROST RISK: Below-freezing temperatures detected")
        
        if precip:
            statistics["total_precip"] = sum(precip)
            statistics["avg_daily_precip"] = sum(precip) / len(precip)
            statistics["max_daily_precip"] = max(precip)
            
            # Precipitation analysis
            if statistics["total_precip"] < 10:
                impact_analysis.append("Very low precipitation - drought conditions")
            elif statistics["total_precip"] > 200:
                impact_analysis.append("Heavy precipitation - potential flooding/waterlogging")
            
            # Count dry days
            dry_days = sum(1 for p in precip if p < 1)
            statistics["dry_days"] = dry_days
            if dry_days > len(precip) * 0.8:
                impact_analysis.append(f"Extended dry period: {dry_days} days with <1mm rain")
    
    return {
        "success": True,
        "location": {"lat": lat, "lon": lon},
        "date_range": {"from": date_from, "to": date_to},
        "weather_data": data,
        "statistics": statistics,
        "impact_analysis": impact_analysis if impact_analysis else ["Normal weather conditions"],
        "timestamp": datetime.now().isoformat()
    }


def get_crop_calendar(
    country: str,
    crop: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get planting and harvest schedules for crop in specific country
    
    Critical for futures traders to anticipate supply timing and
    seasonal price patterns.
    
    Args:
        country: ISO country code (e.g., 'US', 'BR', 'AR', 'UA')
        crop: Crop name (e.g., 'corn', 'wheat', 'soybeans', 'rice')
        api_key: Optional EOSDA API key override
    
    Returns:
        Dict with planting/harvest windows and seasonal patterns
    
    Example:
        >>> result = get_crop_calendar("US", "corn")
        >>> if result['success']:
        ...     print(f"Planting: {result['calendar']['planting_period']}")
        ...     print(f"Harvest: {result['calendar']['harvest_period']}")
    """
    params = {
        "country": country.upper(),
        "crop": crop.lower()
    }
    
    endpoint = "/crop-calendar"
    response = _make_request(endpoint, params=params, api_key=api_key)
    
    if not response["success"]:
        return response
    
    data = response["data"]
    
    # Extract calendar information
    calendar_info = {}
    trading_insights = []
    
    if isinstance(data, dict):
        calendar_info = {
            "country": country.upper(),
            "crop": crop.lower(),
            "planting_period": data.get("planting_start", "N/A") + " to " + data.get("planting_end", "N/A"),
            "harvest_period": data.get("harvest_start", "N/A") + " to " + data.get("harvest_end", "N/A"),
            "growing_season_days": data.get("growing_season_days", 0)
        }
        
        # Generate trading insights
        current_month = datetime.now().month
        
        planting_start_month = data.get("planting_start_month", 0)
        harvest_start_month = data.get("harvest_start_month", 0)
        
        if planting_start_month and abs(current_month - planting_start_month) <= 1:
            trading_insights.append("APPROACHING PLANTING SEASON - Monitor weather and acreage reports")
        
        if harvest_start_month and abs(current_month - harvest_start_month) <= 1:
            trading_insights.append("APPROACHING HARVEST - Expect supply pressure on futures")
        
        # Seasonal patterns
        trading_insights.append(f"Growing season: {calendar_info['growing_season_days']} days")
        trading_insights.append("Monitor: weather forecasts during critical growth phases")
    
    return {
        "success": True,
        "calendar": calendar_info,
        "trading_insights": trading_insights if trading_insights else ["No immediate seasonal catalysts"],
        "raw_data": data,
        "timestamp": datetime.now().isoformat()
    }


def get_field_stats(
    field_id: str,
    api_key: Optional[str] = None
) -> Dict:
    """
    Get aggregate statistics for specific field
    
    Provides comprehensive field-level analytics including area, crop type,
    current conditions, and historical performance.
    
    Args:
        field_id: EOSDA field identifier
        api_key: Optional EOSDA API key override
    
    Returns:
        Dict with field metadata, current stats, and health indicators
    
    Example:
        >>> result = get_field_stats("field_12345")
        >>> if result['success']:
        ...     print(f"Field area: {result['field_info']['area_hectares']} ha")
        ...     print(f"Crop health: {result['health_score']}/100")
    """
    endpoint = f"/fields/{field_id}/stats"
    response = _make_request(endpoint, api_key=api_key)
    
    if not response["success"]:
        return response
    
    data = response["data"]
    
    # Extract field information
    field_info = {}
    health_indicators = []
    
    if isinstance(data, dict):
        field_info = {
            "field_id": field_id,
            "area_hectares": data.get("area", 0),
            "crop_type": data.get("crop", "Unknown"),
            "location": data.get("location", {}),
            "last_updated": data.get("last_updated", "N/A")
        }
        
        # Current conditions
        current_ndvi = data.get("current_ndvi", 0)
        current_moisture = data.get("current_soil_moisture", 0)
        
        field_info["current_ndvi"] = current_ndvi
        field_info["current_soil_moisture"] = current_moisture
        
        # Calculate health score (0-100)
        health_score = 0
        
        # NDVI component (0-50 points)
        if current_ndvi >= 0.6:
            ndvi_points = 50
        elif current_ndvi >= 0.4:
            ndvi_points = 35
        elif current_ndvi >= 0.2:
            ndvi_points = 20
        else:
            ndvi_points = 10
        
        # Soil moisture component (0-50 points)
        if 30 <= current_moisture <= 50:
            moisture_points = 50
        elif 20 <= current_moisture <= 60:
            moisture_points = 35
        elif 10 <= current_moisture <= 70:
            moisture_points = 20
        else:
            moisture_points = 10
        
        health_score = ndvi_points + moisture_points
        
        # Health assessment
        if health_score >= 80:
            health_indicators.append("EXCELLENT field health - optimal growing conditions")
        elif health_score >= 60:
            health_indicators.append("GOOD field health - normal crop development")
        elif health_score >= 40:
            health_indicators.append("MODERATE field health - monitor for stress")
        else:
            health_indicators.append("POOR field health - intervention may be needed")
        
        # Specific alerts
        if current_ndvi < 0.3:
            health_indicators.append("Alert: Low vegetation index - check for crop stress")
        
        if current_moisture < 15:
            health_indicators.append("Alert: Low soil moisture - irrigation recommended")
        elif current_moisture > 60:
            health_indicators.append("Alert: High soil moisture - drainage may be needed")
    
    return {
        "success": True,
        "field_info": field_info,
        "health_score": health_score if 'health_score' in locals() else 0,
        "health_indicators": health_indicators,
        "raw_data": data,
        "timestamp": datetime.now().isoformat()
    }


def get_all_available_metrics() -> Dict:
    """
    List all available EOSDA metrics and endpoints
    
    Returns:
        Dict with available data types and their descriptions
    """
    return {
        "success": True,
        "available_metrics": {
            "ndvi": {
                "name": "NDVI (Normalized Difference Vegetation Index)",
                "description": "Vegetation health and density (-1 to 1, higher = healthier)",
                "use_case": "Crop yield prediction, stress detection",
                "function": "get_ndvi(lat, lon, date_from, date_to)"
            },
            "soil_moisture": {
                "name": "Soil Moisture",
                "description": "Volumetric water content in soil (%)",
                "use_case": "Drought monitoring, irrigation planning",
                "function": "get_soil_moisture(lat, lon, date_from, date_to)"
            },
            "weather": {
                "name": "Weather Data",
                "description": "Temperature, precipitation, solar radiation",
                "use_case": "Crop stress analysis, yield modeling",
                "function": "get_weather(lat, lon, date_from, date_to)"
            },
            "crop_calendar": {
                "name": "Crop Calendar",
                "description": "Planting and harvest schedules by country/crop",
                "use_case": "Seasonal trading patterns, supply timing",
                "function": "get_crop_calendar(country, crop)"
            },
            "field_stats": {
                "name": "Field Statistics",
                "description": "Aggregate field-level analytics and health scores",
                "use_case": "Portfolio monitoring, risk assessment",
                "function": "get_field_stats(field_id)"
            }
        },
        "data_sources": "Sentinel-2, Landsat-8, MODIS satellites",
        "update_frequency": "Daily (weather: hourly)",
        "coverage": "Global",
        "api_key_required": True,
        "get_api_key": "https://eos.com/products/crop-monitoring/api"
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("EOSDA Crop Monitoring API — Satellite Agricultural Data")
    print("=" * 70)
    
    # Show available metrics
    metrics = get_all_available_metrics()
    print("\nAvailable Metrics:")
    for metric_id, info in metrics["available_metrics"].items():
        print(f"\n  {info['name']}")
        print(f"    Description: {info['description']}")
        print(f"    Use Case: {info['use_case']}")
        print(f"    Function: {info['function']}")
    
    print(f"\n\nData Sources: {metrics['data_sources']}")
    print(f"Update Frequency: {metrics['update_frequency']}")
    print(f"Coverage: {metrics['coverage']}")
    
    if not EOSDA_API_KEY:
        print("\n⚠️  EOSDA_API_KEY not set in environment")
        print(f"   Get your free API key: {metrics['get_api_key']}")
    else:
        print("\n✓ EOSDA_API_KEY configured")
    
    print("\n" + "=" * 70)
