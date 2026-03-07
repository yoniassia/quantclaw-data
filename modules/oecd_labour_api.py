#!/usr/bin/env python3
"""
OECD Labour API — Employment, Unemployment & Wage Statistics

Provides comprehensive labor market data across OECD countries including:
- Unemployment rates
- Employment rates  
- Labor force participation rates (LFPR)
- Wage growth statistics
- Cross-country comparisons

Data Points:
- Harmonized unemployment rates (% of labor force)
- Employment-to-population ratios
- Labor force participation rates
- Wage growth (nominal and real)
- Country-specific and OECD aggregate statistics

Updated: Quarterly/Monthly (varies by indicator)
History: 1960+ (varies by indicator and country)
Source: https://stats.oecd.org/restsdmx/sdmx.ashx
Category: Macroeconomic Data — Labor Markets
Free tier: True (no API key required, no rate limits)
Author: QuantClaw Data NightBuilder
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import time

# API Endpoints
OECD_BASE = "https://stats.oecd.org/restsdmx/sdmx.ashx"

# Country code mapping (ISO3 to common names)
COUNTRY_CODES = {
    "USA": "United States",
    "GBR": "United Kingdom", 
    "JPN": "Japan",
    "DEU": "Germany",
    "FRA": "France",
    "ITA": "Italy",
    "CAN": "Canada",
    "AUS": "Australia",
    "KOR": "South Korea",
    "OECD": "OECD Total"
}

# Simple cache to avoid repeated requests
_CACHE = {}
_CACHE_DURATION = timedelta(hours=6)

USER_AGENT = 'QuantClaw-Data/1.0 (https://moneyclaw.com)'


def _parse_sdmx_21(xml_text: str, country_filter: Optional[str] = None) -> List[Dict]:
    """
    Parse SDMX 2.1 XML response into structured data
    
    Args:
        xml_text: Raw XML response from OECD API
        country_filter: Optional country code to filter by (e.g., "USA")
        
    Returns:
        List of data points with time period and value
    """
    try:
        root = ET.fromstring(xml_text)
        
        # SDMX 2.1 namespaces
        ns = {
            'message': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message',
            'generic': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic',
            'common': 'http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common'
        }
        
        data_points = []
        
        # Find all Obs elements
        obs_elements = root.findall('.//generic:Obs', ns)
        
        for obs in obs_elements:
            # Extract ObsKey values
            obs_key = obs.find('generic:ObsKey', ns)
            if obs_key is None:
                continue
            
            # Extract time period and country from ObsKey
            time_period = None
            ref_area = None
            
            for value in obs_key.findall('generic:Value', ns):
                value_id = value.get('id')
                value_val = value.get('value')
                
                if value_id == 'TIME_PERIOD':
                    time_period = value_val
                elif value_id == 'REF_AREA':
                    ref_area = value_val
            
            # Filter by country if specified
            if country_filter and ref_area != country_filter:
                continue
            
            # Extract observation value
            obs_value = obs.find('generic:ObsValue', ns)
            if obs_value is None or time_period is None:
                continue
            
            value = obs_value.get('value')
            if value:
                try:
                    # Parse year from time period (YYYY-MM or YYYY-QN format)
                    year = int(time_period.split('-')[0]) if '-' in time_period else int(time_period[:4])
                    
                    data_points.append({
                        'period': time_period,
                        'value': float(value),
                        'year': year,
                        'country': ref_area
                    })
                except (ValueError, IndexError):
                    continue
        
        return sorted(data_points, key=lambda x: x['period'])
        
    except ET.ParseError:
        return []
    except Exception:
        return []


def get_unemployment_rate(country: str = "USA", start_year: int = 2020) -> List[Dict]:
    """
    Get harmonized unemployment rate for a country
    
    Unemployment rate as % of civilian labor force. Harmonized definition
    across OECD countries for consistent international comparisons.
    
    Args:
        country: ISO3 country code (USA, GBR, JPN, DEU, etc.) or OECD for aggregate
        start_year: Start year for data retrieval (default 2020)
        
    Returns:
        List of dicts with period, value, and year. Empty list on error.
        
    Example:
        >>> data = get_unemployment_rate("USA", 2020)
        >>> for point in data:
        ...     print(f"{point['period']}: {point['value']}%")
    """
    cache_key = f"unemp_{country}_{start_year}"
    
    if cache_key in _CACHE:
        cached_time, cached_data = _CACHE[cache_key]
        if datetime.now() - cached_time < _CACHE_DURATION:
            return cached_data
    
    try:
        end_year = datetime.now().year + 1
        
        # Use MEI (Main Economic Indicators) dataset for unemployment
        url = f"{OECD_BASE}/GetData/MEI_CLI/LRUNTTTT.{country}.ALL?startTime={start_year}&endTime={end_year}"
        
        headers = {'User-Agent': USER_AGENT, 'Accept': 'application/xml'}
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = _parse_sdmx_21(response.text, country)
            if data:
                _CACHE[cache_key] = (datetime.now(), data)
                return data
        
        return []
        
    except Exception:
        return []


def get_employment_rate(country: str = "USA", start_year: int = 2020) -> List[Dict]:
    """
    Get employment-to-population ratio for a country
    
    Employment rate as % of working-age population (ages 15-64).
    Key indicator of labor market health and economic participation.
    
    Args:
        country: ISO3 country code (USA, GBR, JPN, etc.)
        start_year: Start year for data retrieval (default 2020)
        
    Returns:
        List of dicts with period, value, and year
        
    Example:
        >>> data = get_employment_rate("GBR", 2020)
        >>> latest = data[-1] if data else None
        >>> if latest: print(f"UK employment rate: {latest['value']}%")
    """
    cache_key = f"emp_{country}_{start_year}"
    
    if cache_key in _CACHE:
        cached_time, cached_data = _CACHE[cache_key]
        if datetime.now() - cached_time < _CACHE_DURATION:
            return cached_data
    
    try:
        end_year = datetime.now().year + 1
        
        # Try employment rate from MEI
        url = f"{OECD_BASE}/GetData/MEI_CLI/LREMTTTT.{country}.ALL?startTime={start_year}&endTime={end_year}"
        
        headers = {'User-Agent': USER_AGENT, 'Accept': 'application/xml'}
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = _parse_sdmx_21(response.text, country)
            if data:
                _CACHE[cache_key] = (datetime.now(), data)
                return data
        
        return []
        
    except Exception:
        return []


def get_labor_force_participation(country: str = "USA", start_year: int = 2020) -> Dict:
    """
    Get labor force participation rate (LFPR)
    
    LFPR measures the % of working-age population actively participating
    in the labor market (employed + unemployed but seeking work).
    Critical for understanding labor market capacity and demographics.
    
    Args:
        country: ISO3 country code
        start_year: Start year for data (default 2020)
        
    Returns:
        Dict with success status, data points, and metadata
        
    Example:
        >>> result = get_labor_force_participation("JPN", 2020)
        >>> if result['success']:
        ...     print(f"Latest LFPR: {result['latest_value']}%")
    """
    cache_key = f"lfpr_{country}_{start_year}"
    
    if cache_key in _CACHE:
        cached_time, cached_data = _CACHE[cache_key]
        if datetime.now() - cached_time < _CACHE_DURATION:
            return cached_data
    
    try:
        end_year = datetime.now().year + 1
        
        # LFPR from MEI_CLI dataset
        url = f"{OECD_BASE}/GetData/MEI_CLI/LFPR.{country}.ALL?startTime={start_year}&endTime={end_year}"
        
        headers = {'User-Agent': USER_AGENT, 'Accept': 'application/xml'}
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"API returned status {response.status_code}",
                "country": country
            }
        
        data_points = _parse_sdmx_21(response.text, country)
        
        if not data_points:
            return {
                "success": False,
                "error": "No data found for country/period",
                "country": country
            }
        
        result = {
            "success": True,
            "country": country,
            "country_name": COUNTRY_CODES.get(country, country),
            "indicator": "Labor Force Participation Rate",
            "unit": "% of working-age population",
            "data_points": data_points,
            "latest_value": data_points[-1]['value'] if data_points else None,
            "latest_period": data_points[-1]['period'] if data_points else None,
            "count": len(data_points),
            "timestamp": datetime.now().isoformat(),
            "source": "OECD Main Economic Indicators"
        }
        
        _CACHE[cache_key] = (datetime.now(), result)
        return result
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "country": country
        }


def get_wage_growth(country: str = "USA", start_year: int = 2020) -> List[Dict]:
    """
    Get wage growth statistics (year-over-year % change)
    
    Measures nominal wage growth. Key inflation and labor cost indicator.
    Important for central bank policy decisions and inflation forecasting.
    
    Args:
        country: ISO3 country code
        start_year: Start year (default 2020)
        
    Returns:
        List of dicts with period and wage growth values
        
    Note:
        Wage data availability varies by country. Some countries may have
        limited or no wage growth data in OECD databases.
    """
    cache_key = f"wage_{country}_{start_year}"
    
    if cache_key in _CACHE:
        cached_time, cached_data = _CACHE[cache_key]
        if datetime.now() - cached_time < _CACHE_DURATION:
            return cached_data
    
    try:
        end_year = datetime.now().year + 1
        
        # Try average annual wages dataset
        url = f"{OECD_BASE}/GetData/AV_AN_WAGE/{country}.?startTime={start_year}&endTime={end_year}"
        
        headers = {'User-Agent': USER_AGENT, 'Accept': 'application/xml'}
        response = requests.get(url, headers=headers, timeout=20)
        
        if response.status_code == 200:
            data = _parse_sdmx_21(response.text, country)
            
            # Calculate YoY growth if we have absolute values
            if len(data) > 1:
                growth_data = []
                for i in range(1, len(data)):
                    prev_val = data[i-1]['value']
                    curr_val = data[i]['value']
                    if prev_val and prev_val > 0:
                        growth_pct = ((curr_val - prev_val) / prev_val) * 100
                        growth_data.append({
                            'period': data[i]['period'],
                            'value': round(growth_pct, 2),
                            'year': data[i]['year']
                        })
                
                if growth_data:
                    _CACHE[cache_key] = (datetime.now(), growth_data)
                    return growth_data
            
            # Return raw data if growth calc not possible
            if data:
                _CACHE[cache_key] = (datetime.now(), data)
                return data
        
        return []
        
    except Exception:
        return []


def get_oecd_comparison(indicator: str = "unemployment", year: Optional[int] = None) -> Dict:
    """
    Compare labor market indicator across all OECD countries
    
    Get latest or specific year data for all OECD member countries.
    Useful for cross-country benchmarking and relative performance analysis.
    
    Args:
        indicator: Type of data - "unemployment", "employment", or "lfpr"
        year: Specific year (None for latest available)
        
    Returns:
        Dict with country comparisons, OECD average, and rankings
        
    Example:
        >>> comp = get_oecd_comparison("unemployment")
        >>> if comp['success']:
        ...     for c in comp['top_countries'][:5]:
        ...         print(f"{c['country']}: {c['value']}%")
    """
    cache_key = f"compare_{indicator}_{year or 'latest'}"
    
    if cache_key in _CACHE:
        cached_time, cached_data = _CACHE[cache_key]
        if datetime.now() - cached_time < _CACHE_DURATION:
            return cached_data
    
    # Major OECD countries to compare
    countries = ["USA", "GBR", "JPN", "DEU", "FRA", "ITA", "CAN", "AUS", "KOR", "OECD"]
    
    try:
        if not year:
            year = datetime.now().year - 1
        
        country_data = []
        
        for country in countries:
            if indicator == "unemployment":
                data = get_unemployment_rate(country, year)
            elif indicator == "employment":
                data = get_employment_rate(country, year)
            elif indicator == "lfpr":
                lfpr_result = get_labor_force_participation(country, year)
                data = lfpr_result.get('data_points', []) if lfpr_result.get('success') else []
            else:
                return {"success": False, "error": f"Unknown indicator: {indicator}"}
            
            if data:
                latest = data[-1]
                country_data.append({
                    "country": country,
                    "country_name": COUNTRY_CODES.get(country, country),
                    "value": latest['value'],
                    "period": latest['period']
                })
            
            time.sleep(0.2)  # Be respectful
        
        if not country_data:
            return {"success": False, "error": "No data retrieved for any country"}
        
        sorted_data = sorted(country_data, key=lambda x: x['value'])
        
        country_values = [c['value'] for c in country_data if c['country'] != 'OECD']
        oecd_avg = sum(country_values) / len(country_values) if country_values else None
        
        result = {
            "success": True,
            "indicator": indicator,
            "year": year,
            "countries": sorted_data,
            "top_countries": sorted_data[:5],
            "bottom_countries": sorted_data[-5:],
            "oecd_average": round(oecd_avg, 2) if oecd_avg else None,
            "count": len(country_data),
            "timestamp": datetime.now().isoformat(),
            "source": "OECD Labour Force Statistics"
        }
        
        _CACHE[cache_key] = (datetime.now(), result)
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e), "indicator": indicator}


# Convenience aliases
get_unemp = get_unemployment_rate
get_emp = get_employment_rate
get_lfpr = get_labor_force_participation
compare_countries = get_oecd_comparison


if __name__ == "__main__":
    import json
    
    print("=" * 70)
    print("OECD Labour Market Statistics - Macroeconomic Data Module")
    print("=" * 70)
    
    print("\n1. US Unemployment Rate (2020-present):")
    unemp = get_unemployment_rate("USA", 2020)
    print(f"   Data points: {len(unemp)}")
    if unemp:
        print(f"   Latest: {unemp[-1]['period']} = {unemp[-1]['value']}%")
    
    print("\n2. UK Employment Rate (2020-present):")
    emp = get_employment_rate("GBR", 2020)
    print(f"   Data points: {len(emp)}")
    if emp:
        print(f"   Latest: {emp[-1]['period']} = {emp[-1]['value']}%")
    
    print("\n3. Japan LFPR:")
    lfpr = get_labor_force_participation("JPN", 2020)
    if lfpr.get('success'):
        print(f"   Success: {lfpr['latest_value']}%")
    else:
        print(f"   Error: {lfpr.get('error')}")
