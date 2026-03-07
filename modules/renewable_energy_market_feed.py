#!/usr/bin/env python3
"""
Renewable Energy Market Feed — Global Renewable Energy Data Module

Provides comprehensive renewable energy capacity, generation, and cost data from
Our World in Data's energy dataset. Supports analysis of solar, wind, hydro, and
other renewable sources with country-level and global aggregations.

Source: https://github.com/owid/energy-data
Category: Commodities & Energy
Free tier: True
Update frequency: quarterly
Author: QuantClaw Data NightBuilder
Phase: NightBuilder
"""

import requests
import json
import io
from datetime import datetime
from typing import Dict, List, Optional
from functools import lru_cache

# ========== CONFIGURATION ==========

OWID_ENERGY_CSV_URL = "https://raw.githubusercontent.com/owid/energy-data/master/owid-energy-data.csv"
REQUEST_TIMEOUT = 30

# Technology types for cost trends
RENEWABLE_TECHNOLOGIES = [
    'solar', 'wind', 'hydro', 'biofuel', 
    'other_renewable', 'renewables', 'low_carbon'
]

# Key metrics mapping
CAPACITY_FIELDS = {
    'solar': 'solar_electricity',
    'wind': 'wind_electricity', 
    'hydro': 'hydro_electricity',
    'renewables': 'renewables_electricity',
}

SHARE_FIELDS = {
    'solar': 'solar_share_energy',
    'wind': 'wind_share_energy',
    'hydro': 'hydro_share_energy',
    'renewables': 'renewables_share_energy',
}


# ========== DATA FETCHING ==========

@lru_cache(maxsize=1)
def fetch_owid_energy_data() -> List[Dict]:
    """
    Fetch and parse Our World in Data energy CSV
    Cached to avoid repeated downloads
    
    Returns:
        List of dicts with energy data by country/year
    """
    try:
        response = requests.get(OWID_ENERGY_CSV_URL, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        # Parse CSV manually (avoiding pandas dependency)
        lines = response.text.strip().split('\n')
        headers = lines[0].split(',')
        
        data = []
        for line in lines[1:]:
            values = line.split(',')
            if len(values) == len(headers):
                row = {}
                for i, header in enumerate(headers):
                    value = values[i].strip()
                    # Convert numeric fields
                    if value and value not in ['', 'nan', 'N/A']:
                        try:
                            if header in ['year', 'population']:
                                row[header] = int(float(value))
                            elif header in ['country', 'iso_code']:
                                row[header] = value
                            else:
                                row[header] = float(value)
                        except (ValueError, TypeError):
                            row[header] = value
                    else:
                        row[header] = None
                data.append(row)
        
        return data
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"Failed to fetch OWID data: {str(e)}"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Data parsing error: {str(e)}"
        }


def filter_data(
    data: List[Dict],
    country: Optional[str] = None,
    year: Optional[int] = None,
    min_year: Optional[int] = None,
    exclude_aggregates: bool = False
) -> List[Dict]:
    """
    Filter dataset by country and/or year
    
    Args:
        data: Full dataset
        country: Country name or ISO code (case-insensitive)
        year: Specific year
        min_year: Minimum year (for ranges)
        exclude_aggregates: Exclude regional aggregates (OECD, G20, etc.)
    
    Returns:
        Filtered list of records
    """
    filtered = data
    
    if country:
        country_lower = country.lower()
        filtered = [
            r for r in filtered
            if (r.get('country') and r.get('country').lower() == country_lower) or
               (r.get('iso_code') and r.get('iso_code').lower() == country_lower)
        ]
    
    if year:
        filtered = [r for r in filtered if r.get('year') == year]
    
    if min_year:
        filtered = [r for r in filtered if r.get('year', 0) >= min_year]
    
    if exclude_aggregates:
        # Exclude regional/group aggregates
        exclude_terms = ['OECD', 'G20', 'Ember', '(EI)', 'Asia Pacific', 
                         'Non-OECD', 'Europe', 'Africa', 'Americas', 'Asia', 
                         'Middle East', 'ASEAN', 'European Union', 'income',
                         'North America', 'South America', 'Central America',
                         'Eastern Europe', 'Western Europe', 'Sub-Saharan']
        filtered = [
            r for r in filtered
            if not any(term in r.get('country', '') for term in exclude_terms)
        ]
    
    return filtered


# ========== PUBLIC API FUNCTIONS ==========

def get_renewable_capacity(country: str, year: int) -> Dict:
    """
    Get renewable energy capacity for a specific country and year
    
    Args:
        country: Country name (e.g., "United States", "USA", "China")
        year: Year (e.g., 2023)
    
    Returns:
        Dict with renewable capacity by technology in TWh
    """
    try:
        data = fetch_owid_energy_data()
        
        if isinstance(data, dict) and not data.get('success', True):
            return data
        
        filtered = filter_data(data, country=country, year=year)
        
        if not filtered:
            return {
                "success": False,
                "error": f"No data found for {country} in {year}"
            }
        
        record = filtered[0]
        
        capacity = {
            'country': record.get('country'),
            'year': year,
            'solar_twh': record.get('solar_electricity'),
            'wind_twh': record.get('wind_electricity'),
            'hydro_twh': record.get('hydro_electricity'),
            'biofuel_twh': record.get('biofuel_electricity'),
            'other_renewable_twh': record.get('other_renewable_electricity'),
            'total_renewables_twh': record.get('renewables_electricity'),
            'renewables_share_pct': record.get('renewables_share_elec'),
        }
        
        # Remove None values
        capacity = {k: v for k, v in capacity.items() if v is not None}
        
        return {
            "success": True,
            "data": capacity,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_solar_capacity_global(year: int) -> Dict:
    """
    Get global solar capacity for a specific year
    
    Args:
        year: Year (e.g., 2023)
    
    Returns:
        Dict with global solar capacity and top countries
    """
    try:
        data = fetch_owid_energy_data()
        
        if isinstance(data, dict) and not data.get('success', True):
            return data
        
        filtered = filter_data(data, year=year)
        
        # Get World total
        world_data = [r for r in filtered if r.get('country') == 'World']
        world_solar = world_data[0].get('solar_electricity') if world_data else None
        
        # Get top countries (exclude aggregates)
        country_filtered = filter_data(filtered, exclude_aggregates=True)
        country_solar = [
            {
                'country': r.get('country'),
                'solar_twh': r.get('solar_electricity'),
                'solar_share_pct': r.get('solar_share_elec')
            }
            for r in country_filtered
            if r.get('solar_electricity') and r.get('country') != 'World'
        ]
        
        country_solar.sort(key=lambda x: x['solar_twh'], reverse=True)
        top_10 = country_solar[:10]
        
        return {
            "success": True,
            "year": year,
            "global_solar_twh": world_solar,
            "top_countries": top_10,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_wind_capacity_global(year: int) -> Dict:
    """
    Get global wind capacity for a specific year
    
    Args:
        year: Year (e.g., 2023)
    
    Returns:
        Dict with global wind capacity and top countries
    """
    try:
        data = fetch_owid_energy_data()
        
        if isinstance(data, dict) and not data.get('success', True):
            return data
        
        filtered = filter_data(data, year=year)
        
        # Get World total
        world_data = [r for r in filtered if r.get('country') == 'World']
        world_wind = world_data[0].get('wind_electricity') if world_data else None
        
        # Get top countries (exclude aggregates)
        country_filtered = filter_data(filtered, exclude_aggregates=True)
        country_wind = [
            {
                'country': r.get('country'),
                'wind_twh': r.get('wind_electricity'),
                'wind_share_pct': r.get('wind_share_elec')
            }
            for r in country_filtered
            if r.get('wind_electricity') and r.get('country') != 'World'
        ]
        
        country_wind.sort(key=lambda x: x['wind_twh'], reverse=True)
        top_10 = country_wind[:10]
        
        return {
            "success": True,
            "year": year,
            "global_wind_twh": world_wind,
            "top_countries": top_10,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_energy_cost_trends(technology: str, start_year: int = 2010) -> Dict:
    """
    Get energy cost trends for a specific renewable technology
    Note: OWID dataset doesn't include cost data, so we return capacity growth as proxy
    
    Args:
        technology: Technology name ('solar', 'wind', 'hydro', 'renewables')
        start_year: Starting year for trend analysis (default 2010)
    
    Returns:
        Dict with capacity trends over time (proxy for cost reduction via scale)
    """
    try:
        data = fetch_owid_energy_data()
        
        if isinstance(data, dict) and not data.get('success', True):
            return data
        
        # Get world data for the technology
        field_name = CAPACITY_FIELDS.get(technology.lower())
        
        if not field_name:
            return {
                "success": False,
                "error": f"Unknown technology: {technology}. Use: solar, wind, hydro, renewables"
            }
        
        world_data = [
            r for r in data
            if r.get('country') == 'World' and 
               r.get('year', 0) >= start_year and
               r.get(field_name) is not None
        ]
        
        world_data.sort(key=lambda x: x.get('year'))
        
        trends = [
            {
                'year': r.get('year'),
                'capacity_twh': r.get(field_name),
                'growth_pct': r.get(f'{technology}_cons_change_pct')
            }
            for r in world_data
        ]
        
        # Calculate CAGR
        if len(trends) >= 2:
            first_val = trends[0]['capacity_twh']
            last_val = trends[-1]['capacity_twh']
            years = trends[-1]['year'] - trends[0]['year']
            
            if first_val and last_val and years > 0:
                cagr = ((last_val / first_val) ** (1 / years) - 1) * 100
            else:
                cagr = None
        else:
            cagr = None
        
        return {
            "success": True,
            "technology": technology,
            "period": f"{start_year}-{trends[-1]['year']}" if trends else None,
            "cagr_pct": round(cagr, 2) if cagr else None,
            "capacity_growth": trends,
            "note": "Capacity growth as proxy for cost reduction (actual cost data not available in OWID dataset)",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_renewable_share(country: str, recent_years: int = 5) -> Dict:
    """
    Get renewable energy share for a country over recent years
    
    Args:
        country: Country name (e.g., "United States", "USA", "China")
        recent_years: Number of recent years to include (default 5)
    
    Returns:
        Dict with renewable share trends
    """
    try:
        data = fetch_owid_energy_data()
        
        if isinstance(data, dict) and not data.get('success', True):
            return data
        
        # Get all data for country, sorted by year descending
        country_data = filter_data(data, country=country)
        country_data = [r for r in country_data if r.get('renewables_share_energy') is not None]
        country_data.sort(key=lambda x: x.get('year', 0), reverse=True)
        
        if not country_data:
            return {
                "success": False,
                "error": f"No renewable share data found for {country}"
            }
        
        recent_data = country_data[:recent_years]
        recent_data.reverse()  # Chronological order
        
        trends = [
            {
                'year': r.get('year'),
                'renewables_share_energy_pct': r.get('renewables_share_energy'),
                'renewables_share_elec_pct': r.get('renewables_share_elec'),
                'solar_share_pct': r.get('solar_share_energy'),
                'wind_share_pct': r.get('wind_share_energy'),
                'hydro_share_pct': r.get('hydro_share_energy'),
            }
            for r in recent_data
        ]
        
        # Calculate change over period
        if len(trends) >= 2:
            first = trends[0]['renewables_share_energy_pct']
            last = trends[-1]['renewables_share_energy_pct']
            change_pct = last - first if (first and last) else None
        else:
            change_pct = None
        
        return {
            "success": True,
            "country": recent_data[0].get('country'),
            "latest_year": recent_data[0].get('year'),
            "latest_share_pct": recent_data[0].get('renewables_share_energy'),
            "change_over_period_pct": round(change_pct, 2) if change_pct else None,
            "trends": trends,
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def get_global_renewable_snapshot(year: int = 2022) -> Dict:
    """
    Get comprehensive global renewable energy snapshot
    
    Args:
        year: Year for snapshot (default 2022, latest available in OWID)
    
    Returns:
        Dict with global renewable metrics across technologies
    """
    try:
        data = fetch_owid_energy_data()
        
        if isinstance(data, dict) and not data.get('success', True):
            return data
        
        world_data = [r for r in data if r.get('country') == 'World' and r.get('year') == year]
        
        if not world_data:
            return {
                "success": False,
                "error": f"No global data found for {year}"
            }
        
        record = world_data[0]
        
        snapshot = {
            'year': year,
            'total_renewables_twh': record.get('renewables_electricity'),
            'renewables_share_elec_pct': record.get('renewables_share_elec'),
            'renewables_share_energy_pct': record.get('renewables_share_energy'),
            'solar_twh': record.get('solar_electricity'),
            'wind_twh': record.get('wind_electricity'),
            'hydro_twh': record.get('hydro_electricity'),
            'biofuel_twh': record.get('biofuel_electricity'),
            'other_renewable_twh': record.get('other_renewable_electricity'),
            'low_carbon_share_pct': record.get('low_carbon_share_energy'),
            'fossil_share_pct': record.get('fossil_share_energy'),
        }
        
        # Remove None values
        snapshot = {k: v for k, v in snapshot.items() if v is not None}
        
        return {
            "success": True,
            "global_snapshot": snapshot,
            "timestamp": datetime.now().isoformat(),
            "source": "Our World in Data Energy Dataset"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("Renewable Energy Market Feed")
    print("=" * 60)
    
    # Test global snapshot
    print("\n1. Global Renewable Snapshot (2022):")
    snapshot = get_global_renewable_snapshot(2022)
    print(json.dumps(snapshot, indent=2))
    
    # Test country capacity
    print("\n2. USA Renewable Capacity (2022):")
    usa_capacity = get_renewable_capacity("United States", 2022)
    print(json.dumps(usa_capacity, indent=2))
    
    # Test global solar
    print("\n3. Global Solar Capacity (2022):")
    solar = get_solar_capacity_global(2022)
    if solar.get('success'):
        print(f"Global Solar: {solar['global_solar_twh']} TWh")
        print("Top 5 Countries:")
        for c in solar['top_countries'][:5]:
            print(f"  {c['country']}: {c['solar_twh']} TWh ({c['solar_share_pct']}%)")
