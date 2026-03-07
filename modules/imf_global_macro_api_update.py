#!/usr/bin/env python3
"""
IMF Global Macro API Update — Central Bank Policy Rates & Economic Forecasts

Targets IMF's 2026 updated APIs with comprehensive global macro data:
- Central bank policy rates (PRIMRATE, FPOLM datasets)
- WEO GDP and inflation forecasts
- Country macro profiles via DataMapper API
- Global economic outlook summaries

Source: https://data.imf.org/ | http://dataservices.imf.org/REST/SDMX_JSON.svc/
Category: Macro / Central Banks
Free tier: True (no API key required)
Update frequency: Monthly (WEO quarterly)
Author: QuantClaw Data NightBuilder
Phase: 105
"""

import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# ========== API CONFIGURATION ==========

# IMF SDMX API base (for policy rates and monetary data)
SDMX_BASE = "http://dataservices.imf.org/REST/SDMX_JSON.svc"

# IMF DataMapper API (for WEO forecasts and country profiles)
DATAMAPPER_BASE = "https://www.imf.org/external/datamapper/api/v1"

# Common country code mappings
ALPHA2_TO_ALPHA3 = {
    'US': 'USA', 'JP': 'JPN', 'DE': 'DEU', 'GB': 'GBR', 'FR': 'FRA',
    'CN': 'CHN', 'IN': 'IND', 'BR': 'BRA', 'CA': 'CAN', 'IT': 'ITA',
    'ES': 'ESP', 'AU': 'AUS', 'MX': 'MEX', 'KR': 'KOR', 'CH': 'CHE'
}

# WEO indicator codes
WEO_INDICATORS = {
    'NGDP_RPCH': 'Real GDP Growth (%)',
    'PCPIPCH': 'Inflation (CPI %)',
    'LUR': 'Unemployment Rate (%)',
    'NGDPD': 'Nominal GDP (USD billions)',
    'PPPGDP': 'GDP PPP (USD billions)',
    'GGXCNL_NGDP': 'Fiscal Balance (% GDP)',
    'GGXWDG_NGDP': 'Gross Debt (% GDP)',
    'BCA_NGDPD': 'Current Account Balance (% GDP)'
}

# ========== HELPER FUNCTIONS ==========

def _convert_country_code(country: str) -> str:
    """Convert Alpha-2 to Alpha-3 country code if needed."""
    code = country.upper()
    if len(code) == 2:
        return ALPHA2_TO_ALPHA3.get(code, code)
    return code


def _parse_sdmx_response(response_data: Dict, series_key: str = None) -> List[Dict]:
    """Parse SDMX JSON response to extract time series data."""
    try:
        if 'CompactData' not in response_data:
            return []
        
        compact_data = response_data['CompactData']
        if 'DataSet' not in compact_data:
            return []
        
        dataset = compact_data['DataSet']
        if not dataset or 'Series' not in dataset:
            return []
        
        series_list = dataset['Series']
        if not isinstance(series_list, list):
            series_list = [series_list]
        
        observations = []
        for series in series_list:
            if 'Obs' not in series:
                continue
            
            obs_list = series['Obs']
            if not isinstance(obs_list, list):
                obs_list = [obs_list]
            
            for obs in obs_list:
                try:
                    period = obs.get('@TIME_PERIOD', '')
                    value = obs.get('@OBS_VALUE', '')
                    if period and value:
                        observations.append({
                            'date': period,
                            'value': float(value) if value != '' else None
                        })
                except (ValueError, TypeError):
                    continue
        
        # Sort by date
        observations.sort(key=lambda x: x['date'])
        return observations
    
    except Exception as e:
        return []


# ========== POLICY RATES ==========

def get_policy_rates(country: str = "US") -> Dict:
    """
    Get central bank policy rates for a country.
    
    Uses IMF SDMX API to fetch policy rate data from IFS (International Financial Statistics).
    Dataset: IFS - FPOLM (Policy Rate, End of Period)
    
    Args:
        country: ISO Alpha-2 or Alpha-3 country code (default: "US")
    
    Returns:
        Dict with policy rate data, latest value, and historical series
    
    Example:
        >>> rates = get_policy_rates("US")
        >>> print(rates['latest_value'], rates['latest_date'])
    """
    try:
        country_code = _convert_country_code(country)
        
        # IFS dataset code for policy rates
        # Format: CompactData/{database}/{frequency}.{country}.{indicator}
        # FPOLM = Policy Rate, End of Period (Monthly)
        endpoint = f"{SDMX_BASE}/CompactData/IFS/M.{country_code}.FPOLM_PA"
        
        response = requests.get(endpoint, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        observations = _parse_sdmx_response(data)
        
        if not observations:
            # Fallback: try via DataMapper for recent data
            return _get_policy_rates_datamapper(country_code)
        
        # Filter valid observations
        valid_obs = [o for o in observations if o['value'] is not None]
        
        if not valid_obs:
            return {
                'success': False,
                'error': f'No policy rate data available for {country_code}',
                'country': country_code
            }
        
        latest = valid_obs[-1]
        
        # Calculate changes
        changes = {}
        if len(valid_obs) >= 2:
            prev_val = valid_obs[-2]['value']
            changes['period_change'] = latest['value'] - prev_val
        
        if len(valid_obs) >= 12:  # 1 year
            year_ago = valid_obs[-12]['value']
            changes['yoy_change'] = latest['value'] - year_ago
        
        return {
            'success': True,
            'country': country_code,
            'indicator': 'Policy Rate (End of Period)',
            'latest_value': latest['value'],
            'latest_date': latest['date'],
            'changes': changes,
            'observations': valid_obs[-24:],  # Last 2 years
            'source': 'IMF IFS SDMX API',
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'country': country
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'country': country
        }


def _get_policy_rates_datamapper(country_code: str) -> Dict:
    """Fallback: Get policy rates from DataMapper API."""
    try:
        # DataMapper doesn't have direct policy rates, so return graceful fallback
        return {
            'success': False,
            'error': f'Policy rate data not available via DataMapper for {country_code}',
            'country': country_code,
            'note': 'Try using FRED API for US policy rates or central bank sources'
        }
    except Exception as e:
        return {'success': False, 'error': str(e), 'country': country_code}


# ========== GDP FORECASTS ==========

def get_gdp_forecast(country: str = "US", year: int = 2026) -> Dict:
    """
    Get GDP growth forecast from World Economic Outlook (WEO).
    
    Args:
        country: ISO Alpha-2 or Alpha-3 country code (default: "US")
        year: Forecast year (default: 2026)
    
    Returns:
        Dict with GDP forecast, historical data, and trend
    
    Example:
        >>> forecast = get_gdp_forecast("US", 2026)
        >>> print(forecast['forecast_value'], forecast['forecast_year'])
    """
    try:
        country_code = _convert_country_code(country)
        
        # WEO endpoint for real GDP growth
        indicator = 'NGDP_RPCH'  # Real GDP Growth (%)
        endpoint = f"{DATAMAPPER_BASE}/{indicator}"
        
        response = requests.get(endpoint, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'values' not in data or indicator not in data['values']:
            return {
                'success': False,
                'error': 'No GDP forecast data in response',
                'country': country_code,
                'year': year
            }
        
        country_data = data['values'][indicator].get(country_code, {})
        
        if not country_data:
            return {
                'success': False,
                'error': f'No GDP data for country {country_code}',
                'country': country_code,
                'year': year
            }
        
        # Extract forecast for requested year
        forecast_value = country_data.get(str(year))
        
        # Get historical and recent data
        years_data = []
        for yr in sorted([int(y) for y in country_data.keys() if y.isdigit()]):
            val = country_data.get(str(yr))
            if val:
                years_data.append({
                    'year': yr,
                    'value': float(val),
                    'is_forecast': yr > datetime.now().year
                })
        
        # Calculate trend
        recent_years = [d for d in years_data if d['year'] >= datetime.now().year - 5]
        avg_growth = sum(d['value'] for d in recent_years) / len(recent_years) if recent_years else 0
        
        return {
            'success': True,
            'country': country_code,
            'indicator': 'Real GDP Growth (%)',
            'forecast_year': year,
            'forecast_value': float(forecast_value) if forecast_value else None,
            'historical_data': years_data,
            'avg_growth_5y': round(avg_growth, 2),
            'source': 'IMF World Economic Outlook',
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'country': country,
            'year': year
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'country': country,
            'year': year
        }


# ========== INFLATION FORECASTS ==========

def get_inflation_forecast(country: str = "US", year: int = 2026) -> Dict:
    """
    Get inflation (CPI) forecast from World Economic Outlook.
    
    Args:
        country: ISO Alpha-2 or Alpha-3 country code (default: "US")
        year: Forecast year (default: 2026)
    
    Returns:
        Dict with inflation forecast, historical data, and trend
    
    Example:
        >>> inflation = get_inflation_forecast("US", 2026)
        >>> print(inflation['forecast_value'], inflation['forecast_year'])
    """
    try:
        country_code = _convert_country_code(country)
        
        # WEO endpoint for inflation
        indicator = 'PCPIPCH'  # Inflation, average consumer prices (%)
        endpoint = f"{DATAMAPPER_BASE}/{indicator}"
        
        response = requests.get(endpoint, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        
        if 'values' not in data or indicator not in data['values']:
            return {
                'success': False,
                'error': 'No inflation forecast data in response',
                'country': country_code,
                'year': year
            }
        
        country_data = data['values'][indicator].get(country_code, {})
        
        if not country_data:
            return {
                'success': False,
                'error': f'No inflation data for country {country_code}',
                'country': country_code,
                'year': year
            }
        
        # Extract forecast for requested year
        forecast_value = country_data.get(str(year))
        
        # Get historical and forecast data
        years_data = []
        current_year = datetime.now().year
        for yr in sorted([int(y) for y in country_data.keys() if y.isdigit()]):
            val = country_data.get(str(yr))
            if val:
                years_data.append({
                    'year': yr,
                    'value': float(val),
                    'is_forecast': yr > current_year
                })
        
        # Calculate average inflation
        recent_years = [d for d in years_data if d['year'] >= current_year - 5 and d['year'] <= current_year]
        avg_inflation = sum(d['value'] for d in recent_years) / len(recent_years) if recent_years else 0
        
        return {
            'success': True,
            'country': country_code,
            'indicator': 'Inflation, Average Consumer Prices (%)',
            'forecast_year': year,
            'forecast_value': float(forecast_value) if forecast_value else None,
            'historical_data': years_data,
            'avg_inflation_5y': round(avg_inflation, 2),
            'source': 'IMF World Economic Outlook',
            'timestamp': datetime.now().isoformat()
        }
    
    except requests.RequestException as e:
        return {
            'success': False,
            'error': f'HTTP error: {str(e)}',
            'country': country,
            'year': year
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'country': country,
            'year': year
        }


# ========== COUNTRY MACRO PROFILE ==========

def get_country_macro_profile(country: str = "US") -> Dict:
    """
    Get comprehensive macro snapshot for a country.
    
    Includes GDP, inflation, unemployment, fiscal balance, debt, and current account.
    
    Args:
        country: ISO Alpha-2 or Alpha-3 country code (default: "US")
    
    Returns:
        Dict with comprehensive macro indicators and latest forecasts
    
    Example:
        >>> profile = get_country_macro_profile("US")
        >>> print(profile['indicators']['gdp_growth'])
    """
    try:
        country_code = _convert_country_code(country)
        
        profile = {
            'success': True,
            'country': country_code,
            'indicators': {},
            'timestamp': datetime.now().isoformat()
        }
        
        current_year = datetime.now().year
        
        # Fetch all key WEO indicators
        for indicator_code, indicator_name in WEO_INDICATORS.items():
            try:
                endpoint = f"{DATAMAPPER_BASE}/{indicator_code}"
                response = requests.get(endpoint, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if 'values' in data and indicator_code in data['values']:
                        country_data = data['values'][indicator_code].get(country_code, {})
                        
                        if country_data:
                            # Get latest available and forecast
                            latest_val = None
                            forecast_val = None
                            
                            for year in sorted([int(y) for y in country_data.keys() if y.isdigit()], reverse=True):
                                val = country_data.get(str(year))
                                if val:
                                    if year <= current_year and latest_val is None:
                                        latest_val = float(val)
                                    if year == current_year + 1 and forecast_val is None:
                                        forecast_val = float(val)
                                if latest_val and forecast_val:
                                    break
                            
                            profile['indicators'][indicator_code] = {
                                'name': indicator_name,
                                'latest_value': latest_val,
                                'forecast_next_year': forecast_val
                            }
            except Exception:
                continue  # Skip indicators that fail
        
        if not profile['indicators']:
            return {
                'success': False,
                'error': f'No macro data available for {country_code}',
                'country': country_code
            }
        
        return profile
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'country': country
        }


# ========== GLOBAL OUTLOOK ==========

def get_global_outlook() -> Dict:
    """
    Get global economic outlook summary.
    
    Returns world GDP growth and inflation forecasts for major economies.
    
    Returns:
        Dict with global growth forecast and regional breakdowns
    
    Example:
        >>> outlook = get_global_outlook()
        >>> print(outlook['world_gdp_growth'])
    """
    try:
        # Major economies to track
        major_economies = {
            'USA': 'United States',
            'CHN': 'China',
            'JPN': 'Japan',
            'DEU': 'Germany',
            'GBR': 'United Kingdom',
            'FRA': 'France',
            'IND': 'India'
        }
        
        current_year = datetime.now().year
        forecast_year = current_year + 1
        
        global_data = {
            'success': True,
            'world_gdp_growth': None,
            'world_inflation': None,
            'major_economies': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Get world aggregates
        try:
            endpoint = f"{DATAMAPPER_BASE}/NGDP_RPCH"
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and 'NGDP_RPCH' in data['values']:
                    world_data = data['values']['NGDP_RPCH'].get('001', {})  # 001 = World
                    if world_data:
                        global_data['world_gdp_growth'] = {
                            'current': float(world_data.get(str(current_year), 0)),
                            'forecast': float(world_data.get(str(forecast_year), 0))
                        }
        except Exception:
            pass
        
        # Get inflation for world
        try:
            endpoint = f"{DATAMAPPER_BASE}/PCPIPCH"
            response = requests.get(endpoint, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if 'values' in data and 'PCPIPCH' in data['values']:
                    world_data = data['values']['PCPIPCH'].get('001', {})
                    if world_data:
                        global_data['world_inflation'] = {
                            'current': float(world_data.get(str(current_year), 0)),
                            'forecast': float(world_data.get(str(forecast_year), 0))
                        }
        except Exception:
            pass
        
        # Get data for major economies
        for country_code, country_name in major_economies.items():
            profile = get_country_macro_profile(country_code)
            if profile.get('success'):
                global_data['major_economies'][country_code] = {
                    'name': country_name,
                    'gdp_growth': profile['indicators'].get('NGDP_RPCH', {}).get('forecast_next_year'),
                    'inflation': profile['indicators'].get('PCPIPCH', {}).get('forecast_next_year')
                }
        
        return global_data
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


# ========== UTILITY FUNCTIONS ==========

def list_indicators() -> List[Dict]:
    """
    List all available WEO indicators.
    
    Returns:
        List of indicator codes and descriptions
    """
    return [
        {'code': code, 'description': desc}
        for code, desc in WEO_INDICATORS.items()
    ]


# ========== CLI DEMO ==========

if __name__ == "__main__":
    print("=" * 70)
    print("IMF Global Macro API Update - Central Banks & Economic Forecasts")
    print("=" * 70)
    
    # Demo: US Policy Rates
    print("\n[1] Policy Rates (US):")
    rates = get_policy_rates("US")
    print(json.dumps(rates, indent=2))
    
    # Demo: US GDP Forecast
    print("\n[2] GDP Forecast (US, 2026):")
    gdp = get_gdp_forecast("US", 2026)
    print(json.dumps(gdp, indent=2))
    
    # Demo: US Inflation Forecast
    print("\n[3] Inflation Forecast (US, 2026):")
    inflation = get_inflation_forecast("US", 2026)
    print(json.dumps(inflation, indent=2))
    
    # Demo: US Macro Profile
    print("\n[4] Country Macro Profile (US):")
    profile = get_country_macro_profile("US")
    print(json.dumps(profile, indent=2))
    
    # Demo: Global Outlook
    print("\n[5] Global Economic Outlook:")
    outlook = get_global_outlook()
    print(json.dumps(outlook, indent=2))
    
    print("\n" + "=" * 70)
    print(f"Module: imf_global_macro_api_update | Functions: 5 core + 2 helpers")
    print("=" * 70)
