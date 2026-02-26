"""Weather Impact on Commodities Model — Link weather patterns to commodity prices.

Roadmap #332: Models the impact of weather events on agricultural commodities,
energy prices, and other weather-sensitive assets using free Open-Meteo data.
"""

import json
import urllib.request
from datetime import datetime, timedelta
from typing import Dict, List, Optional


OPEN_METEO_BASE = "https://api.open-meteo.com/v1"

# Key agricultural regions and their coordinates
AG_REGIONS = {
    "us_corn_belt": {"lat": 41.5, "lon": -89.0, "name": "US Corn Belt (Illinois)", "commodities": ["corn", "soybeans"]},
    "us_wheat_belt": {"lat": 38.5, "lon": -98.0, "name": "US Wheat Belt (Kansas)", "commodities": ["wheat"]},
    "brazil_soy": {"lat": -12.5, "lon": -50.0, "name": "Brazil Soy (Mato Grosso)", "commodities": ["soybeans", "corn"]},
    "argentina_pampas": {"lat": -34.5, "lon": -60.0, "name": "Argentina Pampas", "commodities": ["soybeans", "wheat", "corn"]},
    "india_wheat": {"lat": 28.5, "lon": 77.0, "name": "India Wheat Belt (Punjab)", "commodities": ["wheat", "rice"]},
    "australia_wheat": {"lat": -33.0, "lon": 148.0, "name": "Australia Wheat (NSW)", "commodities": ["wheat"]},
    "ukraine_grain": {"lat": 49.0, "lon": 32.0, "name": "Ukraine Grain Belt", "commodities": ["wheat", "corn", "sunflower"]},
    "france_wheat": {"lat": 48.0, "lon": 2.5, "name": "France Beauce Region", "commodities": ["wheat"]},
    "us_gulf_energy": {"lat": 29.5, "lon": -90.0, "name": "US Gulf Coast (Energy)", "commodities": ["crude_oil", "natural_gas"]},
    "north_sea_energy": {"lat": 57.0, "lon": 2.0, "name": "North Sea (Energy)", "commodities": ["brent_crude", "natural_gas"]},
}

# Stress thresholds for crops
CROP_STRESS = {
    "corn": {"heat_max": 35, "drought_precip_min": 2, "frost_min": 0, "optimal_temp": (18, 32)},
    "soybeans": {"heat_max": 36, "drought_precip_min": 2, "frost_min": 0, "optimal_temp": (20, 30)},
    "wheat": {"heat_max": 32, "drought_precip_min": 1.5, "frost_min": -5, "optimal_temp": (12, 25)},
    "rice": {"heat_max": 38, "drought_precip_min": 5, "frost_min": 10, "optimal_temp": (22, 35)},
}


def get_region_weather(region: str, days: int = 14) -> Dict:
    """Get current and forecast weather for an agricultural/energy region.
    
    Args:
        region: Region key from AG_REGIONS (e.g. 'us_corn_belt')
        days: Forecast days (1-16)
    
    Returns:
        Dict with temperature, precipitation, wind, and stress indicators.
    """
    region_info = AG_REGIONS.get(region)
    if not region_info:
        return {"error": f"Unknown region: {region}", "available": list(AG_REGIONS.keys())}
    
    try:
        url = (f"{OPEN_METEO_BASE}/forecast?"
               f"latitude={region_info['lat']}&longitude={region_info['lon']}"
               f"&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
               f"wind_speed_10m_max,et0_fao_evapotranspiration"
               f"&timezone=auto&forecast_days={min(days, 16)}")
        
        req = urllib.request.Request(url, headers={"User-Agent": "QuantClaw/1.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        daily = data.get("daily", {})
        dates = daily.get("time", [])
        
        forecast = []
        for i, date in enumerate(dates):
            forecast.append({
                "date": date,
                "temp_max": daily["temperature_2m_max"][i],
                "temp_min": daily["temperature_2m_min"][i],
                "precip_mm": daily["precipitation_sum"][i],
                "wind_max_kmh": daily["wind_speed_10m_max"][i],
                "evapotranspiration": daily.get("et0_fao_evapotranspiration", [None])[i] if i < len(daily.get("et0_fao_evapotranspiration", [])) else None,
            })
        
        return {
            "region": region,
            "name": region_info["name"],
            "commodities": region_info["commodities"],
            "forecast": forecast,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "Open-Meteo"
        }
    except Exception as e:
        return {"region": region, "error": str(e)}


def crop_stress_assessment(region: str, commodity: str = None) -> Dict:
    """Assess weather stress on crops in a given region.
    
    Args:
        region: Region key
        commodity: Specific commodity to assess (or auto-detect from region)
    
    Returns:
        Dict with stress score (0-100), alerts, and trading signals.
    """
    weather = get_region_weather(region, days=14)
    if "error" in weather:
        return weather
    
    region_info = AG_REGIONS.get(region, {})
    commodities = [commodity] if commodity else region_info.get("commodities", [])
    
    assessments = {}
    for crop in commodities:
        thresholds = CROP_STRESS.get(crop)
        if not thresholds:
            assessments[crop] = {"note": "No stress model available for this commodity"}
            continue
        
        alerts = []
        stress_score = 0
        
        for day in weather.get("forecast", []):
            t_max = day.get("temp_max", 20)
            t_min = day.get("temp_min", 10)
            precip = day.get("precip_mm", 0)
            
            # Heat stress
            if t_max > thresholds["heat_max"]:
                stress_score += 5
                alerts.append(f"Heat stress on {day['date']}: {t_max}°C > {thresholds['heat_max']}°C")
            
            # Frost risk
            if t_min < thresholds["frost_min"]:
                stress_score += 8
                alerts.append(f"Frost risk on {day['date']}: {t_min}°C < {thresholds['frost_min']}°C")
            
            # Drought (cumulative check)
            if precip < thresholds["drought_precip_min"] * 0.3:
                stress_score += 2
        
        # Cap at 100
        stress_score = min(stress_score, 100)
        
        if stress_score >= 60:
            signal = f"BULLISH {crop} — severe weather stress, expect supply concerns"
        elif stress_score >= 30:
            signal = f"MILDLY BULLISH {crop} — moderate weather risk"
        else:
            signal = f"NEUTRAL {crop} — favorable growing conditions"
        
        assessments[crop] = {
            "stress_score": stress_score,
            "severity": "severe" if stress_score >= 60 else "moderate" if stress_score >= 30 else "low",
            "alerts": alerts[:10],
            "trading_signal": signal
        }
    
    return {
        "region": region,
        "name": region_info.get("name", region),
        "assessments": assessments,
        "timestamp": datetime.utcnow().isoformat()
    }


def global_weather_commodity_scan() -> Dict:
    """Scan all major agricultural regions for weather stress — the daily briefing.
    
    Returns:
        Dict with stress levels across all regions and top trading signals.
    """
    results = {}
    top_alerts = []
    
    for region in AG_REGIONS:
        assessment = crop_stress_assessment(region)
        results[region] = assessment
        
        for crop, data in assessment.get("assessments", {}).items():
            if isinstance(data, dict) and data.get("stress_score", 0) >= 30:
                top_alerts.append({
                    "region": region,
                    "commodity": crop,
                    "stress_score": data["stress_score"],
                    "signal": data.get("trading_signal", "")
                })
    
    top_alerts.sort(key=lambda x: x["stress_score"], reverse=True)
    
    return {
        "scan_time": datetime.utcnow().isoformat(),
        "regions_scanned": len(AG_REGIONS),
        "top_alerts": top_alerts[:10],
        "all_regions": results,
        "source": "Open-Meteo + QuantClaw Crop Models"
    }
