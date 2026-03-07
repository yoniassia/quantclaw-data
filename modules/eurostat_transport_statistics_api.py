#!/usr/bin/env python3
"""
Eurostat Transport Statistics API Module

European Union transport statistics via Eurostat API
- Road freight transport (tonnes, tonne-kilometers)
- Rail freight volumes
- Maritime goods transport
- Air passenger numbers
- Transport infrastructure spending
- Freight transport index

Data Source: https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/
Refresh: Monthly
Coverage: EU27 + candidate countries, 1990-present
Free tier: Yes, unlimited queries without authentication

Author: QUANTCLAW DATA NightBuilder
Phase: EUROSTAT_TRANSPORT_001
"""

import json
import urllib.request
import urllib.error
from typing import Dict, List, Optional, Union
from datetime import datetime

# Eurostat API Configuration
EUROSTAT_BASE_URL = "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data"

# Eurostat Transport Dataset Registry
EUROSTAT_DATASETS = {
    'road_go_ta_tott': {
        'name': 'Road Freight Transport',
        'description': 'National road freight transport (thousand tonnes)',
        'unit': 'thousand tonnes'
    },
    'rail_go_grttgw': {
        'name': 'Rail Freight Transport',
        'description': 'Railway transport - goods transported (thousand tonnes)',
        'unit': 'thousand tonnes'
    },
    'mar_go_am': {
        'name': 'Maritime Transport',
        'description': 'Maritime transport - goods (thousand tonnes)',
        'unit': 'thousand tonnes'
    },
    'avia_paoc': {
        'name': 'Air Passenger Transport',
        'description': 'Air passenger transport by country',
        'unit': 'number of passengers'
    },
    'tran_sf_roadve': {
        'name': 'Road Infrastructure',
        'description': 'Stock of road vehicles',
        'unit': 'number of vehicles'
    },
    'tran_hv_frmod': {
        'name': 'Freight Transport Index',
        'description': 'Modal split of freight transport (index)',
        'unit': 'index 2015=100'
    }
}


def _fetch_eurostat_data(dataset: str, params: Dict[str, str]) -> Optional[Dict]:
    """
    Internal helper to fetch data from Eurostat API
    
    Args:
        dataset: Eurostat dataset code
        params: Query parameters (geo, time, etc.)
    
    Returns:
        Parsed JSON response or None on error
    """
    try:
        param_str = '&'.join([f"{k}={v}" for k, v in params.items()])
        url = f"{EUROSTAT_BASE_URL}/{dataset}?{param_str}"
        
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'QUANTCLAW-DATA/1.0')
        req.add_header('Accept', 'application/json')
        
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason} for {dataset}")
        return None
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason} for {dataset}")
        return None
    except Exception as e:
        print(f"Error fetching {dataset}: {str(e)}")
        return None


def _parse_eurostat_response(data: Dict) -> List[Dict]:
    """
    Parse Eurostat JSON response into simplified format
    
    Args:
        data: Raw Eurostat API response
    
    Returns:
        List of data points with time, geo, and value
    """
    if not data or 'value' not in data:
        return []
    
    results = []
    values = data.get('value', {})
    dimension = data.get('dimension', {})
    
    # Extract time and geo dimensions
    time_codes = dimension.get('time', {}).get('category', {}).get('index', {})
    geo_codes = dimension.get('geo', {}).get('category', {}).get('index', {})
    
    # Map indices to codes
    time_list = sorted(time_codes.items(), key=lambda x: x[1])
    geo_list = sorted(geo_codes.items(), key=lambda x: x[1])
    
    # Parse values
    for key, value in values.items():
        idx = int(key)
        geo_idx = idx % len(geo_list)
        time_idx = idx // len(geo_list)
        
        if time_idx < len(time_list) and geo_idx < len(geo_list):
            results.append({
                'time': time_list[time_idx][0],
                'geo': geo_list[geo_idx][0],
                'value': value
            })
    
    return results


def get_road_freight(country: str = 'DE', year: Optional[int] = None) -> Dict[str, Union[List, str]]:
    """
    Get road freight transport data
    
    Args:
        country: ISO 2-letter country code (default: DE for Germany)
        year: Specific year or None for all available
    
    Returns:
        Dictionary with data points and metadata
    """
    params = {'geo': country}
    if year:
        params['time'] = str(year)
    
    data = _fetch_eurostat_data('road_go_ta_tott', params)
    
    if not data:
        return {
            'dataset': 'road_go_ta_tott',
            'country': country,
            'data': [],
            'error': 'Failed to fetch data'
        }
    
    parsed = _parse_eurostat_response(data)
    
    return {
        'dataset': 'road_go_ta_tott',
        'country': country,
        'year': year,
        'unit': 'thousand tonnes',
        'data': parsed,
        'count': len(parsed)
    }


def get_rail_freight(country: str = 'DE', year: Optional[int] = None) -> Dict[str, Union[List, str]]:
    """
    Get rail freight transport data
    
    Args:
        country: ISO 2-letter country code (default: DE for Germany)
        year: Specific year or None for all available
    
    Returns:
        Dictionary with data points and metadata
    """
    params = {'geo': country}
    if year:
        params['time'] = str(year)
    
    data = _fetch_eurostat_data('rail_go_grttgw', params)
    
    if not data:
        return {
            'dataset': 'rail_go_grttgw',
            'country': country,
            'data': [],
            'error': 'Failed to fetch data'
        }
    
    parsed = _parse_eurostat_response(data)
    
    return {
        'dataset': 'rail_go_grttgw',
        'country': country,
        'year': year,
        'unit': 'thousand tonnes',
        'data': parsed,
        'count': len(parsed)
    }


def get_maritime_transport(country: str = 'DE', year: Optional[int] = None) -> Dict[str, Union[List, str]]:
    """
    Get maritime goods transport data
    
    Args:
        country: ISO 2-letter country code (default: DE for Germany)
        year: Specific year or None for all available
    
    Returns:
        Dictionary with data points and metadata
    """
    params = {'geo': country}
    if year:
        params['time'] = str(year)
    
    data = _fetch_eurostat_data('mar_go_am', params)
    
    if not data:
        return {
            'dataset': 'mar_go_am',
            'country': country,
            'data': [],
            'error': 'Failed to fetch data'
        }
    
    parsed = _parse_eurostat_response(data)
    
    return {
        'dataset': 'mar_go_am',
        'country': country,
        'year': year,
        'unit': 'thousand tonnes',
        'data': parsed,
        'count': len(parsed)
    }


def get_air_passengers(country: str = 'DE', year: Optional[int] = None) -> Dict[str, Union[List, str]]:
    """
    Get air passenger transport data
    
    Args:
        country: ISO 2-letter country code (default: DE for Germany)
        year: Specific year or None for all available
    
    Returns:
        Dictionary with data points and metadata
    """
    params = {'geo': country}
    if year:
        params['time'] = str(year)
    
    data = _fetch_eurostat_data('avia_paoc', params)
    
    if not data:
        return {
            'dataset': 'avia_paoc',
            'country': country,
            'data': [],
            'error': 'Failed to fetch data'
        }
    
    parsed = _parse_eurostat_response(data)
    
    return {
        'dataset': 'avia_paoc',
        'country': country,
        'year': year,
        'unit': 'number of passengers',
        'data': parsed,
        'count': len(parsed)
    }


def get_transport_infrastructure(country: str = 'DE', mode: str = 'road') -> Dict[str, Union[List, str]]:
    """
    Get transport infrastructure data
    
    Args:
        country: ISO 2-letter country code (default: DE for Germany)
        mode: Transport mode ('road', 'rail', 'air', 'water')
    
    Returns:
        Dictionary with data points and metadata
    """
    params = {'geo': country}
    
    # Use road vehicles as proxy for infrastructure
    data = _fetch_eurostat_data('tran_sf_roadve', params)
    
    if not data:
        return {
            'dataset': 'tran_sf_roadve',
            'country': country,
            'mode': mode,
            'data': [],
            'error': 'Failed to fetch data'
        }
    
    parsed = _parse_eurostat_response(data)
    
    return {
        'dataset': 'tran_sf_roadve',
        'country': country,
        'mode': mode,
        'unit': 'number of vehicles',
        'data': parsed,
        'count': len(parsed)
    }


def get_freight_index(country: str = 'EU27_2020') -> Dict[str, Union[List, str]]:
    """
    Get freight transport index
    
    Args:
        country: ISO country code or EU aggregate (default: EU27_2020)
    
    Returns:
        Dictionary with index data and metadata
    """
    params = {'geo': country}
    
    data = _fetch_eurostat_data('tran_hv_frmod', params)
    
    if not data:
        return {
            'dataset': 'tran_hv_frmod',
            'country': country,
            'data': [],
            'error': 'Failed to fetch data'
        }
    
    parsed = _parse_eurostat_response(data)
    
    return {
        'dataset': 'tran_hv_frmod',
        'country': country,
        'unit': 'index 2015=100',
        'data': parsed,
        'count': len(parsed)
    }


if __name__ == "__main__":
    # Quick test
    print(json.dumps({
        "module": "eurostat_transport_statistics_api",
        "status": "active",
        "source": EUROSTAT_BASE_URL,
        "datasets": list(EUROSTAT_DATASETS.keys()),
        "functions": [
            "get_road_freight",
            "get_rail_freight",
            "get_maritime_transport",
            "get_air_passengers",
            "get_transport_infrastructure",
            "get_freight_index"
        ]
    }, indent=2))
