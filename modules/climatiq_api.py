#!/usr/bin/env python3
"""
Climatiq API — Carbon Emissions Calculation Module

Provides carbon emission calculations based on activity data using scientifically vetted emission factors.
Supports corporate carbon footprints, climate risk assessments, and ESG analytics for quant trading strategies.

Key capabilities:
- Emission calculations for electricity, travel, vehicles
- Emission factor database search
- Multi-category activity tracking
- Real-time carbon footprint analysis

Source: https://www.climatiq.io/docs
Category: ESG & Climate
Free tier: True (10,000 requests/month, no credit card required)
Update frequency: Real-time calculations, datasets updated quarterly
Author: QuantClaw Data NightBuilder
"""

import os
import json
import requests
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from quantclaw-data root
load_dotenv(Path(__file__).parent.parent / ".env")

# Climatiq API Configuration
CLIMATIQ_BASE_URL = "https://api.climatiq.io"
CLIMATIQ_API_KEY = os.environ.get("CLIMATIQ_API_KEY", "")

# Common headers for API requests
def _get_headers() -> Dict[str, str]:
    """Get headers for Climatiq API requests"""
    if not CLIMATIQ_API_KEY:
        raise ValueError("CLIMATIQ_API_KEY not found in environment variables")
    return {
        "Authorization": f"Bearer {CLIMATIQ_API_KEY}",
        "Content-Type": "application/json"
    }


def estimate_emissions(activity_id: str, parameters: dict) -> dict:
    """
    Calculate carbon emissions for a specific activity.
    
    Args:
        activity_id: Activity identifier (e.g., "electricity-supply_grid-source_supplier_mix")
        parameters: Activity parameters (e.g., {"energy": 100, "energy_unit": "kWh"})
    
    Returns:
        dict: Emission calculation result with CO2e values
    
    Example:
        >>> estimate_emissions("electricity-supply_grid-source_supplier_mix", 
        ...                    {"energy": 100, "energy_unit": "kWh", "region": "US"})
    """
    try:
        url = f"{CLIMATIQ_BASE_URL}/estimate"
        payload = {
            "emission_factor": {
                "activity_id": activity_id
            },
            "parameters": parameters
        }
        
        response = requests.post(url, headers=_get_headers(), json=payload, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        return {
            "success": True,
            "co2e": data.get("co2e"),
            "co2e_unit": data.get("co2e_unit"),
            "co2e_calculation_method": data.get("co2e_calculation_method"),
            "emission_factor": data.get("emission_factor", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


def search_emission_factors(query: str, category: str = None) -> list:
    """
    Search the emission factor database.
    
    Args:
        query: Search term
        category: Optional category filter
    
    Returns:
        list: List of matching emission factors
    
    Example:
        >>> search_emission_factors("electricity", category="Energy")
    """
    try:
        url = f"{CLIMATIQ_BASE_URL}/search"
        params = {"query": query}
        if category:
            params["category"] = category
        
        response = requests.get(url, headers=_get_headers(), params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        results = data.get("results", [])
        
        return [{
            "activity_id": item.get("activity_id"),
            "name": item.get("name"),
            "category": item.get("category"),
            "source": item.get("source"),
            "region": item.get("region"),
            "year": item.get("year"),
            "unit_type": item.get("unit_type")
        } for item in results]
        
    except requests.exceptions.RequestException as e:
        return [{"error": str(e)}]
    except Exception as e:
        return [{"error": f"Unexpected error: {str(e)}"}]


def get_electricity_emissions(energy_kwh: float, country: str = "US") -> dict:
    """
    Calculate carbon emissions from electricity consumption.
    
    Args:
        energy_kwh: Energy consumption in kWh
        country: Country/region code (default: "US")
    
    Returns:
        dict: Emission calculation with CO2e values
    
    Example:
        >>> get_electricity_emissions(100, "US")
    """
    try:
        # Use grid electricity activity ID
        activity_id = f"electricity-supply_grid-source_supplier_mix"
        parameters = {
            "energy": energy_kwh,
            "energy_unit": "kWh"
        }
        
        # Add region if not US (default)
        if country and country != "US":
            parameters["region"] = country
        
        result = estimate_emissions(activity_id, parameters)
        result["activity_type"] = "electricity"
        result["energy_kwh"] = energy_kwh
        result["country"] = country
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Electricity emissions calculation failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


def get_flight_emissions(from_airport: str, to_airport: str, cabin_class: str = "economy") -> dict:
    """
    Calculate carbon emissions from air travel.
    
    Args:
        from_airport: Departure airport code (IATA)
        to_airport: Arrival airport code (IATA)
        cabin_class: Cabin class (economy/premium_economy/business/first)
    
    Returns:
        dict: Emission calculation with CO2e values
    
    Example:
        >>> get_flight_emissions("JFK", "LAX", "economy")
    """
    try:
        # Use passenger flight activity ID
        activity_id = f"passenger_flight-route_type_domestic-aircraft_type_na-distance_na-class_{cabin_class}"
        
        # Note: Climatiq requires distance or route lookup
        # For production, you'd need to calculate distance or use their route API
        # This is a simplified version using activity parameters
        parameters = {
            "passengers": 1,
            "distance": 1.0,  # Placeholder - needs actual distance calculation
            "distance_unit": "km"
        }
        
        result = estimate_emissions(activity_id, parameters)
        result["activity_type"] = "flight"
        result["route"] = f"{from_airport}-{to_airport}"
        result["cabin_class"] = cabin_class
        result["note"] = "Distance estimation required for accurate calculation"
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Flight emissions calculation failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


def get_vehicle_emissions(distance_km: float, vehicle_type: str = "car") -> dict:
    """
    Calculate carbon emissions from vehicle travel.
    
    Args:
        distance_km: Distance traveled in kilometers
        vehicle_type: Vehicle type (car/van/motorbike/bus)
    
    Returns:
        dict: Emission calculation with CO2e values
    
    Example:
        >>> get_vehicle_emissions(100, "car")
    """
    try:
        # Map vehicle types to activity IDs
        vehicle_map = {
            "car": "passenger_vehicle-vehicle_type_car-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na",
            "van": "passenger_vehicle-vehicle_type_van-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na",
            "motorbike": "passenger_vehicle-vehicle_type_motorbike-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na",
            "bus": "passenger_vehicle-vehicle_type_bus-fuel_source_na-engine_size_na-vehicle_age_na-vehicle_weight_na"
        }
        
        activity_id = vehicle_map.get(vehicle_type.lower(), vehicle_map["car"])
        parameters = {
            "distance": distance_km,
            "distance_unit": "km"
        }
        
        result = estimate_emissions(activity_id, parameters)
        result["activity_type"] = "vehicle"
        result["distance_km"] = distance_km
        result["vehicle_type"] = vehicle_type
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Vehicle emissions calculation failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }


def list_categories() -> list:
    """
    List available emission factor categories.
    
    Returns:
        list: Available categories in the database
    
    Example:
        >>> list_categories()
    """
    try:
        # Common Climatiq categories based on documentation
        categories = [
            "Energy",
            "Transport",
            "Waste",
            "Materials",
            "Food",
            "Water",
            "Buildings",
            "Cloud Computing",
            "Fuels",
            "Freight"
        ]
        
        return [{
            "category": cat,
            "description": f"{cat} related emission factors",
            "available": True
        } for cat in categories]
        
    except Exception as e:
        return [{"error": f"Failed to list categories: {str(e)}"}]


# ========== TESTING & VALIDATION ==========

def validate_api_key() -> bool:
    """Validate that API key is configured and working"""
    try:
        if not CLIMATIQ_API_KEY:
            return False
        
        # Try a simple search request
        url = f"{CLIMATIQ_BASE_URL}/search"
        response = requests.get(url, headers=_get_headers(), params={"query": "electricity"}, timeout=10)
        return response.status_code == 200
        
    except Exception:
        return False


if __name__ == "__main__":
    # Basic module info and validation
    info = {
        "module": "climatiq_api",
        "status": "active",
        "source": "https://www.climatiq.io/docs",
        "category": "ESG & Climate",
        "api_key_configured": bool(CLIMATIQ_API_KEY),
        "functions": [
            "estimate_emissions",
            "search_emission_factors", 
            "get_electricity_emissions",
            "get_flight_emissions",
            "get_vehicle_emissions",
            "list_categories"
        ],
        "timestamp": datetime.utcnow().isoformat()
    }
    print(json.dumps(info, indent=2))
