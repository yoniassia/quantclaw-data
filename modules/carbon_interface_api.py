"""
Carbon Interface API — Carbon emissions estimates via dedicated REST API

Provides carbon emissions estimates for electricity usage, flights, shipping,
vehicles, and fuel combustion using standardized emission factors from Carbon Interface.
Unlike carbon_footprint module which uses sector averages, this uses real-time API data.

Source: https://www.carboninterface.com/developers
Category: ESG & Climate
Free tier: 1000 requests/month with API key (no credit card required)
API Key: Set CARBON_INTERFACE_API_KEY environment variable
"""

import os
import json
import urllib.request
import urllib.error
from typing import Any
from datetime import datetime


API_BASE_URL = "https://www.carboninterface.com/api/v1"


def _get_api_key() -> str | None:
    """Get Carbon Interface API key from environment."""
    return os.environ.get("CARBON_INTERFACE_API_KEY")


def _make_request(endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
    """Make authenticated POST request to Carbon Interface API.
    
    Args:
        endpoint: API endpoint path (e.g., "/estimates")
        data: Request payload dictionary
        
    Returns:
        API response as dictionary
        
    Raises:
        ValueError: If API key is not set
        urllib.error.HTTPError: If API request fails
    """
    api_key = _get_api_key()
    if not api_key:
        raise ValueError(
            "CARBON_INTERFACE_API_KEY not set. Get free API key at "
            "https://www.carboninterface.com/users/sign_up"
        )
    
    url = f"{API_BASE_URL}{endpoint}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    
    payload = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        raise urllib.error.HTTPError(
            e.url, e.code, f"API Error: {error_body}", e.hdrs, e.fp
        )


def estimate_electricity(
    electricity_value: float,
    electricity_unit: str = "mwh",
    country: str = "us",
    state: str | None = None,
) -> dict[str, Any]:
    """Estimate carbon emissions from electricity consumption.
    
    Args:
        electricity_value: Amount of electricity consumed
        electricity_unit: Unit of measurement ("mwh" or "kwh")
        country: ISO 2-letter country code (e.g., "us", "gb", "de")
        state: US state code (optional, e.g., "ca", "ny")
        
    Returns:
        Dict with carbon estimate in kg CO2e and metadata
    """
    payload = {
        "type": "electricity",
        "electricity_unit": electricity_unit,
        "electricity_value": electricity_value,
        "country": country,
    }
    if state:
        payload["state"] = state
        
    try:
        result = _make_request("/estimates", payload)
        return {
            "estimate_kg_co2e": result["data"]["attributes"]["carbon_kg"],
            "electricity_value": electricity_value,
            "electricity_unit": electricity_unit,
            "country": country,
            "state": state,
            "estimate_id": result["data"]["id"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except ValueError as e:
        return {"error": str(e), "requires_api_key": True}
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}


def estimate_flight(
    passengers: int,
    departure_airport: str,
    destination_airport: str,
    cabin_class: str = "economy",
) -> dict[str, Any]:
    """Estimate carbon emissions from flight travel.
    
    Args:
        passengers: Number of passengers
        departure_airport: IATA airport code (e.g., "SFO", "JFK")
        destination_airport: IATA airport code (e.g., "LAX", "LHR")
        cabin_class: "economy", "premium", "business", or "first"
        
    Returns:
        Dict with carbon estimate in kg CO2e and flight details
    """
    payload = {
        "type": "flight",
        "passengers": passengers,
        "legs": [
            {
                "departure_airport": departure_airport,
                "destination_airport": destination_airport,
                "cabin_class": cabin_class,
            }
        ],
    }
    
    try:
        result = _make_request("/estimates", payload)
        attrs = result["data"]["attributes"]
        return {
            "estimate_kg_co2e": attrs["carbon_kg"],
            "passengers": passengers,
            "departure_airport": departure_airport,
            "destination_airport": destination_airport,
            "cabin_class": cabin_class,
            "distance_value": attrs.get("distance_value"),
            "distance_unit": attrs.get("distance_unit"),
            "estimate_id": result["data"]["id"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except ValueError as e:
        return {"error": str(e), "requires_api_key": True}
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}


def estimate_vehicle(
    distance_value: float,
    distance_unit: str = "mi",
    vehicle_make: str = "Toyota",
    vehicle_model: str = "Camry",
    vehicle_year: int = 2020,
) -> dict[str, Any]:
    """Estimate carbon emissions from vehicle travel.
    
    Args:
        distance_value: Distance traveled
        distance_unit: "mi" (miles) or "km" (kilometers)
        vehicle_make: Vehicle manufacturer
        vehicle_model: Vehicle model name
        vehicle_year: Vehicle model year
        
    Returns:
        Dict with carbon estimate in kg CO2e and vehicle details
    """
    payload = {
        "type": "vehicle",
        "distance_unit": distance_unit,
        "distance_value": distance_value,
        "vehicle_model_id": f"{vehicle_make}-{vehicle_model}-{vehicle_year}",
    }
    
    try:
        result = _make_request("/estimates", payload)
        return {
            "estimate_kg_co2e": result["data"]["attributes"]["carbon_kg"],
            "distance_value": distance_value,
            "distance_unit": distance_unit,
            "vehicle_make": vehicle_make,
            "vehicle_model": vehicle_model,
            "vehicle_year": vehicle_year,
            "estimate_id": result["data"]["id"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except ValueError as e:
        return {"error": str(e), "requires_api_key": True}
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}


def estimate_shipping(
    weight_value: float,
    weight_unit: str = "lb",
    distance_value: float = 100,
    distance_unit: str = "mi",
    transport_method: str = "truck",
) -> dict[str, Any]:
    """Estimate carbon emissions from shipping/freight.
    
    Args:
        weight_value: Package weight
        weight_unit: "lb" (pounds), "kg" (kilograms), or "g" (grams)
        distance_value: Shipping distance
        distance_unit: "mi" (miles) or "km" (kilometers)
        transport_method: "ship", "train", "truck", or "plane"
        
    Returns:
        Dict with carbon estimate in kg CO2e and shipping details
    """
    payload = {
        "type": "shipping",
        "weight_value": weight_value,
        "weight_unit": weight_unit,
        "distance_value": distance_value,
        "distance_unit": distance_unit,
        "transport_method": transport_method,
    }
    
    try:
        result = _make_request("/estimates", payload)
        return {
            "estimate_kg_co2e": result["data"]["attributes"]["carbon_kg"],
            "weight_value": weight_value,
            "weight_unit": weight_unit,
            "distance_value": distance_value,
            "distance_unit": distance_unit,
            "transport_method": transport_method,
            "estimate_id": result["data"]["id"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except ValueError as e:
        return {"error": str(e), "requires_api_key": True}
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}


def estimate_fuel_combustion(
    fuel_source_type: str,
    fuel_source_value: float,
    fuel_source_unit: str = "gallon",
) -> dict[str, Any]:
    """Estimate carbon emissions from burning fuel.
    
    Args:
        fuel_source_type: Type of fuel (e.g., "diesel", "petrol", "ng", "coal")
        fuel_source_value: Amount of fuel consumed
        fuel_source_unit: Unit of measurement (e.g., "gallon", "liter", "btu")
        
    Returns:
        Dict with carbon estimate in kg CO2e and fuel details
    """
    payload = {
        "type": "fuel_combustion",
        "fuel_source_type": fuel_source_type,
        "fuel_source_unit": fuel_source_unit,
        "fuel_source_value": fuel_source_value,
    }
    
    try:
        result = _make_request("/estimates", payload)
        return {
            "estimate_kg_co2e": result["data"]["attributes"]["carbon_kg"],
            "fuel_source_type": fuel_source_type,
            "fuel_source_value": fuel_source_value,
            "fuel_source_unit": fuel_source_unit,
            "estimate_id": result["data"]["id"],
            "timestamp": datetime.utcnow().isoformat(),
        }
    except ValueError as e:
        return {"error": str(e), "requires_api_key": True}
    except Exception as e:
        return {"error": f"API request failed: {str(e)}"}


def get_api_status() -> dict[str, Any]:
    """Check if API key is configured and get module info.
    
    Returns:
        Dict with API configuration status and module metadata
    """
    api_key = _get_api_key()
    return {
        "module": "carbon_interface_api",
        "api_key_configured": api_key is not None,
        "api_key_length": len(api_key) if api_key else 0,
        "base_url": API_BASE_URL,
        "free_tier": "1000 requests/month",
        "signup_url": "https://www.carboninterface.com/users/sign_up",
        "functions": [
            "estimate_electricity",
            "estimate_flight",
            "estimate_vehicle",
            "estimate_shipping",
            "estimate_fuel_combustion",
            "get_api_status",
        ],
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    # Demo output showing module capabilities
    status = get_api_status()
    print(json.dumps(status, indent=2))
