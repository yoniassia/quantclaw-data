#!/usr/bin/env python3
"""
World Bank Labor Dataset API — Labor & Demographics Module

The World Bank Open Data API provides global labor and demographic indicators including
unemployment rates, labor force participation, employment ratios, and productivity metrics.

Indicators:
- SL.UEM.TOTL.ZS: Unemployment rate (% of total labor force)
- SL.TLF.CACT.ZS: Labor force participation rate (% of population ages 15+)
- SL.EMP.TOTL.SP.ZS: Employment to population ratio (% ages 15+)
- SL.GDP.PCAP.EM.KD: GDP per person employed (constant 2021 PPP $)

Data Coverage: 200+ countries, updated annually
Free tier: Unlimited queries, no API key needed (rate limited to 50 req/min)
Source: https://data.worldbank.org/
Category: Labor & Demographics
Author: QuantClaw Data NightBuilder
Generated: 2026-03-07
"""

import requests
import time
from typing import Dict, List, Optional
from datetime import datetime, timedelta

# World Bank API base URL
BASE_URL = "https://api.worldbank.org/v2"

# Indicator codes
INDICATORS = {
    'unemployment': 'SL.UEM.TOTL.ZS',
    'labor_participation': 'SL.TLF.CACT.ZS',
    'employment_ratio': 'SL.EMP.TOTL.SP.ZS',
    'gdp_per_employed': 'SL.GDP.PCAP.EM.KD'
}

# Major economies for global summaries
MAJOR_ECONOMIES = ['US', 'GB', 'DE', 'JP', 'CN', 'FR', 'IT', 'CA', 'BR', 'IN']

# Simple in-memory cache
_CACHE = {}
_CACHE_DURATION = timedelta(hours=6)  # World Bank updates annually, 6hr cache is fine

USER_AGENT = 'QuantClaw-Data/1.0 (https://moneyclaw.com)'


def _fetch_indicator(indicator: str, country: str, start_year: int = 2015, end_year: int = 2025, 
                     use_cache: bool = True) -> Optional[List[Dict]]:
    """
    Fetch indicator data from World Bank API
    
    Args:
        indicator: World Bank indicator code (e.g., SL.UEM.TOTL.ZS)
        country: ISO 2-letter country code (e.g., US, GB, DE)
        start_year: Start year for data range
        end_year: End year for data range
        use_cache: Whether to use cached data if available
        
    Returns:
        List of data points with year and value, or None on error
    """
    cache_key = f"{indicator}:{country}:{start_year}:{end_year}"
    
    # Check cache
    if use_cache and cache_key in _CACHE:
        cached_time = _CACHE.get(f"{cache_key}:timestamp")
        if cached_time and datetime.now() - cached_time < _CACHE_DURATION:
            return _CACHE[cache_key]
    
    try:
        # Construct API URL
        url = f"{BASE_URL}/country/{country}/indicator/{indicator}"
        params = {
            'date': f"{start_year}:{end_year}",
            'format': 'json',
            'per_page': 500  # Enough for annual data
        }
        
        headers = {'User-Agent': USER_AGENT}
        
        # Add small delay to respect rate limits
        time.sleep(0.1)
        
        response = requests.get(url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        # World Bank API returns array where [0] is metadata, [1] is data
        if not isinstance(data, list) or len(data) < 2:
            return None
        
        raw_data = data[1]
        
        if not raw_data:
            return None
        
        # Extract and clean data points
        results = []
        for point in raw_data:
            if point.get('value') is not None:
                results.append({
                    'year': int(point['date']),
                    'value': float(point['value']),
                    'country': point.get('country', {}).get('value', country),
                    'country_code': point.get('countryiso3code', country)
                })
        
        # Sort by year descending (most recent first)
        results.sort(key=lambda x: x['year'], reverse=True)
        
        # Cache the result
        _CACHE[cache_key] = results
        _CACHE[f"{cache_key}:timestamp"] = datetime.now()
        
        return results
        
    except requests.RequestException as e:
        print(f"API request failed: {e}")
        return None
    except (ValueError, KeyError) as e:
        print(f"Data parsing error: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        return None


def get_unemployment(country: str = "US", start_year: int = 2015, end_year: int = 2025) -> Dict:
    """
    Get unemployment rate data for a country
    
    Unemployment rate is the percentage of the total labor force that is
    unemployed but actively seeking employment and willing to work.
    
    Args:
        country: ISO 2-letter country code (default: US)
        start_year: Start year for data range (default: 2015)
        end_year: End year for data range (default: 2025)
        
    Returns:
        Dict with success status, data list, and metadata
        
    Example:
        >>> data = get_unemployment("US", 2020, 2025)
        >>> print(data['latest_value'])
        >>> for point in data['data']:
        ...     print(f"{point['year']}: {point['value']}%")
    """
    indicator = INDICATORS['unemployment']
    raw_data = _fetch_indicator(indicator, country, start_year, end_year)
    
    if not raw_data:
        return {
            "success": False,
            "error": f"No unemployment data available for {country}",
            "country": country,
            "indicator": indicator
        }
    
    return {
        "success": True,
        "indicator": "Unemployment Rate",
        "indicator_code": indicator,
        "country": raw_data[0]['country'],
        "country_code": country,
        "data": raw_data,
        "latest_year": raw_data[0]['year'],
        "latest_value": raw_data[0]['value'],
        "count": len(raw_data),
        "unit": "% of labor force",
        "timestamp": datetime.now().isoformat(),
        "source": "World Bank Open Data"
    }


def get_labor_participation(country: str = "US", start_year: int = 2015, end_year: int = 2025) -> Dict:
    """
    Get labor force participation rate for a country
    
    Labor force participation rate is the proportion of the population ages 15+
    that is economically active: all people who supply labor for the production
    of goods and services during a specified period.
    
    Args:
        country: ISO 2-letter country code (default: US)
        start_year: Start year for data range (default: 2015)
        end_year: End year for data range (default: 2025)
        
    Returns:
        Dict with success status, data list, and metadata
    """
    indicator = INDICATORS['labor_participation']
    raw_data = _fetch_indicator(indicator, country, start_year, end_year)
    
    if not raw_data:
        return {
            "success": False,
            "error": f"No labor participation data available for {country}",
            "country": country,
            "indicator": indicator
        }
    
    return {
        "success": True,
        "indicator": "Labor Force Participation Rate",
        "indicator_code": indicator,
        "country": raw_data[0]['country'],
        "country_code": country,
        "data": raw_data,
        "latest_year": raw_data[0]['year'],
        "latest_value": raw_data[0]['value'],
        "count": len(raw_data),
        "unit": "% of population ages 15+",
        "timestamp": datetime.now().isoformat(),
        "source": "World Bank Open Data"
    }


def get_employment_ratio(country: str = "US", start_year: int = 2015, end_year: int = 2025) -> Dict:
    """
    Get employment to population ratio for a country
    
    Employment to population ratio is the proportion of a country's population
    ages 15+ that is employed. High ratios indicate a labor market that is
    efficiently absorbing the working-age population.
    
    Args:
        country: ISO 2-letter country code (default: US)
        start_year: Start year for data range (default: 2015)
        end_year: End year for data range (default: 2025)
        
    Returns:
        Dict with success status, data list, and metadata
    """
    indicator = INDICATORS['employment_ratio']
    raw_data = _fetch_indicator(indicator, country, start_year, end_year)
    
    if not raw_data:
        return {
            "success": False,
            "error": f"No employment ratio data available for {country}",
            "country": country,
            "indicator": indicator
        }
    
    return {
        "success": True,
        "indicator": "Employment to Population Ratio",
        "indicator_code": indicator,
        "country": raw_data[0]['country'],
        "country_code": country,
        "data": raw_data,
        "latest_year": raw_data[0]['year'],
        "latest_value": raw_data[0]['value'],
        "count": len(raw_data),
        "unit": "% of population ages 15+",
        "timestamp": datetime.now().isoformat(),
        "source": "World Bank Open Data"
    }


def get_country_comparison(indicator: str = "SL.UEM.TOTL.ZS", 
                          countries: List[str] = None,
                          year: Optional[int] = None) -> Dict:
    """
    Compare a labor indicator across multiple countries
    
    Args:
        indicator: World Bank indicator code (default: unemployment)
        countries: List of ISO 2-letter country codes (default: major economies)
        year: Specific year to compare (default: latest available)
        
    Returns:
        Dict with comparison data across countries
        
    Example:
        >>> comparison = get_country_comparison("SL.UEM.TOTL.ZS", ["US", "GB", "DE", "JP"])
        >>> for country, value in comparison['comparison'].items():
        ...     print(f"{country}: {value}%")
    """
    if countries is None:
        countries = ["US", "GB", "DE", "JP"]
    
    # Determine year range
    if year:
        start_year = year
        end_year = year
    else:
        end_year = datetime.now().year
        start_year = end_year - 5  # Get last 5 years to find latest
    
    comparison = {}
    errors = []
    
    for country in countries:
        raw_data = _fetch_indicator(indicator, country, start_year, end_year, use_cache=True)
        
        if raw_data and len(raw_data) > 0:
            # Use the most recent data point
            latest = raw_data[0]
            comparison[country] = {
                'value': latest['value'],
                'year': latest['year'],
                'country_name': latest['country']
            }
        else:
            errors.append(f"No data for {country}")
    
    if not comparison:
        return {
            "success": False,
            "error": "No data available for any requested country",
            "countries_requested": countries,
            "errors": errors
        }
    
    # Calculate rankings
    ranked = sorted(comparison.items(), key=lambda x: x[1]['value'], reverse=True)
    
    # Determine indicator name
    indicator_name = {
        'SL.UEM.TOTL.ZS': 'Unemployment Rate',
        'SL.TLF.CACT.ZS': 'Labor Force Participation Rate',
        'SL.EMP.TOTL.SP.ZS': 'Employment to Population Ratio',
        'SL.GDP.PCAP.EM.KD': 'GDP per Person Employed'
    }.get(indicator, indicator)
    
    return {
        "success": True,
        "indicator": indicator_name,
        "indicator_code": indicator,
        "comparison": comparison,
        "ranked": [{"rank": i+1, "country": code, **data} for i, (code, data) in enumerate(ranked)],
        "highest": ranked[0][0] if ranked else None,
        "lowest": ranked[-1][0] if ranked else None,
        "average": sum(c['value'] for c in comparison.values()) / len(comparison) if comparison else 0,
        "countries_compared": len(comparison),
        "errors": errors if errors else None,
        "timestamp": datetime.now().isoformat(),
        "source": "World Bank Open Data"
    }


def get_global_labor_summary() -> Dict:
    """
    Get latest labor statistics for major economies
    
    Provides a comprehensive snapshot of unemployment, labor participation,
    and employment ratios across the world's largest economies.
    
    Returns:
        Dict with labor stats for major economies and global insights
        
    Example:
        >>> summary = get_global_labor_summary()
        >>> print(summary['global_averages'])
        >>> for country in summary['countries']:
        ...     print(f"{country['code']}: {country['unemployment']}% unemployment")
    """
    countries_data = {}
    
    for country in MAJOR_ECONOMIES:
        # Fetch all three indicators
        unemployment = _fetch_indicator(INDICATORS['unemployment'], country, 2020, 2025, use_cache=True)
        labor_part = _fetch_indicator(INDICATORS['labor_participation'], country, 2020, 2025, use_cache=True)
        emp_ratio = _fetch_indicator(INDICATORS['employment_ratio'], country, 2020, 2025, use_cache=True)
        
        # Build country summary
        country_summary = {
            'code': country,
            'unemployment': unemployment[0]['value'] if unemployment else None,
            'unemployment_year': unemployment[0]['year'] if unemployment else None,
            'labor_participation': labor_part[0]['value'] if labor_part else None,
            'labor_participation_year': labor_part[0]['year'] if labor_part else None,
            'employment_ratio': emp_ratio[0]['value'] if emp_ratio else None,
            'employment_ratio_year': emp_ratio[0]['year'] if emp_ratio else None,
            'country_name': unemployment[0]['country'] if unemployment else country
        }
        
        countries_data[country] = country_summary
    
    # Calculate global averages (excluding None values)
    unemployment_values = [c['unemployment'] for c in countries_data.values() if c['unemployment'] is not None]
    labor_part_values = [c['labor_participation'] for c in countries_data.values() if c['labor_participation'] is not None]
    emp_ratio_values = [c['employment_ratio'] for c in countries_data.values() if c['employment_ratio'] is not None]
    
    global_averages = {
        'unemployment': round(sum(unemployment_values) / len(unemployment_values), 2) if unemployment_values else None,
        'labor_participation': round(sum(labor_part_values) / len(labor_part_values), 2) if labor_part_values else None,
        'employment_ratio': round(sum(emp_ratio_values) / len(emp_ratio_values), 2) if emp_ratio_values else None
    }
    
    # Find extremes
    unemployment_sorted = sorted([(c, v['unemployment']) for c, v in countries_data.items() if v['unemployment']], 
                                 key=lambda x: x[1])
    
    return {
        "success": True,
        "countries": list(countries_data.values()),
        "global_averages": global_averages,
        "highest_unemployment": {
            "country": unemployment_sorted[-1][0] if unemployment_sorted else None,
            "value": unemployment_sorted[-1][1] if unemployment_sorted else None
        } if unemployment_sorted else None,
        "lowest_unemployment": {
            "country": unemployment_sorted[0][0] if unemployment_sorted else None,
            "value": unemployment_sorted[0][1] if unemployment_sorted else None
        } if unemployment_sorted else None,
        "countries_analyzed": len([c for c in countries_data.values() if c['unemployment'] is not None]),
        "timestamp": datetime.now().isoformat(),
        "source": "World Bank Open Data",
        "note": "Based on major economies: " + ", ".join(MAJOR_ECONOMIES)
    }


# Convenience aliases
get_unemp = get_unemployment
get_labor = get_labor_participation
get_employment = get_employment_ratio
compare_countries = get_country_comparison
global_summary = get_global_labor_summary


if __name__ == "__main__":
    import json
    
    print("=" * 70)
    print("World Bank Labor Dataset API - Data Module")
    print("=" * 70)
    
    # Test 1: US Unemployment
    print("\n1. US Unemployment (2020-2025):")
    us_unemp = get_unemployment("US", 2020, 2025)
    print(json.dumps(us_unemp, indent=2))
    
    # Test 2: Country Comparison
    print("\n2. Country Comparison (US, GB, DE, JP):")
    comparison = get_country_comparison("SL.UEM.TOTL.ZS", ["US", "GB", "DE", "JP"])
    print(json.dumps(comparison, indent=2))
    
    # Test 3: Global Summary
    print("\n3. Global Labor Summary:")
    summary = get_global_labor_summary()
    print(json.dumps(summary, indent=2))
