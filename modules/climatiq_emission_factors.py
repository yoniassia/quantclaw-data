"""
Climatiq Emission Factors API
Carbon emission calculations for ESG reporting and climate risk assessment

Free tier: 10,000 requests/month
API docs: https://www.climatiq.io/docs
"""

import requests
from typing import Dict, List, Optional


BASE_URL = "https://beta3.api.climatiq.io"


def calculate_emissions(
    activity_id: str,
    parameters: Dict,
    api_key: Optional[str] = None
) -> Dict:
    """
    Calculate carbon emissions based on activity data.
    
    Args:
        activity_id: Activity type (e.g., 'electricity-supply_grid', 'transport-vehicle_type_car')
        parameters: Activity parameters (e.g., {'energy': 100, 'energy_unit': 'kWh'})
        api_key: Climatiq API key (optional for testing, required for production)
    
    Returns:
        Dict with emission results including kg CO2e
    
    Example:
        >>> result = calculate_emissions(
        ...     'electricity-supply_grid',
        ...     {'energy': 100, 'energy_unit': 'kWh', 'region': 'US'}
        ... )
        >>> print(f"Emissions: {result['co2e']} kg CO2e")
    """
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    payload = {
        'emission_factor': {'activity_id': activity_id},
        'parameters': parameters
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/estimate",
            json=payload,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {'error': str(e), 'activity_id': activity_id}


def search_emission_factors(
    query: str,
    region: Optional[str] = None,
    api_key: Optional[str] = None
) -> List[Dict]:
    """
    Search available emission factors.
    
    Args:
        query: Search term (e.g., 'electricity', 'shipping')
        region: ISO 2-letter country code (e.g., 'US', 'GB')
        api_key: Climatiq API key
    
    Returns:
        List of emission factor dictionaries
    
    Example:
        >>> factors = search_emission_factors('electricity', region='US')
        >>> for f in factors[:3]:
        ...     print(f"{f['activity_id']}: {f['name']}")
    """
    headers = {}
    if api_key:
        headers['Authorization'] = f'Bearer {api_key}'
    
    params = {'query': query}
    if region:
        params['region'] = region
    
    try:
        response = requests.get(
            f"{BASE_URL}/search",
            params=params,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return data.get('results', [])
    except requests.exceptions.RequestException as e:
        return [{'error': str(e)}]


def get_transport_emissions(
    distance_km: float,
    transport_mode: str = 'car',
    fuel_type: str = 'petrol',
    api_key: Optional[str] = None
) -> Dict:
    """
    Calculate transport emissions.
    
    Args:
        distance_km: Distance traveled in kilometers
        transport_mode: 'car', 'truck', 'plane', 'train', 'ship'
        fuel_type: 'petrol', 'diesel', 'electric', etc.
        api_key: Climatiq API key
    
    Returns:
        Emission estimate dictionary
    
    Example:
        >>> result = get_transport_emissions(100, 'car', 'petrol')
        >>> print(f"Trip emissions: {result.get('co2e', 'N/A')} kg CO2e")
    """
    activity_id = f"transport-vehicle_type_{transport_mode}-fuel_{fuel_type}"
    
    parameters = {
        'distance': distance_km,
        'distance_unit': 'km'
    }
    
    return calculate_emissions(activity_id, parameters, api_key)


def get_electricity_emissions(
    kwh: float,
    region: str = 'US',
    api_key: Optional[str] = None
) -> Dict:
    """
    Calculate electricity consumption emissions.
    
    Args:
        kwh: Energy consumption in kilowatt-hours
        region: ISO 2-letter country code
        api_key: Climatiq API key
    
    Returns:
        Emission estimate dictionary
    
    Example:
        >>> result = get_electricity_emissions(1000, 'US')
        >>> print(f"Grid emissions: {result.get('co2e', 'N/A')} kg CO2e")
    """
    parameters = {
        'energy': kwh,
        'energy_unit': 'kWh',
        'region': region
    }
    
    return calculate_emissions('electricity-supply_grid', parameters, api_key)


def get_shipping_emissions(
    weight_kg: float,
    distance_km: float,
    method: str = 'sea',
    api_key: Optional[str] = None
) -> Dict:
    """
    Calculate freight shipping emissions.
    
    Args:
        weight_kg: Cargo weight in kilograms
        distance_km: Distance in kilometers
        method: 'sea', 'air', 'road', 'rail'
        api_key: Climatiq API key
    
    Returns:
        Emission estimate dictionary
    
    Example:
        >>> result = get_shipping_emissions(1000, 5000, 'sea')
        >>> print(f"Shipping emissions: {result.get('co2e', 'N/A')} kg CO2e")
    """
    activity_id = f"freight-{method}"
    
    parameters = {
        'weight': weight_kg,
        'weight_unit': 'kg',
        'distance': distance_km,
        'distance_unit': 'km'
    }
    
    return calculate_emissions(activity_id, parameters, api_key)


if __name__ == '__main__':
    import sys
    
    # Test with demo data (no API key needed for basic testing)
    print("Climatiq Emission Factors Demo\n")
    
    # Test electricity
    print("1. Electricity emissions (100 kWh, US grid):")
    result = get_electricity_emissions(100, 'US')
    if 'error' not in result:
        print(f"   CO2e: {result.get('co2e', 'N/A')} kg")
    else:
        print(f"   Note: {result['error']}")
    
    # Test transport
    print("\n2. Transport emissions (100 km by car):")
    result = get_transport_emissions(100, 'car', 'petrol')
    if 'error' not in result:
        print(f"   CO2e: {result.get('co2e', 'N/A')} kg")
    else:
        print(f"   Note: {result['error']}")
    
    # Test shipping
    print("\n3. Shipping emissions (1000 kg, 5000 km by sea):")
    result = get_shipping_emissions(1000, 5000, 'sea')
    if 'error' not in result:
        print(f"   CO2e: {result.get('co2e', 'N/A')} kg")
    else:
        print(f"   Note: {result['error']}")
    
    print("\n✅ Module loaded successfully")
    print("Note: API key recommended for production use (10k requests/month free)")
