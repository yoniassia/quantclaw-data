#!/usr/bin/env python3
"""
Open Earth Foundation Climate Dataset API Module

Provides access to OpenClimate data including emissions, climate targets, 
and climate policy metrics for countries, regions, cities, and organizations.

Source: https://openclimate.network / https://github.com/Open-Earth-Foundation/OpenClimate
Category: ESG & Climate
Free tier: True (public API, no authentication required)
Update frequency: Weekly
Author: QuantClaw Data NightBuilder
"""

import requests
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# OpenClimate API Configuration
BASE_URL = "https://openclimate.network/api/v1"

# ========== HELPER FUNCTIONS ==========

def _make_request(endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
    """
    Make HTTP request to OpenClimate API with error handling.
    
    Args:
        endpoint: API endpoint path (without base URL)
        params: Optional query parameters
        
    Returns:
        dict: API response data or error dict
    """
    try:
        url = f"{BASE_URL}/{endpoint.lstrip('/')}"
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        # Some endpoints return data directly (like coverage/stats)
        # Others wrap in {success, data, message}
        if isinstance(data, dict):
            # If has 'success' field, use standard format
            if 'success' in data:
                if not data.get('success', False):
                    return {
                        'error': True,
                        'message': data.get('message', 'API request failed'),
                        'data': None
                    }
                return data.get('data', {})
            else:
                # Direct data response (like coverage/stats)
                return data
        
        # List response (like search)
        return data
        
    except requests.exceptions.Timeout:
        return {'error': True, 'message': 'Request timeout', 'data': None}
    except requests.exceptions.RequestException as e:
        return {'error': True, 'message': f'Request failed: {str(e)}', 'data': None}
    except json.JSONDecodeError:
        return {'error': True, 'message': 'Invalid JSON response', 'data': None}
    except Exception as e:
        return {'error': True, 'message': f'Unexpected error: {str(e)}', 'data': None}


def _normalize_actor_id(region_or_country: str) -> str:
    """
    Normalize region/country input to actor_id format.
    
    Args:
        region_or_country: Country name, code, or region identifier
        
    Returns:
        str: Normalized actor_id (ISO codes when possible)
    """
    # Common mappings
    mappings = {
        'EU': 'EU',
        'USA': 'US',
        'US': 'US',
        'United States': 'US',
        'UK': 'GB',
        'China': 'CN',
        'India': 'IN',
        'Germany': 'DE',
        'France': 'FR',
        'Canada': 'CA',
        'Japan': 'JP',
        'Brazil': 'BR',
        'Australia': 'AU',
    }
    
    return mappings.get(region_or_country, region_or_country.upper())


# ========== CORE API FUNCTIONS ==========

def get_emission_data(country: str, year: Optional[int] = None) -> Dict[str, Any]:
    """
    Get CO2 emissions data for a country or region.
    
    Args:
        country: Country name or ISO code (e.g., 'US', 'Germany', 'CN')
        year: Optional year filter (e.g., 2024). If None, returns all years.
        
    Returns:
        dict: Emissions data including total_emissions, year, datasources
        
    Example:
        >>> data = get_emission_data('US', 2023)
        >>> print(data['total_emissions'], 'tonnes CO2E')
    """
    actor_id = _normalize_actor_id(country)
    data = _make_request(f"actor/{actor_id}/emissions")
    
    if isinstance(data, dict) and data.get('error'):
        return data
    
    # Parse emissions from all datasources
    emissions = []
    
    for datasource_id, source_data in data.items():
        for emission_record in source_data.get('data', []):
            if year is None or emission_record.get('year') == year:
                emissions.append({
                    'year': emission_record.get('year'),
                    'total_emissions': emission_record.get('total_emissions'),
                    'datasource': source_data.get('name'),
                    'publisher': source_data.get('publisher'),
                    'published': source_data.get('published'),
                })
    
    # Sort by year descending
    emissions.sort(key=lambda x: x.get('year', 0), reverse=True)
    
    return {
        'actor_id': actor_id,
        'country': country,
        'emissions': emissions,
        'latest_year': emissions[0]['year'] if emissions else None,
        'latest_emissions': emissions[0]['total_emissions'] if emissions else None,
        'count': len(emissions)
    }


def get_climate_policy_index(country: str) -> Dict[str, Any]:
    """
    Get climate policy metrics based on targets and emissions trajectory.
    
    Derives a policy score from:
    - Number of climate targets set
    - Net zero commitments
    - Progress toward targets (percent achieved)
    
    Args:
        country: Country name or ISO code
        
    Returns:
        dict: Climate policy metrics including targets, net_zero status, progress
    """
    actor_id = _normalize_actor_id(country)
    data = _make_request(f"actor/{actor_id}")
    
    if isinstance(data, dict) and data.get('error'):
        return data
    
    targets = data.get('targets', [])
    
    # Calculate policy metrics
    net_zero_targets = [t for t in targets if t.get('is_net_zero')]
    absolute_targets = [t for t in targets if t.get('target_type') == 'absolute']
    
    # Average progress across targets with percent_achieved
    progress_values = [t.get('percent_achieved', 0) for t in targets if t.get('percent_achieved') is not None]
    avg_progress = sum(progress_values) / len(progress_values) if progress_values else 0
    
    return {
        'actor_id': actor_id,
        'country': country,
        'total_targets': len(targets),
        'net_zero_committed': len(net_zero_targets) > 0,
        'net_zero_year': net_zero_targets[0].get('target_year') if net_zero_targets else None,
        'absolute_reduction_targets': len(absolute_targets),
        'average_progress_pct': round(avg_progress, 2),
        'targets': targets,
        'policy_score': min(100, len(targets) * 10 + (50 if net_zero_targets else 0) + avg_progress * 0.3)
    }


def get_carbon_pricing(region: str) -> Dict[str, Any]:
    """
    Get carbon pricing indicators based on emissions targets and reductions.
    
    Note: OpenClimate doesn't provide direct carbon pricing data. This function
    derives implicit carbon price pressure from reduction targets and trajectories.
    For EU, aggregates data from major member states.
    
    Args:
        region: Region or country code (e.g., 'EU', 'US', 'CA', 'Germany')
        
    Returns:
        dict: Emission reduction targets that imply carbon pricing mechanisms
    """
    # Handle EU as aggregate of member states
    if region.upper() == 'EU':
        eu_countries = ['DE', 'FR', 'IT', 'ES', 'NL', 'PL', 'BE']
        all_targets = []
        
        for country in eu_countries:
            data = _make_request(f"actor/{country}")
            if not (isinstance(data, dict) and data.get('error')):
                targets = data.get('targets', [])
                for t in targets:
                    t['country'] = country
                all_targets.extend(targets)
        
        pricing_relevant = [
            t for t in all_targets 
            if 'Absolute' in str(t.get('target_type', '')) or 'percentage' in str(t.get('target_type', '')).lower()
        ]
        
        return {
            'actor_id': 'EU',
            'region': region,
            'countries_analyzed': eu_countries,
            'has_carbon_pricing_signals': len(pricing_relevant) > 0,
            'total_targets': len(pricing_relevant),
            'latest_target_year': max([t.get('target_year', 0) for t in pricing_relevant]) if pricing_relevant else None,
            'note': 'EU data aggregated from major member states. For actual ETS prices, see ICE or EEX exchanges.'
        }
    
    actor_id = _normalize_actor_id(region)
    data = _make_request(f"actor/{actor_id}")
    
    if isinstance(data, dict) and data.get('error'):
        return data
    
    targets = data.get('targets', [])
    
    # Filter for percentage and absolute targets (imply pricing mechanisms)
    pricing_relevant = [
        t for t in targets 
        if 'Absolute' in str(t.get('target_type', '')) or 'percentage' in str(t.get('target_type', '')).lower()
    ]
    
    return {
        'actor_id': actor_id,
        'region': region,
        'has_carbon_pricing_signals': len(pricing_relevant) > 0,
        'reduction_targets': pricing_relevant,
        'latest_target_year': max([t.get('target_year', 0) for t in pricing_relevant]) if pricing_relevant else None,
        'note': 'Derived from emissions reduction targets. For actual carbon prices, see World Bank Carbon Pricing Dashboard.'
    }


def get_transition_risk(sector: Optional[str] = None, country: Optional[str] = None) -> Dict[str, Any]:
    """
    Get transition risk metrics based on emissions intensity and reduction trajectories.
    
    Note: Sector-specific data limited in OpenClimate. This provides country-level
    transition risk based on emissions trends.
    
    Args:
        sector: Optional sector name (e.g., 'energy', 'transport', 'agriculture')
        country: Optional country filter
        
    Returns:
        dict: Transition risk indicators based on emissions trajectory
    """
    if country:
        actor_id = _normalize_actor_id(country)
        data = _make_request(f"actor/{actor_id}")
        
        if isinstance(data, dict) and data.get('error'):
            return data
        
        # Get emissions trend
        emissions_sources = data.get('emissions', {})
        all_emissions = []
        
        for source_data in emissions_sources.values():
            all_emissions.extend(source_data.get('data', []))
        
        # Sort by year
        all_emissions.sort(key=lambda x: x.get('year', 0))
        
        # Calculate trend
        if len(all_emissions) >= 2:
            recent = all_emissions[-1].get('total_emissions', 0)
            baseline = all_emissions[0].get('total_emissions', 1)
            change_pct = ((recent - baseline) / baseline) * 100 if baseline else 0
        else:
            change_pct = 0
        
        return {
            'actor_id': actor_id,
            'country': country,
            'sector': sector or 'economy-wide',
            'emissions_trend_pct': round(change_pct, 2),
            'transition_risk_level': 'HIGH' if change_pct > 10 else 'MEDIUM' if change_pct > -10 else 'LOW',
            'data_points': len(all_emissions),
            'note': 'Risk level derived from emissions trajectory. Rising = higher transition risk.'
        }
    else:
        return {
            'sector': sector or 'all',
            'note': 'Provide country parameter for transition risk analysis',
            'error': True
        }


def get_carbon_market_data() -> Dict[str, Any]:
    """
    Get global carbon market coverage statistics from OpenClimate.
    
    Returns:
        dict: Coverage statistics including data sources, actor counts, emissions records
    """
    data = _make_request("coverage/stats")
    
    if isinstance(data, dict) and data.get('error'):
        return data
    
    return {
        'timestamp': datetime.utcnow().isoformat(),
        'data_sources': data.get('number_of_data_sources'),
        'countries_with_emissions': data.get('number_of_countries_with_emissions'),
        'countries_with_targets': data.get('number_of_countries_with_targets'),
        'cities_with_emissions': data.get('number_of_cities_with_emissions'),
        'total_emissions_records': data.get('number_of_emissions_records'),
        'total_target_records': data.get('number_of_target_records'),
        'companies': data.get('number_of_companies'),
        'facilities': data.get('number_of_facilities'),
        'market_coverage': 'global',
        'note': 'OpenClimate tracks climate action across countries, cities, and organizations'
    }


def search_actor(query: str, actor_type: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Search for climate actors (countries, cities, companies, facilities).
    
    Args:
        query: Search term (name or identifier)
        actor_type: Optional filter ('country', 'city', 'organization', 'site', 'adm1', 'adm2')
        
    Returns:
        list: Matching actors with their IDs, names, types, and data availability
    """
    params = {'q': query}
    if actor_type:
        params['type'] = actor_type
    
    data = _make_request("search/actor", params=params)
    
    if isinstance(data, dict) and data.get('error'):
        return []
    
    # OpenClimate returns array directly
    if isinstance(data, list):
        return data
    
    return []


def get_actor_overview(actor_id: str) -> Dict[str, Any]:
    """
    Get comprehensive climate data for a specific actor.
    
    Args:
        actor_id: Actor identifier (e.g., 'US', 'US-CA', 'GBLON')
        
    Returns:
        dict: Complete actor data including emissions, targets, population, GDP
    """
    return _make_request(f"actor/{actor_id}")


# ========== CONVENIENCE FUNCTIONS ==========

def get_top_emitters(limit: int = 10) -> List[Dict[str, Any]]:
    """
    Search for major emitting countries.
    
    Args:
        limit: Maximum number of results
        
    Returns:
        list: Top emitting countries with their latest emissions
    """
    # Major emitters
    major_countries = ['US', 'CN', 'IN', 'RU', 'JP', 'DE', 'IR', 'KR', 'SA', 'ID', 'CA', 'BR', 'MX', 'AU', 'GB']
    
    results = []
    for country_code in major_countries[:limit]:
        emission_data = get_emission_data(country_code)
        if not emission_data.get('error'):
            results.append({
                'country': country_code,
                'latest_year': emission_data.get('latest_year'),
                'latest_emissions': emission_data.get('latest_emissions'),
            })
    
    # Sort by latest emissions
    results.sort(key=lambda x: x.get('latest_emissions', 0) or 0, reverse=True)
    return results


# ========== MODULE TEST ==========

if __name__ == "__main__":
    print(json.dumps({
        "module": "open_earth_foundation_climate_dataset_api",
        "status": "active",
        "source": "https://openclimate.network",
        "functions": [
            "get_emission_data",
            "get_climate_policy_index",
            "get_carbon_pricing",
            "get_transition_risk",
            "get_carbon_market_data",
            "search_actor",
            "get_actor_overview",
            "get_top_emitters"
        ]
    }, indent=2))
