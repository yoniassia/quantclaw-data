#!/usr/bin/env python3
"""
IMF PortWatch — Global Maritime Trade & Port Congestion Module

Provides real-time data on global maritime trade flows, port congestion, and shipping volumes
to monitor disruptions in supply chains. Aggregates satellite and AIS data for insights into
export volumes, transit times, and port performance metrics.

Source: https://portwatch.imf.org/
Category: Infrastructure & Transport
Free tier: True (requires registration for API access)
Update frequency: Daily
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import requests
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# IMF PortWatch API Configuration
PORTWATCH_BASE_URL = "https://portwatch.imf.org/api"
DEFAULT_TIMEOUT = 15

# Major maritime chokepoints
CHOKEPOINTS = {
    'suez': {'name': 'Suez Canal', 'region': 'Middle East'},
    'panama': {'name': 'Panama Canal', 'region': 'Central America'},
    'hormuz': {'name': 'Strait of Hormuz', 'region': 'Persian Gulf'},
    'malacca': {'name': 'Strait of Malacca', 'region': 'Southeast Asia'},
    'gibraltar': {'name': 'Strait of Gibraltar', 'region': 'Mediterranean'},
    'bosporus': {'name': 'Bosporus Strait', 'region': 'Turkey'}
}

# Major global ports registry
MAJOR_PORTS = {
    'CNSHA': {'name': 'Shanghai', 'country': 'China', 'region': 'East Asia'},
    'SGSIN': {'name': 'Singapore', 'country': 'Singapore', 'region': 'Southeast Asia'},
    'NLRTM': {'name': 'Rotterdam', 'country': 'Netherlands', 'region': 'Europe'},
    'USNYC': {'name': 'New York/New Jersey', 'country': 'USA', 'region': 'North America'},
    'USLAX': {'name': 'Los Angeles', 'country': 'USA', 'region': 'North America'},
    'USLGB': {'name': 'Long Beach', 'country': 'USA', 'region': 'North America'},
    'CNNGB': {'name': 'Ningbo-Zhoushan', 'country': 'China', 'region': 'East Asia'},
    'CNSZX': {'name': 'Shenzhen', 'country': 'China', 'region': 'East Asia'},
    'KRPUS': {'name': 'Busan', 'country': 'South Korea', 'region': 'East Asia'},
    'AEJEA': {'name': 'Jebel Ali', 'country': 'UAE', 'region': 'Middle East'},
    'DEHAM': {'name': 'Hamburg', 'country': 'Germany', 'region': 'Europe'},
    'USHOU': {'name': 'Houston', 'country': 'USA', 'region': 'North America'},
    'HKHKG': {'name': 'Hong Kong', 'country': 'Hong Kong', 'region': 'East Asia'},
    'THLCH': {'name': 'Laem Chabang', 'country': 'Thailand', 'region': 'Southeast Asia'},
    'BEANR': {'name': 'Antwerp', 'country': 'Belgium', 'region': 'Europe'}
}


def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """
    Internal helper to make API requests with error handling
    
    Args:
        endpoint: API endpoint path
        params: Optional query parameters
    
    Returns:
        Dict with success flag and data or error
    """
    try:
        url = f"{PORTWATCH_BASE_URL}/{endpoint}"
        response = requests.get(url, params=params, timeout=DEFAULT_TIMEOUT)
        
        # Handle different response scenarios
        if response.status_code == 200:
            try:
                data = response.json()
                return {'success': True, 'data': data}
            except json.JSONDecodeError:
                # API might return HTML or non-JSON
                return {
                    'success': False,
                    'error': 'Invalid JSON response from API',
                    'status_code': response.status_code
                }
        elif response.status_code == 404:
            return {
                'success': False,
                'error': f'Endpoint not found: {endpoint}',
                'status_code': 404,
                'note': 'API endpoint may require authentication or different path'
            }
        elif response.status_code == 401:
            return {
                'success': False,
                'error': 'Authentication required',
                'status_code': 401,
                'note': 'Register at https://portwatch.imf.org for API access'
            }
        else:
            return {
                'success': False,
                'error': f'HTTP {response.status_code}',
                'status_code': response.status_code
            }
    
    except requests.Timeout:
        return {
            'success': False,
            'error': 'Request timeout',
            'note': 'API did not respond within timeout period'
        }
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'Request failed: {str(e)}'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }


def get_port_congestion(port_id: Optional[str] = None, country: Optional[str] = None) -> Dict:
    """
    Get current port congestion levels globally or for specific port/country
    
    Congestion is measured by vessel wait times, berth occupancy, and cargo throughput delays.
    
    Args:
        port_id: Optional port code (e.g., 'CNSHA' for Shanghai)
        country: Optional country filter (e.g., 'China', 'USA')
    
    Returns:
        Dict with congestion metrics, wait times, and status indicators
    
    Example:
        >>> data = get_port_congestion(port_id='CNSHA')
        >>> print(data['congestion_level'])
    """
    params = {}
    if port_id:
        params['port_id'] = port_id
    if country:
        params['country'] = country
    
    result = _make_request('port-congestion', params)
    
    if not result['success']:
        # Provide sample structure for when API is unavailable
        sample_ports = []
        ports_to_show = [port_id] if port_id else list(MAJOR_PORTS.keys())[:5]
        
        for pid in ports_to_show:
            if pid in MAJOR_PORTS:
                port_info = MAJOR_PORTS[pid]
                sample_ports.append({
                    'port_id': pid,
                    'port_name': port_info['name'],
                    'country': port_info['country'],
                    'congestion_level': 'unknown',
                    'avg_wait_hours': None,
                    'berth_occupancy_pct': None,
                    'status': 'data_unavailable',
                    'last_updated': datetime.now().isoformat()
                })
        
        return {
            'success': False,
            'error': result.get('error'),
            'note': result.get('note'),
            'sample_structure': sample_ports,
            'timestamp': datetime.now().isoformat()
        }
    
    return {
        'success': True,
        'congestion_data': result['data'],
        'timestamp': datetime.now().isoformat()
    }


def get_trade_disruptions(region: Optional[str] = None) -> Dict:
    """
    Get active trade disruption alerts globally or by region
    
    Tracks disruptions from weather events, political issues, labor strikes,
    equipment failures, and other factors affecting maritime trade.
    
    Args:
        region: Optional region filter (e.g., 'East Asia', 'Europe', 'Middle East')
    
    Returns:
        Dict with active disruptions, severity levels, and affected routes
    
    Example:
        >>> alerts = get_trade_disruptions(region='Middle East')
        >>> for alert in alerts['disruptions']:
        ...     print(f"{alert['type']}: {alert['description']}")
    """
    params = {}
    if region:
        params['region'] = region
    
    result = _make_request('trade-disruptions', params)
    
    if not result['success']:
        # Provide sample structure
        sample_disruptions = [
            {
                'id': 'sample_1',
                'type': 'congestion',
                'region': region or 'global',
                'severity': 'unknown',
                'description': 'API unavailable - sample structure',
                'affected_ports': [],
                'start_date': datetime.now().isoformat(),
                'status': 'data_unavailable'
            }
        ]
        
        return {
            'success': False,
            'error': result.get('error'),
            'note': result.get('note'),
            'sample_structure': sample_disruptions,
            'timestamp': datetime.now().isoformat()
        }
    
    return {
        'success': True,
        'disruptions': result['data'],
        'timestamp': datetime.now().isoformat()
    }


def get_port_throughput(
    port_id: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> Dict:
    """
    Get historical port throughput data (container volume, cargo tonnage)
    
    Args:
        port_id: Port code (e.g., 'CNSHA', 'SGSIN')
        start_date: Optional start date in YYYY-MM-DD format (default: 90 days ago)
        end_date: Optional end date in YYYY-MM-DD format (default: today)
    
    Returns:
        Dict with time series throughput data, trends, and growth metrics
    
    Example:
        >>> data = get_port_throughput('CNSHA', start_date='2026-01-01')
        >>> print(data['total_teu'])  # Twenty-foot equivalent units
    """
    if not start_date:
        start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')
    
    params = {
        'port_id': port_id,
        'start_date': start_date,
        'end_date': end_date
    }
    
    result = _make_request('port-throughput', params)
    
    if not result['success']:
        # Provide sample structure
        port_info = MAJOR_PORTS.get(port_id, {'name': 'Unknown', 'country': 'Unknown'})
        
        return {
            'success': False,
            'error': result.get('error'),
            'note': result.get('note'),
            'port_id': port_id,
            'port_name': port_info['name'],
            'country': port_info['country'],
            'sample_structure': {
                'time_series': [],
                'total_teu': None,
                'avg_daily_teu': None,
                'period_growth_pct': None
            },
            'timestamp': datetime.now().isoformat()
        }
    
    return {
        'success': True,
        'port_id': port_id,
        'throughput_data': result['data'],
        'period': {'start': start_date, 'end': end_date},
        'timestamp': datetime.now().isoformat()
    }


def get_chokepoint_status() -> Dict:
    """
    Get status of key maritime chokepoints
    
    Monitors critical shipping passages including Suez Canal, Panama Canal,
    Strait of Hormuz, Strait of Malacca, and others for congestion, closures,
    or restrictions.
    
    Returns:
        Dict with status of each chokepoint, transit times, and capacity utilization
    
    Example:
        >>> status = get_chokepoint_status()
        >>> suez = status['chokepoints']['suez']
        >>> print(f"Suez Canal: {suez['status']}")
    """
    result = _make_request('chokepoints')
    
    if not result['success']:
        # Provide sample structure with known chokepoints
        chokepoint_data = {}
        
        for cp_id, cp_info in CHOKEPOINTS.items():
            chokepoint_data[cp_id] = {
                'name': cp_info['name'],
                'region': cp_info['region'],
                'status': 'unknown',
                'transit_delay_hours': None,
                'capacity_utilization_pct': None,
                'vessels_waiting': None,
                'restrictions': [],
                'last_updated': datetime.now().isoformat()
            }
        
        return {
            'success': False,
            'error': result.get('error'),
            'note': result.get('note'),
            'sample_structure': chokepoint_data,
            'timestamp': datetime.now().isoformat()
        }
    
    return {
        'success': True,
        'chokepoints': result['data'],
        'timestamp': datetime.now().isoformat()
    }


def list_ports(country: Optional[str] = None) -> Dict:
    """
    List available ports with IDs and metadata
    
    Args:
        country: Optional country filter (e.g., 'China', 'USA', 'Netherlands')
    
    Returns:
        Dict with list of ports including codes, names, countries, and regions
    
    Example:
        >>> ports = list_ports(country='USA')
        >>> for port in ports['ports']:
        ...     print(f"{port['port_id']}: {port['name']}")
    """
    # Filter MAJOR_PORTS by country if specified
    filtered_ports = []
    
    for port_id, port_info in MAJOR_PORTS.items():
        if country and port_info['country'].lower() != country.lower():
            continue
        
        filtered_ports.append({
            'port_id': port_id,
            'name': port_info['name'],
            'country': port_info['country'],
            'region': port_info['region']
        })
    
    # Try API request as well
    params = {}
    if country:
        params['country'] = country
    
    result = _make_request('ports', params)
    
    if result['success']:
        # API data available - merge with local registry
        api_ports = result['data']
        return {
            'success': True,
            'ports': api_ports,
            'local_registry_count': len(filtered_ports),
            'timestamp': datetime.now().isoformat()
        }
    else:
        # Fall back to local registry
        return {
            'success': True,
            'ports': filtered_ports,
            'count': len(filtered_ports),
            'source': 'local_registry',
            'note': 'Using local port registry - API unavailable',
            'api_error': result.get('error'),
            'timestamp': datetime.now().isoformat()
        }


def get_global_trade_summary() -> Dict:
    """
    Get summary of global maritime trade activity
    
    Returns:
        Dict with aggregate metrics across all monitored ports and routes
    
    Example:
        >>> summary = get_global_trade_summary()
        >>> print(summary['total_ports_monitored'])
    """
    result = _make_request('global-summary')
    
    if not result['success']:
        return {
            'success': False,
            'error': result.get('error'),
            'note': result.get('note'),
            'sample_structure': {
                'total_ports_monitored': len(MAJOR_PORTS),
                'ports_with_congestion': None,
                'active_disruptions': None,
                'avg_global_wait_hours': None,
                'chokepoints_operational': len(CHOKEPOINTS),
                'data_coverage': 'unavailable'
            },
            'timestamp': datetime.now().isoformat()
        }
    
    return {
        'success': True,
        'global_summary': result['data'],
        'timestamp': datetime.now().isoformat()
    }


def list_all_functions() -> Dict:
    """
    List all available functions in this module with descriptions
    
    Returns:
        Dict with function registry and usage examples
    """
    functions = [
        {
            'name': 'get_port_congestion',
            'description': 'Get current port congestion levels',
            'params': ['port_id (optional)', 'country (optional)'],
            'example': "get_port_congestion(port_id='CNSHA')"
        },
        {
            'name': 'get_trade_disruptions',
            'description': 'Get active trade disruption alerts',
            'params': ['region (optional)'],
            'example': "get_trade_disruptions(region='East Asia')"
        },
        {
            'name': 'get_port_throughput',
            'description': 'Get historical port throughput data',
            'params': ['port_id (required)', 'start_date (optional)', 'end_date (optional)'],
            'example': "get_port_throughput('SGSIN', start_date='2026-01-01')"
        },
        {
            'name': 'get_chokepoint_status',
            'description': 'Get status of key maritime chokepoints',
            'params': [],
            'example': "get_chokepoint_status()"
        },
        {
            'name': 'list_ports',
            'description': 'List available ports with IDs',
            'params': ['country (optional)'],
            'example': "list_ports(country='USA')"
        },
        {
            'name': 'get_global_trade_summary',
            'description': 'Get global maritime trade summary',
            'params': [],
            'example': "get_global_trade_summary()"
        }
    ]
    
    return {
        'success': True,
        'module': 'imf_portwatch',
        'function_count': len(functions),
        'functions': functions,
        'major_ports_count': len(MAJOR_PORTS),
        'chokepoints_count': len(CHOKEPOINTS),
        'api_base': PORTWATCH_BASE_URL,
        'note': 'Some functions may require API authentication at https://portwatch.imf.org'
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("IMF PortWatch - Global Maritime Trade & Port Congestion Monitor")
    print("=" * 70)
    
    # List all functions
    funcs = list_all_functions()
    print(f"\nModule: {funcs['module']}")
    print(f"Functions: {funcs['function_count']}")
    print(f"Major Ports: {funcs['major_ports_count']}")
    print(f"Chokepoints: {funcs['chokepoints_count']}")
    
    print("\n" + json.dumps(funcs, indent=2))
