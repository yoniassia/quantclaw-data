#!/usr/bin/env python3
"""
World Bank Climate Change Data API — Free Climate & ESG Indicators

Provides country-level climate indicators including GHG emissions, precipitation,
temperature anomalies, and climate vulnerability metrics. All data is open access
with no API key required for standard usage.

Useful for:
- Climate risk assessment for sovereign bonds
- ESG scoring and portfolio screening
- Agricultural commodity climate exposure
- Country-level climate transition analysis

Source: https://api.worldbank.org/v2/
Category: ESG & Climate
Free tier: True (no API key required, rate limit ~120 req/min)
Author: QuantClaw Data NightBuilder
Generated: 2026-03-07
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional, Union

# World Bank API Configuration
WB_BASE_URL = "https://api.worldbank.org/v2"
WB_TIMEOUT = 15
DEFAULT_LOOKBACK_YEARS = 10

# ========== CLIMATE INDICATORS REGISTRY ==========

CLIMATE_INDICATORS = {
    # ===== GREENHOUSE GAS EMISSIONS =====
    'GHG_TOTAL': {
        'EN.GHG.ALL.MT.CE.AR5': 'Total GHG emissions excluding LULUCF (Mt CO2e)',
        'EN.GHG.ALL.LU.MT.CE.AR5': 'Total GHG emissions including LULUCF (Mt CO2e)',
        'EN.GHG.ALL.PC.CE.AR5': 'Total GHG emissions per capita (t CO2e/capita)',
        'EN.GHG.TOT.ZG.AR5': 'Total GHG emissions % change from 1990',
    },
    
    # ===== CO2 EMISSIONS =====
    'CO2_EMISSIONS': {
        'EN.GHG.CO2.MT.CE.AR5': 'CO2 emissions total excluding LULUCF (Mt CO2e)',
        'EN.GHG.CO2.PC.CE.AR5': 'CO2 emissions per capita (t CO2e/capita)',
        'EN.GHG.CO2.ZG.AR5': 'CO2 emissions % change from 1990',
        'EN.GHG.CO2.RT.GDP.KD': 'Carbon intensity of GDP (kg CO2e per $)',
        'EN.GHG.CO2.PI.MT.CE.AR5': 'CO2 from Power Industry (Mt CO2e)',
        'EN.GHG.CO2.TR.MT.CE.AR5': 'CO2 from Transport (Mt CO2e)',
        'EN.GHG.CO2.IC.MT.CE.AR5': 'CO2 from Industrial Combustion (Mt CO2e)',
        'EN.GHG.CO2.BU.MT.CE.AR5': 'CO2 from Buildings (Mt CO2e)',
    },
    
    # ===== METHANE (CH4) =====
    'METHANE': {
        'EN.GHG.CH4.MT.CE.AR5': 'Total methane emissions (Mt CO2e)',
        'EN.GHG.CH4.AG.MT.CE.AR5': 'Methane from Agriculture (Mt CO2e)',
        'EN.GHG.CH4.WA.MT.CE.AR5': 'Methane from Waste (Mt CO2e)',
        'EN.GHG.CH4.FE.MT.CE.AR5': 'Methane from Fugitive Emissions (Mt CO2e)',
        'EN.GHG.CH4.ZG.AR5': 'Methane emissions % change from 1990',
    },
    
    # ===== NITROUS OXIDE (N2O) =====
    'NITROUS_OXIDE': {
        'EN.GHG.N2O.MT.CE.AR5': 'Total nitrous oxide emissions (Mt CO2e)',
        'EN.GHG.N2O.AG.MT.CE.AR5': 'N2O from Agriculture (Mt CO2e)',
        'EN.GHG.N2O.PI.MT.CE.AR5': 'N2O from Power Industry (Mt CO2e)',
        'EN.GHG.N2O.ZG.AR5': 'N2O emissions % change from 1990',
    },
    
    # ===== CLIMATE VULNERABILITY =====
    'CLIMATE_RISK': {
        'AG.LND.PRCP.MM': 'Average precipitation (mm per year)',
        'EN.CLC.MDAT.ZS': 'Droughts, floods, extreme temps (% population)',
    },
    
    # ===== CORPORATE ESG =====
    'CORPORATE_ESG': {
        'IC.FRM.CO2.ZS': 'Firms monitoring CO2 emissions (% of firms)',
        'IC.FRM.ENGM.ZS': 'Firms adopting energy management (% of firms)',
    }
}


def _fetch_wb_indicator(
    country_code: str,
    indicator_id: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    per_page: int = 100
) -> Dict:
    """
    Internal helper to fetch single World Bank indicator
    
    Args:
        country_code: ISO3 country code (e.g., 'USA', 'GBR', 'IND')
        indicator_id: World Bank indicator ID
        start_year: Optional start year
        end_year: Optional end year
        per_page: Results per page (max 100)
    
    Returns:
        Dict with indicator data or error
    """
    try:
        # Build date filter
        date_filter = ""
        if start_year and end_year:
            date_filter = f"&date={start_year}:{end_year}"
        elif start_year:
            date_filter = f"&date={start_year}:{datetime.now().year}"
        
        url = f"{WB_BASE_URL}/country/{country_code}/indicator/{indicator_id}"
        params = f"?format=json&per_page={per_page}{date_filter}"
        
        response = requests.get(url + params, timeout=WB_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # World Bank returns [metadata, data] array
        if len(data) < 2 or not data[1]:
            return {
                "success": False,
                "error": "No data available for this indicator",
                "indicator_id": indicator_id,
                "country_code": country_code
            }
        
        # Filter out null values
        observations = [obs for obs in data[1] if obs['value'] is not None]
        
        if not observations:
            return {
                "success": False,
                "error": "No valid observations found",
                "indicator_id": indicator_id,
                "country_code": country_code
            }
        
        # Calculate statistics
        values = [obs['value'] for obs in observations]
        latest = observations[0]  # WB returns newest first
        
        stats = {
            'latest_value': latest['value'],
            'latest_year': latest['date'],
            'min': min(values),
            'max': max(values),
            'avg': sum(values) / len(values),
            'count': len(observations)
        }
        
        # Calculate trends
        if len(observations) >= 2:
            oldest = observations[-1]
            stats['total_change'] = latest['value'] - oldest['value']
            stats['total_change_pct'] = ((latest['value'] - oldest['value']) / oldest['value'] * 100) if oldest['value'] != 0 else 0
        
        return {
            "success": True,
            "indicator_id": indicator_id,
            "indicator_name": latest['indicator']['value'],
            "country": latest['country']['value'],
            "country_code": country_code,
            "statistics": stats,
            "observations": [
                {
                    'year': obs['date'],
                    'value': obs['value']
                } for obs in observations
            ]
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "indicator_id": indicator_id,
            "country_code": country_code
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "indicator_id": indicator_id,
            "country_code": country_code
        }


def get_country_climate_data(
    country_code: str,
    indicator: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None
) -> Dict:
    """
    Get specific climate indicator for a country
    
    Args:
        country_code: ISO3 country code (USA, GBR, IND, etc.)
        indicator: Indicator ID or category name
        start_year: Optional start year
        end_year: Optional end year
    
    Returns:
        Dict with indicator data and trends
    
    Examples:
        >>> get_country_climate_data('USA', 'EN.GHG.CO2.MT.CE.AR5')
        >>> get_country_climate_data('GBR', 'EN.GHG.ALL.PC.CE.AR5', 2010, 2020)
    """
    if not end_year:
        end_year = datetime.now().year
    if not start_year:
        start_year = end_year - DEFAULT_LOOKBACK_YEARS
    
    return _fetch_wb_indicator(country_code, indicator, start_year, end_year)


def get_temperature_projections(
    country_code: str,
    scenario: str = 'historical'
) -> Dict:
    """
    Get temperature and climate projections for a country
    Note: World Bank API has limited projection data in main API
    This function returns historical precipitation and climate vulnerability
    
    Args:
        country_code: ISO3 country code
        scenario: 'historical' or 'risk_indicators'
    
    Returns:
        Dict with climate data
    """
    if scenario == 'historical':
        precip = _fetch_wb_indicator(country_code, 'AG.LND.PRCP.MM', 
                                     start_year=2000, end_year=datetime.now().year)
        return {
            'success': True,
            'scenario': 'historical',
            'country_code': country_code,
            'precipitation': precip,
            'note': 'For detailed climate projections, use specialized climate APIs'
        }
    elif scenario == 'risk_indicators':
        risk = _fetch_wb_indicator(country_code, 'EN.CLC.MDAT.ZS',
                                   start_year=1990, end_year=2020)
        return {
            'success': True,
            'scenario': 'risk_indicators',
            'country_code': country_code,
            'extreme_events': risk
        }
    else:
        return {
            'success': False,
            'error': f"Scenario '{scenario}' not supported. Use 'historical' or 'risk_indicators'"
        }


def get_precipitation_projections(country_code: str) -> Dict:
    """
    Get historical precipitation data for a country
    
    Args:
        country_code: ISO3 country code
    
    Returns:
        Dict with precipitation trends
    """
    return _fetch_wb_indicator(country_code, 'AG.LND.PRCP.MM', 
                               start_year=2000, end_year=datetime.now().year)


def get_climate_risk_indicators(country_code: str) -> Dict:
    """
    Get composite climate risk metrics for a country
    Includes GHG emissions intensity, vulnerability, and corporate action
    
    Args:
        country_code: ISO3 country code
    
    Returns:
        Dict with multiple risk indicators
    """
    risk_indicators = {
        'ghg_per_capita': 'EN.GHG.ALL.PC.CE.AR5',
        'carbon_intensity_gdp': 'EN.GHG.CO2.RT.GDP.KD',
        'precipitation': 'AG.LND.PRCP.MM',
        'extreme_events': 'EN.CLC.MDAT.ZS',
        'firms_monitoring_co2': 'IC.FRM.CO2.ZS',
    }
    
    results = {}
    for name, indicator_id in risk_indicators.items():
        data = _fetch_wb_indicator(country_code, indicator_id, 
                                   start_year=datetime.now().year - 5,
                                   end_year=datetime.now().year)
        if data['success']:
            results[name] = data['statistics']
    
    # Calculate risk score (simplified)
    risk_score = 0
    risk_factors = []
    
    if 'ghg_per_capita' in results and results['ghg_per_capita']['latest_value'] > 10:
        risk_score += 2
        risk_factors.append('High per capita emissions (>10t CO2e)')
    
    if 'carbon_intensity_gdp' in results and results['carbon_intensity_gdp']['latest_value'] > 0.3:
        risk_score += 2
        risk_factors.append('High carbon intensity of GDP')
    
    if 'extreme_events' in results and results['extreme_events']['latest_value'] > 5:
        risk_score += 1
        risk_factors.append('Elevated climate vulnerability')
    
    return {
        'success': True,
        'country_code': country_code,
        'risk_indicators': results,
        'risk_score': risk_score,
        'risk_level': 'High' if risk_score >= 4 else 'Medium' if risk_score >= 2 else 'Low',
        'risk_factors': risk_factors if risk_factors else ['No major risk factors identified'],
        'timestamp': datetime.now().isoformat()
    }


def get_historical_climate(
    country_code: str,
    start_year: int,
    end_year: int
) -> Dict:
    """
    Get historical climate and emissions data for a country
    
    Args:
        country_code: ISO3 country code
        start_year: Start year
        end_year: End year
    
    Returns:
        Dict with historical trends across multiple indicators
    """
    indicators = {
        'total_ghg': 'EN.GHG.ALL.MT.CE.AR5',
        'co2_total': 'EN.GHG.CO2.MT.CE.AR5',
        'methane': 'EN.GHG.CH4.MT.CE.AR5',
        'precipitation': 'AG.LND.PRCP.MM',
    }
    
    results = {}
    for name, indicator_id in indicators.items():
        data = _fetch_wb_indicator(country_code, indicator_id, start_year, end_year)
        if data['success']:
            results[name] = {
                'statistics': data['statistics'],
                'time_series': data['observations']
            }
    
    return {
        'success': True,
        'country_code': country_code,
        'period': f"{start_year}-{end_year}",
        'historical_data': results,
        'timestamp': datetime.now().isoformat()
    }


def compare_countries_climate(
    country_codes: List[str],
    indicator: str,
    year: Optional[int] = None
) -> Dict:
    """
    Compare climate indicator across multiple countries
    
    Args:
        country_codes: List of ISO3 country codes
        indicator: Indicator ID (e.g., 'EN.GHG.CO2.PC.CE.AR5')
        year: Specific year to compare (default: latest available)
    
    Returns:
        Dict with country comparison
    
    Examples:
        >>> compare_countries_climate(['USA', 'GBR', 'IND'], 'EN.GHG.CO2.PC.CE.AR5')
    """
    if not year:
        year = datetime.now().year
    
    comparison = {}
    for country_code in country_codes:
        data = _fetch_wb_indicator(country_code, indicator, 
                                   start_year=year-1, end_year=year)
        if data['success']:
            comparison[country_code] = {
                'country': data['country'],
                'latest_value': data['statistics']['latest_value'],
                'latest_year': data['statistics']['latest_year'],
                'trend': data['statistics'].get('total_change_pct', 0)
            }
    
    # Rank countries
    if comparison:
        sorted_countries = sorted(comparison.items(), 
                                 key=lambda x: x[1]['latest_value'], 
                                 reverse=True)
        
        return {
            'success': True,
            'indicator': indicator,
            'comparison': comparison,
            'ranking': [
                {
                    'rank': i+1,
                    'country_code': code,
                    'country': data['country'],
                    'value': data['latest_value']
                } for i, (code, data) in enumerate(sorted_countries)
            ],
            'timestamp': datetime.now().isoformat()
        }
    else:
        return {
            'success': False,
            'error': 'No data available for comparison'
        }


def list_all_indicators() -> Dict:
    """
    List all available climate indicators in this module
    
    Returns:
        Dict with all indicators organized by category
    """
    all_indicators = {}
    total_count = 0
    
    for category, indicators in CLIMATE_INDICATORS.items():
        all_indicators[category] = {
            'count': len(indicators),
            'indicators': [
                {'id': ind_id, 'name': name} 
                for ind_id, name in indicators.items()
            ]
        }
        total_count += len(indicators)
    
    return {
        'success': True,
        'total_indicators': total_count,
        'categories': all_indicators,
        'module': 'world_bank_climate_change_data_api',
        'source': 'World Bank Open Data API'
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 70)
    print("World Bank Climate Change Data API Module")
    print("=" * 70)
    
    # Show available indicators
    indicators = list_all_indicators()
    print(f"\nTotal Indicators: {indicators['total_indicators']}")
    print("\nCategories:")
    for cat, info in indicators['categories'].items():
        print(f"  {cat}: {info['count']} indicators")
    
    print("\n" + json.dumps(indicators, indent=2))
