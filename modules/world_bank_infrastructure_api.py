#!/usr/bin/env python3
"""
World Bank Infrastructure API — Global Infrastructure Data Module

Specialized module for infrastructure and transport data from the World Bank API.
Covers key infrastructure metrics including:
- Rail and road networks (kilometers)
- Air transport (passengers)
- Container port traffic (TEU)
- Electricity access (% population)
- Broadband subscriptions
- Infrastructure spending (% GDP)

Source: https://api.worldbank.org/v2/
Category: Infrastructure & Transport
Free tier: True (no API key required)
Author: QuantClaw Data NightBuilder
Phase: NightBuilder
"""

import requests
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# World Bank API Configuration
WB_BASE_URL = "https://api.worldbank.org/v2"
WB_DEFAULT_TIMEOUT = 15

# ========== INFRASTRUCTURE INDICATORS REGISTRY ==========

WB_INFRASTRUCTURE_INDICATORS = {
    # ===== TRANSPORT NETWORKS =====
    'TRANSPORT': {
        'IS.RRS.TOTL.KM': 'Rail lines (total route-km)',
        'IS.ROD.TOTL.KM': 'Roads, total network (km)',
        'IS.ROD.PAVE.ZS': 'Roads, paved (% of total roads)',
        'IS.AIR.PSGR': 'Air transport, passengers carried',
        'IS.AIR.DPRT': 'Air transport, registered carrier departures worldwide',
        'IS.SHP.GOOD.TU': 'Container port traffic (TEU: 20 foot equivalent units)',
    },
    
    # ===== ENERGY & ELECTRICITY =====
    'ENERGY': {
        'EG.ELC.ACCS.ZS': 'Access to electricity (% of population)',
        'EG.ELC.ACCS.RU.ZS': 'Access to electricity, rural (% of rural population)',
        'EG.ELC.ACCS.UR.ZS': 'Access to electricity, urban (% of urban population)',
        'EG.USE.ELEC.KH.PC': 'Electric power consumption (kWh per capita)',
        'EG.ELC.LOSS.ZS': 'Electric power transmission and distribution losses (% of output)',
    },
    
    # ===== DIGITAL INFRASTRUCTURE =====
    'DIGITAL': {
        'IT.NET.BBND': 'Fixed broadband subscriptions',
        'IT.NET.BBND.P2': 'Fixed broadband subscriptions (per 100 people)',
        'IT.CEL.SETS': 'Mobile cellular subscriptions',
        'IT.CEL.SETS.P2': 'Mobile cellular subscriptions (per 100 people)',
        'IT.NET.USER.ZS': 'Individuals using the Internet (% of population)',
    },
    
    # ===== INFRASTRUCTURE SPENDING =====
    'SPENDING': {
        'GC.XPN.INFC.ZS': 'General government final consumption expenditure (% of GDP)',
        'NE.CON.GOVT.ZS': 'General government final consumption expenditure (% of GDP)',
    },
    
    # ===== WATER & SANITATION =====
    'WATER': {
        'SH.H2O.BASW.ZS': 'People using at least basic drinking water services (% of population)',
        'SH.H2O.BASW.RU.ZS': 'People using at least basic drinking water services, rural (% of rural population)',
        'SH.H2O.BASW.UR.ZS': 'People using at least basic drinking water services, urban (% of urban population)',
        'SH.STA.BASS.ZS': 'People using at least basic sanitation services (% of population)',
    },
}


def get_indicator_data(
    country_code: str,
    indicator: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    most_recent: int = 10
) -> Dict:
    """
    Fetch single World Bank indicator data for a country
    
    Args:
        country_code: ISO 3166-1 alpha-3 country code (e.g., 'USA', 'CHN', 'GBR')
        indicator: World Bank indicator code (e.g., 'IS.RRS.TOTL.KM')
        start_year: Start year for data range (optional)
        end_year: End year for data range (optional)
        most_recent: Number of most recent values to return (default 10)
    
    Returns:
        Dict with indicator data, latest value, and historical trends
    """
    try:
        url = f"{WB_BASE_URL}/country/{country_code}/indicator/{indicator}"
        params = {
            "format": "json",
            "per_page": most_recent if not (start_year or end_year) else 100,
        }
        
        # Add date range if specified
        if start_year or end_year:
            params["date"] = f"{start_year or ''}:{end_year or ''}"
        
        response = requests.get(url, params=params, timeout=WB_DEFAULT_TIMEOUT)
        response.raise_for_status()
        
        data = response.json()
        
        # World Bank API returns [metadata, data] array
        if len(data) < 2 or not data[1]:
            return {
                "success": False,
                "error": "No data available for this indicator/country combination",
                "country_code": country_code,
                "indicator": indicator
            }
        
        # Extract observations (filter out nulls)
        observations = [
            {
                "year": int(obs["date"]),
                "value": float(obs["value"]),
                "country": obs["country"]["value"],
                "indicator": obs["indicator"]["value"]
            }
            for obs in data[1] if obs["value"] is not None
        ]
        
        if not observations:
            return {
                "success": False,
                "error": "No valid observations found",
                "country_code": country_code,
                "indicator": indicator
            }
        
        # Sort by year (newest first)
        observations.sort(key=lambda x: x["year"], reverse=True)
        
        # Calculate changes
        latest = observations[0]
        changes = {}
        
        if len(observations) >= 2:
            prev_val = observations[1]["value"]
            changes["year_change"] = latest["value"] - prev_val
            changes["year_change_pct"] = ((latest["value"] - prev_val) / prev_val * 100) if prev_val != 0 else 0
        
        if len(observations) >= 5:
            five_year_ago = observations[min(4, len(observations) - 1)]["value"]
            changes["five_year_change"] = latest["value"] - five_year_ago
            changes["five_year_change_pct"] = ((latest["value"] - five_year_ago) / five_year_ago * 100) if five_year_ago != 0 else 0
        
        if len(observations) >= 10:
            ten_year_ago = observations[min(9, len(observations) - 1)]["value"]
            changes["ten_year_change"] = latest["value"] - ten_year_ago
            changes["ten_year_change_pct"] = ((latest["value"] - ten_year_ago) / ten_year_ago * 100) if ten_year_ago != 0 else 0
        
        return {
            "success": True,
            "country_code": country_code,
            "country_name": latest["country"],
            "indicator": indicator,
            "indicator_name": latest["indicator"],
            "latest_value": latest["value"],
            "latest_year": latest["year"],
            "changes": changes,
            "observations": observations,
            "count": len(observations)
        }
    
    except requests.RequestException as e:
        return {
            "success": False,
            "error": f"HTTP error: {str(e)}",
            "country_code": country_code,
            "indicator": indicator
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "country_code": country_code,
            "indicator": indicator
        }


def get_transport_infrastructure(country_code: str) -> Dict:
    """
    Get comprehensive transport infrastructure metrics for a country
    Includes rail, roads, air, and maritime transport
    
    Args:
        country_code: ISO 3166-1 alpha-3 country code (e.g., 'USA', 'CHN')
    
    Returns:
        Dict with all transport infrastructure metrics
    """
    transport_indicators = WB_INFRASTRUCTURE_INDICATORS['TRANSPORT']
    results = {}
    
    for indicator_code, name in transport_indicators.items():
        data = get_indicator_data(country_code, indicator_code)
        if data['success']:
            results[indicator_code] = {
                'name': name,
                'value': data['latest_value'],
                'year': data['latest_year'],
                'five_year_change_pct': data['changes'].get('five_year_change_pct', 0)
            }
    
    # Calculate insights
    insights = []
    if 'IS.RRS.TOTL.KM' in results:
        rail_km = results['IS.RRS.TOTL.KM']['value']
        insights.append(f"Rail network: {rail_km:,.0f} km")
    
    if 'IS.ROD.TOTL.KM' in results:
        road_km = results['IS.ROD.TOTL.KM']['value']
        insights.append(f"Road network: {road_km:,.0f} km")
    
    if 'IS.AIR.PSGR' in results:
        air_pax = results['IS.AIR.PSGR']['value']
        insights.append(f"Air passengers: {air_pax:,.0f} annually")
    
    return {
        'success': True,
        'country_code': country_code,
        'transport_infrastructure': results,
        'insights': insights,
        'timestamp': datetime.now().isoformat()
    }


def get_energy_infrastructure(country_code: str) -> Dict:
    """
    Get energy and electricity infrastructure metrics for a country
    
    Args:
        country_code: ISO 3166-1 alpha-3 country code
    
    Returns:
        Dict with energy infrastructure metrics
    """
    energy_indicators = WB_INFRASTRUCTURE_INDICATORS['ENERGY']
    results = {}
    
    for indicator_code, name in energy_indicators.items():
        data = get_indicator_data(country_code, indicator_code)
        if data['success']:
            results[indicator_code] = {
                'name': name,
                'value': data['latest_value'],
                'year': data['latest_year'],
                'year_change': data['changes'].get('year_change', 0)
            }
    
    # Assess energy access
    insights = []
    if 'EG.ELC.ACCS.ZS' in results:
        access_pct = results['EG.ELC.ACCS.ZS']['value']
        if access_pct >= 99:
            insights.append('Near-universal electricity access')
        elif access_pct >= 90:
            insights.append('High electricity access coverage')
        elif access_pct >= 75:
            insights.append('Moderate electricity access')
        else:
            insights.append('Limited electricity access - infrastructure gap')
    
    if 'EG.USE.ELEC.KH.PC' in results:
        per_capita = results['EG.USE.ELEC.KH.PC']['value']
        if per_capita > 10000:
            insights.append('High per-capita electricity consumption (developed economy)')
        elif per_capita > 3000:
            insights.append('Moderate per-capita electricity consumption')
        else:
            insights.append('Low per-capita electricity consumption (developing)')
    
    return {
        'success': True,
        'country_code': country_code,
        'energy_infrastructure': results,
        'insights': insights,
        'timestamp': datetime.now().isoformat()
    }


def get_digital_infrastructure(country_code: str) -> Dict:
    """
    Get digital infrastructure metrics (broadband, mobile, internet)
    
    Args:
        country_code: ISO 3166-1 alpha-3 country code
    
    Returns:
        Dict with digital infrastructure metrics
    """
    digital_indicators = WB_INFRASTRUCTURE_INDICATORS['DIGITAL']
    results = {}
    
    for indicator_code, name in digital_indicators.items():
        data = get_indicator_data(country_code, indicator_code)
        if data['success']:
            results[indicator_code] = {
                'name': name,
                'value': data['latest_value'],
                'year': data['latest_year'],
                'five_year_change_pct': data['changes'].get('five_year_change_pct', 0)
            }
    
    # Assess digital readiness
    insights = []
    if 'IT.NET.BBND.P2' in results:
        broadband = results['IT.NET.BBND.P2']['value']
        if broadband > 40:
            insights.append('High broadband penetration (>40 per 100 people)')
        elif broadband > 20:
            insights.append('Moderate broadband penetration')
        else:
            insights.append('Low broadband penetration - digital divide')
    
    if 'IT.NET.USER.ZS' in results:
        internet_users = results['IT.NET.USER.ZS']['value']
        if internet_users > 80:
            insights.append('High internet penetration (>80%)')
        elif internet_users > 50:
            insights.append('Moderate internet penetration')
        else:
            insights.append('Low internet penetration - connectivity gap')
    
    return {
        'success': True,
        'country_code': country_code,
        'digital_infrastructure': results,
        'insights': insights,
        'timestamp': datetime.now().isoformat()
    }


def get_water_infrastructure(country_code: str) -> Dict:
    """
    Get water and sanitation infrastructure metrics
    
    Args:
        country_code: ISO 3166-1 alpha-3 country code
    
    Returns:
        Dict with water/sanitation access metrics
    """
    water_indicators = WB_INFRASTRUCTURE_INDICATORS['WATER']
    results = {}
    
    for indicator_code, name in water_indicators.items():
        data = get_indicator_data(country_code, indicator_code)
        if data['success']:
            results[indicator_code] = {
                'name': name,
                'value': data['latest_value'],
                'year': data['latest_year']
            }
    
    insights = []
    if 'SH.H2O.BASW.ZS' in results:
        water_access = results['SH.H2O.BASW.ZS']['value']
        if water_access >= 95:
            insights.append('Near-universal water access')
        elif water_access >= 75:
            insights.append('Moderate water access')
        else:
            insights.append('Limited water access - infrastructure priority')
    
    return {
        'success': True,
        'country_code': country_code,
        'water_infrastructure': results,
        'insights': insights,
        'timestamp': datetime.now().isoformat()
    }


def get_infrastructure_snapshot(country_code: str) -> Dict:
    """
    Get comprehensive infrastructure snapshot for a country
    Combines all infrastructure categories into single report
    
    Args:
        country_code: ISO 3166-1 alpha-3 country code (e.g., 'USA', 'CHN', 'IND')
    
    Returns:
        Dict with all infrastructure metrics across categories
    """
    snapshot = {
        'country_code': country_code,
        'timestamp': datetime.now().isoformat()
    }
    
    # Fetch all categories
    transport = get_transport_infrastructure(country_code)
    if transport['success']:
        snapshot['transport'] = transport['transport_infrastructure']
    
    energy = get_energy_infrastructure(country_code)
    if energy['success']:
        snapshot['energy'] = energy['energy_infrastructure']
    
    digital = get_digital_infrastructure(country_code)
    if digital['success']:
        snapshot['digital'] = digital['digital_infrastructure']
    
    water = get_water_infrastructure(country_code)
    if water['success']:
        snapshot['water'] = water['water_infrastructure']
    
    # Aggregate insights
    all_insights = []
    if transport['success']:
        all_insights.extend(transport.get('insights', []))
    if energy['success']:
        all_insights.extend(energy.get('insights', []))
    if digital['success']:
        all_insights.extend(digital.get('insights', []))
    if water['success']:
        all_insights.extend(water.get('insights', []))
    
    snapshot['insights'] = all_insights
    
    return {
        'success': True,
        'infrastructure_snapshot': snapshot,
        'source': 'World Bank API'
    }


def compare_countries(country_codes: List[str], indicator: str) -> Dict:
    """
    Compare single infrastructure indicator across multiple countries
    
    Args:
        country_codes: List of ISO country codes (e.g., ['USA', 'CHN', 'IND'])
        indicator: World Bank indicator code to compare
    
    Returns:
        Dict with comparison data ranked by latest value
    """
    comparison = []
    
    for country_code in country_codes:
        data = get_indicator_data(country_code, indicator)
        if data['success']:
            comparison.append({
                'country_code': country_code,
                'country_name': data['country_name'],
                'value': data['latest_value'],
                'year': data['latest_year'],
                'five_year_change_pct': data['changes'].get('five_year_change_pct', 0)
            })
    
    # Sort by value (descending)
    comparison.sort(key=lambda x: x['value'], reverse=True)
    
    # Get indicator name from first result
    indicator_name = ""
    if comparison:
        sample = get_indicator_data(comparison[0]['country_code'], indicator)
        if sample['success']:
            indicator_name = sample['indicator_name']
    
    return {
        'success': True,
        'indicator': indicator,
        'indicator_name': indicator_name,
        'comparison': comparison,
        'timestamp': datetime.now().isoformat()
    }


def list_all_indicators() -> Dict:
    """
    List all available infrastructure indicators organized by category
    
    Returns:
        Dict with all indicators and counts by category
    """
    all_indicators = {}
    total_count = 0
    
    for category, indicators_dict in WB_INFRASTRUCTURE_INDICATORS.items():
        all_indicators[category] = {
            'count': len(indicators_dict),
            'indicators': [{'code': code, 'name': name} for code, name in indicators_dict.items()]
        }
        total_count += len(indicators_dict)
    
    return {
        'success': True,
        'total_indicators': total_count,
        'categories': all_indicators,
        'module': 'world_bank_infrastructure_api'
    }


if __name__ == "__main__":
    # CLI demonstration
    print("=" * 60)
    print("World Bank Infrastructure API - Global Infrastructure Data")
    print("=" * 60)
    
    # Show available indicators
    indicators_list = list_all_indicators()
    print(f"\nTotal Indicators: {indicators_list['total_indicators']}")
    print("\nCategories:")
    for cat, info in indicators_list['categories'].items():
        print(f"  {cat}: {info['count']} indicators")
    
    print("\n" + json.dumps(indicators_list, indent=2))
